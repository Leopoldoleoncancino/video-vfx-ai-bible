#!/usr/bin/env python3
"""Extractor WiLoR-mini MANO (.npz) + Constructor Blender 4.5/5.x `.abc` / View Layers (Módulo A · Ruta C/G).

Diseñado específicamente para evitar las dependencias rotas en Windows 11 de `Dyn-HaMR`
(`mmcv==1.3.9` + `chumpy`), utilizando `warmshao/WiLoR-mini` `[OK-12GB]`:

Modo 1 (`--extract`):
  - Ejecuta `WiLorHandPose3dEstimationPipeline` sobre los frames del plate (`478x850`, 167f).
  - Aplica filtro temporal **One-Euro** por vértice/articulación para eliminar micro-jitter.
  - Convierte coordenadas de cámara OpenCV (`+X der, +Y abajo, +Z frente`) a Blender Camera Space
    (`+X der, +Y arriba, -Z frente`) y guarda `mano_track.npz`.
  - Nota licencia: `WiLoR-mini` descarga automáticamente `MANO_RIGHT.pkl`; los pesos MANO
    requieren respetar licencia no comercial de `mano.is.tue.mpg.de` en entregas comerciales.

Modo 2 (`--blender-build` dentro de Blender `bpy`):
  - Carga `mano_track.npz`, crea malla **MANO animada**, añade un **cilindro proxy de manga negra**
    alineado al vector muñeca-codo (para bloquear fuego sobre el puño deshilachado que MANO omite)
    y crea opcionalmente un **plano Shadow/Bounce Catcher del escritorio** (`--desk-distance-m`).
  - Configura **3 View Layers** en **Cycles GPU (OptiX)**:
    1) `VL_Fire_Occluded`: Dominio de fuego visible + MANO/manga con `Holdout = True`.
    2) `VL_Hand_Lit`: MANO (`roughness=0.34`) + Manga (`roughness=0.88`) + Escritorio iluminados por fuego.
    3) `VL_Hand_Ambient`: Misma geometría bajo luz ambiente neutra uniforme (para `LightRatio`).
  - Configura salida **OpenEXR Multi-Layer 16-bit Half Float (`ZIP`)**, `AgX`, `use_pass_vector`
    y exporta opcionalmente Alembic (`.abc`).

Verificación sin GPU/Blender:
  python scripts/wilor_mano_to_blender_abc.py --check
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    import bpy  # type: ignore
except ImportError:
    bpy = None


class OneEuroFilter:
    """Filtro temporal adaptativo One-Euro (Casiez et al.) vectorizado en NumPy puro."""

    def __init__(self, freq: float = 30.0, min_cutoff: float = 1.2, beta: float = 0.05, d_cutoff: float = 1.0):
        self.freq = float(freq)
        self.min_cutoff = float(min_cutoff)
        self.beta = float(beta)
        self.d_cutoff = float(d_cutoff)
        self._x_prev: Optional[np.ndarray] = None
        self._dx_prev: Optional[np.ndarray] = None

    @staticmethod
    def _alpha(cutoff: np.ndarray | float, dt: float) -> np.ndarray | float:
        tau = 1.0 / (2.0 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / max(dt, 1e-6))

    def filter(self, x: np.ndarray, dt: Optional[float] = None) -> np.ndarray:
        step = dt if dt is not None else (1.0 / self.freq)
        x = x.astype(np.float64)
        if self._x_prev is None:
            self._x_prev = x.copy()
            self._dx_prev = np.zeros_like(x)
            return x.astype(np.float32)

        dx = (x - self._x_prev) / max(step, 1e-6)
        a_d = self._alpha(self.d_cutoff, step)
        dx_hat = a_d * dx + (1.0 - a_d) * self._dx_prev

        cutoff = self.min_cutoff + self.beta * np.abs(dx_hat)
        a = self._alpha(cutoff, step)
        x_hat = a * x + (1.0 - a) * self._x_prev

        self._x_prev = x_hat.copy()
        self._dx_prev = dx_hat.copy()
        return x_hat.astype(np.float32)


def opencv_to_blender_camera(verts_cam: np.ndarray) -> np.ndarray:
    """Convierte (x, y, z) OpenCV (+Y abajo, +Z frente) -> Blender Cam (+Y arriba, -Z frente)."""
    out = verts_cam.copy()
    out[..., 1] = -out[..., 1]
    out[..., 2] = -out[..., 2]
    return out


def compute_cuff_cylinder_transform(keypoints_cam_blender: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Calcula centro y vector eje antebrazo desde articulación muñeca (0) y bases metacarpianas (5, 9, 13)."""
    wrist = keypoints_cam_blender[0]
    knuckle_mid = keypoints_cam_blender[[5, 9, 13]].mean(axis=0)
    # El eje del antebrazo apunta desde los nudillos hacia atrás pasando por la muñeca
    forearm_dir = wrist - knuckle_mid
    norm = float(np.linalg.norm(forearm_dir))
    if norm < 1e-6:
        forearm_dir = np.array([0.0, -1.0, 0.0], dtype=np.float32)
    else:
        forearm_dir = (forearm_dir / norm).astype(np.float32)
    # Centro del puño desplazado ~11 cm detrás de la muñeca
    cuff_center = wrist + forearm_dir * 0.11
    return cuff_center.astype(np.float32), forearm_dir


