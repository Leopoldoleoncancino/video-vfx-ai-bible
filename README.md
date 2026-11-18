# Biblia de Herramientas: Video IA Local, VFX, TouchDesigner, Blender, ArtCraft & Adobe

> **Edición Fundacional (Fase 1 · Noviembre 2026)** — Base de conocimiento viva, plantillas MCP, *Skills* de agente, scripts Windows 11 y **Radar Diario Automatizado**.

---

## Perfil de Hardware Objetivo (Calibrado al Milímetro)

| Componente | Especificación | Implicación Crítica en Video IA & VFX |
|---|---|---|
| **GPU** | **NVIDIA RTX 3060 · 12 GB VRAM** *(Ampere)* | Los **12 GB** superan el muro de las 8 GB, pero **no hay FP8 Tensor Core nativo**: prioriza pesos **`GGUF (Q4_K_M / Q5_K_M)`** o **`INT8` (`mmgp`)** + `SageAttention` + `Tiled VAE`. |
| **CPU** | **AMD Ryzen 9 5900X** *(12C / 24T)* | Excelente para offloading BlockSwap, **FilmCraft / EffectCraft (Rust)**, encoding, VapourSynth y FreeMoCap multi-cámara. |
| **RAM** | **32 GB DDR4** | **Techo operativo real (~22–24 GB libres en Win 11):** evita Text Encoders BF16 gigantes junto a DiT 14B/22B sin cuantizar, cierra Premiere/AE/Chrome antes de difusión y fija Pagefile NVMe >=32 GB. |
| **OS** | **Windows 11** | Usa ruedas Windows de **`woct0rdho/triton-windows`**, **`woct0rdho/SageAttention`**, **Spout2** y puente `PlayerDebugMode = 1` para CEP Adobe. |

---

## Mapa Maestro de la Biblia (7 Capítulos + Recursos Operativos)

