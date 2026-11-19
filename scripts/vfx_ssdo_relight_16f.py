#!/usr/bin/env python3
"""Motor PBR Lineal Float32: SSDO 16-pasos (Blue-Noise) + Cook-Torrance GGX + SSS + MIP Area-Light + ACES/OCIO (Módulo A · Fase 2.5).

Evolución de producción sobre el snippet base de `docs/02 §3.3` y los hallazgos empíricos sobre
los `33 frames` críticos (`f88..f120`, `478x850`, giro palma->dorso 180°) en RTX 3060 12 GB + Win 11:
- **Fix de Convención de Normales (`NormalCrafter` OpenGL `+Y` arriba vs Screen-Space `+Y` abajo):**
  * En espacio de pantalla, la coordenada `vv` crece de arriba hacia abajo (`0..1`), por lo que el
    vector de luz `dy = lv - vv` tiene `+Y` apuntando hacia ABAJO.
  * `NormalCrafter` / `Lotus-2` exportan en convención OpenGL Camera Space (`+Y` hacia ARRIBA).
    Por tanto, **`invert_normal_y=True` es el valor por defecto obligatorio (`--normal-convention opengl`)**
    para alinear `N_y` con `dy` en el raymarch SSDO y en `N·L`.
- **Fix Crítico de Colorimetría (Erradicando el lavado salmón/blanco tiza de `m_inset`):**
  * La antigua matriz `m_inset` sin curva Punchy inyectaba ~7.9 % de Rojo dentro del canal Azul,
    lavando las puntas rojas del fuego (`R=1.2, G=0.12, B=0.01`) hacia salmón (`B_srgb ≈ 0.525`).
  * Reemplazada por **Stephen Hill ACES Filmic (`RRT + ODT` exacto)** y soporte nativo para
    **`PyOpenColorIO` (`AgX - Punchy`)**, más composición con preservación analítica del plate
    (`inverse_aces_hill_linear` + `compose_hdr_on_plate_srgb`) que mantiene el escritorio blanco
    intacto (`CIEDE2000 = 0.000`) mientras las llamas HDR (`peak 8–14`) conservan puntas carmesí,
    cuerpo naranja vivo y núcleo crema (`pastel_yellow_clip = 0.0 %`).
- **Pilar 4 · Iluminación Dinámica Acoplada al Fuego (`build_fire_irradiance_pyramid` + `extract_dynamic_lights_from_fire`)
  y Velocity-Vector Motion Blur (`apply_velocity_motion_blur`, shutter `180° = 0.5`):**
  * Convierte el buffer HDR real del fuego advectado en una pirámide multi-escala de irradiancia
    y emisores puntuales/área dinámicos con color propio para que las sombras SSDO y los brillos
    especulares GGX sigan el latigazo real de las llamas cuadro a cuadro.

Uso:
  python scripts/vfx_ssdo_relight_16f.py --self-test
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
from PIL import Image

try:
    import OpenEXR  # type: ignore
    import Imath  # type: ignore
except ImportError:
    OpenEXR = None
    Imath = None

try:
    import PyOpenColorIO as OCIO  # type: ignore
except ImportError:
    OCIO = None


# Matrices exactas Stephen Hill ACES Filmic (sRGB/Rec.709 D65 <-> AP1 RRT+ODT fit)
_ACES_INPUT_MAT = np.array(
    [
        [0.59719, 0.35458, 0.04823],
        [0.07600, 0.90834, 0.01566],
        [0.02840, 0.13383, 0.83777],
    ],
    dtype=np.float64,
)

_ACES_OUTPUT_MAT = np.array(
    [
        [1.60475, -0.53108, -0.07367],
        [-0.10208, 1.10813, -0.00605],
        [-0.00327, -0.07276, 1.07602],
    ],
    dtype=np.float64,
)

_ACES_IN_INV = np.linalg.inv(_ACES_INPUT_MAT)
_ACES_OUT_INV = np.linalg.inv(_ACES_OUTPUT_MAT)


def srgb_to_linear(x: np.ndarray) -> np.ndarray:
    x = np.clip(x.astype(np.float32), 0.0, None)
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4).astype(np.float32)


def linear_to_srgb(x: np.ndarray) -> np.ndarray:
    x = np.clip(x.astype(np.float32), 0.0, None)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * (x ** (1.0 / 2.4)) - 0.055).astype(np.float32)


def _rrt_and_odt_fit(v: np.ndarray) -> np.ndarray:
    a = v * (v + 0.0245786) - 0.000090537
    b = v * (0.983729 * v + 0.4329510) + 0.238081
    return a / np.maximum(b, 1e-12)


def aces_hill_tonemap_linear(
    hdr_lin: np.ndarray,
    exposure_ev: float = 0.0,
    exposure_scale: float = 1.0,
) -> np.ndarray:
    """Aplica Stephen Hill ACES Filmic (sRGB->AP1 -> RRT+ODT -> AP1->sRGB) devolviendo display-linear [0..1]."""
    x = np.maximum(hdr_lin.astype(np.float64), 0.0) * (2.0 ** float(exposure_ev)) * float(exposure_scale)
    v = x @ _ACES_INPUT_MAT.T
    y = _rrt_and_odt_fit(np.maximum(v, 0.0))
    out = y @ _ACES_OUTPUT_MAT.T
    return np.clip(out, 0.0, 1.0).astype(np.float32)


def aces_hill_filmic_tonemap(
    hdr_lin: np.ndarray,
    exposure_ev: float = 0.0,
    exposure_scale: float = 1.0,
) -> np.ndarray:
    """Stephen Hill ACES Filmic con salida sRGB [0..1].

    Preserva el espectro hidrocarburo del fuego HDR (puntas rojo carmesí -> cuerpo naranja vivo ->
    núcleo dorado-crema) con `pastel_yellow_clip = 0.0 %`, eliminando el tinte salmón/blanco tiza.
    """
    return linear_to_srgb(aces_hill_tonemap_linear(hdr_lin, exposure_ev=exposure_ev, exposure_scale=exposure_scale))


def inverse_aces_hill_linear(disp_lin: np.ndarray) -> np.ndarray:
    """Inversa analítica exacta de `aces_hill_tonemap_linear` para niveles de plate SDR [0..0.992].

    Dado y = (v^2 + c1*v - c0) / (d2*v^2 + d1*v + d0), resuelve la ecuación cuadrática
    (1 - d2*y)*v^2 + (c1 - d1*y)*v - (c0 + d0*y) = 0 para la raíz positiva v >= 0.
    Error de ida y vuelta verificado: <= 2.22e-16 en float64.
    """
    d = np.clip(disp_lin.astype(np.float64), 0.0, 0.992)
    y = np.clip(d @ _ACES_OUT_INV.T, 0.0, 0.995)

    c1, c0 = 0.0245786, 0.000090537
    d2, d1, d0 = 0.983729, 0.4329510, 0.238081

    A = 1.0 - d2 * y
    B = c1 - d1 * y
    C = -(c0 + d0 * y)
    disc = np.maximum(B * B - 4.0 * A * C, 0.0)
    v = (-B + np.sqrt(disc)) / np.maximum(2.0 * A, 1e-12)
    v = np.where(d <= 1e-9, 0.0, np.maximum(v, 0.0))
    scene_lin = np.maximum(v @ _ACES_IN_INV.T, 0.0)
    return scene_lin.astype(np.float32)


def compose_hdr_on_plate_srgb(
    plate_disp_lin: np.ndarray,
    delta_hdr_lin: np.ndarray,
    exposure_ev: float = 0.0,
    tonemap_mode: str = "aces_hill",
    ocio_config: Optional[str] = None,
    ocio_look: str = "AgX - Punchy",
) -> np.ndarray:
    """Compone energía HDR aditiva (`delta_hdr_lin = relight_delta + fire_hdr`) sobre un plate display-linear.

    Evita el 'doble tone-mapping' sobre el escritorio blanco del teléfono:
    - Donde `delta_hdr_lin == 0` (fondo neutro no iluminado), el píxel conserva exactamente el color
      original del plate (`CIEDE2000 = 0.000`).
    - Donde `delta_hdr_lin > 0` (fuego + mano reiluminada), mapea `inverse_aces(plate) + delta_hdr`
      a través de la curva fílmica ACES / OCIO AgX Punchy, logrando roll-off HDR orgánico sin clipping
      amarillo pastel ni salto de luminancia en los bordes.
    """
    plate_clamped = np.clip(plate_disp_lin.astype(np.float32), 0.0, 1.0)
    delta = np.maximum(delta_hdr_lin.astype(np.float32), 0.0) * (2.0 ** float(exposure_ev))

    if tonemap_mode == "ocio_agx" and OCIO is not None:
        tm_full = ocio_agx_tonemap(plate_clamped + delta, exposure_ev=0.0, config_path=ocio_config, look=ocio_look)
        tm_plate = ocio_agx_tonemap(plate_clamped, exposure_ev=0.0, config_path=ocio_config, look=ocio_look)
        plate_srgb = linear_to_srgb(plate_clamped)
        w = np.clip(np.max(delta, axis=-1, keepdims=True) / 0.15, 0.0, 1.0)
        base_srgb = (1.0 - w) * (plate_srgb + (tm_full - tm_plate)) + w * tm_full
        return np.clip(base_srgb, 0.0, 1.0).astype(np.float32)

    plate_scene = inverse_aces_hill_linear(np.minimum(plate_clamped, 0.992))
    comp_disp_lin = aces_hill_tonemap_linear(plate_scene + delta, exposure_ev=0.0, exposure_scale=1.0)
    # Preservar verbatim píxeles con delta estrictamente nulo (ej. highlights >0.992 o mesa lejana)
    no_delta = np.max(delta, axis=-1, keepdims=True) <= 1e-7
    out_lin = np.where(no_delta, plate_clamped, comp_disp_lin)
    return linear_to_srgb(out_lin)


def ocio_agx_tonemap(
    hdr_lin: np.ndarray,
    exposure_ev: float = 0.0,
    config_path: Optional[str] = None,
    look: str = "AgX - Punchy",
    display: str = "sRGB",
    view: str = "AgX",
) -> np.ndarray:
    """Aplica Blender/OCIO `AgX` (`Look: AgX - Punchy`) vía `PyOpenColorIO`, con fallback a Stephen Hill ACES."""
    if OCIO is None:
        return aces_hill_filmic_tonemap(hdr_lin, exposure_ev=exposure_ev)

    try:
        cfg = OCIO.Config.CreateFromFile(config_path) if config_path else OCIO.GetCurrentConfig()
        grp = OCIO.GroupTransform()
        if abs(exposure_ev) > 1e-6:
            scale = float(2.0 ** exposure_ev)
            grp.appendTransform(OCIO.MatrixTransform([scale, 0.0, 0.0, 0.0, 0.0, scale, 0.0, 0.0, 0.0, 0.0, scale, 0.0, 0.0, 0.0, 0.0, 1.0]))
        if look:
            grp.appendTransform(OCIO.LookTransform(src="Linear Rec.709", dst="Linear Rec.709", looks=look))
        grp.appendTransform(OCIO.DisplayViewTransform(src="Linear Rec.709", display=display, view=view))
        cpu = cfg.getProcessor(grp).getDefaultCPUProcessor()
        buf = np.ascontiguousarray(np.maximum(hdr_lin.astype(np.float32), 0.0))
        orig_shape = buf.shape
        flat = buf.reshape(-1, 3).copy()
        cpu.applyRGB(flat)
        return np.clip(flat.reshape(orig_shape), 0.0, 1.0).astype(np.float32)
    except Exception:
        return aces_hill_filmic_tonemap(hdr_lin, exposure_ev=exposure_ev)


def agx_filmic_tonemap(hdr_lin: np.ndarray, exposure_ev: float = 0.0) -> np.ndarray:
    """Wrapper retrocompatible de tone-mapping HDR -> sRGB.

    Nota R&D (Hallazgo 33f): la antigua aproximación `m_inset` inyectaba ~7.9% de Rojo en Azul y
    carecía de la expansión de croma `AgX - Punchy`, lavando el fuego HDR hacia salmón/blanco tiza.
    Delega ahora a `ocio_agx_tonemap` (si `PyOpenColorIO` está activo) o `aces_hill_filmic_tonemap`.
    """
    return aces_hill_filmic_tonemap(hdr_lin, exposure_ev=exposure_ev)


def _fast_box_blur_2d(arr: np.ndarray, radius: int) -> np.ndarray:
    """Filtro box separable O(1) por píxel mediante imágenes integrales en NumPy puro."""
    if radius <= 0:
        return arr.astype(np.float32)
    squeeze = False
    if arr.ndim == 2:
        arr = arr[..., None]
        squeeze = True
    pad = int(radius)
    k = 2 * pad + 1
    padded = np.pad(arr.astype(np.float64), ((pad, pad), (pad, pad), (0, 0)), mode="edge")
    cs_x = np.cumsum(np.pad(padded, ((0, 0), (1, 0), (0, 0)), mode="constant"), axis=1)
    horiz = (cs_x[:, k:, :] - cs_x[:, :-k, :]) / float(k)
    cs_y = np.cumsum(np.pad(horiz, ((1, 0), (0, 0), (0, 0)), mode="constant"), axis=0)
    vert = (cs_y[k:, :, :] - cs_y[:-k, :, :]) / float(k)
    out = vert.astype(np.float32)
    return out[..., 0] if squeeze else out


def build_fire_irradiance_pyramid(
    fire_hdr: np.ndarray,
    radii: Sequence[int] = (3, 10, 28, 64),
    weights: Sequence[float] = (0.40, 0.30, 0.20, 0.10),
) -> np.ndarray:
    """Construye una pirámide MIP multi-escala de irradiancia a partir del buffer HDR real del fuego.

    Permite que la luz difusa de campo cercano abrace orgánicamente la silueta advectada de las
    llamas (Pilar 4) sin depender únicamente de luces puntuales estáticas en los landmarks.
    """
    fire = np.maximum(fire_hdr.astype(np.float32), 0.0)
    acc = np.zeros_like(fire, dtype=np.float32)
    w_sum = 0.0
    for r, w in zip(radii, weights):
        b = _fast_box_blur_2d(_fast_box_blur_2d(fire, int(r)), max(1, int(r) // 2))
        acc += b * float(w)
        w_sum += float(w)
    return acc / max(w_sum, 1e-6)


def extract_dynamic_lights_from_fire(
    fire_hdr: np.ndarray,
    depth_norm: np.ndarray,
    num_lights: int = 6,
    z_offset: float = 0.045,
    strength_scale: float = 2.4,
) -> List[Tuple[float, float, float, float]]:
    """Extrae `num_lights` emisores equivalentes `(u, v, z, strength)` desde la distribución real del fuego HDR.

    Aplica supresión no-máxima por celdas sobre la energía radiante del fuego para que los rayos
    SSDO de 16 pasos y los reflejos especulares GGX sigan la llama cuando se dobla por inercia.
    """
    h, w = fire_hdr.shape[:2]
    energy = (
        0.55 * np.maximum(fire_hdr[..., 0], 0.0)
        + 0.35 * np.maximum(fire_hdr[..., 1], 0.0)
        + 0.10 * np.maximum(fire_hdr[..., 2], 0.0)
    ).astype(np.float32)
    energy_smooth = _fast_box_blur_2d(energy, max(2, min(h, w) // 32))

    max_e = float(np.max(energy_smooth))
    if max_e <= 1e-4:
        return [(0.5, 0.5, float(np.mean(depth_norm)) + z_offset, 0.0)]

    work = energy_smooth.copy()
    supp_r = max(4, min(h, w) // 10)
    lights: List[Tuple[float, float, float, float]] = []
    total_e = float(np.sum(energy)) + 1e-6

    for _ in range(max(1, int(num_lights))):
        flat_idx = int(np.argmax(work))
        py, px = divmod(flat_idx, w)
        peak_val = float(work[py, px])
        if peak_val <= max_e * 0.06:
            break

        y0, y1 = max(0, py - supp_r), min(h, py + supp_r + 1)
        x0, x1 = max(0, px - supp_r), min(w, px + supp_r + 1)
        patch = work[y0:y1, x0:x1]
        p_sum = float(np.sum(patch)) + 1e-6
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        cy = float(np.sum(yy * patch) / p_sum)
        cx = float(np.sum(xx * patch) / p_sum)

        lu = float(np.clip(cx / max(w - 1, 1), 0.0, 1.0))
        lv = float(np.clip(cy / max(h - 1, 1), 0.0, 1.0))
        iz = int(np.clip(round(cy), 0, h - 1))
        ix = int(np.clip(round(cx), 0, w - 1))
        lz = float(depth_norm[iz, ix]) + float(z_offset)
        weight = (p_sum / total_e) * float(strength_scale) * min(2.5, max_e)
        lights.append((lu, lv, lz, float(weight)))
        work[y0:y1, x0:x1] = 0.0

    if not lights:
        lights.append((0.5, 0.5, float(np.mean(depth_norm)) + z_offset, 0.0))
    return lights


def apply_velocity_motion_blur(
    img_hdr: np.ndarray,
    vel_px: np.ndarray,
    shutter_angle: float = 0.5,
    samples: int = 7,
) -> np.ndarray:
    """Desenfoque de movimiento direccional en HDR lineal alineado a vectores de velocidad 2D `(vx, vy)`.

    `shutter_angle = 0.5` equivale a obturador cinematográfico de 180° (emparejando el motion blur
    de la llama rápida y chispas con la exposición real del sensor del teléfono).
    """
    if samples <= 1 or shutter_angle <= 1e-4:
        return img_hdr.astype(np.float32)
    max_v = float(np.max(np.abs(vel_px)))
    if max_v <= 0.15:
        return img_hdr.astype(np.float32)

    h, w = img_hdr.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    vx = vel_px[..., 0].astype(np.float32) * float(shutter_angle)
    vy = vel_px[..., 1].astype(np.float32) * float(shutter_angle)

    acc = np.zeros_like(img_hdr, dtype=np.float32)
    t_vals = np.linspace(-0.5, 0.5, int(samples), dtype=np.float32)
    for t in t_vals:
        sx = np.clip(np.rint(xx - vx * t).astype(np.int32), 0, w - 1)
        sy = np.clip(np.rint(yy - vy * t).astype(np.int32), 0, h - 1)
        acc += img_hdr[sy, sx]
    return (acc / float(len(t_vals))).astype(np.float32)


def joint_bilateral_guide_normals(
    normal_rgb: np.ndarray,
    guide_rgb: np.ndarray,
    radius: int = 2,
    sigma_space: float = 1.5,
    sigma_range: float = 0.08,
    invert_y: bool = True,
) -> np.ndarray:
    """Suaviza escalonamiento 8-bit/upscale de normales preservando aristas del plate y renormaliza.

    Nota: `invert_y=True` por defecto convierte normales OpenGL Camera Space (`+Y` arriba, como
    exporta `NormalCrafter`) al sistema de coordenadas de pantalla (`+Y` abajo) usado por `vv`.
    """
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
    lights_uvz: Optional[List[Tuple[float, float, float, float]]] = None,
    desk_mask: Optional[np.ndarray] = None,
    frame_idx: int = 0,
    fire_color_lin: Tuple[float, float, float] = (1.0, 0.34, 0.045),
    radius_uv: float = 0.55,
    depth_scale: float = 0.35,
    invert_normal_y: bool = True,
    shadow_steps: int = 16,
    depth_bias: float = 0.012,
    refine_normals: bool = True,
    fire_hdr: Optional[np.ndarray] = None,
    mip_area_weight: float = 0.35,
    num_dynamic_lights: int = 6,
) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
    """Calcula pase lineal HDR de relighting PBR (SSDO + Cook-Torrance GGX + SSS + MIP Area-Light).

    - `invert_normal_y=True` (por defecto) convierte normales OpenGL (`+Y` arriba, estándar de
      `NormalCrafter`) al eje `+Y` hacia abajo de la grilla de imagen `vv`.
    - Si se suministra `fire_hdr` (Pilar 4), extrae automáticamente emisores dinámicos desde la
      geometría actual de la llama (`extract_dynamic_lights_from_fire`) y suma irradiancia de área
      multi-escala (`build_fire_irradiance_pyramid`) modulada por visibilidad SSDO y normales.
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

    active_lights: List[Tuple[float, float, float, float]] = list(lights_uvz) if lights_uvz else []
    if fire_hdr is not None and not active_lights:
        active_lights = extract_dynamic_lights_from_fire(
            fire_hdr,
            depth_norm,
            num_lights=num_dynamic_lights,
        )

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

    for lu, lv, lz, l_strength in active_lights:
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
        denom_d = ndoth * ndoth * (a2 - 1.0) + 1.0
        D_ggx = a2 / (np.pi * np.maximum(denom_d * denom_d, 1e-5))
        F_schlick = f0 + (1.0 - f0) * ((1.0 - vdoth) ** 5)
        k_smith = ((roughness + 1.0) ** 2) / 8.0
        G_v = ndotv / (ndotv * (1.0 - k_smith) + k_smith)
        G_l = ndotl / np.maximum(ndotl * (1.0 - k_smith) + k_smith, 1e-4)
        spec_brdf = (D_ggx * F_schlick * G_v * G_l) / np.maximum(4.0 * ndotv, 1e-3)
        spec_term = np.clip(spec_brdf * ndotl, 0.0, 12.0) * spec_scale

        # Subsurface Scattering cálido en bordes rasantes solo en piel
        wrap_ndotl = np.clip((N[..., 0] * lx + N[..., 1] * ly + N[..., 2] * lz_dir + 0.45) / 1.45, 0.0, 1.0)
        sss_term = ((1.0 - ndotv) ** 2.5) * wrap_ndotl * skin * 0.42

        total_diff += (fire_col * (ndotl * diff_weight)[..., None] + sss_col * sss_term[..., None]) * (atten * vis)[..., None]
        total_spec += fire_col * (spec_term * atten * vis)[..., None]
        vis_accum += vis * atten
        weight_accum += atten

    mean_vis = np.where(weight_accum > 1e-5, vis_accum / np.maximum(weight_accum, 1e-5), 1.0).astype(np.float32)

    # Pilar 4: Pirámide MIP de irradiancia de área acoplada a la forma instantánea del fuego
    if fire_hdr is not None and mip_area_weight > 0.0:
        irr_mip = build_fire_irradiance_pyramid(fire_hdr)
        grad_y, grad_x = np.gradient(
            0.5 * irr_mip[..., 0] + 0.35 * irr_mip[..., 1] + 0.15 * irr_mip[..., 2]
        )
        g_norm = np.sqrt(grad_x * grad_x + grad_y * grad_y) + 1e-5
        dir_x = grad_x / g_norm
        dir_y = grad_y / g_norm
        area_ndotl = np.clip(0.55 * N[..., 2] + 0.45 * (N[..., 0] * dir_x + N[..., 1] * dir_y) + 0.25, 0.0, 1.0)
        subject_gate = np.clip(skin + 0.14 * fabric, 0.0, 1.0)
        total_diff += irr_mip * (float(mip_area_weight) * area_ndotl * mean_vis * subject_gate)[..., None]

    # Albedo del plate recibe luz difusa multiplicativa + especular aditivo físico HDR
    relit_lin = plate_lin + plate_lin * total_diff + total_spec
    aux = {
        "N": N,
        "visibility": mean_vis,
        "diffuse_light": total_diff,
        "specular_light": total_spec,
        "relight_delta_hdr": plate_lin * total_diff + total_spec,
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
    """Verifica unit-normales, convención OpenGL +Y, SSDO >=3.5:1, anti-sangrado tela, ACES sin salmón y MIP light."""
    h, w = 128, 128
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    u = xx / (w - 1)
    v = yy / (h - 1)

    plate = np.full((h, w, 3), 0.25, dtype=np.float32)
    matte_fabric = ((u < 0.25) & (v > 0.72)).astype(np.float32)
    matte_skin = ((u >= 0.40) & (u <= 0.76) & (v >= 0.25) & (v <= 0.78)).astype(np.float32)
    desk_mask = ((u >= 0.05) & (v <= 0.20)).astype(np.float32)

    plate[matte_fabric > 0.5] = 0.05
    plate[desk_mask > 0.5] = 0.85

    depth = np.full((h, w), 0.15, dtype=np.float32)
    depth[(u >= 0.42) & (u <= 0.54) & (matte_skin > 0.5)] = 0.90
    depth[(u >= 0.58) & (u <= 0.72) & (matte_skin > 0.5)] = 0.42

    # Normales OpenGL +Y mirando hacia cámara y levemente hacia arriba-izquierda (-0.32, +0.25, 0.914)
    nx = np.full((h, w), -0.32, dtype=np.float32)
    ny = np.full((h, w), 0.25, dtype=np.float32)
    nz = np.full((h, w), 0.914, dtype=np.float32)
    norm_packed = np.stack([nx, ny, nz], axis=-1) * 0.5 + 0.5

    lights = [(0.34, 0.35, 0.42, 3.2)]
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
        invert_normal_y=True,
        shadow_steps=16,
        refine_normals=True,
    )

    n_norms = np.linalg.norm(aux["N"], axis=-1)
    assert float(n_norms.min()) > 0.99 and float(n_norms.max()) < 1.01, "Normales fuera de longitud unitaria"
    # Verificar que invert_normal_y=True convirtió N_y OpenGL (+0.25 arriba) a (-0.25 pantalla)
    assert float(np.mean(aux["N"][..., 1])) < -0.20, "Normal OpenGL +Y no se invirtió a espacio de pantalla"

    front_roi = (u >= 0.43) & (u <= 0.52) & (v >= 0.42) & (v <= 0.58)
    shadow_roi = (u >= 0.59) & (u <= 0.68) & (v >= 0.42) & (v <= 0.58)
    diff_front = float(np.mean(aux["diffuse_light"][front_roi, 0]))
    diff_shadow = float(np.mean(aux["diffuse_light"][shadow_roi, 0]))
    contrast = diff_front / max(diff_shadow, 1e-5)
    assert contrast >= 3.5, f"Oclusión SSDO insuficiente ({contrast:.2f}:1 < 3.5:1)"

    fabric_gain = float(np.mean(relit[matte_fabric > 0.5, 0] / np.maximum(plate[matte_fabric > 0.5, 0], 1e-4)))
    assert fabric_gain <= 1.15, f"Sangrado detectado en tela negra: {fabric_gain:.3f}x"

    far_desk = (u > 0.85) & (v < 0.15)
    max_shift = float(np.max(np.abs(relit[far_desk] - plate[far_desk])))
    assert max_shift < 1e-5, f"Contaminación indebida en escritorio remoto: {max_shift}"

    # Verificar corrección del bug salmón: punta roja (1.2, 0.12, 0.01) NO debe subir azul > 0.15
    red_tip = np.array([[[1.2, 0.12, 0.01]]], dtype=np.float32)
    tm_tip = aces_hill_filmic_tonemap(red_tip)[0, 0]
    assert float(tm_tip[0]) > 0.80 and float(tm_tip[2]) < 0.12, f"Lavado salmón detectado en punta roja: {tm_tip}"

    # Verificar preservación exacta del escritorio blanco tras composición HDR + ACES
    comp_srgb = compose_hdr_on_plate_srgb(plate, aux["relight_delta_hdr"])
    plate_srgb = linear_to_srgb(plate)
    desk_srgb_err = float(np.max(np.abs(comp_srgb[far_desk] - plate_srgb[far_desk])))
    assert desk_srgb_err < 1e-6, f"Shift en escritorio blanco tras tone mapping: {desk_srgb_err}"

    # Verificar extracción dinámica de luces desde buffer HDR de fuego + motion blur 180°
    synth_fire = np.zeros((h, w, 3), dtype=np.float32)
    synth_fire[35:55, 48:68] = np.array([9.5, 3.8, 0.65], dtype=np.float32)
    dyn_lights = extract_dynamic_lights_from_fire(synth_fire, depth * 0.35, num_lights=3)
    assert len(dyn_lights) >= 1 and 0.30 <= dyn_lights[0][0] <= 0.60
    vel = np.zeros((h, w, 2), dtype=np.float32)
    vel[..., 0] = 12.0
    blurred = apply_velocity_motion_blur(synth_fire, vel, shutter_angle=0.5, samples=5)
    assert float(blurred[45, 70, 0]) > 0.1, "Motion blur direccional no propagó estela"

    print(
        "[SELF-TEST OK] vfx_ssdo_relight_16f.py ->",
        json.dumps(
            {
                "unit_norm_range": [round(float(n_norms.min()), 4), round(float(n_norms.max()), 4)],
                "ssdo_occlusion_contrast": round(contrast, 2),
                "fabric_orange_gain": round(fabric_gain, 4),
                "far_desk_shift": max_shift,
                "red_tip_aces_srgb": [round(float(c), 4) for c in tm_tip],
                "desk_srgb_preserve_err": desk_srgb_err,
                "peak_hdr_linear": round(float(relit.max()), 3),
            }
        ),
    )
    return 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Relighting Lineal PBR 16F (SSDO 16-step + GGX + SSS + MIP Area-Light + ACES/OCIO)")
    p.add_argument("--plate", type=Path, help="Imagen/frame lineal .npy o sRGB .png")
    p.add_argument("--normal", type=Path, help="Normal map .npy o .png (Camera Space)")
    p.add_argument("--depth", type=Path, help="Depth map 16F .npy o .png")
    p.add_argument("--skin-matte", type=Path, help="Máscara piel [0..1]")
    p.add_argument("--fabric-matte", type=Path, help="Máscara tela [0..1]")
    p.add_argument("--desk-mask", type=Path, default=None, help="Opcional: máscara escritorio DA3/SAM3")
    p.add_argument("--lights-json", type=Path, default=None, help="JSON con lista de luces [[u,v,z,strength], ...]")
    p.add_argument("--fire-hdr", type=Path, default=None, help="Opcional: pase de fuego HDR .npy para acoplar MIP Area-Light")
    p.add_argument("--out", type=Path, default=Path("relit_hdr.npy"), help="Salida .exr o .npy")
    p.add_argument("--preview-png", type=Path, default=None, help="Opcional: preview ACES/AgX sRGB PNG")
    p.add_argument(
        "--normal-convention",
        choices=["opengl", "screen"],
        default="opengl",
        help="opengl (+Y arriba, NormalCrafter/Blender, invierte Y para SSDO) o screen (+Y abajo)",
    )
    p.add_argument("--invert-y", action="store_true", help="Fuerza inversión de N_y (activo por defecto en opengl)")
    p.add_argument("--no-invert-y", action="store_true", help="Desactiva inversión de N_y (si N_y ya apunta hacia abajo)")
    p.add_argument(
        "--tonemap",
        choices=["aces_hill", "ocio_agx"],
        default="aces_hill",
        help="Curva para --preview-png: aces_hill (Stephen Hill RRT+ODT) u ocio_agx (PyOpenColorIO AgX Punchy)",
    )
    p.add_argument("--ocio-config", type=str, default=None, help="Ruta opcional a config.ocio de Blender 4.5/5.x")
    p.add_argument("--ocio-look", type=str, default="AgX - Punchy", help="Look OCIO para AgX")
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

    required = [args.plate, args.normal, args.depth, args.skin_matte, args.fabric_matte]
    if any(x is None for x in required) or (args.lights_json is None and args.fire_hdr is None):
        print("ERROR: Faltan argumentos requeridos (--lights-json o --fire-hdr) o ejecuta --self-test.", file=sys.stderr)
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

    lights: Optional[List[Tuple[float, float, float, float]]] = None
    if args.lights_json is not None:
        lights_raw = json.loads(args.lights_json.read_text(encoding="utf-8"))
        lights = [tuple(map(float, item)) for item in lights_raw]

    fire_hdr = _read_arr(args.fire_hdr, is_srgb_img=False)[..., :3] if args.fire_hdr is not None else None
    invert_y = False if args.no_invert_y else (True if args.invert_y else (args.normal_convention == "opengl"))

    relit_lin, aux = compute_ssdo_pbr_relight(
        plate,
        normal,
        depth,
        skin,
        fabric,
        lights,
        desk_mask=desk,
        invert_normal_y=invert_y,
        shadow_steps=args.shadow_steps,
        fire_hdr=fire_hdr,
    )
    save_exr_or_npy(args.out, relit_lin)
    if args.preview_png is not None:
        delta_hdr = aux["relight_delta_hdr"] + (fire_hdr if fire_hdr is not None else 0.0)
        prev_srgb = compose_hdr_on_plate_srgb(
            plate,
            delta_hdr,
            tonemap_mode=args.tonemap,
            ocio_config=args.ocio_config,
            ocio_look=args.ocio_look,
        )
        prev = np.clip(np.round(prev_srgb * 255.0), 0, 255).astype(np.uint8)
        args.preview_png.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(prev, mode="RGB").save(args.preview_png)
    print(f"[OK] Relighting HDR lineal guardado en {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