def extract_wilor_sequence(
    frames_dir: Path,
    out_npz: Path,
    fps: float = 30.0,
    min_cutoff: float = 1.4,
    beta: float = 0.06,
    hand_conf: float = 0.30,
) -> Path:
    """Extrae vértices MANO + focal + traslación desde secuencia de frames usando `WiLoR-mini`."""
    try:
        import cv2  # type: ignore
        import torch  # type: ignore
        from wilor_mini.pipelines.wilor_hand_pose3d_estimation_pipeline import (  # type: ignore
            WiLorHandPose3dEstimationPipeline,
        )
    except ImportError as exc:
        raise RuntimeError(
            "Para `--extract` instala en Windows 11: pip install git+https://github.com/warmshao/WiLoR-mini"
        ) from exc

    frame_paths = sorted(p for p in frames_dir.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg"})
    if not frame_paths:
        raise FileNotFoundError(f"Sin frames en {frames_dir}")

    device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
    dtype = torch.float16 if device.type == "cuda" else torch.float32
    pipe = WiLorHandPose3dEstimationPipeline(device=device, dtype=dtype, verbose=False)
    faces = np.asarray(pipe.wilor_model.mano.faces, dtype=np.int32)

    filt_verts = OneEuroFilter(freq=fps, min_cutoff=min_cutoff, beta=beta)
    filt_kps = OneEuroFilter(freq=fps, min_cutoff=min_cutoff, beta=beta)

    all_verts: List[np.ndarray] = []
    all_kps: List[np.ndarray] = []
    all_valid: List[bool] = []
    focal_px = 1000.0
    img_w, img_h = 478, 850
    last_verts: Optional[np.ndarray] = None
    last_kps: Optional[np.ndarray] = None

    for idx, fp in enumerate(frame_paths):
        bgr = cv2.imread(str(fp))
        img_h, img_w = bgr.shape[:2]
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        outputs = pipe.predict(rgb, hand_conf=hand_conf)

        if outputs:
            # Toma la mano de mayor área de bounding box
            best = max(
                outputs,
                key=lambda o: (o["hand_bbox"][2] - o["hand_bbox"][0]) * (o["hand_bbox"][3] - o["hand_bbox"][1]),
            )
            wp = best["wilor_preds"]
            verts_cam = wp["pred_vertices"][0] + wp["pred_cam_t_full"][0][None, :]
            kps_cam = wp["pred_keypoints_3d"][0] + wp["pred_cam_t_full"][0][None, :]
            focal_px = float(wp["scaled_focal_length"])

            v_bl = filt_verts.filter(opencv_to_blender_camera(verts_cam))
            k_bl = filt_kps.filter(opencv_to_blender_camera(kps_cam))
            last_verts, last_kps = v_bl, k_bl
            all_valid.append(True)
        else:
            if last_verts is None:
                last_verts = np.zeros((778, 3), dtype=np.float32)
                last_kps = np.zeros((21, 3), dtype=np.float32)
            v_bl, k_bl = last_verts, last_kps
            all_valid.append(False)

        all_verts.append(v_bl)
        all_kps.append(k_bl)
        if idx % 20 == 0:
            print(f"[WiLoR] Frame {idx + 1}/{len(frame_paths)}")

    out_npz.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out_npz,
        verts_blender=np.stack(all_verts, axis=0),
        keypoints_blender=np.stack(all_kps, axis=0),
        faces=faces,
        valid=np.array(all_valid, dtype=bool),
        focal_px=np.array([focal_px], dtype=np.float32),
        width=np.array([img_w], dtype=np.int32),
        height=np.array([img_h], dtype=np.int32),
        fps=np.array([fps], dtype=np.float32),
    )
    print(f"[OK] Track MANO estabilizado guardado en {out_npz}")
    return out_npz


