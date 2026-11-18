# 06 · Blender 4.5+/5.x, 3D VFX, 3D Gaussian Splatting, Mocap, Natron & DaVinci Resolve

Este pilar conecta el mundo **3D / Compositing / Etalonaje** con la automatización por agentes (**MCP**) y la IA generativa local en **Windows 11 + RTX 3060 12 GB + Ryzen 9 5900X**.

---

## 1. Blender 4.5 LTS – 5.2+ MCPs (Control por Agentes IA)

| Proyecto | Repo / Fuente | Stars | Enfoque |
|---|---|---|---|
| **Official Blender MCP** | [`blender.org/lab/mcp-server/`](https://www.blender.org/lab/mcp-server/) (Blender Lab) | Oficial | Extensión oficial integrada para Blender 5.1 / 5.2 LTS (y 4.5 LTS); usa `uv` y expone Python API con interfaz oficial para Claude, Codex y Antigravity. |
| **MCP for Blender** *(antes `blender-mcp`)* | [`ahujasid/mcp-for-blender`](https://github.com/ahujasid/mcp-for-blender) (MIT · PyPI `mcp-for-blender`) | **34,936** | El estándar comunitario: socket puerto `9876`, asistente `uvx mcp-for-blender setup` (detecta **Antigravity**), PolyHaven/Sketchfab/Hyper3D y scripts `bpy`. |
| **Blender MCP Ultra** | [`carlosh7/blender-mcp`](https://github.com/carlosh7/blender-mcp) (MIT · `blender-mcp-ultra`) | 21 | **248 herramientas tipadas**, loop visual EEVEE, blocklist AST de seguridad y pruebas E2E headless Windows/Linux/macOS. |
| **Blender MCP Pro** | [`youichi-uda/blender-mcp-pro`](https://github.com/youichi-uda/blender-mcp-pro) | 34 | Más de **100 herramientas granulares** para Geometry Nodes, Shader Nodes, luces, modificadores y animación. |
| **VFX Agent Toolkit** | [`sideshowroberto/vfx-agent-toolkit`](https://github.com/sideshowroberto/vfx-agent-toolkit) (MIT) | 19 | Marketplace de **+70 skills y conectores MCP para estudios VFX**: **Blender, Nuke, Houdini, Unreal Engine 5.8, Maya, ComfyUI, Magnific y Seedance**. |

---

## 2. Bridges ComfyUI ↔ Blender, Spout2, Generación 3D & 3DGS

### A. Texturas, Spout2, Renders e IA 3D en 12 GB VRAM
- **[`maybites/TextureSharing`](https://github.com/maybites/TextureSharing)** (★188 · `v9.1.1+`) & **[`fonotipooo/blender-video-input`](https://github.com/fonotipooo/blender-video-input)**: puente **Spout2 / NDI / OMT** en Blender 4.5 / 5.x. Enviar cámara/Z-Depth/**Normal Pass** ([`scripts/blender_normal_pass_setup.py`](../scripts/blender_normal_pass_setup.py)) desde Blender hacia TouchDesigner va a GPU 0 ms (`Spout Sender`), mientras que recibir video dentro de Blender copia vía CPU (`Image.pixels`). Ver capítulo completo [`docs/08-normal-passes-realtime-post.md`](08-normal-passes-realtime-post.md).
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
| **RGBMoCap Suite (GVHMR + FlowHMR + ExMR + PEAR)** | [`toyxyz/toyxyz_RGBMocap`](https://github.com/toyxyz/toyxyz_RGBMocap) | Activo Nov '26 | MIT / Ver repo | GUI todo-en-uno para Windows 11 (`install.cmd`) que unifica **GVHMR** (~**4.20 GiB VRAM** / 6.87 GiB RAM), **FlowHMR** (`flowhmr/flowhmr`), corrección de pisadas, retarget Mixamo/VRM/PMX y exportación directa **FBX / BVH / `.blend`**. |
| **GVHMR** *(SIGGRAPH Asia / TPAMI 2026)* | [`zju3dv/GVHMR`](https://github.com/zju3dv/GVHMR) | 2,306 | Ver repo | **MoCap monocular en coordenadas de mundo**: recupera movimiento 3D humano completo desde un video de celular **sin drifting aunque la cámara se mueva** (`Gravity-View Coordinates`). |
| **FreeMoCap + Blender Addon** | [`freemocap/freemocap`](https://github.com/freemocap/freemocap) + [`freemocap_blender_addon`](https://github.com/freemocap/freemocap_blender_addon) | 10,840 | AGPL-3.0 | Sistema multi-webcam sincronizado gratuito (usa tus puertos USB del Ryzen 9 5900X) que exporta esqueletos 3D y datos de dedos/rostro directo a Blender. |
| **WiLoR / Dyn-HaMR (Malla MANO 3D)** | [`rolpotamias/WiLoR`](https://github.com/rolpotamias/WiLoR) · [`ZhengdiYu/Dyn-HaMR`](https://github.com/ZhengdiYu/Dyn-HaMR) | — | Ver repos | **`[OK-12GB]` / `[TIGHT-12GB]`:** Reconstrucción anatómica de manos 3D (**MANO**) desde video monocular (incluso con cámara móvil dinámica). Exportable a **Alembic `.abc`** hacia Blender para oclusión dedo-a-dedo exacta, normales sin ruido y colisión física de fluidos (supera ampliamente a proxies cilíndricos). *(Aplicar filtro Kalman / One-Euro antes de simular fluidos).* |

> 👉 **Guía práctica completa (Fase 2):** Configs paso a paso de Blender + Antigravity + TouchDesigner + Spout2 + OSC + GVHMR en [`docs/modules/MODULE_C_TD_BLENDER_VFX.md`](modules/MODULE_C_TD_BLENDER_VFX.md).

---

## 4. Compositing Nodal & Etalonaje / Finishing

### A. DaVinci Resolve + MCP
- **[`samuelgursky/davinci-resolve-mcp`](https://github.com/samuelgursky/davinci-resolve-mcp)** (★4,196 · MIT · v5.3.4):
  - **Cobertura completa (37 a 390 tools)** del API de DaVinci Resolve Studio (Media Pool, Edición, Fusion, Color, Fairlight, Render Queue) + panel de control web local.
  - **Seguridad incorporada:** Bloquea operaciones destructivas irreversibles (como `copy_grades` sin confirmar) a menos que se pase `acknowledge_trap: true`.
  - **Tip VFX Relighting (`ReLight`):** En Color usa el esquema 2 nodos (`Output Surface Map` cacheado ➔ `Use Input 2`); en Fusion conecta tu Normal Pass externo (EXR 16F de Blender, `NormalCrafter` o `Lotus-2`) directo al **puerto verde `Normals`** de `Relight [RLT]` ([ver Pilar 08](08-normal-passes-realtime-post.md)).
  - *Requisito:* DaVinci Resolve **Studio** (la versión gratuita bloquea el API scripting externo en IPC).

### B. Natron (Compositor Nodal Open-Source & OpenFX)
- **[`NatronGitHub/Natron`](https://github.com/NatronGitHub/Natron)** (★5,731 · GPL-2.0):
  - Compositor nodal estilo Nuke con pipeline de color flotante 32-bit lineal y ecosistema **`openfx-misc`** / **`openfx-io`**.
  - *Nota honesta:* Aunque los repos reciben mantenimiento comunitario continuo de compilación y parches, su arquitectura core no evoluciona al ritmo de Nuke/Fusion o EffectCraft; úsalo especialmente para pipelines headless batch de OpenFX sin licencias.

### C. Intercambio Universal de Timelines: OpenTimelineIO
- **[`AcademySoftwareFoundation/OpenTimelineIO`](https://github.com/AcademySoftwareFoundation/OpenTimelineIO)** (★2,102 · Apache-2.0):
  - La "Piedra de Rosetta" para automatizar entre **Premiere XML ↔ DaVinci Resolve ↔ Kdenlive ↔ Blender VSE ↔ scripts Python**: lee, transforma, sustituye rutas de clips procesados con IA y re-exporta sin corromper cortes ni marcadores.

---

## 5. Simulación Física de Fuego, OpenEXR Multi-Layer & Compositing Lineal (`ACEScg` / `AgX`)

Cuando un plano VFX involucra fuego o energía interactuando con anatomía humana, componer MP4s en `8-bit yuv420p` destruye las altas luces (>1.0) y provoca clipping amarillo pastel. El estándar físico en **RTX 3060 12 GB + Blender 4.5+** combina simulación limpia con pases lineales:

### 5.1 Simulación de Fuego Realista en Blender (Mantaflow o OpenVDB Externo) `[OK-12GB]`
- **Geometría de Colisión & Emisión:** Importa la malla **MANO (`.abc`)** desde `WiLoR` / `Dyn-HaMR` + un proxy cilíndrico para antebrazo/ropa. Configura la velocidad de emisión heredada del movimiento de los dedos para que el fuego arrastre inercia en giros rápidos.
- **Parámetros Mantaflow (Ryzen 9 5900X + Adaptive Domain):** `Resolution Divisions: 224–288` con **Adaptive Domain** activado, `Noise Upres Factor: 2` (`Wavelet Noise` para micro-filamentos), `Vorticity: 1.8–2.5`, `Flame Smoke: 0.0–0.05` (evita nubes opacas grises). Alternativamente, importa simulaciones `.vdb` (ej. EmberGen) vinculadas a los huesos del rig.
- **Shader `Principled Volume` Blackbody:** Conduce `Blackbody Intensity` por `Temperature` (`1400K` bordes rojo-ámbar → `3200K` núcleo blanco incandescente) modulada por un `Noise Texture 3D` advectado que rompa la suavidad uniforme del voxel.

### 5.2 Receta de View Layers OpenEXR 16-bit Half-Float y *Albedo-Divided Light Ratio*
Complementando [`scripts/blender_normal_pass_setup.py`](../scripts/blender_normal_pass_setup.py) (Pilar 08), para transferir iluminación y sombras reales del fuego sobre la piel **sin mostrar la textura sintética del modelo 3D**:

```python
# Referencia Blender Python (bpy): Setup de OpenEXR Multi-Layer Lineal + View Layers para Fuego/Relight
import bpy

scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "GPU"  # OPTIX en RTX 3060

# 1) Salida estrictamente Lineal 16-bit Half-Float (el Tone Map AgX/ACES es solo visualizador, NO se hornea en EXR)
scene.render.image_settings.file_format = "OPEN_EXR_MULTILAYER"
scene.render.image_settings.color_depth = "16"
scene.render.image_settings.exr_codec = "ZIP"
scene.view_settings.view_transform = "AgX"

# 2) Habilitar AOVs esenciales en el View Layer activo
vl = bpy.context.view_layer
vl.use_pass_normal = True
vl.use_pass_vector = True             # Motion vectors reales para motion blur en compositor
vl.use_pass_z = True
vl.use_pass_cryptomatte_object = True # Máscaras exactas por objeto (mano vs manga vs escritorio)

# 3) Arquitectura de 3 View Layers en Compositing:
# - VL_Fire_Occluded: Dominio de fuego visible + malla MANO (.abc) y proxy manga con Holdout = True
# - VL_Hand_Lit: Malla MANO (Principled Roughness ~0.35 piel, ~0.88 tela) + proxy fondo iluminados SOLO
#                por emisión del volumen (Dominio con visible_camera = False)
# - VL_Hand_Ambient: Misma geometría bajo luz ambiente neutra uniforme
# En compositor: LightRatio = VL_Hand_Lit / max(VL_Hand_Ambient, 1e-4) -> multiplicar sobre Plate Real Lineal
```

### 5.3 Orden Estricto del Compositing Óptico Lineal (`ACEScg` / `Linear Rec.709`)

```text
[01. Plate Original] ──► (sRGB → Linear / ACEScg) ──► (De-grain temporal leve)
                                                               │
[02. Matte Piel + Matte Ropa] ──┐                              ▼
[03. Normales 16f + Depth 16f] ─┼──► [04. Relighting (Light Ratio / Normales + Sombras SSDO)]
[05. Light Ratio / UniLumos] ───┘              │
                                               ▼
[06. Fuego BACK (Detrás del sujeto)] ──► (Linear Plus / Over HDR)
                                               │
                                               ▼
                                    [07. Sujeto Reiluminado]
                                               │
                                               ▼
[08. Fuego FRONT (Oclusión 3D)] ──────► (Core Opacity + Emisión HDR > 1.0)
                                               │
                                               ▼
[09. Óptica de Lente en HDR Lineal (SIEMPRE ANTES DEL TONE MAPPER)]
     ├── Exponential Glow (3 radios: núcleo 4px, medio 24px, atmosférico 96px)
     ├── Red Halation (sangrado rojo sutil en sensor para picos > 1.5)
     ├── Heat Haze / Refraction (distorsión ascendente por gradiente térmico)
     └── Light Wrap de contorno (2–4 px en silueta iluminada; bloqueado en zonas opacas sombreadas)
                                               │
                                               ▼
[10. ACES Filmic / AgX Tone Map] ──► [11. Re-grain igualado al sensor + Aberración Cromática] ──► [sRGB]
```

| Motor de Compositing | Pipeline `32-bit Linear` + `EXR` | Relighting con Normales | Mejor Uso en Tu Estación |
|---|---|---|---|
| **Blender Compositor** | Nativo (`AgX` / OCIO) | Nativo con pases Cycles | Ideal cuando ya simulas el fuego/malla MANO en Blender. |
| **DaVinci Resolve (Fusion)** | Nativo (`ACEScct` / `Linear`) | `Relight [RLT]` (puerto verde) | Etalonaje final + finishing comercial multipista (Studio requerido para API MCP). |
| **Natron (`openfx-misc`)** | Nativo 32-bit float | `Shadertoy` / plugins OFX | Automatización batch headless sin licencias ni Python OpenCV artesanal. |
| **After Effects (`32 bpc`)** | Via OCIO + `32 bpc` | `Normality` / `Normal Mapper` | Entregas comerciales de agencia y motion graphics integrados vía MCP. |
| **EffectCraft (`wgpu`)** | GPU Rust lineal (`wgpu`) | Shaders WGSL / 3D PBR | Previsualización ágil/UI y motion vectorial Lottie; usar Blender/Fusion/AE `32 bpc` para EXR multi-layer complejo. |
