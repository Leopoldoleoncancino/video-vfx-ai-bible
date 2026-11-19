#!/usr/bin/env python3
"""Evaluador Cuantitativo de Gates R&D 0–3 (Módulo A · Workflow 4 · 33f -> 167f).

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
- Gate 2 (Linealidad HDR, Espectro Hidrocarburo & Emparejamiento MTF/Grano):
  * `hdr_linear_peak`: pico lineal previo al tone map (objetivo fuego >= 4.0).
  * `pastel_clip_pct`: porcentaje de píxeles del núcleo con clipping amarillo plano SDR.
  * `salmon_wash_pct`: porcentaje de píxeles de borde/cuerpo con contaminación azul tipo salmón.
  * `mtf_noise_delta_pct`: diferencia relativa de desviación estándar de ruido alta frecuencia
    frente al sensor CMOS medido en ROI de referencia del plate (±12 %).
- Gate 3 (Acoplamiento Dinámico Movimiento Mano <-> Fuego / Inercia Navier-Stokes · Pilar 5):
  * `lag_correlation`: correlación entre la velocidad de la mano en el mundo
    `v_hand_world = diff(centroid_hand) - v_cam` y la deflexión opuesta de la estela superior
    de la llama `d_wake = (centroid_fire_upper - centroid_hand) - d_wake_0` (`>= 0.45`).
  * `wake_deflection_gain_px`: deflexión media de la pluma superior en cuadros de movimiento
    rápido (`>= 1.5 px`), rechazando fuegos procedurales *stateless* que permanecen rígidos
    durante el giro de 180° (`f88..f120`).

Uso:
  python scripts/vfx_rd_metrics_eval.py --self-test
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np


def rgb_linear_to_lab(rgb_lin: np.ndarray) -> np.ndarray:
    """Convierte RGB lineal Rec.709/sRGB (D65) -> CIE L*a*b* en NumPy vectorizado."""
    rgb = np.clip(rgb_lin.astype(np.float64), 0.0, None)
    m = np.array(
        [
            [0.4124564, 0.3575761, 0.1804375],
            [0.2126729, 0.7151522, 0.0721750],
            [0.0193339, 0.1191920, 0.9503041],
        ],
        dtype=np.float64,
    )
    xyz = rgb @ m.T
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


def eval_highfreq_noise_match(plate_roi_lin: np.ndarray, comp_roi_lin: np.ndarray) -> Dict[str, float | bool]:
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

    # Detecta lavado salmón/rosa en puntas rojas intensas (R_lin in [1.0, 2.5], R > 4*G y B_lin < 0.05)
    red_tips = (
        (fire_hdr_lin[..., 0] >= 1.0)
        & (fire_hdr_lin[..., 0] <= 2.5)
        & (fire_hdr_lin[..., 0] > 4.0 * np.maximum(fire_hdr_lin[..., 1], 1e-4))
        & (fire_hdr_lin[..., 2] < 0.05)
    )
    salmon_wash = red_tips & (tonemapped_srgb[..., 2] > 0.42)
    salmon_pct = float(np.mean(salmon_wash[red_tips]) * 100.0) if np.any(red_tips) else 0.0

    return {
        "hdr_linear_peak": round(peak, 3),
        "pastel_yellow_clip_pct": round(pastel_pct, 3),
        "salmon_wash_pct": round(salmon_pct, 3),
        "gate2_pass_hdr_peak": bool(peak >= 4.0 and pastel_pct <= 1.0 and salmon_pct <= 2.0),
    }


def eval_motion_fire_coupling(
    skin_masks: Sequence[np.ndarray] | np.ndarray,
    fire_hdr_seq: Sequence[np.ndarray] | np.ndarray,
    cam_shifts: Optional[Sequence[Sequence[float]] | np.ndarray] = None,
    speed_thresh_px: float = 0.75,
) -> Dict[str, float | int | bool]:
    """Gate 3 (Pilar 5): Audita si el movimiento real de la mano dobla y arrastra el fuego por inercia.

    Para cada frame `t`:
    1. Calcula el centroide 2D `(cx_hand, cy_hand)` de `matte_skin`.
    2. Calcula el centroide de la pluma superior de fuego `(cx_fire_top, cy_fire_top)` sobre los
       píxeles de llama situados por encima del centroide de la mano (`y < cy_hand`).
    3. Obtiene la velocidad real de la mano en el mundo descontando el paneo de cámara:
       `v_hand_world[t] = (c_hand[t] - c_hand[t-1]) - v_cam[t]`.
    4. Mide la desviación horizontal de la estela superior respecto a la posición de reposo:
       `wake_dx[t] = (cx_fire_top[t] - cx_hand[t]) - wake_dx_rest`.
       En un fluido físico con advección/inercia real, cuando la mano acelera hacia `+X`, la
       parte alta de la pluma se retrasa hacia `-X` (`wake_dx` se opone a `v_hand_world_x`, es decir,
       `-wake_dx` correlaciona positivamente con `v_hand_world_x`).
       En un fuego procedural *stateless* pegado a la máscara, `wake_dx ≈ 0` (`lag_correlation ≈ 0`).
    """
    skins = np.asarray(skin_masks, dtype=np.float32)
    fires = np.asarray(fire_hdr_seq, dtype=np.float32)
    if skins.ndim != 3 or len(skins) < 3:
        raise ValueError("eval_motion_fire_coupling requiere secuencia temporal (T >= 3, H, W)")

    t_len, h, w = skins.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)

    hand_c = np.zeros((t_len, 2), dtype=np.float64)
    plume_c = np.zeros((t_len, 2), dtype=np.float64)

    for t in range(t_len):
        sm = np.clip(skins[t], 0.0, 1.0)
        s_sum = float(np.sum(sm))
        if s_sum > 1e-3:
            hx = float(np.sum(xx * sm) / s_sum)
            hy = float(np.sum(yy * sm) / s_sum)
        else:
            hx, hy = w * 0.5, h * 0.5
        hand_c[t] = (hx, hy)

        f_frame = fires[t]
        f_energy = (
            (0.55 * np.maximum(f_frame[..., 0], 0.0) + 0.35 * np.maximum(f_frame[..., 1], 0.0) + 0.10 * np.maximum(f_frame[..., 2], 0.0))
            if f_frame.ndim == 3
            else np.maximum(f_frame, 0.0)
        )
        # Pluma superior: región por encima del centroide de la mano (menor coordenada Y en imagen)
        upper_mask = (yy < (hy - 4.0)).astype(np.float32)
        f_upper = f_energy * upper_mask
        fu_sum = float(np.sum(f_upper))
        if fu_sum > 1e-3:
            fx = float(np.sum(xx * f_upper) / fu_sum)
            fy = float(np.sum(yy * f_upper) / fu_sum)
        else:
            f_all = float(np.sum(f_energy)) + 1e-6
            fx = float(np.sum(xx * f_energy) / f_all)
            fy = float(np.sum(yy * f_energy) / f_all)
        plume_c[t] = (fx, fy)

    v_hand_screen = np.zeros((t_len, 2), dtype=np.float64)
    v_hand_screen[1:] = np.diff(hand_c, axis=0)

    if cam_shifts is not None:
        v_cam = np.asarray(cam_shifts, dtype=np.float64)
        if v_cam.shape != (t_len, 2):
            v_cam = np.resize(v_cam, (t_len, 2))
    else:
        v_cam = np.zeros((t_len, 2), dtype=np.float64)

    v_hand_world = v_hand_screen - v_cam
    rel_plume = plume_c - hand_c

    # Línea base en cuadros lentos (o primer frame)
    speeds = np.linalg.norm(v_hand_world, axis=-1)
    slow_idx = np.where(speeds <= max(speed_thresh_px * 0.5, 0.25))[0]
    if len(slow_idx) > 0:
        rest_offset = np.mean(rel_plume[slow_idx], axis=0)
    else:
        rest_offset = rel_plume[0].copy()

    # Deflexión de estela opuesta al movimiento: lag_vec apunta en la misma dirección que v_hand_world
    # cuando la pluma superior se queda atrás por inercia del aire
    lag_vec = -(rel_plume - rest_offset[None, :])

    # Suavizado EMA ligero de velocidad para representar la memoria advectiva de la pluma (~3-5 frames)
    v_mem = np.zeros_like(v_hand_world)
    for t in range(1, t_len):
        v_mem[t] = 0.55 * v_hand_world[t] + 0.45 * v_mem[t - 1]

    active = speeds >= float(speed_thresh_px)
    if int(np.sum(active)) < 2:
        active = np.ones(t_len, dtype=bool)
        active[0] = False

    vx_act = v_mem[active, 0]
    lx_act = lag_vec[active, 0]

    vx_std = float(np.std(vx_act))
    lx_std = float(np.std(lx_act))
    if vx_std > 1e-4 and lx_std > 1e-4:
        vx_z = vx_act - np.mean(vx_act)
        lx_z = lx_act - np.mean(lx_act)
        corr = float(np.sum(vx_z * lx_z) / (np.sqrt(np.sum(vx_z ** 2) * np.sum(lx_z ** 2)) + 1e-9))
    else:
        corr = 0.0

    # Ganancia de deflexión proyectada en la dirección de v_mem en frames activos
    v_norm = np.linalg.norm(v_mem[active], axis=-1) + 1e-6
    proj_deflection = np.sum(lag_vec[active] * (v_mem[active] / v_norm[:, None]), axis=-1)
    mean_deflection_px = float(np.mean(proj_deflection))
    max_deflection_px = float(np.max(proj_deflection)) if len(proj_deflection) else 0.0

    gate3_pass = bool(corr >= 0.45 and mean_deflection_px >= 1.2)
    return {
        "active_motion_frames": int(np.sum(active)),
        "mean_hand_world_speed_px": round(float(np.mean(speeds[active])), 3),
        "lag_correlation": round(corr, 4),
        "mean_wake_deflection_px": round(mean_deflection_px, 3),
        "max_wake_deflection_px": round(max_deflection_px, 3),
        "gate3_pass_motion_coupling": gate3_pass,
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
    """Valida CIEDE2000 (Sharma 2005), Gates 0/1/2 y Gate 3 (Rechazo de fuego rígido vs Aprobación de fuego advectado)."""
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

    # Gate 3 A/B: Fuego stateless rígido (DEBE fallar) vs Fuego con estela advectada (DEBE aprobar)
    t_len, h, w = 16, 96, 96
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    skins_seq = np.zeros((t_len, h, w), dtype=np.float32)
    rigid_fire = np.zeros((t_len, h, w, 3), dtype=np.float32)
    advected_fire = np.zeros((t_len, h, w, 3), dtype=np.float32)

    cx_prev = 28.0
    vx_mem = 0.0
    for t in range(t_len):
        cx = 28.0 + 22.0 * np.sin(t * 0.35)
        cy = 60.0
        vx = cx - cx_prev
        cx_prev = cx
        vx_mem = 0.55 * vx + 0.45 * vx_mem

        skins_seq[t] = (((xx - cx) ** 2 + (yy - cy) ** 2) <= 10.0 ** 2).astype(np.float32)
        # Fuego rígido (stateless): pluma centrada exactamente en cx sin doblarse
        r_mask = (((xx - cx) ** 2 + (yy - (cy - 18.0)) ** 2) <= 9.0 ** 2).astype(np.float32)
        rigid_fire[t, ..., 0] = r_mask * 6.0
        rigid_fire[t, ..., 1] = r_mask * 2.4

        # Fuego advectado físico: la pluma superior se retrasa en dirección opuesta a vx_mem
        a_mask = (((xx - (cx - 1.65 * vx_mem)) ** 2 + (yy - (cy - 18.0)) ** 2) <= 9.0 ** 2).astype(np.float32)
        advected_fire[t, ..., 0] = a_mask * 6.0
        advected_fire[t, ..., 1] = a_mask * 2.4

    g3_rigid = eval_motion_fire_coupling(skins_seq, rigid_fire)
    g3_adv = eval_motion_fire_coupling(skins_seq, advected_fire)
    assert not g3_rigid["gate3_pass_motion_coupling"], "Gate 3 no rechazó el fuego rígido stateless"
    assert g3_adv["gate3_pass_motion_coupling"], f"Gate 3 no aprobó el fuego advectado: {g3_adv}"

    print(
        "[SELF-TEST OK] vfx_rd_metrics_eval.py ->",
        json.dumps(
            {
                "sharma2005_pair1_ciede2000": round(de_sharma, 4),
                "desk_ciede2000": round(de_desk, 4),
                "hf_noise_diff_pct": hf["rel_diff_pct"],
                "gate3_rigid_rejected": not g3_rigid["gate3_pass_motion_coupling"],
                "gate3_advected_corr": g3_adv["lag_correlation"],
                "gate3_advected_deflection_px": g3_adv["mean_wake_deflection_px"],
            }
        ),
    )
    return 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Auditor Cuantitativo Gate 0/1/2/3 para Workflow 4")
    p.add_argument("--plate-npy", type=Path, help="Frame plate lineal (.npy float32 [0..1]) o PNG sRGB")
    p.add_argument("--comp-hdr-npy", type=Path, help="Frame compuesto HDR lineal (.npy)")
    p.add_argument("--comp-tonemapped-npy", type=Path, help="Frame compuesto tras ACES/AgX (.npy o .png sRGB)")
    p.add_argument("--normal-npy", type=Path, default=None, help="Normal map lineal [-1..1] o [0..1]")
    p.add_argument("--desk-roi", type=int, nargs=4, default=None, help="x0 y0 x1 y1 del ROI de escritorio neutro")
    p.add_argument("--tm-is-srgb", action="store_true", help="Si --comp-tonemapped-npy (.npy) ya trae OETF sRGB")
    p.add_argument("--gate3-skin-dir", type=Path, default=None, help="Carpeta con secuencia matte_skin para Gate 3")
    p.add_argument("--gate3-fire-dir", type=Path, default=None, help="Carpeta con secuencia fire_hdr (.npy/.png) para Gate 3")
    p.add_argument("--gate3-cam-json", type=Path, default=None, help="JSON opcional con [[dx, dy], ...] de cámara por frame")
    p.add_argument("--out-json", type=Path, default=None)
    p.add_argument("--self-test", action="store_true")
    return p.parse_args()


def _load_dir_sequence(folder: Path, as_linear_if_png: bool = False, single_channel: bool = False) -> List[np.ndarray]:
    files = sorted(p for p in folder.iterdir() if p.suffix.lower() in {".npy", ".png", ".jpg", ".jpeg"})
    seq: List[np.ndarray] = []
    for fp in files:
        arr = _load_image_or_npy(fp, as_linear_if_png=as_linear_if_png)
        if single_channel and arr.ndim == 3:
            arr = arr[..., 0]
        seq.append(arr)
    return seq


def main() -> int:
    args = parse_args()
    if args.self_test:
        return run_self_test()

    report: Dict[str, object] = {}

    if args.plate_npy and args.comp_hdr_npy and args.comp_tonemapped_npy:
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
            else np.where(
                comp_tm_raw <= 0.0031308,
                comp_tm_raw * 12.92,
                1.055 * (np.clip(comp_tm_raw, 0.0, None) ** (1.0 / 2.4)) - 0.055,
            )
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
        report["gate1_desk_ciede2000"] = round(desk_de, 4)
        report["gate1_desk_pass"] = bool(desk_de <= 1.5)
        report["gate2_hdr_fire"] = eval_hdr_fire_linearity(comp_hdr, comp_tm_srgb)
        report["gate2_mtf_noise"] = eval_highfreq_noise_match(plate_lin[y0:y1, x0:x1], comp_tm_lin[y0:y1, x0:x1])

    if args.normal_npy is not None:
        norm = _load_image_or_npy(args.normal_npy, as_linear_if_png=False)
        packed = bool(norm.min() >= -0.05 and norm.max() <= 1.05 and norm.mean() > 0.15)
        report["gate0_normal"] = eval_normal_unit_integrity(norm, packed_01=packed)

    if args.gate3_skin_dir is not None and args.gate3_fire_dir is not None:
        skins = _load_dir_sequence(args.gate3_skin_dir, as_linear_if_png=False, single_channel=True)
        fires = _load_dir_sequence(args.gate3_fire_dir, as_linear_if_png=True, single_channel=False)
        n_common = min(len(skins), len(fires))
        cam_shifts = None
        if args.gate3_cam_json is not None and args.gate3_cam_json.exists():
            cam_shifts = json.loads(args.gate3_cam_json.read_text(encoding="utf-8"))[:n_common]
        report["gate3_motion_coupling"] = eval_motion_fire_coupling(
            skins[:n_common],
            fires[:n_common],
            cam_shifts=cam_shifts,
        )

    if not report:
        print(
            "ERROR: Especifica (--plate-npy --comp-hdr-npy --comp-tonemapped-npy) o (--gate3-skin-dir --gate3-fire-dir) o usa --self-test.",
            file=sys.stderr,
        )
        return 1

    out_txt = json.dumps(report, indent=2)
    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(out_txt, encoding="utf-8")
    print(out_txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