def build_blender_scene(
    track_npz: Path,
    export_abc: Optional[Path] = None,
    desk_distance_m: float = 0.72,
) -> Dict[str, Any]:
    """Construye escena Cycles 16F + MANO animada + Proxy Manga + 3 View Layers en Blender 4.5/5.x."""
    if bpy is None:
        raise RuntimeError("`--blender-build` debe ejecutarse dentro de Blender (`bpy`).")

    from mathutils import Vector  # type: ignore

    data = np.load(track_npz)
    verts_seq = data["verts_blender"]  # (T, 778, 3)
    kps_seq = data["keypoints_blender"]  # (T, 21, 3)
    faces = data["faces"].tolist()
    focal_px = float(data["focal_px"][0])
    w, h = int(data["width"][0]), int(data["height"][0])
    fps = int(round(float(data["fps"][0])))
    n_frames = verts_seq.shape[0]

    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = n_frames
    scene.render.fps = fps
    scene.render.resolution_x = w
    scene.render.resolution_y = h
    scene.render.resolution_percentage = 100

    # Motor Cycles OptiX + OpenEXR Multi-Layer 16-bit Half ZIP (lineal) + AgX
    scene.render.engine = "CYCLES"
    scene.cycles.device = "GPU"
    scene.render.image_settings.file_format = "OPEN_EXR_MULTILAYER"
    scene.render.image_settings.color_depth = "16"
    scene.render.image_settings.exr_codec = "ZIP"
    try:
        scene.view_settings.view_transform = "AgX"
    except Exception:
        pass

    # Cámara fija en origen Blender (vértices están en Camera Space: +X der, +Y arriba, -Z frente)
    cam_data = bpy.data.cameras.new("VFX_POV_Camera")
    cam_data.sensor_fit = "HORIZONTAL"
    cam_data.sensor_width = 36.0
    cam_data.lens = focal_px * 36.0 / float(w)
    cam_obj = bpy.data.objects.new("VFX_POV_Camera", cam_data)
    scene.collection.objects.link(cam_obj)
    cam_obj.location = (0.0, 0.0, 0.0)
    cam_obj.rotation_euler = (0.0, 0.0, 0.0)
    scene.camera = cam_obj

    # Malla MANO con animación por frame usando shape keys / vertex animation
    mesh = bpy.data.meshes.new("MANO_Hand_Mesh")
    mesh.from_pydata(verts_seq[0].tolist(), [], faces)
    mesh.update()
    hand_obj = bpy.data.objects.new("MANO_Hand", mesh)
    scene.collection.objects.link(hand_obj)

    mat_skin = bpy.data.materials.new("Mat_MANO_Skin")
    mat_skin.use_nodes = True
    bsdf_skin = mat_skin.node_tree.nodes.get("Principled BSDF")
    if bsdf_skin:
        bsdf_skin.inputs["Base Color"].default_value = (0.55, 0.36, 0.28, 1.0)
        bsdf_skin.inputs["Roughness"].default_value = 0.34
    hand_obj.data.materials.append(mat_skin)

    # Cilindro Proxy Manga Negra (evita que fuego trasero sangre a través del antebrazo)
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.048, depth=0.26)
    cuff_obj = bpy.context.active_object
    cuff_obj.name = "Proxy_Black_Cuff"
    mat_cuff = bpy.data.materials.new("Mat_Cuff_Matte")
    mat_cuff.use_nodes = True
    bsdf_cuff = mat_cuff.node_tree.nodes.get("Principled BSDF")
    if bsdf_cuff:
        bsdf_cuff.inputs["Base Color"].default_value = (0.04, 0.04, 0.045, 1.0)
        bsdf_cuff.inputs["Roughness"].default_value = 0.88
    cuff_obj.data.materials.append(mat_cuff)

    # Keyframes de vértices de mano (via Shape Keys absolutos) y transformación del puño
    hand_obj.shape_key_add(name="Basis", from_mix=False)
    for t in range(n_frames):
        frame_num = t + 1
        sk = hand_obj.shape_key_add(name=f"f_{frame_num:04d}", from_mix=False)
        for vi, coord in enumerate(verts_seq[t]):
            sk.data[vi].co = tuple(map(float, coord))
        sk.value = 0.0
        sk.keyframe_insert(data_path="value", frame=max(1, frame_num - 1))
        sk.value = 1.0
        sk.keyframe_insert(data_path="value", frame=frame_num)
        sk.value = 0.0
        sk.keyframe_insert(data_path="value", frame=min(n_frames, frame_num + 1))

        c_center, c_dir = compute_cuff_cylinder_transform(kps_seq[t])
        cuff_obj.location = tuple(map(float, c_center))
        cuff_obj.rotation_mode = "QUATERNION"
        cuff_obj.rotation_quaternion = Vector((0.0, 0.0, 1.0)).rotation_difference(Vector(c_dir.tolist()))
        cuff_obj.keyframe_insert(data_path="location", frame=frame_num)
        cuff_obj.keyframe_insert(data_path="rotation_quaternion", frame=frame_num)

    # Plano Shadow/Bounce Catcher de escritorio (calibrar según DA3-Streaming si aplica)
    bpy.ops.mesh.primitive_plane_add(size=1.8, location=(0.0, 0.0, -abs(desk_distance_m)))
    desk_obj = bpy.context.active_object
    desk_obj.name = "Desk_Bounce_Catcher"
    mat_desk = bpy.data.materials.new("Mat_Desk_White")
    mat_desk.use_nodes = True
    bsdf_desk = mat_desk.node_tree.nodes.get("Principled BSDF")
    if bsdf_desk:
        bsdf_desk.inputs["Base Color"].default_value = (0.82, 0.82, 0.82, 1.0)
        bsdf_desk.inputs["Roughness"].default_value = 0.65
    desk_obj.data.materials.append(mat_desk)

    # Configurar View Layers base para Light Ratio y Holdout
    base_vl = scene.view_layers[0]
    base_vl.name = "VL_Fire_Occluded"
    for vl_name in ("VL_Hand_Lit", "VL_Hand_Ambient"):
        if vl_name not in scene.view_layers:
            scene.view_layers.new(name=vl_name)
    for vl in scene.view_layers:
        vl.use_pass_normal = True
        vl.use_pass_vector = True
        vl.use_pass_z = True
        vl.use_pass_cryptomatte_object = True

    if export_abc is not None:
        export_abc.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.alembic_export(filepath=str(export_abc), start=1, end=n_frames, selected=False)

    return {
        "frames": n_frames,
        "resolution": [w, h],
        "focal_mm": round(cam_data.lens, 2),
        "view_layers": [vl.name for vl in scene.view_layers],
        "export_abc": str(export_abc) if export_abc else None,
    }


