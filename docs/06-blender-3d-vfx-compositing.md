# 06 · Blender 4.5+/5.x, 3D VFX, 3D Gaussian Splatting, Mocap, Natron & DaVinci Resolve

Este pilar conecta el mundo **3D / Compositing / Etalonaje** con la automatización por agentes (**MCP**) y la IA generativa local en **Windows 11 + RTX 3060 12 GB + Ryzen 9 5900X**.

---

## 1. Blender 4.5 LTS – 5.2+ MCPs (Control por Agentes IA)

| Proyecto | Repo / Fuente | Stars | Enfoque |
|---|---|---|---|
| **Official Blender MCP** | [`blender.org/lab/mcp-server/`](https://www.blender.org/lab/mcp-server/) (Blender Lab) | Oficial | Extensión oficial integrada para Blender 5.1 / 5.2 LTS (y 4.5 LTS); usa `uv` y expone Python API con interfaz oficial para Claude, Codex y Antigravity. |
| **MCP for Blender** *(antes `blender-mcp`)* | [`ahujasid/mcp-for-blender`](https://github.com/ahujasid/mcp-for-blender) (MIT · PyPI `mcp-for-blender`) | **34,935** | El estándar comunitario: socket puerto `9876`, descarga automática de assets PolyHaven/Sketchfab/Hyper3D, inspección de escena y ejecución de scripts `bpy`. |
| **Blender MCP Pro** | [`youichi-uda/blender-mcp-pro`](https://github.com/youichi-uda/blender-mcp-pro) | 34 | Más de **100 herramientas granulares** para Geometry Nodes, Shader Nodes, luces, modificadores y animación. |
| **VFX Agent Toolkit** | [`sideshowroberto/vfx-agent-toolkit`](https://github.com/sideshowroberto/vfx-agent-toolkit) (MIT) | 19 | Marketplace de **+70 skills y conectores MCP para estudios VFX**: **Blender, Nuke, Houdini, Unreal Engine 5.8, Maya, ComfyUI, Magnific y Seedance**. |

---

## 2. Bridges ComfyUI ↔ Blender, Generación 3D & 3D Gaussian Splatting (3DGS)

### A. Texturas, Renders e IA 3D en 12 GB VRAM
- **[`AIGODLIKE/ComfyUI-BlenderAI-node`](https://github.com/AIGODLIKE/ComfyUI-BlenderAI-node)** (★1,594 · GPL-3.0): Ejecuta ComfyUI desde dentro de Blender para proyectar texturas generadas por IA, upscaling de renders Cycles y estilos por viewport.
- **[`microsoft/TRELLIS.2`](https://github.com/microsoft/TRELLIS.2)** (★12,993 · MIT) + **[`visualbruno/ComfyUI-Trellis2`](https://github.com/visualbruno/ComfyUI-Trellis2)** (★890 · MIT): Conversión *Image-to-3D* con latentes estructurados compactos y exportación `.glb` limpia hacia Blender.
- **[`Tencent-Hunyuan/Hunyuan3D-2.1`](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1)** (★4,484): Mallas 3D de alta fidelidad con mapas PBR (albedo/roughness/metallic). En **3060 12 GB**, usa las opciones de low-VRAM/cuantización o el nodo integrado de **Wan2GP (`mmgp`)**.
- **[`MrForExample/ComfyUI-3D-Pack`](https://github.com/MrForExample/ComfyUI-3D-Pack)** (★3,913 · MIT): Suite veterana multi-algoritmo (3DGS, TripoSR, meshes, UV unwrapping).

### B. 3D Gaussian Splatting (3DGS) para Integración VFX
- **[`Kiri-Innovation/3dgs-render-blender-addon`](https://github.com/Kiri-Innovation/3dgs-render-blender-addon)** (★1,269 · GPL-2.0): Renderiza y edita archivos `.ply` de 3D Gaussian Splatting nativamente dentro de Blender con sombras/cámaras reales.
- **[`nerfstudio-project/gsplat`](https://github.com/nerfstudio-project/gsplat)** (★5,918 · Apache-2.0): Motor CUDA ultrarrápido de entrenamiento y rasterización 3DGS (totalmente acelerado en tu RTX 3060).
- **[`storytold/spark`](https://github.com/storytold/spark)** (★142 · MIT): Renderer 3DGS avanzado para Three.js usado dentro del ecosistema ArtCraft.

---

## 3. Motion Capture sin Marcadores (Video / Webcam → Blender Rig)

| Herramienta | Repo | Stars | Licencia | Qué resuelve en local |
|---|---|---|---|---|
| **GVHMR** *(SIGGRAPH Asia / TPAMI 2026)* | [`zju3dv/GVHMR`](https://github.com/zju3dv/GVHMR) | 2,306 | Ver repo | **MoCap monocular en coordenadas de mundo**: recupera movimiento 3D humano completo desde un simple video de celular **sin drifting aunque la cámara se mueva** (`Gravity-View Coordinates`). Corre cómodo en 12 GB VRAM. |
| **FreeMoCap + Blender Addon** | [`freemocap/freemocap`](https://github.com/freemocap/freemocap) + [`freemocap_blender_addon`](https://github.com/freemocap/freemocap_blender_addon) | 10,840 | AGPL-3.0 | Sistema multi-webcam sincronizado gratuito (usa tus puertos USB del Ryzen 9 5900X) que exporta esqueletos 3D y datos de dedos/rostro directo a Blender. |

---

## 4. Compositing Nodal & Etalonaje / Finishing

### A. DaVinci Resolve + MCP
- **[`samuelgursky/davinci-resolve-mcp`](https://github.com/samuelgursky/davinci-resolve-mcp)** (★4,196 · MIT · v5.3.4):
  - **Cobertura completa (37 a 390 tools)** del API de DaVinci Resolve Studio (Media Pool, Edición, Fusion, Color, Fairlight, Render Queue) + panel de control web local.
  - **Seguridad incorporada:** Bloquea operaciones destructivas irreversibles (como `copy_grades` sin confirmar) a menos que se pase `acknowledge_trap: true`.
  - *Requisito:* DaVinci Resolve **Studio** (la versión gratuita bloquea el API scripting externo en IPC).

### B. Natron (Compositor Nodal Open-Source & OpenFX)
- **[`NatronGitHub/Natron`](https://github.com/NatronGitHub/Natron)** (★5,731 · GPL-2.0):
  - Compositor nodal estilo Nuke con pipeline de color flotante 32-bit lineal y ecosistema **`openfx-misc`** / **`openfx-io`**.
  - *Nota honesta:* Aunque los repos reciben mantenimiento comunitario continuo de compilación y parches, su arquitectura core no evoluciona al ritmo de Nuke/Fusion o EffectCraft; úsalo especialmente para pipelines headless batch de OpenFX sin licencias.

### C. Intercambio Universal de Timelines: OpenTimelineIO
- **[`AcademySoftwareFoundation/OpenTimelineIO`](https://github.com/AcademySoftwareFoundation/OpenTimelineIO)** (★2,102 · Apache-2.0):
  - La "Piedra de Rosetta" para automatizar entre **Premiere XML ↔ DaVinci Resolve ↔ Kdenlive ↔ Blender VSE ↔ scripts Python**: lee, transforma, sustituye rutas de clips procesados con IA y re-exporta sin corromper cortes ni marcadores.
