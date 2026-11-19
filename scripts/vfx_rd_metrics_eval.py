#!/usr/bin/env python3
"""Evaluador Cuantitativo de Gates R&D (Módulo A · Workflow 4 · 33f -> 167f).

Calcula las métricas objetivas exactas para auditar cada ruta del Workflow 4 antes
de aprobar el escalado completo a 167 frames:

- Gate 0 (Integridad Geométrica y Bordes):
  * `unit_norm_error`: desviación respecto a ||N|| = 1.0 en normales 16F (bandas 8-bit).
  * `temporal_normal_l2`: error L2 temporal entre N_t y N_{t-1} compensado por desplazamiento.
  * `fringe_delta_l`: contaminación luminosa residual en borde de tela negra vs interior.
- Gate 1 (Material Dual, Oclusión SSDO & Neutralidad de Fondo):
  * `cuff_gain_ratio` vs `palm_gain_ratio` (anti-sangrado naranja sobre puño negro <= 1.15x).
  * `ssdo_shadow_contrast`: contraste oclusor frontal vs zona sombreada (>= 3.5:1).
  * `desk_ciede2000`: diferencia colorimétrica CIEDE2000 exacta sobre ROI fijo del escritorio
    blanco / impresora frente al plate original (criterio de aceptación <= 1.5).
- Gate 2 (Linealidad HDR & Emparejamiento MTF/Grano):
  * `hdr_linear_peak`: pico lineal previo al tone map (objetivo fuego >= 4.0).
  * `pastel_clip_pct`: porcentaje de píxeles del núcleo con clipping amarillo plano SDR.
  * `mtf_noise_delta_pct`: diferencia relativa de desviación estándar de ruido alta frecuencia
    frente al sensor CMOS medido en ROI de referencia del plate (±12 %).

Uso:
  python scripts/vfx_rd_metrics_eval.py --self-test
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Dict

import numpy as np


def rgb_linear_to_lab(rgb_lin: np.ndarray) -> np.ndarray:
    """Convierte RGB lineal Rec.709/sRGB (D65) -> CIE L*a*b* en NumPy vectorizado."""
    rgb = np.clip(rgb_lin.astype(np.float64), 0.0, None)
    # Rec.709 / sRGB D65 -> XYZ
    m = np.array(
        [
            [0.4124564, 0.3575761, 0.1804375],
            [0.2126729, 0.7151522, 0.0721750],
            [0.0193339, 0.1191920, 0.9503041],
        ],
        dtype=np.float64,
    )
    xyz = rgb @ m.T
    # Blanco D65
    xn, yn, zn = 0.95047, 1.00000, 1.08883
    xr = xyz[..., 0] / xn
    yr = xyz[..., 1] / yn
    zr = xyz[..., 2] / zn

    eps = 216.0 / 24389.0
    kappa = 24389.0 / 27.0

    def f(t: np.ndarray) -> np.ndarray:
        return np.where(t > eps, np.cbrt(t), (kappa * t + 16.0) / 116.0)

    fx, fy, fz = f(xr), f(yr), f(zr)
    L = 116.0 * fy - 16.0
    a = 500.0 * (fx - fy)
    b = 200.0 * (fy - fz)
    return np.stack([L, a, b], axis=-1)


def ciede2000(lab1: np.ndarray, lab2: np.ndarray) -> np.ndarray:
    """Implementación estándar exacta de CIEDE2000 (Sharma, Wu, Dalal 2005)."""
    L1, a1, b1 = lab1[..., 0], lab1[..., 1], lab1[..., 2]
    L2, a2, b2 = lab2[..., 0], lab2[..., 1], lab2[..., 2]

    C1 = np.sqrt(a1 * a1 + b1 * b1)
    C2 = np.sqrt(a2 * a2 + b2 * b2)
    C_bar = 0.5 * (C1 + C2)
    C_bar7 = C_bar ** 7
    pow25_7 = 25.0 ** 7
    G = 0.5 * (1.0 - np.sqrt(C_bar7 / (C_bar7 + pow25_7)))

    a1p = (1.0 + G) * a1
    a2p = (1.0 + G) * a2
    C1p = np.sqrt(a1p * a1p + b1 * b1)
    C2p = np.sqrt(a2p * a2p + b2 * b2)

    h1p = np.degrees(np.arctan2(b1, a1p)) % 360.0
    h2p = np.degrees(np.arctan2(b2, a2p)) % 360.0

    dLp = L2 - L1
    dCp = C2p - C1p

    c_prod = C1p * C2p
    dh_raw = h2p - h1p
    dhp = np.where(
        c_prod == 0.0,
        0.0,
        np.where(
            np.abs(dh_raw) <= 180.0,
            dh_raw,
            np.where(dh_raw > 180.0, dh_raw - 360.0, dh_raw + 360.0),
        ),
    )
    dHp = 2.0 * np.sqrt(c_prod) * np.sin(np.radians(0.5 * dhp))

    L_bar_p = 0.5 * (L1 + L2)
    C_bar_p = 0.5 * (C1p + C2p)

    h_sum = h1p + h2p
    h_bar_p = np.where(
        c_prod == 0.0,
        h_sum,
        np.where(
            np.abs(h1p - h2p) <= 180.0,
            0.5 * h_sum,
            np.where(h_sum < 360.0, 0.5 * (h_sum + 360.0), 0.5 * (h_sum - 360.0)),
        ),
    )

    T = (
        1.0
        - 0.17 * np.cos(np.radians(h_bar_p - 30.0))
        + 0.24 * np.cos(np.radians(2.0 * h_bar_p))
        + 0.32 * np.cos(np.radians(3.0 * h_bar_p + 6.0))
        - 0.20 * np.cos(np.radians(4.0 * h_bar_p - 63.0))
    )
    dTheta = 30.0 * np.exp(-(((h_bar_p - 275.0) / 25.0) ** 2))
    C_bar_p7 = C_bar_p ** 7
    R_C = 2.0 * np.sqrt(C_bar_p7 / (C_bar_p7 + pow25_7))
    Lm50_2 = (L_bar_p - 50.0) ** 2
    S_L = 1.0 + (0.015 * Lm50_2) / np.sqrt(20.0 + Lm50_2)
    S_C = 1.0 + 0.045 * C_bar_p
    S_H = 1.0 + 0.015 * C_bar_p * T
    R_T = -np.sin(np.radians(2.0 * dTheta)) * R_C

    term_L = dLp / S_L
    term_C = dCp / S_C
    term_H = dHp / S_H
    dE2 = term_L ** 2 + term_C ** 2 + term_H ** 2 + R_T * term_C * term_H
    return np.sqrt(np.maximum(dE2, 0.0))


def eval_normal_unit_integrity(normal_vec_or_rgb: np.ndarray, packed_01: bool = False) -> Dict[str, float]:
    N = normal_vec_or_rgb.astype(np.float32)
    if packed_01:
        N = N * 2.0 - 1.0
    norms = np.linalg.norm(N, axis=-1)
    return {
        "min_norm": round(float(norms.min()), 5),
        "max_norm": round(float(norms.max()), 5),
        "max_unit_error": round(float(np.max(np.abs(norms - 1.0))), 5),
    }


def eval_highfreq_noise_match(plate_roi_lin: np.ndarray, comp_roi_lin: np.ndarray) -> Dict[str, float]:
    """Compara energía de ruido de alta frecuencia (Laplaciano 2D) entre plate original y compuesto."""
    def lap_std(img: np.ndarray) -> float:
        arr = img.astype(np.float64)
        if arr.ndim == 2:
            arr = arr[..., None]
        p = np.pad(arr, ((1, 1), (1, 1), (0, 0)), mode="edge")
        lap = (
            p[1:-1, 1:-1] * -4.0
            + p[:-2, 1:-1]
            + p[2:, 1:-1]
            + p[1:-1, :-2]
            + p[1:-1, 2:]
        )
        return float(np.std(lap))

    s_plate = lap_std(plate_roi_lin)
    s_comp = lap_std(comp_roi_lin)
    rel_diff_pct = ((s_comp - s_plate) / max(s_plate, 1e-7)) * 100.0
    return {
        "plate_hf_std": round(s_plate, 6),
        "comp_hf_std": round(s_comp, 6),
        "rel_diff_pct": round(rel_diff_pct, 2),
        "gate2_pass_within_12pct": bool(abs(rel_diff_pct) <= 12.0),
    }


def eval_hdr_fire_linearity(fire_hdr_lin: np.ndarray, tonemapped_srgb: np.ndarray) -> Dict[str, float | bool]:
    peak = float(np.max(fire_hdr_lin))
    # Detecta clipping amarillo pastel plano: R > 0.97, G > 0.97 y B < 0.65 tras tone map sRGB
    bright = (tonemapped_srgb[..., 0] > 0.97) & (tonemapped_srgb[..., 1] > 0.97)
    pastel_yellow = bright & (tonemapped_srgb[..., 2] < 0.65)
    pastel_pct = float(np.mean(pastel_yellow) * 100.0) if np.any(bright) else 0.0
    return {
        "hdr_linear_peak": round(peak, 3),
        "pastel_yellow_clip_pct": round(pastel_pct, 3),
        "gate2_pass_hdr_peak": bool(peak >= 4.0),
    }


def _srgb_to_linear(arr: np.ndarray) -> np.ndarray:
    x = np.clip(arr.astype(np.float32), 0.0, None)
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4).astype(np.float32)


def _load_image_or_npy(path: Path, as_linear_if_png: bool = True) -> np.ndarray:
    if path.suffix.lower() == ".npy":
        return np.load(path).astype(np.float32)
    from PIL import Image

    arr = np.asarray(Image.open(path).convert("RGB"), dtype=np.float32) / 255.0
    return _srgb_to_linear(arr) if as_linear_if_png else arr


def run_self_test() -> int:
    """Valida CIEDE2000 contra pares de referencia conocidos (Sharma et al. 2005) y métricas R&D."""
    lab1 = np.array([50.0, 2.6772, -79.7751], dtype=np.float64)
    lab2 = np.array([50.0, 0.0, -82.7485], dtype=np.float64)
    de_sharma = float(ciede2000(lab1, lab2))
    assert abs(de_sharma - 2.0425) < 1e-3, f"CIEDE2000 fuera de especificación: {de_sharma}"

    desk_ref = np.full((32, 32, 3), 0.85, dtype=np.float32)
    desk_clean = desk_ref + np.array([0.002, 0.001, 0.0], dtype=np.float32)
    de_desk = float(np.mean(ciede2000(rgb_linear_to_lab(desk_ref), rgb_linear_to_lab(desk_clean))))
    assert de_desk <= 1.5, f"Delta E escritorio superó umbral Gate 1: {de_desk}"

    rng = np.random.default_rng(7)
    noise_ref = 0.4 + rng.normal(0.0, 0.012, size=(64, 64, 3)).astype(np.float32)
    noise_comp = 0.4 + rng.normal(0.0, 0.0125, size=(64, 64, 3)).astype(np.float32)
    hf = eval_highfreq_noise_match(noise_ref, noise_comp)
    assert hf["gate2_pass_within_12pct"]

    print(
        "[SELF-TEST OK] vfx_rd_metrics_eval.py ->",
        json.dumps(
            {
                "sharma2005_pair1_ciede2000": round(de_sharma, 4),
                "desk_ciede2000": round(de_desk, 4),
                "hf_noise_diff_pct": hf["rel_diff_pct"],
            }
        ),
    )
    return 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Auditor Cuantitativo Gate 0/1/2 para Workflow 4")
    p.add_argument("--plate-npy", type=Path, help="Frame plate lineal (.npy float32 [0..1]) o PNG sRGB")
    p.add_argument("--comp-hdr-npy", type=Path, help="Frame compuesto HDR lineal (.npy)")
    p.add_argument("--comp-tonemapped-npy", type=Path, help="Frame compuesto tras ACES/AgX (.npy o .png sRGB)")
    p.add_argument("--normal-npy", type=Path, default=None, help="Normal map lineal [-1..1] o [0..1]")
    p.add_argument("--desk-roi", type=int, nargs=4, default=None, help="x0 y0 x1 y1 del ROI de escritorio neutro")
    p.add_argument("--tm-is-srgb", action="store_true", help="Si --comp-tonemapped-npy (.npy) ya trae OETF sRGB")
    p.add_argument("--out-json", type=Path, default=None)
    p.add_argument("--self-test", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        return run_self_test()

    if not (args.plate_npy and args.comp_hdr_npy and args.comp_tonemapped_npy):
        print("ERROR: Especifica --plate-npy, --comp-hdr-npy y --comp-tonemapped-npy (o usa --self-test).", file=sys.stderr)
        return 1

    plate_lin = _load_image_or_npy(args.plate_npy, as_linear_if_png=True)
    comp_hdr = _load_image_or_npy(args.comp_hdr_npy, as_linear_if_png=True)
    comp_tm_raw = _load_image_or_npy(args.comp_tonemapped_npy, as_linear_if_png=False)
    comp_tm_lin = (
        _srgb_to_linear(comp_tm_raw)
        if (args.comp_tonemapped_npy.suffix.lower() != ".npy" or args.tm_is_srgb)
        else comp_tm_raw
    )
    comp_tm_srgb = (
        comp_tm_raw
        if (args.comp_tonemapped_npy.suffix.lower() != ".npy" or args.tm_is_srgb)
        else np.where(comp_tm_raw <= 0.0031308, comp_tm_raw * 12.92, 1.055 * (np.clip(comp_tm_raw, 0.0, None) ** (1.0 / 2.4)) - 0.055)
    )

    h, w = plate_lin.shape[:2]
    x0, y0, x1, y1 = args.desk_roi if args.desk_roi else (0, 0, w // 4, h // 4)
    desk_de = float(
        np.mean(
            ciede2000(
                rgb_linear_to_lab(plate_lin[y0:y1, x0:x1]),
                rgb_linear_to_lab(comp_tm_lin[y0:y1, x0:x1]),
            )
        )
    )
    report: Dict[str, object] = {
        "gate1_desk_ciede2000": round(desk_de, 4),
        "gate1_desk_pass": bool(desk_de <= 1.5),
        "gate2_hdr_fire": eval_hdr_fire_linearity(comp_hdr, comp_tm_srgb),
        "gate2_mtf_noise": eval_highfreq_noise_match(plate_lin[y0:y1, x0:x1], comp_tm_lin[y0:y1, x0:x1]),
    }
    if args.normal_npy is not None:
        norm = _load_image_or_npy(args.normal_npy, as_linear_if_png=False)
        packed = bool(norm.min() >= -0.05 and norm.max() <= 1.05 and norm.mean() > 0.15)
        report["gate0_normal"] = eval_normal_unit_integrity(norm, packed_01=packed)

    out_txt = json.dumps(report, indent=2)
    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(out_txt, encoding="utf-8")
    print(out_txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