| Pilar | Documento | Qué cubre |
|---|---|---|
| **01 · IA Video Local** | [`docs/01-local-ai-video-12gb-32gb.md`](docs/01-local-ai-video-12gb-32gb.md) | Wan 2.2 (5B/14B GGUF), LTX-2.3/2.5 + LTX-Desktop, HunyuanVideo 1.5, FramePack, VACE, SkyReels-V2, Wan2GP (`mmgp`), ComfyUI (`GGUF`, `SageAttention`), InfiniteTalk, EchoMimic v3, `comfy-mcp`. |
| **02 · Roto, Matting & Depth** | [`docs/02-rotoscoping-matting-chroma-depth.md`](docs/02-rotoscoping-matting-chroma-depth.md) | MatAnyone 2 (CVPR '26), SAM 3, VideoMaMa (CVPR '26), ComfyUI-RMBG/BiRefNet/RVM, EffectErase (CVPR '26 objeto+sombra+reflejo), ProPainter, DiffuEraser, Video Depth Anything, DepthCrafter, Relit-LiVE (SIGGRAPH '26). |
| **03 · Enfoque Especial: ArtCraft** | [`docs/03-artcraft-deep-dive.md`](docs/03-artcraft-deep-dive.md) | **ArtCraft Studio** (`storytold/artcraft`) + **17 Crafting Apps en Rust puro** (FilmCraft, EffectCraft, AniCraft, PhotoCraft, LightCraft, TextureCraft, MaterialCraft, SoundCraft, etc.), Lottie/JSON, `.mcp.json` nativo y matriz honesta de paridad alpha vs Adobe. |
| **04 · Enfoque Especial: Adobe** | [`docs/04-adobe-video-deep-dive.md`](docs/04-adobe-video-deep-dive.md) | Premiere Object Mask & Media Intelligence, MCPs (`premiere-pro-mcp`, `Adobe_Premiere_Pro_MCP`, `opencutagent`, `@kumoproductions/mcp-aftereffects`, `Dakkshin/after-effects-mcp`), `Bolt UXP` / `Bolt CEP`, puentes ProRes 4444 ↔ IA Local ↔ EffectCraft. |
| **05 · TouchDesigner Real-Time** | [`docs/05-touchdesigner-realtime.md`](docs/05-touchdesigner-realtime.md) | TouchDesigner 2025+ **POPs/POPX**, oficial **`TouchDesigner/TDMCP`** + `TDMCPSkills` (con soporte nativo Antigravity!), **`Embody / Envoy`** (TDXN YAML Git), `touchdesigner-mcp`, `td-mcp-rs`, StreamDiffusionTD, ComfyUI-TD, MediaPipe-TD, Spout2/NDI. |
| **06 · Blender, 3D VFX & Resolve** | [`docs/06-blender-3d-vfx-compositing.md`](docs/06-blender-3d-vfx-compositing.md) | Blender Official MCP (5.1/5.2+), `mcp-for-blender`, `vfx-agent-toolkit`, ComfyUI-BlenderAI-node, TRELLIS.2, Hunyuan3D 2.1, 3DGS (`Kiri-Innovation`, `gsplat`, `spark`), MoCap (`GVHMR`, `FreeMoCap`), `davinci-resolve-mcp`, Natron/OpenFX, OpenTimelineIO. |
| **07 · NLEs Open-Source, CLI & VSR** | [`docs/07-opensource-nles-cli-upscaling.md`](docs/07-opensource-nles-cli-upscaling.md) | `OpenCut`, `LosslessCut`, `Shotcut`, `Kdenlive` (aviso Olive pausado), `auto-editor`, `PySceneDetect`, `MoviePy`, `VapourSynth + vs-mlrt`, `Remotion`, `Motion Canvas`, **SeedVR2**, **FlashVSR/FlashVSR+**, **Practical-RIFE**. |
| **Workflows End-to-End** | [`workflows/END_TO_END_PIPELINES.md`](workflows/END_TO_END_PIPELINES.md) | Blueprints paso a paso para VFX híbrido, Sweet-Spot 480p→SeedVR2→RIFE y automatización IA/Live. |
| **Plantillas MCP (Win 11)** | [`mcps/README.md`](mcps/README.md) | [`win11_unified_mcp_config.json`](mcps/win11_unified_mcp_config.json) & [`artcraft_adobe_mcp.json`](mcps/artcraft_adobe_mcp.json). |
| **Skills de Agente IA** | [`skills/`](skills/) | 3 skills listas: `video-vfx-3060-12gb-local`, `artcraft-adobe-vfx-bridge`, `daily-vfx-radar`. |
| **Scripts Windows 11 & VFX** | [`scripts/`](scripts/) | `check_3060_env.ps1`, `comfyui_3060_12gb_launch.bat`, `ffmpeg_nvenc_prores_helpers.ps1`, `batch_matting_pipeline.py`, `daily_radar.py`. |
| **Automatización Diaria (`/automation`)** | [`automation/ANTIGRAVITY_DAILY_AUTOMATION.md`](automation/ANTIGRAVITY_DAILY_AUTOMATION.md) | Guía `/automation` Antigravity + GitHub Action diario ([`.github/workflows/daily-radar.yml`](.github/workflows/daily-radar.yml)) + [`RADAR_DAILY.md`](RADAR_DAILY.md). |

---

## Matriz Comparativa Rápida — ¿Qué Herramienta Uso Hoy en Mi PC?

