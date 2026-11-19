#!/usr/bin/env python3
"""Matting Dual Piel/Tela + Foreground Color Decontamination (Módulo A · Workflow 4 Paso 0).

Resuelve la Falla #1 de `v10` (halo blanco del escritorio contaminando los hilos negros
deshilachados del puño y sangrado naranja plano sobre la manga):
1. Combina mattes independientes `matte_skin` (piel/uñas) y `matte_fabric` (manga/tela).
2. Estima el color puro del foreground F resolviendo I = alpha * F + (1 - alpha) * B
   mediante `pymatting.estimate_foreground_ml` (si está instalado en Windows 11) o un
   estimador vectorial multi-escala determinista en NumPy puro.
3. Limpia hilos claros contaminados dentro de la zona de borde de tela oscura (`EdgeCleanup`).
4. Mide la fuga residual de luminancia (delta L) en el borde frente al interior de la tela.

Uso en producción (Windows 11):
  python scripts/vfx_dual_matte_decontam.py ^
    --plate-dir job/01_plate_lin ^
    --skin-matte-dir job/02_matte_skin ^
    --fabric-matte-dir job/02_matte_fabric ^
    --out-dir job/03_decontam

Prueba unitaria sintética (sin requerir GPU ni video externo):
  python scripts/vfx_dual_matte_decontam.py --self-test
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Tuple

import numpy as np
from PIL import Image

try:
    from pymatting import estimate_foreground_ml as _pymatting_fg  # type: ignore
except ImportError:
    _pymatting_fg = None


def _box_blur(arr: np.ndarray, radius: int) -> np.ndarray:
    """Separable box filter using integral images in pure NumPy (supports HxW or HxWxC)."""
    if radius <= 0:
        return arr
    squeeze = False
    if arr.ndim == 2:
        arr = arr[..., None]
        squeeze = True
    h, w, c = arr.shape
    pad = radius
    padded = np.pad(arr.astype(np.float64), ((pad, pad), (pad, pad), (0, 0)), mode="edge")
    # Horizontal integral
    k = 2 * radius + 1
    cs_x = np.cumsum(np.pad(padded, ((0, 0), (1, 0), (0, 0)), mode="constant"), axis=1)
    horiz = (cs_x[:, k:, :] - cs_x[:, :-k, :]) / float(k)
    # Vertical integral
    cs_y = np.cumsum(np.pad(horiz, ((1, 0), (0, 0), (0, 0)), mode="constant"), axis=0)
    vert = (cs_y[k:, :, :] - cs_y[:-k, :, :]) / float(k)
    out = vert.astype(np.float32)
    return out[..., 0] if squeeze else out


def _binary_dilate(mask: np.ndarray, radius: int) -> np.ndarray:
    if radius <= 0:
        return mask
    return _box_blur(mask.astype(np.float32), radius) > 0.0


def _binary_erode(mask: np.ndarray, radius: int) -> np.ndarray:
    if radius <= 0:
        return mask
    return _box_blur(mask.astype(np.float32), radius) >= (1.0 - 1e-5)


def estimate_foreground_local_numpy(
    img_rgb: np.ndarray,
    alpha: np.ndarray,
    radius: int = 12,
    passes: int = 2,
) -> np.ndarray:
    """Recupera F puro en bordes semitransparentes propagando color del interior sólido.

    Si `pymatting` está disponible en el entorno local, el caller puede delegar a
    `estimate_foreground_ml`; esta función provee una alternativa rápida sin dependencias
    pesadas para entornos sin Numba/PyMatting o pruebas CI.
    """
    img = np.clip(img_rgb.astype(np.float32), 0.0, 1.0)
    a = np.clip(alpha.astype(np.float32), 0.0, 1.0)
    sure_fg = (a >= 0.96).astype(np.float32)

    # Propagar color de foreground interior hacia el borde con pirámide de promedios
    fg_est = img.copy()
    w_acc = sure_fg[..., None] + 1e-6
    color_num = img * sure_fg[..., None]
    for r in (radius, max(3, radius // 2), 2):
        num = _box_blur(color_num, r)
        den = _box_blur(w_acc, r)
        valid = den > 1e-4
        prop = np.where(valid, num / np.maximum(den, 1e-4), fg_est)
        # Actualizar pesos solo donde ya propagamos señal de foreground
        fg_est = np.where((sure_fg[..., None] < 0.5) & valid, prop, fg_est)
        color_num = fg_est * np.where(valid, np.maximum(w_acc, 0.25), w_acc)
        w_acc = np.where(valid, np.maximum(w_acc, 0.25), w_acc)

    # Refinamiento analítico acotado por I = a*F + (1-a)*B en la banda de transición
    fg_out = img.copy()
    band = (a > 0.02) & (a < 0.96)
    sure_bg = (a <= 0.02).astype(np.float32)
    bg_num = _box_blur(img * sure_bg[..., None], radius)
    bg_den = _box_blur(sure_bg[..., None], radius)
    bg_est = np.where(bg_den > 1e-4, bg_num / np.maximum(bg_den, 1e-4), img)

    for _ in range(passes):
        solved = (img - (1.0 - a[..., None]) * bg_est) / np.maximum(a[..., None], 0.08)
        # Mezcla guiada hacia el color sólido cercano cuando alpha es muy bajo (<0.35)
        conf = np.clip((a - 0.05) / 0.50, 0.0, 1.0)[..., None]
        refined = conf * np.clip(solved, 0.0, 1.0) + (1.0 - conf) * fg_est
        fg_out = np.where(band[..., None], refined, np.where(a[..., None] >= 0.96, img, fg_est))
        fg_est = fg_out

    return np.clip(fg_out, 0.0, 1.0)


def decontaminate_frame(
    img_rgb: np.ndarray,
    matte_skin: np.ndarray,
    matte_fabric: np.ndarray,
    regularization: float = 1e-5,
    bright_threshold: float = 0.06,
    ref_radius: int = 12,
    edge_zone_px: int = 16,
    use_pymatting: bool = True,
) -> Tuple[np.ndarray, np.ndarray, dict]:
    """Descontamina bordes deshilachados y suprime halos claros sobre tela oscura."""
    alpha_skin = np.clip(matte_skin.astype(np.float32), 0.0, 1.0)
    alpha_fabric = np.clip(matte_fabric.astype(np.float32), 0.0, 1.0)
    alpha_total = np.clip(np.maximum(alpha_skin, alpha_fabric), 0.0, 1.0)

    if use_pymatting and _pymatting_fg is not None:
        fg = _pymatting_fg(
            img_rgb.astype(np.float64),
            alpha_total.astype(np.float64),
            regularization=regularization,
        ).astype(np.float32)
        fg = np.clip(fg, 0.0, 1.0)
        backend = "pymatting_ml"
    else:
        fg = estimate_foreground_local_numpy(img_rgb, alpha_total, radius=ref_radius)
        backend = "numpy_local_multiscale"

    # Limpieza dirigida SOLO dentro de la zona de borde de tela oscura (evita dañar uñas/piel clara)
    luma_weights = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    lum_before = (img_rgb * luma_weights).sum(axis=-1)
    lum_fg = (fg * luma_weights).sum(axis=-1)

    fabric_solid = alpha_fabric >= 0.85
    fabric_inner = _binary_erode(fabric_solid, max(2, edge_zone_px // 2))
    fabric_band = (alpha_fabric > 0.02) & _binary_dilate(alpha_fabric > 0.02, edge_zone_px) & (~fabric_inner)

    # Referencia local de tela sólida oscura
    core_w = fabric_inner.astype(np.float32)[..., None]
    ref_num = _box_blur(fg * core_w, ref_radius)
    ref_den = _box_blur(core_w, ref_radius)
    has_ref = ref_den[..., 0] > 1e-4
    ref_color = np.where(has_ref[..., None], ref_num / np.maximum(ref_den, 1e-4), fg)
    ref_lum = (ref_color * luma_weights).sum(axis=-1)

    # Detecta píxeles del borde de tela más luminosos que su tela vecina (halo blanco residual)
    excess = np.clip((lum_fg - ref_lum - bright_threshold) / max(bright_threshold, 1e-3), 0.0, 1.0)
    fix_mask = np.where(fabric_band & has_ref, excess, 0.0)
    fg_clean = fg * (1.0 - fix_mask[..., None]) + ref_color * fix_mask[..., None]

    # Empaqueta Dual Matte RGB: R=Skin, G=Fabric, B=Transitional Fringe Zone
    trans_band = np.clip((alpha_total > 0.02) & (alpha_total < 0.98), 0.0, 1.0).astype(np.float32)
    dual_matte_rgb = np.stack([alpha_skin, alpha_fabric, trans_band], axis=-1)

    # Métricas diagnósticas de borde
    lum_after = (fg_clean * luma_weights).sum(axis=-1)
    if np.any(fabric_inner) and np.any(fabric_band):
        core_l = float(np.median(lum_before[fabric_inner]))
        fringe_before = float(np.mean(np.abs(lum_before[fabric_band] - core_l)))
        fringe_after = float(np.mean(np.abs(lum_after[fabric_band] - core_l)))
    else:
        core_l, fringe_before, fringe_after = 0.0, 0.0, 0.0

    stats = {
        "backend": backend,
        "fabric_core_luma": round(core_l, 5),
        "fringe_delta_l_before": round(fringe_before, 5),
        "fringe_delta_l_after": round(fringe_after, 5),
    }
    return fg_clean, dual_matte_rgb, stats


def _load_rgb(path: Path) -> np.ndarray:
    if path.suffix.lower() == ".npy":
        return np.load(path).astype(np.float32)[..., :3]
    arr = np.asarray(Image.open(path).convert("RGB"), dtype=np.float32)
    return arr / 255.0


def _load_mask(path: Path) -> np.ndarray:
    if path.suffix.lower() == ".npy":
        arr = np.load(path).astype(np.float32)
        return arr[..., 0] if arr.ndim == 3 else arr
    return np.asarray(Image.open(path).convert("L"), dtype=np.float32) / 255.0


def _save_rgb16_png_or_npy(path: Path, arr: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".npy":
        np.save(path, arr.astype(np.float32))
    else:
        u8 = np.clip(np.round(arr * 255.0), 0, 255).astype(np.uint8)
        Image.fromarray(u8, mode="RGB").save(path)


def run_self_test() -> int:
    """Valida matemáticamente la descontaminación de halo blanco sobre manga negra."""
    h, w = 96, 96
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    # Fondo escritorio blanco neutro (0.92)
    bg = np.full((h, w, 3), 0.92, dtype=np.float32)
    # Tela negra real (0.045) a la izquierda con borde deshilachado suave
    edge_x = 48.0 + 3.0 * np.sin(yy * 0.35)
    alpha_fabric = np.clip((edge_x - xx) / 3.0 + 0.5, 0.0, 1.0)
    alpha_skin = np.clip(1.0 - np.hypot(xx - 66.0, yy - 34.0) / 14.0, 0.0, 1.0)
    alpha_skin = np.clip((alpha_skin - 0.2) * 3.0, 0.0, 1.0) * (1.0 - alpha_fabric)

    true_fabric = np.full((h, w, 3), 0.045, dtype=np.float32)
    true_skin = np.array([0.62, 0.44, 0.36], dtype=np.float32)[None, None, :]
    fg_true = true_fabric * alpha_fabric[..., None] + true_skin * alpha_skin[..., None]
    alpha_tot = np.clip(alpha_fabric + alpha_skin, 0.0, 1.0)
    composite = fg_true + (1.0 - alpha_tot[..., None]) * bg

    fg_clean, dual_matte, stats = decontaminate_frame(
        composite, alpha_skin, alpha_fabric, use_pymatting=False
    )
    assert dual_matte.shape == (h, w, 3)
    assert stats["fringe_delta_l_after"] < 0.03, (
        f"Esperado delta_L < 0.03 tras descontaminar borde; obtenido {stats['fringe_delta_l_after']}"
    )
    assert stats["fringe_delta_l_after"] < stats["fringe_delta_l_before"] * 0.25, (
        f"Descontaminación insuficiente: {stats}"
    )
    print("[SELF-TEST OK] vfx_dual_matte_decontam.py ->", json.dumps(stats))
    return 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Descontaminación Dual Matte Piel/Tela (Módulo A)")
    p.add_argument("--plate-dir", type=Path, help="Carpeta con frames RGB originales (.png/.npy)")
    p.add_argument("--skin-matte-dir", type=Path, help="Carpeta con mattes de piel")
    p.add_argument("--fabric-matte-dir", type=Path, help="Carpeta con mattes de tela/manga")
    p.add_argument("--out-dir", type=Path, default=Path("./out_decontam"), help="Carpeta de salida")
    p.add_argument("--regularization", type=float, default=1e-5)
    p.add_argument("--bright-threshold", type=float, default=0.06)
    p.add_argument("--no-pymatting", action="store_true", help="Fuerza estimador NumPy puro")
    p.add_argument("--self-test", action="store_true", help="Ejecuta verificación sintética")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        return run_self_test()

    if not (args.plate_dir and args.skin_matte_dir and args.fabric_matte_dir):
        print("ERROR: Especifica --plate-dir, --skin-matte-dir y --fabric-matte-dir (o usa --self-test).", file=sys.stderr)
        return 1

    plates = sorted(p for p in args.plate_dir.iterdir() if p.suffix.lower() in {".png", ".jpg", ".npy"})
    skins = sorted(p for p in args.skin_matte_dir.iterdir() if p.suffix.lower() in {".png", ".jpg", ".npy"})
    fabrics = sorted(p for p in args.fabric_matte_dir.iterdir() if p.suffix.lower() in {".png", ".jpg", ".npy"})
    n = min(len(plates), len(skins), len(fabrics))
    if n == 0:
        print("ERROR: No se encontraron frames emparejados en las carpetas indicadas.", file=sys.stderr)
        return 1

    fg_dir = args.out_dir / "fg_decontaminated"
    dm_dir = args.out_dir / "dual_matte_rgb"
    report = []
    for idx in range(n):
        img = _load_rgb(plates[idx])
        ms = _load_mask(skins[idx])
        mf = _load_mask(fabrics[idx])
        fg_clean, dual_rgb, stats = decontaminate_frame(
            img,
            ms,
            mf,
            regularization=args.regularization,
            bright_threshold=args.bright_threshold,
            use_pymatting=not args.no_pymatting,
        )
        stem = plates[idx].stem
        _save_rgb16_png_or_npy(fg_dir / f"{stem}.npy", fg_clean)
        _save_rgb16_png_or_npy(dm_dir / f"{stem}.png", dual_rgb)
        stats["frame"] = idx
        report.append(stats)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "decontam_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(f"[OK] Procesados {n} frames en {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
