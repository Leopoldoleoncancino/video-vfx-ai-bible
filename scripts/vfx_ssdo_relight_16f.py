#!/usr/bin/env python3
"""Motor PBR Lineal Float32: SSDO 16-pasos (Blue-Noise) + Cook-Torrance GGX + SSS + Caída 1/d² (Módulo A).

Evolución de producción sobre el snippet base de `docs/02 §3.3`, diseñado para erradicar
simultáneamente las Fallas #1, #2, #3, #4 y #5b de `v10`:
- Normal Pass renormalizado (`N = normalize(N)`) + filtro bilateral guiado por luminancia del plate
  (recupera nitidez tras inferir `NormalCrafter --max-res 512` en `478x850`).
- SSDO raymarch de 16 pasos con jitter temporal tipo R2/Blue-Noise + suavizado bilateral guiado
  por Depth (elimina el *banding* de 8 pasos y produce sombras reales dedo-a-dedo).
- BRDF físico **Cook-Torrance GGX** diferenciado por material:
  * `matte_skin` (`roughness=0.34`, `F0=0.028`, `diffuse=1.0`, `SSS` cálido en borde `1 - N·V`).
  * `matte_fabric` (`roughness=0.88`, `F0=0.015`, `diffuse=0.14`, cero naranja plano en manga negra).
  * `desk_mask` opcional (`DA3-Streaming` / `SAM3`): caída estricta `1 / (1 + k * d²)` dentro del
    radio cercano de la mano; fondo blanco/impresora remoto permanece 100 % neutro (`CIEDE2000 <= 1.5`).
- Salida lineal HDR (`float32` `.npy` o OpenEXR 16F si `OpenEXR`/`cv2` está disponible) +
  preview opcional con curva **AgX** aproximada para evitar clipping amarillo pastel SDR.

Uso:
  python scripts/vfx_ssdo_relight_16f.py --self-test
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

try:
    import OpenEXR  # type: ignore
    import Imath  # type: ignore
except ImportError:
    OpenEXR = None
    Imath = None


def srgb_to_linear(x: np.ndarray) -> np.ndarray:
    x = np.clip(x.astype(np.float32), 0.0, None)
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4).astype(np.float32)


def linear_to_srgb(x: np.ndarray) -> np.ndarray:
    x = np.clip(x.astype(np.float32), 0.0, None)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * (x ** (1.0 / 2.4)) - 0.055).astype(np.float32)


def agx_filmic_tonemap(hdr_lin: np.ndarray, exposure_ev: float = 0.0) -> np.ndarray:
    """Aproximación limpia tipo AgX: desatura suavemente las altas luces > 1.0 hacia crema/blanco."""
    x = np.maximum(hdr_lin.astype(np.float32), 0.0) * (2.0 ** exposure_ev)
    # Matriz suave inset (evita amarillo pastel plano en R=1,G=1,B=0.2)
    m_inset = np.array(
        [
            [0.842479, 0.078433, 0.079224],
            [0.042328, 0.878469, 0.079166],
            [0.042376, 0.078434, 0.879143],
        ],
        dtype=np.float32,
    )
    x = x @ m_inset.T
    # Curva sigmoide log-cónica en dominio positivo
    eps = 1e-6
    x = np.maximum(x, eps)
    log_x = np.clip((np.log2(x) + 10.0) / 16.5, 0.0, 1.0)
    # Polinomio suave S-curve monotónico
    y = log_x * log_x * (3.0 - 2.0 * log_x)
    y = 0.5 * y + 0.5 * (y * y * (3.0 - 2.0 * y))
    m_out = np.linalg.inv(m_inset)
    out = np.clip(y @ m_out.T, 0.0, 1.0)
    return linear_to_srgb(out)


def joint_bilateral_guide_normals(
    normal_rgb: np.ndarray,
    guide_rgb: np.ndarray,
    radius: int = 2,
    sigma_space: float = 1.5,
    sigma_range: float = 0.08,
    invert_y: bool = False,
) -> np.ndarray:
    """Suaviza escalonamiento 8-bit/upscale de normales preservando aristas del plate y renormaliza."""
    N = normal_rgb.astype(np.float32) * 2.0 - 1.0
    if invert_y:
        N[..., 1] = -N[..., 1]
    N = N / np.maximum(np.linalg.norm(N, axis=-1, keepdims=True), 1e-5)

    if radius <= 0:
        return N

    h, w, _ = N.shape
    luma = (0.2126 * guide_rgb[..., 0] + 0.7152 * guide_rgb[..., 1] + 0.0722 * guide_rgb[..., 2]).astype(
        np.float32
    )
    pad_n = np.pad(N, ((radius, radius), (radius, radius), (0, 0)), mode="edge")
    pad_g = np.pad(luma, ((radius, radius), (radius, radius)), mode="edge")

    acc = np.zeros_like(N, dtype=np.float32)
    w_sum = np.zeros((h, w, 1), dtype=np.float32)
    inv_2ss = 1.0 / (2.0 * sigma_space * sigma_space)
    inv_2sr = 1.0 / (2.0 * sigma_range * sigma_range)

    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            ws = np.exp(-(dx * dx + dy * dy) * inv_2ss)
            g_nbr = pad_g[radius + dy : radius + dy + h, radius + dx : radius + dx + w]
            dg = g_nbr - luma
            wr = np.exp(-(dg * dg) * inv_2sr) * ws
            n_nbr = pad_n[radius + dy : radius + dy + h, radius + dx : radius + dx + w, :]
            acc += n_nbr * wr[..., None]
            w_sum += wr[..., None]

    out = acc / np.maximum(w_sum, 1e-5)
    return out / np.maximum(np.linalg.norm(out, axis=-1, keepdims=True), 1e-5)


def _r2_blue_jitter(h: int, w: int, frame_idx: int) -> np.ndarray:
    """Genera ruido temporal tipo R2 (low-discrepancy quasirandom) para romper banding en SSDO."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    # Constantes R2 Roberts + desfase dorado temporal
    phi = (xx * 0.7548776662 + yy * 0.5698402910 + frame_idx * 0.6180339887) % 1.0
    return phi.astype(np.float32)


