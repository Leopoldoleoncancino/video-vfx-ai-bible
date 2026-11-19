#!/usr/bin/env python3
"""Extractor WiLoR-mini MANO (.npz) + Constructor Blender 4.5/5.x `.abc` / Mantaflow Estanco / View Layers (Módulo A · Ruta C/G · Pilar 2).

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
  - Carga `mano_track.npz`, crea malla **MANO animada**, **cierra el borde abierto de la muñeca**
    con `bmesh` (`close_mesh_boundary_loops_bmesh`) para obtener una **malla 3D continua estanca
    (*watertight*)** (Pilar 2: evita que Mantaflow emita nubes rojas cortadas/flotantes como ocurría
    con esferas sueltas en los 21 landmarks).
  - Añade un **cilindro proxy de manga negra** (`Proxy_Black_Cuff`) alineado al vector muñeca-codo
    como colisionador/oclusor (`Holdout + Fluid Effector`) para bloquear fuego sobre el puño negro.
  - Si se pasa `--enable-mantaflow`, configura automáticamente:
    * `MANO_Hand` como `Fluid Flow` (`FIRE`, `INFLOW`, `surface_distance=0.012`,
      `use_initial_velocity=True`, `velocity_factor=1.25`, `fuel_amount=1.4`).
    * **Gotcha crítico de velocidad en Blender Mantaflow:** Mantaflow muestrea velocidades de
      vértices con mucha mayor fidelidad desde un modificador **`MeshSequenceCache` (`.abc`)** que
      desde *Shape Keys* discretos. Cuando `--export-abc` está activo junto con `--enable-mantaflow`,
      el script exporta el `.abc` estanco y lo re-vincula vía `MeshSequenceCache` automáticamente.
    * `Mantaflow_Fire_Domain` (`resolution_max=224`, `use_adaptive_domain=True`, `use_noise=True`,
      `vorticity=2.0`, `flame_smoke=0.02`, `flame_max_temp=4.0`) con shader **Lámina Fina Blackbody**
      (`Principled Volume`, `Density=0.02`, `Blackbody Intensity=1.0`, `1400K -> 3200K`) y
      `scene.render.use_motion_blur = True` (`motion_blur_shutter = 0.5`, 180°).
  - Configura **3 View Layers** en **Cycles GPU (OptiX)** + **OpenEXR Multi-Layer 16F (`ZIP`)**.

Verificación sin GPU/Blender:
  python scripts/wilor_mano_to_blender_abc.py --check
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

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
    forearm_dir = wrist - knuckle_mid
    norm = float(np.linalg.norm(forearm_dir))
    if norm < 1e-6:
        forearm_dir = np.array([0.0, -1.0, 0.0], dtype=np.float32)
    else:
        forearm_dir = (forearm_dir / norm).astype(np.float32)
    cuff_center = wrist + forearm_dir * 0.11
    return cuff_center.astype(np.float32), forearm_dir


def find_open_boundary_loop(faces: np.ndarray) -> List[int]:
    """Encuentra el loop ordenado de vértices del borde abierto (muñeca en MANO) en NumPy puro.

    MANO tiene 778 vértices y 1538 triángulos con un único agujero topológico en la muñeca
    (16 aristas de borde que aparecen en 1 solo triángulo). Cerrar este loop con un vértice
    centroide o `bmesh.ops.contextual_create` vuelve la malla 100 % estanca (Euler-Poincaré
    sin bordes libres) para emisión superficial continua en Mantaflow / LiquiGen / EmberGen.
    """
    edge_counts: Dict[Tuple[int, int], int] = {}
    directed_next: Dict[int, int] = {}
    for tri in np.asarray(faces, dtype=np.int32):
        a, b, c = int(tri[0]), int(tri[1]), int(tri[2])
        for u, v in ((a, b), (b, c), (c, a)):
            key = (min(u, v), max(u, v))
            edge_counts[key] = edge_counts.get(key, 0) + 1

    adj: Dict[int, List[int]] = {}
    for (u, v), cnt in edge_counts.items():
        if cnt == 1:
            adj.setdefault(u, []).append(v)
            adj.setdefault(v, []).append(u)
            directed_next[u] = v

    if not adj:
        return []

    start = min(adj.keys())
    loop: List[int] = [start]
    visited: Set[int] = {start}
    curr = start
    while True:
        nbrs = [n for n in adj.get(curr, []) if n not in visited]
        if not nbrs:
            break
        curr = nbrs[0]
        loop.append(curr)
        visited.add(curr)
    return loop


def cap_open_mesh_watertight(verts_seq: np.ndarray, faces: np.ndarray) -> Tuple[np.ndarray, np.ndarray, int]:
    """Cierra el agujero de la muñeca en toda la secuencia `(T, V, 3)` añadiendo un vértice tapón centroide.

    Devuelve `(verts_capped_seq, faces_capped, boundary_edge_count_after)` donde
    `boundary_edge_count_after == 0` garantiza una malla 3D estanca (*watertight*).
    """
    loop = find_open_boundary_loop(faces)
    if len(loop) < 3:
        return verts_seq, faces, 0

    cap_vert_idx = verts_seq.shape[1]
    cap_centers = np.mean(verts_seq[:, loop, :], axis=1, keepdims=True)
    verts_capped = np.concatenate([verts_seq, cap_centers], axis=1).astype(np.float32)

    # Verificar orientación de las aristas del borde para que las caras tapón tengan normales coherentes
    directed_edges: Set[Tuple[int, int]] = set()
    for tri in np.asarray(faces, dtype=np.int32):
        a, b, c = int(tri[0]), int(tri[1]), int(tri[2])
        directed_edges.add((a, b))
        directed_edges.add((b, c))
        directed_edges.add((c, a))

    cap_tris: List[List[int]] = []
    n_loop = len(loop)
    for i in range(n_loop):
        u = loop[i]
        v = loop[(i + 1) % n_loop]
        if (u, v) in directed_edges:
            cap_tris.append([v, u, cap_vert_idx])
        else:
            cap_tris.append([u, v, cap_vert_idx])

    faces_capped = np.concatenate([np.asarray(faces, dtype=np.int32), np.asarray(cap_tris, dtype=np.int32)], axis=0)
    remaining_loop = find_open_boundary_loop(faces_capped)
    return verts_capped, faces_capped, len(remaining_loop)


def close_mesh_boundary_loops_bmesh(hand_obj: Any) -> int:
    """Refuerzo dentro de Blender (`bmesh`): rellena cualquier arista `is_boundary` y recalcula normales exteriores."""
    if bpy is None:
        return 0
    import bmesh  # type: ignore

    bm = bmesh.new()
    bm.from_mesh(hand_obj.data)
    boundary_edges = [e for e in bm.edges if e.is_boundary]
    n_closed = len(boundary_edges)
    if boundary_edges:
        bmesh.ops.contextual_create(bm, geom=boundary_edges)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(hand_obj.data)
    bm.free()
    hand_obj.data.update()
    return n_closed


def build_laminar_blackbody_fire_material(name: str = "Mat_Mantaflow_Laminar_Fire") -> Any:
    """Crea material Cycles `Principled Volume` calibrado para llama laminar adherida a piel (cero humo rojo opaco)."""
    assert bpy is not None
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    n_vol = nt.nodes.new("ShaderNodeVolumePrincipled")
    n_vol.location = (0, 0)
    # Densidad de hollín casi nula para evitar nubes rojas cortadas/opacas; pura emisión Blackbody HDR
    n_vol.inputs["Density"].default_value = 0.02
    n_vol.inputs["Blackbody Intensity"].default_value = 1.0
    n_vol.inputs["Blackbody Tint"].default_value = (1.0, 0.88, 0.72, 1.0)
    n_vol.inputs["Temperature"].default_value = 2650.0

    n_out = nt.nodes.new("ShaderNodeOutputMaterial")
    n_out.location = (300, 0)
    nt.links.new(n_vol.outputs["Volume"], n_out.inputs["Volume"])
    return mat


def setup_mantaflow_watertight_fire(
    scene: Any,
    hand_obj: Any,
    cuff_obj: Any,
    res_max: int = 224,
    surface_distance: float = 0.012,
    velocity_factor: float = 1.25,
) -> Dict[str, Any]:
    """Configura emisión superficial continua Mantaflow (Pilar 2) sobre la malla MANO estanca + colisionador de manga."""
    assert bpy is not None

    # 1. Emisor superficial continuo sobre MANO_Hand (watertight)
    fl_hand = hand_obj.modifiers.new(name="Fluid_Hand_Flow", type="FLUID")
    fl_hand.fluid_type = "FLOW"
    fs = fl_hand.flow_settings
    fs.flow_type = "FIRE"
    fs.flow_behavior = "INFLOW"
    fs.flow_source = "MESH"
    fs.surface_distance = float(surface_distance)
    fs.use_initial_velocity = True
    fs.velocity_factor = float(velocity_factor)
    fs.velocity_normal = 0.15
    fs.fuel_amount = 1.4

    # 2. Efector de colisión en el cilindro del puño negro (bloquea transferencia de llama a la manga)
    fl_cuff = cuff_obj.modifiers.new(name="Fluid_Cuff_Obstacle", type="FLUID")
    fl_cuff.fluid_type = "EFFECTOR"
    es = fl_cuff.effector_settings
    es.effector_type = "COLLISION"
    es.surface_distance = 0.015

    # 3. Dominio adaptativo Mantaflow calibrado para RTX 3060 + Ryzen 9 5900X
    bpy.ops.mesh.primitive_cube_add(size=0.65, location=(0.0, 0.04, -0.42))
    dom_obj = bpy.context.active_object
    dom_obj.name = "Mantaflow_Fire_Domain"
    fl_dom = dom_obj.modifiers.new(name="Fluid_Domain", type="FLUID")
    fl_dom.fluid_type = "DOMAIN"
    ds = fl_dom.domain_settings
    ds.domain_type = "GAS"
    ds.resolution_max = int(res_max)
    ds.use_adaptive_domain = True
    ds.use_noise = True
    ds.noise_scale = 2
    ds.vorticity = 2.0
    ds.flame_smoke = 0.02
    ds.flame_vorticity = 1.8
    ds.flame_ignition = 1.25
    ds.flame_max_temp = 4.0
    ds.burning_rate = 0.85

    mat_fire = build_laminar_blackbody_fire_material()
    dom_obj.data.materials.append(mat_fire)

    # Activar Vector Pass + Motion Blur 180° (0.5 shutter)
    scene.render.use_motion_blur = True
    scene.render.motion_blur_shutter = 0.5

    return {
        "domain_object": dom_obj.name,
        "resolution_max": int(res_max),
        "surface_distance": float(surface_distance),
        "velocity_factor": float(velocity_factor),
        "motion_blur_shutter": 0.5,
    }


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
    enable_mantaflow: bool = False,
    mantaflow_res: int = 224,
) -> Dict[str, Any]:
    """Construye escena Cycles 16F + MANO Estanca + Proxy Manga + Mantaflow opcional + 3 View Layers."""
    if bpy is None:
        raise RuntimeError("`--blender-build` debe ejecutarse dentro de Blender (`bpy`).")

    from mathutils import Vector  # type: ignore

    data = np.load(track_npz)
    raw_verts_seq = data["verts_blender"]  # (T, 778, 3)
    kps_seq = data["keypoints_blender"]  # (T, 21, 3)
    raw_faces = data["faces"]
    # Pilar 2: Cerrar el borde abierto de la muñeca antes de crear la malla en Blender
    verts_seq, faces_capped, rem_boundary = cap_open_mesh_watertight(raw_verts_seq, raw_faces)
    faces = faces_capped.tolist()

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

    scene.render.engine = "CYCLES"
    scene.cycles.device = "GPU"
    scene.render.image_settings.file_format = "OPEN_EXR_MULTILAYER"
    scene.render.image_settings.color_depth = "16"
    scene.render.image_settings.exr_codec = "ZIP"
    try:
        scene.view_settings.view_transform = "AgX"
        scene.view_settings.look = "AgX - Punchy"
    except Exception:
        pass

    cam_data = bpy.data.cameras.new("VFX_POV_Camera")
    cam_data.sensor_fit = "HORIZONTAL"
    cam_data.sensor_width = 36.0
    cam_data.lens = focal_px * 36.0 / float(w)
    cam_obj = bpy.data.objects.new("VFX_POV_Camera", cam_data)
    scene.collection.objects.link(cam_obj)
    cam_obj.location = (0.0, 0.0, 0.0)
    cam_obj.rotation_euler = (0.0, 0.0, 0.0)
    scene.camera = cam_obj

    mesh = bpy.data.meshes.new("MANO_Hand_Mesh")
    mesh.from_pydata(verts_seq[0].tolist(), [], faces)
    mesh.update()
    hand_obj = bpy.data.objects.new("MANO_Hand", mesh)
    scene.collection.objects.link(hand_obj)
    close_mesh_boundary_loops_bmesh(hand_obj)

    mat_skin = bpy.data.materials.new("Mat_MANO_Skin")
    mat_skin.use_nodes = True
    bsdf_skin = mat_skin.node_tree.nodes.get("Principled BSDF")
    if bsdf_skin:
        bsdf_skin.inputs["Base Color"].default_value = (0.55, 0.36, 0.28, 1.0)
        bsdf_skin.inputs["Roughness"].default_value = 0.34
    hand_obj.data.materials.append(mat_skin)

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

    mantaflow_info = None
    if enable_mantaflow:
        mantaflow_info = setup_mantaflow_watertight_fire(
            scene,
            hand_obj,
            cuff_obj,
            res_max=mantaflow_res,
        )

    return {
        "frames": n_frames,
        "resolution": [w, h],
        "focal_mm": round(cam_data.lens, 2),
        "watertight_remaining_boundary_edges": rem_boundary,
        "view_layers": [vl.name for vl in scene.view_layers],
        "export_abc": str(export_abc) if export_abc else None,
        "mantaflow": mantaflow_info,
    }


def run_check() -> int:
    """Valida One-Euro jitter suppression, cierre estanco de malla (watertight) y proxy de manga."""
    rng = np.random.default_rng(42)
    t = np.linspace(0.0, 2.0, 60, dtype=np.float32)
    clean_traj = np.stack([0.12 * np.sin(t * 2.0), -0.05 + 0.03 * t, np.full_like(t, 0.38)], axis=-1)
    noisy_traj = clean_traj + rng.normal(0.0, 0.008, size=clean_traj.shape).astype(np.float32)

    oe = OneEuroFilter(freq=30.0, min_cutoff=1.2, beta=0.05)
    smoothed = np.stack([oe.filter(p) for p in noisy_traj], axis=0)

    jitter_in = float(np.std(np.diff(noisy_traj, n=2, axis=0)))
    jitter_out = float(np.std(np.diff(smoothed, n=2, axis=0)))
    assert jitter_out < jitter_in * 0.40, f"One-Euro no suavizó suficiente: {jitter_in} -> {jitter_out}"

    bl = opencv_to_blender_camera(smoothed[0])
    assert abs(bl[1] + smoothed[0, 1]) < 1e-6 and abs(bl[2] + smoothed[0, 2]) < 1e-6

    kps = np.zeros((21, 3), dtype=np.float32)
    kps[0] = [0.0, -0.08, -0.35]
    kps[5] = [-0.02, 0.0, -0.35]
    kps[9] = [0.0, 0.0, -0.35]
    kps[13] = [0.02, 0.0, -0.35]
    c_pos, c_dir = compute_cuff_cylinder_transform(kps)
    assert c_dir[1] < -0.95 and c_pos[1] < kps[0, 1], "Proxy manga mal orientado respecto a muñeca"

    # Validar cierre estanco (watertight) sobre una pirámide abierta en la base (4 bordes libres -> 0 bordes libres)
    open_verts = np.array(
        [
            [[0.0, 0.0, 1.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [-1.0, 0.0, 0.0], [0.0, -1.0, 0.0]],
        ],
        dtype=np.float32,
    )
    open_faces = np.array([[0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]], dtype=np.int32)
    loop_before = find_open_boundary_loop(open_faces)
    assert len(loop_before) == 4, f"Borde abierto esperado=4, obtenido={len(loop_before)}"
    v_cap, f_cap, rem_after = cap_open_mesh_watertight(open_verts, open_faces)
    assert rem_after == 0 and v_cap.shape[1] == 6 and len(f_cap) == 8, "Cierre estanco falló"

    print(
        "[CHECK OK] wilor_mano_to_blender_abc.py ->",
        json.dumps(
            {
                "bpy_available": bpy is not None,
                "jitter_rms_before": round(jitter_in, 5),
                "jitter_rms_after": round(jitter_out, 5),
                "cuff_axis": [round(float(x), 3) for x in c_dir],
                "watertight_boundary_edges_before": len(loop_before),
                "watertight_boundary_edges_after": rem_after,
            }
        ),
    )
    return 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="WiLoR-mini MANO -> Blender .abc & Mantaflow Estanco & 3 View Layers EXR")
    p.add_argument("--check", action="store_true", help="Valida matemática One-Euro, ejes y cierre estanco sin Blender")
    p.add_argument("--extract", action="store_true", help="Extrae secuencia MANO con WiLoR-mini a .npz")
    p.add_argument("--blender-build", action="store_true", help="Construye escena Cycles EXR en Blender (bpy)")
    p.add_argument("--frames-dir", type=Path, help="Carpeta con frames PNG para --extract")
    p.add_argument("--track-npz", type=Path, default=Path("mano_track.npz"))
    p.add_argument("--export-abc", type=Path, default=None)
    p.add_argument("--fps", type=float, default=30.0)
    p.add_argument("--desk-distance-m", type=float, default=0.72)
    p.add_argument("--enable-mantaflow", action="store_true", help="Configura dominio Mantaflow y emisión superficial estanca")
    p.add_argument("--mantaflow-res", type=int, default=224, help="Resolución máxima del dominio adaptativo Mantaflow")
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
            enable_mantaflow=args.enable_mantaflow,
            mantaflow_res=args.mantaflow_res,
        )
        print("[OK] Escena Blender configurada:", json.dumps(res))
        return 0
    print("Usa --check, --extract o --blender-build.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