| Necesito... | Elección #1 en 3060 12GB (Local) | Alternativa Rápida / Estudio | Integración Agente (MCP/CLI) |
|---|---|---|---|
| **Generar video T2V / I2V sin frustraciones** | **Wan2GP (`mmgp`)** con Wan 2.2 5B / 14B INT8 | ComfyUI + `WanVideoWrapper` + `GGUF Q4_K_M` | `Comfy-Org/comfy-mcp` |
| **Video con audio y diálogos nativos** | **LTX-2.3 / 2.5 GGUF** o `LTX-Desktop` | `InfiniteTalk` / `EchoMimic v3` (para talking heads) | `ComfyUI-LTXVideo` |
| **Video largo (>15s) desde una imagen** | **FramePack** (6–8 GB VRAM) | Wan Animate + `ComfyUI-WanAnimatePlus` | CLI / Gradio / ComfyUI |
| **Rotoscopia de cabello/ropa sin green screen** | **SAM 2/3 ➔ MatAnyone 2** | **VideoMaMa** (conserva *motion blur*) / Premiere Object Mask | Subproceso Python / ComfyUI |
| **Borrar persona/objeto + su sombra y reflejo** | **EffectErase** (`Wan2.1-1.3B-InP`) | **ProPainter** (cables/marcas rígidas rápido) | CLI Python |
| **Z-Depth consistente para compositing** | **Video Depth Anything** (Small/Base) | **DepthCrafter** (transparencias/reflejos) | ComfyUI / CLI |
| **Re-iluminar un video grabado** | **Relit-LiVE** (SIGGRAPH 2026) | IC-Light / GenLit (por stills) | CLI Python |
| **Motion Graphics por código / Git / Lottie** | **EffectCraft** (`storytold`) | **Remotion** / **Motion Canvas** | **`effectcraft-cli mcp`** (nativo) |
| **Motion Graphics / VFX comerciales clientes** | **Adobe After Effects** + **Premiere Pro** | **DaVinci Resolve Studio** (Fusion/Color) | `@kumoproductions/mcp-aftereffects` + `premiere-pro-mcp` |
| **Limpiar silencios y retakes al instante** | **Open Cut Agent** (Premiere) o **`auto-editor`** | `LosslessCut` (recorte manual sin re-encode) | Puerto `3001` / CLI XML |
| **Visuales interactivos y audio-reactivos** | **TouchDesigner 2025+ (POPs)** + **StreamDiffusionTD** | Blender 5.x + Geometry Nodes / **Spout2** | **`TouchDesigner/TDMCP`** o **`Embody`** |
| **3D VFX, 3DGS y MoCap sin traje** | **Blender 5.x** + **GVHMR** + `3dgs-render-blender-addon` | **ArtCraft Studio** (previs rápida) + **TRELLIS.2** | Oficial Blender MCP / `mcp-for-blender` / `vfx-agent-toolkit` |
| **Escalar 480p→1080p y pasar 16→32/60fps** | **SeedVR2 (3B/block-swap)** + **Practical-RIFE** | **FlashVSR** (con tiling) / VapourSynth `vs-mlrt` | ComfyUI / CLI |

---

## Hoja de Ruta Progresiva (Fase 1 → Fase 2)

- **Fase 1 (Completada en este repo):** Mapa integral de los 6 pilares, calibración estricta 3060 12GB / 32GB RAM / Windows 11, enfoque profundo en ArtCraft y Adobe, configs MCP verificadas, 3 Skills, scripts operativos y Radar Diario automatizado.
- **Fase 2 (Módulos Profundos bajo demanda):** Cuando decidas atacar un módulo específico, podemos profundizar con guías paso a paso y JSON exportables en:
  1. **Módulo A — Tuning & Workflows JSON ComfyUI 3060:** Workflows `.json` importables listos para Wan 2.2 GGUF + MatAnyone 2 + SeedVR2.
  2. **Módulo B — Taller Práctico ArtCraft + Adobe Bridge:** Compilar `effectcraft-cli.exe` / `filmcraft-cli.exe` en Windows 11, crear un plugin propio UXP/CEP con `bolt-uxp` conectado a ComfyUI.
  3. **Módulo C — TouchDesigner + Blender MCP en Vivo:** Setup de `TDMCP` + `Embody` + `StreamDiffusionTD` + `GVHMR` → rig Blender.