def _depth_bilateral_smooth(val: np.ndarray, depth: np.ndarray, radius: int = 2, sigma_z: float = 0.04) -> np.ndarray:
    if radius <= 0:
        return val
    h, w = val.shape
    pv = np.pad(val, ((radius, radius), (radius, radius)), mode="edge")
    pz = np.pad(depth, ((radius, radius), (radius, radius)), mode="edge")
    acc = np.zeros_like(val, dtype=np.float32)
    wsum = np.zeros_like(val, dtype=np.float32)
    inv_2sz = 1.0 / (2.0 * sigma_z * sigma_z)
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            dz = pz[radius + dy : radius + dy + h, radius + dx : radius + dx + w] - depth
            wt = np.exp(-(dz * dz) * inv_2sz) * (1.0 / (1.0 + dx * dx + dy * dy))
            acc += pv[radius + dy : radius + dy + h, radius + dx : radius + dx + w] * wt
            wsum += wt
    return acc / np.maximum(wsum, 1e-5)


def compute_ssdo_pbr_relight(
    plate_lin: np.ndarray,
    normal_rgb: np.ndarray,
    depth_map: np.ndarray,
    matte_skin: np.ndarray,
    matte_fabric: np.ndarray,
    lights_uvz: List[Tuple[float, float, float, float]],
    desk_mask: Optional[np.ndarray] = None,
    frame_idx: int = 0,
    fire_color_lin: Tuple[float, float, float] = (1.0, 0.34, 0.045),
    radius_uv: float = 0.55,
    depth_scale: float = 0.35,
    invert_normal_y: bool = False,
    shadow_steps: int = 16,
    depth_bias: float = 0.012,
    refine_normals: bool = True,
) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
    """Calcula pase lineal HDR de relighting PBR (SSDO + Cook-Torrance GGX + SSS + caída mesa).

    `depth_scale` escala el relieve Z normalizado del sujeto [0..1] a unidades proporcionales al UV
    (p. ej. ~0.35 anchos de encuadre para una mano vertical `478x850`), de modo que `lights_uvz`
    tenga z en rango `[0.0 .. depth_scale + 0.18]` sin comprimir en exceso el eje Z ni cortar `radius_uv`.
    """
    h, w = depth_map.shape
    depth = depth_map.astype(np.float32)
    subj = np.maximum(matte_skin, matte_fabric) > 0.25
    if np.any(subj):
        z_min = float(np.percentile(depth[subj], 2))
        z_max = float(np.percentile(depth[subj], 98))
        span = max(z_max - z_min, 1e-4)
        depth_norm = np.clip((depth - z_min) / span, 0.0, 1.2) * depth_scale
    else:
        depth_norm = np.clip(depth, 0.0, 1.0) * depth_scale

    if refine_normals:
        N = joint_bilateral_guide_normals(normal_rgb, plate_lin, radius=1, invert_y=invert_normal_y)
    else:
        N = normal_rgb.astype(np.float32) * 2.0 - 1.0
        if invert_normal_y:
            N[..., 1] = -N[..., 1]
        N = N / np.maximum(np.linalg.norm(N, axis=-1, keepdims=True), 1e-5)

    uu, vv = np.meshgrid(
        np.linspace(0.0, 1.0, w, dtype=np.float32),
        np.linspace(0.0, 1.0, h, dtype=np.float32),
    )
    jitter = _r2_blue_jitter(h, w, frame_idx)

    skin = np.clip(matte_skin.astype(np.float32), 0.0, 1.0)
    fabric = np.clip(matte_fabric.astype(np.float32), 0.0, 1.0)
    desk = np.clip(desk_mask.astype(np.float32), 0.0, 1.0) if desk_mask is not None else np.zeros((h, w), dtype=np.float32)

    # Pesos PBR estrictos por material (erradica sangrado naranja en puño negro)
    roughness = np.clip(0.34 * skin + 0.88 * fabric + 0.65 * (1.0 - np.maximum(skin, fabric)), 0.08, 0.99)
    alpha_ggx = roughness * roughness
    f0 = 0.028 * skin + 0.015 * fabric + 0.02 * (1.0 - np.maximum(skin, fabric))
    diff_weight = 1.00 * skin + 0.14 * fabric + 0.35 * desk
    spec_scale = 0.65 * skin + 0.04 * fabric + 0.08 * desk

    fire_col = np.array(fire_color_lin, dtype=np.float32)[None, None, :]
    sss_col = np.array([1.0, 0.14, 0.015], dtype=np.float32)[None, None, :]

    ndotv = np.clip(N[..., 2], 1e-3, 1.0)  # Vista V = (0, 0, 1)
    total_diff = np.zeros_like(plate_lin, dtype=np.float32)
    total_spec = np.zeros_like(plate_lin, dtype=np.float32)
    vis_accum = np.zeros((h, w), dtype=np.float32)
    weight_accum = np.zeros((h, w), dtype=np.float32)

    for lu, lv, lz, l_strength in lights_uvz:
        dx = lu - uu
        dy = lv - vv
        dz = lz - depth_norm
        dist = np.sqrt(dx * dx + dy * dy + dz * dz) + 1e-5
        lx, ly, lz_dir = dx / dist, dy / dist, dz / dist

        # Caída física suave 1/d² combinada con ventana de radio (cero tinte lejano en escritorio)
        falloff_inv2 = 1.0 / (1.0 + (dist / max(radius_uv * 0.35, 1e-3)) ** 2)
        window = np.clip(1.0 - (dist / max(radius_uv, 1e-3)) ** 2, 0.0, 1.0) ** 2
        atten = falloff_inv2 * window * l_strength

        # 16-pasos SSDO con Blue-Noise temporal jitter + suavizado guiado por profundidad
        vis = np.ones((h, w), dtype=np.float32)
        for s in range(shadow_steps):
            t = (s + 0.2 + 0.6 * jitter) / float(shadow_steps)
            sx = np.clip((uu + dx * t) * (w - 1), 0.0, w - 1.0)
            sy = np.clip((vv + dy * t) * (h - 1), 0.0, h - 1.0)
            sx_i = np.rint(sx).astype(np.int32)
            sy_i = np.rint(sy).astype(np.int32)
            ray_z = depth_norm + dz * t
            z_delta = depth_norm[sy_i, sx_i] - ray_z
            hit = (z_delta > depth_bias) & (z_delta < depth_scale * 0.95) & (t > 0.12)
            vis = np.where(hit, vis * 0.52, vis)

        vis = _depth_bilateral_smooth(vis, depth_norm, radius=1, sigma_z=max(0.02, 0.12 * depth_scale))

        ndotl = np.clip(N[..., 0] * lx + N[..., 1] * ly + N[..., 2] * lz_dir, 0.0, 1.0)

        # Cook-Torrance Microfacet GGX (D * F * G / (4 * NdotV * NdotL))
        hx, hy, hz = lx, ly, lz_dir + 1.0
        hlen = np.sqrt(hx * hx + hy * hy + hz * hz) + 1e-5
        hx, hy, hz = hx / hlen, hy / hlen, hz / hlen
        ndoth = np.clip(N[..., 0] * hx + N[..., 1] * hy + N[..., 2] * hz, 0.0, 1.0)
        vdoth = np.clip(hz, 0.0, 1.0)

        a2 = alpha_ggx * alpha_ggx
        denom_d = (ndoth * ndoth * (a2 - 1.0) + 1.0)
        D_ggx = a2 / (np.pi * np.maximum(denom_d * denom_d, 1e-5))
        F_schlick = f0 + (1.0 - f0) * ((1.0 - vdoth) ** 5)
        k_smith = ((roughness + 1.0) ** 2) / 8.0
        G_v = ndotv / (ndotv * (1.0 - k_smith) + k_smith)
        G_l = ndotl / np.maximum(ndotl * (1.0 - k_smith) + k_smith, 1e-4)
        spec_brdf = (D_ggx * F_schlick * G_v * G_l) / np.maximum(4.0 * ndotv, 1e-3)
        # Normalizado para estabilidad HDR en piel aceitosa sin explotar en grazing angles
        spec_term = np.clip(spec_brdf * ndotl, 0.0, 12.0) * spec_scale

        # Subsurface Scattering cálido en bordes rasantes solo en piel
        wrap_ndotl = np.clip((N[..., 0] * lx + N[..., 1] * ly + N[..., 2] * lz_dir + 0.45) / 1.45, 0.0, 1.0)
        sss_term = ((1.0 - ndotv) ** 2.5) * wrap_ndotl * skin * 0.42

        total_diff += (fire_col * (ndotl * diff_weight)[..., None] + sss_col * sss_term[..., None]) * (atten * vis)[..., None]
        total_spec += fire_col * (spec_term * atten * vis)[..., None]
        vis_accum += vis * atten
        weight_accum += atten

    # Albedo del plate recibe luz difusa multiplicativa + especular aditivo físico HDR
    relit_lin = plate_lin + plate_lin * total_diff + total_spec
    aux = {
        "N": N,
        "visibility": np.where(weight_accum > 1e-5, vis_accum / np.maximum(weight_accum, 1e-5), 1.0),
        "diffuse_light": total_diff,
        "specular_light": total_spec,
    }
    return relit_lin.astype(np.float32), aux


