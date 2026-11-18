"""Helper Blender 4.5 / 5.x para crear Shader AOVs y Material Override de Normal Pass.

Genera dos assets listos para VFX y transmisión en vivo Spout2 (`maybites/TextureSharing`):
1. Material `VFX_Normal_CameraSpace_OpenGL`: emite normales en espacio de cámara OpenGL
   empaquetadas en [0, 1] via (N * 0.5 + 0.5), ideal para:
   - Enviar por Spout2 (`BlenderNormals`) hacia TouchDesigner / StreamDiffusionTD ControlNet.
   - Exportar mapa compatible con NormalCrafter / Lotus / After Effects `Normality` / Fusion.
2. Shader AOVs en el View Layer activo (`VFX_CamNormal` y `VFX_WorldNormal`) para exportar
   EXR 16-bit Half Float / 32-bit Float lineal sin alterar el material original (Cycles/EEVEE).

Uso en Blender (Scripting tab o Blender MCP `execute_blender_code`):
    exec(open(r"C:\\Tools\\video-vfx-ai-bible\\scripts\\blender_normal_pass_setup.py").read())

Verificación sintáctica fuera de Blender:
    python scripts/blender_normal_pass_setup.py --check
"""

from __future__ import annotations

import argparse
import sys

try:
    import bpy  # type: ignore
except ImportError:
    bpy = None


def build_camera_normal_material(name: str = "VFX_Normal_CameraSpace_OpenGL"):
    """Crea (o recrea) un material Emission puro con Normal OpenGL Camera-Space [0..1]."""
    assert bpy is not None
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    n_geom = nt.nodes.new("ShaderNodeNewGeometry")
    n_geom.location = (-600, 0)

    n_vtrans = nt.nodes.new("ShaderNodeVectorTransform")
    n_vtrans.location = (-360, 0)
    n_vtrans.vector_type = "NORMAL"
    n_vtrans.convert_from = "WORLD"
    n_vtrans.convert_to = "CAMERA"

    # Empaque [ -1, +1 ] -> [ 0, 1 ]: N_cam * (0.5, 0.5, 0.5) + (0.5, 0.5, 0.5)
    # Nota: en Blender Camera Space, +X es derecha, +Y es arriba (OpenGL +Y), +Z sale hacia la cámara.
    n_madd = nt.nodes.new("ShaderNodeVectorMath")
    n_madd.location = (-120, 0)
    n_madd.operation = "MULTIPLY_ADD"
    n_madd.inputs[1].default_value = (0.5, 0.5, 0.5)
    n_madd.inputs[2].default_value = (0.5, 0.5, 0.5)

    n_emit = nt.nodes.new("ShaderNodeEmission")
    n_emit.location = (120, 0)
    n_emit.inputs["Strength"].default_value = 1.0

    n_out = nt.nodes.new("ShaderNodeOutputMaterial")
    n_out.location = (340, 0)

    nt.links.new(n_geom.outputs["Normal"], n_vtrans.inputs["Vector"])
    nt.links.new(n_vtrans.outputs["Vector"], n_madd.inputs[0])
    nt.links.new(n_madd.outputs["Vector"], n_emit.inputs["Color"])
    nt.links.new(n_emit.outputs["Emission"], n_out.inputs["Surface"])
    return mat


def register_viewlayer_aovs(scene) -> list[str]:
    """Registra Shader AOVs en el View Layer activo para salida OpenEXR lineal."""
    vl = bpy.context.view_layer
    created: list[str] = []
    for aov_name in ("VFX_CamNormal", "VFX_WorldNormal"):
        existing = next((a for a in vl.aovs if a.name == aov_name), None)
        if existing is None:
            aov = vl.aovs.add()
            aov.name = aov_name
            aov.type = "COLOR"
            created.append(aov_name)
    # Activar el pase Normal estándar del View Layer también (útil en Cycles/EEVEE Compositor)
    vl.use_pass_normal = True
    return created


def configure_linear_exr_defaults(scene) -> None:
    """Configura View Transform Raw / Standard para evitar distorsión gamma al previsualizar."""
    # Para transmisión directa de Spout2 en Normal Override, Standard/Raw evita curva Filmic/AgX.
    # Mantenemos nota explícita sin destruir el look si el usuario solo quería los AOVs.
    img = scene.render.image_settings
    if img.file_format in {"OPEN_EXR", "OPEN_EXR_MULTILAYER"}:
        img.color_depth = "16"
        img.exr_codec = "DWAA"


def setup_normal_passes(apply_override: bool = False) -> dict[str, object]:
    if bpy is None:
        raise RuntimeError(
            "Este script debe ejecutarse dentro de Blender (Python `bpy`). "
            "Para pruebas fuera de Blender usa `--check`."
        )
    scene = bpy.context.scene
    mat = build_camera_normal_material()
    added_aovs = register_viewlayer_aovs(scene)
    configure_linear_exr_defaults(scene)
    if apply_override:
        bpy.context.view_layer.material_override = mat
        scene.view_settings.view_transform = "Raw"
    return {
        "material": mat.name,
        "aovs_added": added_aovs,
        "override_applied": apply_override,
        "view_layer": bpy.context.view_layer.name,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Setup VFX Normal Pass (Camera/World + Spout2) en Blender")
    parser.add_argument("--check", action="store_true", help="Valida sintaxis CLI sin requerir Blender `bpy`.")
    parser.add_argument(
        "--apply-override",
        action="store_true",
        help="Asigna VFX_Normal_CameraSpace_OpenGL como Material Override del View Layer activo y View Transform=Raw.",
    )
    args, _ = parser.parse_known_args(argv)

    if args.check:
        print("OK: blender_normal_pass_setup.py listo para Blender 4.5 / 5.x (bpy disponible:", bpy is not None, ")")
        return 0

    if bpy is None:
        print(
            "Aviso: `bpy` no está disponible fuera de Blender. Ejecuta este script dentro de Blender "
            "o usa `--check` para validar la instalación.",
            file=sys.stderr,
        )
        return 1

    res = setup_normal_passes(apply_override=args.apply_override)
    print("Blender Normal Pass Setup OK:", res)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