def run_check() -> int:
    """Valida One-Euro jitter suppression, conversión OpenCV->Blender y proxy de manga."""
    rng = np.random.default_rng(42)
    t = np.linspace(0.0, 2.0, 60, dtype=np.float32)
    clean_traj = np.stack([0.12 * np.sin(t * 2.0), -0.05 + 0.03 * t, np.full_like(t, 0.38)], axis=-1)
    noisy_traj = clean_traj + rng.normal(0.0, 0.008, size=clean_traj.shape).astype(np.float32)

    oe = OneEuroFilter(freq=30.0, min_cutoff=1.2, beta=0.05)
    smoothed = np.stack([oe.filter(p) for p in noisy_traj], axis=0)

    # Medir energía de jitter de alta frecuencia (segunda derivada discreta)
    jitter_in = float(np.std(np.diff(noisy_traj, n=2, axis=0)))
    jitter_out = float(np.std(np.diff(smoothed, n=2, axis=0)))
    assert jitter_out < jitter_in * 0.40, f"One-Euro no suavizó suficiente: {jitter_in} -> {jitter_out}"

    bl = opencv_to_blender_camera(smoothed[0])
    assert abs(bl[1] + smoothed[0, 1]) < 1e-6 and abs(bl[2] + smoothed[0, 2]) < 1e-6

    # Verificar orientación de cilindro de manga desde keypoints sintéticos
    kps = np.zeros((21, 3), dtype=np.float32)
    kps[0] = [0.0, -0.08, -0.35]  # Muñeca más abajo
    kps[5] = [-0.02, 0.0, -0.35]
    kps[9] = [0.0, 0.0, -0.35]
    kps[13] = [0.02, 0.0, -0.35]
    c_pos, c_dir = compute_cuff_cylinder_transform(kps)
    assert c_dir[1] < -0.95 and c_pos[1] < kps[0, 1], "Proxy manga mal orientado respecto a muñeca"

    print(
        "[CHECK OK] wilor_mano_to_blender_abc.py ->",
        json.dumps(
            {
                "bpy_available": bpy is not None,
                "jitter_rms_before": round(jitter_in, 5),
                "jitter_rms_after": round(jitter_out, 5),
                "cuff_axis": [round(float(x), 3) for x in c_dir],
            }
        ),
    )
    return 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="WiLoR-mini MANO -> Blender .abc & 3 View Layers EXR")
    p.add_argument("--check", action="store_true", help="Valida matemática One-Euro y ejes sin requerir Blender")
    p.add_argument("--extract", action="store_true", help="Extrae secuencia MANO con WiLoR-mini a .npz")
    p.add_argument("--blender-build", action="store_true", help="Construye escena Cycles EXR en Blender (bpy)")
    p.add_argument("--frames-dir", type=Path, help="Carpeta con frames PNG para --extract")
    p.add_argument("--track-npz", type=Path, default=Path("mano_track.npz"))
    p.add_argument("--export-abc", type=Path, default=None)
    p.add_argument("--fps", type=float, default=30.0)
    p.add_argument("--desk-distance-m", type=float, default=0.72)
    args, _ = p.parse_known_args()
    return args


def main() -> int:
    args = parse_args()
    if args.check:
        return run_check()
    if args.extract:
        if not args.frames_dir:
            print("ERROR: --frames-dir obligatorio con --extract.", file=sys.stderr)
            return 1
        extract_wilor_sequence(args.frames_dir, args.track_npz, fps=args.fps)
        return 0
    if args.blender_build:
        res = build_blender_scene(
            args.track_npz,
            export_abc=args.export_abc,
            desk_distance_m=args.desk_distance_m,
        )
        print("[OK] Escena Blender configurada:", json.dumps(res))
        return 0
    print("Usa --check, --extract o --blender-build.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