def save_exr_or_npy(path: Path, arr: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".exr" and OpenEXR is not None and Imath is not None:
        h, w = arr.shape[:2]
        hdr = OpenEXR.Header(w, h)
        half = Imath.PixelType(Imath.PixelType.HALF)
        hdr["channels"] = {c: Imath.Channel(half) for c in ("R", "G", "B")}
        exr = OpenEXR.OutputFile(str(path), hdr)
        f16 = arr.astype(np.float16)
        exr.writePixels({"R": f16[..., 0].tobytes(), "G": f16[..., 1].tobytes(), "B": f16[..., 2].tobytes()})
        exr.close()
    else:
        np.save(path.with_suffix(".npy"), arr.astype(np.float32))


def run_self_test() -> int:
    """Verifica unit-normales, oclusión dedo-a-dedo (>=3.5:1), anti-sangrado tela y neutralidad mesa."""
    h, w = 128, 128
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    u = xx / (w - 1)
    v = yy / (h - 1)

    plate = np.full((h, w, 3), 0.25, dtype=np.float32)
    # Manga negra en esquina inferior izquierda, escritorio blanco en banda superior derecha
    matte_fabric = ((u < 0.25) & (v > 0.72)).astype(np.float32)
    matte_skin = (((u >= 0.40) & (u <= 0.76) & (v >= 0.25) & (v <= 0.78))).astype(np.float32)
    desk_mask = ((u >= 0.05) & (v <= 0.20)).astype(np.float32)

    plate[matte_fabric > 0.5] = 0.05
    plate[desk_mask > 0.5] = 0.85

    depth = np.full((h, w), 0.15, dtype=np.float32)
    # Dedo frontal oclusor alto en u in [0.42, 0.54]
    depth[(u >= 0.42) & (u <= 0.54) & (matte_skin > 0.5)] = 0.90
    # Dedo trasero en u in [0.58, 0.72] (dentro del radio de luz para validar oclusión real)
    depth[(u >= 0.58) & (u <= 0.72) & (matte_skin > 0.5)] = 0.42

    # Normales OpenGL +Y mirando hacia cámara y levemente hacia la fuente izquierda (-0.35, 0, 0.937)
    nx = np.full((h, w), -0.35, dtype=np.float32)
    ny = np.zeros((h, w), dtype=np.float32)
    nz = np.full((h, w), 0.937, dtype=np.float32)
    norm_packed = np.stack([nx, ny, nz], axis=-1) * 0.5 + 0.5

    # Luz situada delante del dedo frontal (z = 0.42 en unidades depth_scale=0.35, donde dedo=0.35)
    lights = [(0.34, 0.50, 0.42, 3.2)]
    relit, aux = compute_ssdo_pbr_relight(
        plate,
        norm_packed,
        depth,
        matte_skin,
        matte_fabric,
        lights,
        desk_mask=desk_mask,
        radius_uv=0.50,
        depth_scale=0.35,
        shadow_steps=16,
        refine_normals=True,
    )

    n_norms = np.linalg.norm(aux["N"], axis=-1)
    assert float(n_norms.min()) > 0.99 and float(n_norms.max()) < 1.01, "Normales fuera de longitud unitaria"

    front_roi = (u >= 0.43) & (u <= 0.52) & (v >= 0.42) & (v <= 0.58)
    shadow_roi = (u >= 0.59) & (u <= 0.68) & (v >= 0.42) & (v <= 0.58)
    diff_front = float(np.mean(aux["diffuse_light"][front_roi, 0]))
    diff_shadow = float(np.mean(aux["diffuse_light"][shadow_roi, 0]))
    contrast = diff_front / max(diff_shadow, 1e-5)
    assert contrast >= 3.5, f"Oclusión SSDO insuficiente ({contrast:.2f}:1 < 3.5:1)"

    # Anti-sangrado en manga negra fuera del radio cercano
    fabric_gain = float(np.mean(relit[matte_fabric > 0.5, 0] / np.maximum(plate[matte_fabric > 0.5, 0], 1e-4)))
    assert fabric_gain <= 1.15, f"Sangrado detectado en tela negra: {fabric_gain:.3f}x"

    # Neutralidad del escritorio lejano (distancia > radius_uv=0.50)
    far_desk = (u > 0.85) & (v < 0.15)
    max_shift = float(np.max(np.abs(relit[far_desk] - plate[far_desk])))
    assert max_shift < 1e-5, f"Contaminación indebida en escritorio remoto: {max_shift}"

    agx_preview = agx_filmic_tonemap(relit)
    assert agx_preview.min() >= 0.0 and agx_preview.max() <= 1.0

    print(
        "[SELF-TEST OK] vfx_ssdo_relight_16f.py ->",
        json.dumps(
            {
                "unit_norm_range": [round(float(n_norms.min()), 4), round(float(n_norms.max()), 4)],
                "ssdo_occlusion_contrast": round(contrast, 2),
                "fabric_orange_gain": round(fabric_gain, 4),
                "far_desk_shift": max_shift,
                "peak_hdr_linear": round(float(relit.max()), 3),
            }
        ),
    )
    return 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Relighting Lineal PBR 16F (SSDO 16-step + GGX + SSS)")
    p.add_argument("--plate", type=Path, help="Imagen/frame lineal .npy o sRGB .png")
    p.add_argument("--normal", type=Path, help="Normal map .npy o .png (Camera Space)")
    p.add_argument("--depth", type=Path, help="Depth map 16F .npy o .png")
    p.add_argument("--skin-matte", type=Path, help="Máscara piel [0..1]")
    p.add_argument("--fabric-matte", type=Path, help="Máscara tela [0..1]")
    p.add_argument("--desk-mask", type=Path, default=None, help="Opcional: máscara escritorio DA3/SAM3")
    p.add_argument("--lights-json", type=Path, help="JSON con lista de luces [[u,v,z,strength], ...]")
    p.add_argument("--out", type=Path, default=Path("relit_hdr.npy"), help="Salida .exr o .npy")
    p.add_argument("--preview-png", type=Path, default=None, help="Opcional: preview AgX sRGB PNG")
    p.add_argument("--invert-y", action="store_true", help="Si el normal viene en DirectX -Y")
    p.add_argument("--shadow-steps", type=int, default=16)
    p.add_argument("--self-test", action="store_true")
    return p.parse_args()


def _read_arr(path: Path, is_srgb_img: bool = False) -> np.ndarray:
    if path.suffix.lower() == ".npy":
        return np.load(path).astype(np.float32)
    img = Image.open(path)
    arr = np.asarray(img, dtype=np.float32) / 255.0
    return srgb_to_linear(arr) if is_srgb_img else arr


def main() -> int:
    args = parse_args()
    if args.self_test:
        return run_self_test()

    required = [args.plate, args.normal, args.depth, args.skin_matte, args.fabric_matte, args.lights_json]
    if any(x is None for x in required):
        print("ERROR: Faltan argumentos requeridos (o ejecuta --self-test).", file=sys.stderr)
        return 1

    plate = _read_arr(args.plate, is_srgb_img=(args.plate.suffix.lower() != ".npy"))[..., :3]
    normal = _read_arr(args.normal, is_srgb_img=False)[..., :3]
    depth = _read_arr(args.depth, is_srgb_img=False)
    if depth.ndim == 3:
        depth = depth[..., 0]
    skin = _read_arr(args.skin_matte, is_srgb_img=False)
    if skin.ndim == 3:
        skin = skin[..., 0]
    fabric = _read_arr(args.fabric_matte, is_srgb_img=False)
    if fabric.ndim == 3:
        fabric = fabric[..., 0]
    desk = None
    if args.desk_mask is not None:
        desk = _read_arr(args.desk_mask, is_srgb_img=False)
        if desk.ndim == 3:
            desk = desk[..., 0]

    lights_raw = json.loads(args.lights_json.read_text(encoding="utf-8"))
    lights = [tuple(map(float, item)) for item in lights_raw]

    relit_lin, _ = compute_ssdo_pbr_relight(
        plate,
        normal,
        depth,
        skin,
        fabric,
        lights,
        desk_mask=desk,
        invert_normal_y=args.invert_y,
        shadow_steps=args.shadow_steps,
    )
    save_exr_or_npy(args.out, relit_lin)
    if args.preview_png is not None:
        prev = np.clip(np.round(agx_filmic_tonemap(relit_lin) * 255.0), 0, 255).astype(np.uint8)
        args.preview_png.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(prev, mode="RGB").save(args.preview_png)
    print(f"[OK] Relighting HDR lineal guardado en {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
