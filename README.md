# Biblia de Herramientas: Video IA Local, VFX, TouchDesigner, Blender, ArtCraft, Adobe & JS Motion

> **Edición Completa (11 Pilares + Módulos A & C · Noviembre 2026)** — Base de conocimiento viva, guías para agentes IA ([`AGENTS.md`](AGENTS.md) · [`GEMINI.md`](GEMINI.md) · [`CLAUDE.md`](CLAUDE.md)), plantillas MCP, *Skills*, scripts Windows 11 y **Radar Diario Automatizado**.

---

## Perfil de Hardware Objetivo (Calibrado al Milímetro)

| Componente | Especificación | Implicación Crítica en Video IA & VFX |
|---|---|---|
| **GPU** | **NVIDIA RTX 3060 · 12 GB VRAM** *(Ampere)* | Los **12 GB** superan el muro de las 8 GB, pero **no hay FP8 Tensor Core nativo**: prioriza pesos **`GGUF (Q4_K_M / Q5_K_M)`** o **`INT8` (`mmgp`)** + `SageAttention` + `Tiled VAE`. |
| **CPU** | **AMD Ryzen 9 5900X** *(12C / 24T)* | Excelente para offloading BlockSwap, **FilmCraft / EffectCraft (Rust)**, **Remotion / Motion Canvas / Playwright (animaciones JS en CPU)**, audio (`DeepFilterNet`), COLMAP y VapourSynth. |
| **RAM** | **32 GB DDR4** | **Techo operativo real (~22–24 GB libres en Win 11):** evita Text Encoders BF16 gigantes junto a DiT 14B/22B sin cuantizar, cierra Premiere/AE/Chrome antes de difusión y fija Pagefile NVMe >=32 GB. |
| **OS** | **Windows 11** | Usa ruedas Windows de **`woct0rdho/triton-windows`**, **`woct0rdho/SageAttention`**, **Spout2** y puente `PlayerDebugMode = 1` para CEP Adobe. |

---

## Mapa Maestro de la Biblia (11 Pilares + Guías para Agentes + Recursos)

| Pilar | Documento | Qué cubre |
|---|---|---|
| **🤖 Para Agentes IA** | [`AGENTS.md`](AGENTS.md) · [`GEMINI.md`](GEMINI.md) · [`CLAUDE.md`](CLAUDE.md) | **Punto de entrada para otro agente:** reglas duras de VRAM/RAM, tabla de enrutamiento de tareas, inventario exacto de 11 pilares/scripts/MCPs y checklist de validación. |
| **01 · IA Video Local** | [`docs/01-local-ai-video-12gb-32gb.md`](docs/01-local-ai-video-12gb-32gb.md) | Wan 2.2 (5B/14B GGUF), LTX-2.3/2.5 + LTX-Desktop, HunyuanVideo 1.5, FramePack, VACE, SkyReels-V2, Wan2GP (`mmgp`), ComfyUI (`GGUF`, `SageAttention`), InfiniteTalk, EchoMimic v3, `comfy-mcp`. |
| **02 · Roto, Matting & Depth** | [`docs/02-rotoscoping-matting-chroma-depth.md`](docs/02-rotoscoping-matting-chroma-depth.md) | MatAnyone 2 (CVPR '26), SAM 3, VideoMaMa (CVPR '26), ComfyUI-RMBG/BiRefNet/RVM, **`MatteDesk`** (`pymatting`), EffectErase (CVPR '26), ProPainter, Video Depth Anything, DepthCrafter, **`vfx_ssdo_relight_16f`** (*`Relit-LiVE` `[CLOUD / >24GB]`*). |
| **03 · Enfoque Especial: ArtCraft** | [`docs/03-artcraft-deep-dive.md`](docs/03-artcraft-deep-dive.md) | **ArtCraft Studio** (`storytold/artcraft`) + **17 Crafting Apps en Rust puro** (FilmCraft, EffectCraft, AniCraft, PhotoCraft, LightCraft, TextureCraft, MaterialCraft, SoundCraft, etc.), Lottie/JSON, `.mcp.json` nativo y matriz honesta de paridad alpha vs Adobe. |
| **04 · Enfoque Especial: Adobe** | [`docs/04-adobe-video-deep-dive.md`](docs/04-adobe-video-deep-dive.md) | Premiere Object Mask & Media Intelligence, MCPs (`premiere-pro-mcp`, `Adobe_Premiere_Pro_MCP`, `opencutagent`, `@kumoproductions/mcp-aftereffects`, `Dakkshin/after-effects-mcp`), `Bolt UXP` / `Bolt CEP`, expresiones JS ES6+, puentes ProRes 4444. |
| **05 · TouchDesigner Real-Time** | [`docs/05-touchdesigner-realtime.md`](docs/05-touchdesigner-realtime.md) | TouchDesigner 2025+ **POPs/POPX**, oficial **`TouchDesigner/TDMCP`** + `TDMCPSkills` (con soporte nativo Antigravity!), **`Embody / Envoy`** (TDXN YAML Git), `touchdesigner-mcp`, `td-mcp-rs`, StreamDiffusionTD, ComfyUI-TD, `td-native-inference` (`DAViD`), Spout2/NDI y **`Web Render TOP`** (Chromium 132.0). |
| **06 · Blender, 3D VFX & Resolve** | [`docs/06-blender-3d-vfx-compositing.md`](docs/06-blender-3d-vfx-compositing.md) | Blender Official MCP (5.1/5.2+), `mcp-for-blender`, `vfx-agent-toolkit`, ComfyUI-BlenderAI-node, TRELLIS.2, Hunyuan3D 2.1, 3DGS (`Kiri-Innovation`, `gsplat`, `spark`), MoCap (`GVHMR`, `FreeMoCap`, `WiLoR-mini`), `davinci-resolve-mcp`, Natron/OpenFX, OpenTimelineIO. |
| **07 · NLEs Open-Source, JS & VSR** | [`docs/07-opensource-nles-cli-upscaling.md`](docs/07-opensource-nles-cli-upscaling.md) | `OpenCut`, `LosslessCut`, `Shotcut`, `Kdenlive` (aviso Olive pausado), `auto-editor`, `PySceneDetect`, `MoviePy`, `VapourSynth + vs-mlrt`, **Animaciones JS (`Remotion`, `Motion Canvas`, `Three.js/R3F`, `GSAP`, `Anime.js`, `Theatre.js`, `p5.js`, `Rive`, `lottie-web`)**, **SeedVR2**, **FlashVSR/FlashVSR+**, **Practical-RIFE**. |
| **08 · Normales (Tiempo Real + Post)** | [`docs/08-normal-passes-realtime-post.md`](docs/08-normal-passes-realtime-post.md) | **`DAViDNormals.tox`** (~10 ms GPU en TD), MRT GLSL MAT (`Render Select TOP`), Blender AOV + Spout2, **`NormalCrafter`** (`--max-res 512`), **`Lotus` / `Lotus-2`**, **`StableNormal-turbo`**, **`MoGe-2/3`**, **`DSINE`**, EXR lineal (`radiance` / `ACES-IO`), OpenGL `+Y` vs DX `-Y`, Resolve `ReLight` & AE `Normality`. |
| **09 · Camera Track 3D & Matchmoving** | [`docs/09-camera-tracking-matchmoving-3d.md`](docs/09-camera-tracking-matchmoving-3d.md) | **`Depth-Anything-3` (`DA3-Streaming`)**, **`VGGT-1B`** (export `COLMAP`), **`Pi3X`** (`disable_multimodal()`), **`MapAnything`**, **`CoTracker3` / `AllTracker`**, **`COLMAP`** (con GLOMAP integrado), **`Meshroom`**, **`fSpy` + `fSpy-Blender`**, Blender Tracking (`.abc`/`.fbx`/`.usd`) y **`DeepBump` + `StableDelight`**. |
| **10 · Color OCIO, Audio IA, Face & OBS** | [`docs/10-color-ocio-audio-face-obs.md`](docs/10-color-ocio-audio-face-obs.md) | **OpenColorIO (`ACES 2.0` / `AgX`)** en Blender/TD (`OpenColorIO TOP`)/Resolve/ComfyUI (`radiance`, `ACES-IO`), **Audio IA** (**`MMAudio`** ~6 GB Foley, **`WhisperX`/`faster-whisper`** word-sync, `audio-separator`/`Demucs`, `DeepFilterNet`, **`Chatterbox`/`F5-TTS`/`Kokoro`**), **`LivePortrait`** + **`ReActor`**, y **OBS (`obs-spout2-plugin` + `obs-mcp`)**. |
| **11 · Usos Prácticos TD & Workflows** | [`docs/11-usos-practicos-touchdesigner-vfx.md`](docs/11-usos-practicos-touchdesigner-vfx.md) | **8 Recetas Reproducibles:** CRT/VHS GLSL 16F, Feedback + Optical Flow + Datamosh, Ecos BPM + `DAViDHuman` + `Time Machine TOP`, `MediaPipe` + `POPs` + Raymarching (`glsl_daily_practice`), Relighting PBR `SSDO` ➔ OBS, Multicámara (`Orbbec`/`TDOAK`/`TDXDepthCamMerger`) + `Web Render TOP`, Zero-Copy **`cuda-link`** + `StreamDiffusionTD`, y Checklist Anti-Nodos-Rojos ComfyUI / E-Commerce. |
| **Módulo A · ComfyUI VFX, Fluido GPU & PBR `33f->167f`** | [`docs/modules/MODULE_A_COMFYUI_VFX_3060.md`](docs/modules/MODULE_A_COMFYUI_VFX_3060.md) · [`HAND_FIRE_PBR_V6C_SPEC.md`](docs/modules/HAND_FIRE_PBR_V6C_SPEC.md) | Manual profundo RTX 3060 `sm_86` (Fase 2.5 + **Spec `V6-C Cinema Suite`**): Gates 0–3, Brinkman + Poisson, MacCormack, ascuas $\omega \times r$, Area-Light PBR, ACES RRT+ODT y benchmarks `73.1 s / <2.5 GB VRAM`. |
| **Módulo C · TD + Blender Live VFX** | [`docs/modules/MODULE_C_TD_BLENDER_VFX.md`](docs/modules/MODULE_C_TD_BLENDER_VFX.md) | `TDMCP` + 19 `td-*` skills / `Embody`, puente Blender↔TD Spout2/OSC, `StreamDiffusionTD`, `GVHMR` y presupuestos VRAM. |
| **Workflows End-to-End** | [`workflows/END_TO_END_PIPELINES.md`](workflows/END_TO_END_PIPELINES.md) | Blueprints paso a paso para VFX híbrido, Sweet-Spot 480p→SeedVR2→RIFE, automatización IA/JS/Live y **Workflow 4: 7 Rutas Comparadas (`Ruta G` SOTA + `33f` ➔ `167f` + Gates 0–3)** + JSONs [`workflows/comfyui/`](workflows/comfyui/README.md). |
| **Plantillas MCP (Win 11)** | [`mcps/README.md`](mcps/README.md) | [`win11_unified_mcp_config.json`](mcps/win11_unified_mcp_config.json) (incl. OBS), [`artcraft_adobe_mcp.json`](mcps/artcraft_adobe_mcp.json) & [`antigravity_td_blender_mcp.json`](mcps/antigravity_td_blender_mcp.json). |
| **Skills de Agente IA** | [`skills/`](skills/) | 3 skills listas y sincronizadas: `video-vfx-3060-12gb-local`, `artcraft-adobe-vfx-bridge`, `daily-vfx-radar`. |
| **Scripts Windows 11, Fluido GPU, PBR & Gates** | [`scripts/`](scripts/) | `check_3060_env.ps1`, `comfyui_3060_12gb_launch.bat`, `batch_matting_pipeline.py`, `vfx_dual_matte_decontam.py`, `vfx_ssdo_relight_16f.py`, `vfx_incompressible_fire_sim.py`, `wilor_mano_to_blender_abc.py`, `vfx_rd_metrics_eval.py`, `blender_td_osc_bridge.py`, `blender_normal_pass_setup.py`, shaders `.frag`, `daily_radar.py`. |
| **Automatización Diaria (`/automation`)** | [`automation/ANTIGRAVITY_DAILY_AUTOMATION.md`](automation/ANTIGRAVITY_DAILY_AUTOMATION.md) | Guía `/automation` Antigravity + GitHub Action diario ([`.github/workflows/daily-radar.yml`](.github/workflows/daily-radar.yml)) + [`RADAR_DAILY.md`](RADAR_DAILY.md). |

---

## Matriz Comparativa Rápida — ¿Qué Herramienta Uso Hoy en Mi PC?

| Necesito... | Elección #1 en 3060 12GB (Local) | Alternativa Rápida / Estudio | Integración Agente (MCP/CLI) |
|---|---|---|---|
| **Generar video T2V / I2V sin frustraciones** | **Wan2GP (`mmgp`)** con Wan 2.2 5B / 14B INT8 | ComfyUI + `WanVideoWrapper` + `GGUF Q4_K_M` / `Q4_K_S` | `Comfy-Org/comfy-mcp` |
| **Video con audio y diálogos nativos** | **LTX-2.3 / 2.5 GGUF** o `LTX-Desktop` | `InfiniteTalk` / `EchoMimic v3` (para talking heads) | `ComfyUI-LTXVideo` |
| **Video largo (>15s) desde una imagen** | **FramePack** (6–8 GB VRAM) | Wan Animate + `ComfyUI-WanAnimatePlus` | CLI / Gradio / ComfyUI |
| **Rotoscopia de cabello/ropa sin green screen** | **SAM 2/3 ➔ MatAnyone 2** (`+ MatteDesk`) | **VideoMaMa** (conserva *motion blur*) / Premiere Object Mask | [`vfx_dual_matte_decontam.py`](scripts/vfx_dual_matte_decontam.py) |
| **Borrar persona/objeto + su sombra y reflejo** | **EffectErase** (`Wan2.1-1.3B-InP`) | **ProPainter** (cables/marcas rígidas rápido) | CLI Python |
| **Z-Depth consistente para compositing** | **Video Depth Anything** (Small/Base) | **DepthCrafter** (transparencias/reflejos) / `MoGe-2` | ComfyUI / CLI |
| **Camera Tracking 3D / Matchmoving / Point Track** | **Video IA:** `Depth-Anything-3` (`DA3-Streaming`) o `Pi3X`<br>**Sub-píxel:** **Blender Tracker** / `COLMAP` | **Point tracking c/ oclusión:** `CoTracker3` / `AllTracker`<br>**1 foto:** `fSpy` + `fSpy-Blender` | `COLMAP` / `.abc`/`.fbx` / `.json` |
| **Capa de Normales (Tiempo Real / Post VFX)** | **Tiempo real:** `DAViDNormals.tox` (~10 ms) o TD MRT / Blender Spout2<br>**Post video:** `NormalCrafter --max-res 512` (~6 GB) | **Post stills/detalle:** `Lotus-2` (FLUX GGUF) / `StableNormal-turbo` / `MoGe-2` | ComfyUI (`mod_a_01`) / TDMCP / `blender_normal_pass_setup.py` |
| **Re-iluminar un video grabado** | **PBR `SSDO` 16F + MIP Area-Light** ([`vfx_ssdo_relight_16f.py`](scripts/vfx_ssdo_relight_16f.py)) + **`UniLumos 1.3B`** | Fusion **`Relight` (puerto Normals)** / AE **`Normality`** (EXR 32F) · *(`Relit-LiVE` = `[CLOUD / >24GB]`)* | `mod_a_02` / CLI / NLE |
| **Color Cinematográfico sin clipping (`EXR` / `OCIO`)** | **Blender 5 (`ACES 2.0` / `AgX`)** + **Stephen Hill ACES / `PyOpenColorIO AgX Punchy`** | **Resolve Studio (`ACEScct` / `ACES 2.0`)** + **`FXTD-Studios/radiance`** | `.ocio` / Python `OpenEXR` |
| **Foley, Stems, Voz IA & Subtítulos Word-Sync** | **Foley:** `MMAudio` (~6 GB fp16) · **Subs:** `WhisperX`<br>**TTS:** `Chatterbox` / `Kokoro` | **Limpieza CPU:** `DeepFilterNet` · **Stems:** `python-audio-separator` | CLI Python ➔ SRT/JSON Remotion |
| **Corregir mirada / Face VFX limpio** | **`LivePortrait`** (re-targeting mirada, parpadeo y gestos) | `ComfyUI-ReActor` + `CodeFormer` (avisos 128px/flicker) | CLI / ComfyUI |
| **Captura GPU 60 FPS & Switching en vivo** | **OBS Studio + `obs-spout2-plugin`** (Direct3D 11 zero-copy) | `Spout In/Out` directo TD ↔ Blender | `royshil/obs-mcp` / `xDarkzx/OBS_MCP` |
| **Fuego / Energía VFX sobre anatomía (7 Rutas · R&D)** | **Ruta G / B SOTA:** `Paso 0` (`~60s/33f`) + **Fluido GPU Incompresible** ([`vfx_incompressible_fire_sim.py`](scripts/vfx_incompressible_fire_sim.py)) o **MANO Estanco Mantaflow/EmberGen** + **SSDO MIP Area-Light** (`ACES Hill` / `OCIO AgX Punchy`) | **Ruta A ComfyUI** (`VACE-Fun` `Q3_K_M`/`Q4_K_S` + `UniLumos`) · *(`DiffusionRenderer` video = `[CLOUD / >24GB]`)* | [`MODULE_A`](docs/modules/MODULE_A_COMFYUI_VFX_3060.md) / [`vfx_incompressible_fire_sim.py`](scripts/vfx_incompressible_fire_sim.py) / [`vfx_rd_metrics_eval.py`](scripts/vfx_rd_metrics_eval.py) |
| **Animaciones JS / HUDs / 3D WebGL (0 VRAM IA)** | **Offline:** **Remotion** (`--prores-profile=4444 --pixel-format=yuva444p10le`) o **Motion Canvas**<br>**Vivo 60 FPS:** **GSAP / Three.js / Rive** en TD **`Web Render TOP`** | **Playwright** (`omitBackground: true`) ➔ `ConvertTo-ProRes4444Alpha` | Código React/TSX generado directo por Agente IA |
| **Motion Graphics por código / Git / Lottie** | **EffectCraft** (`storytold`) | **Remotion** / **Motion Canvas** / **Lottie (`lottie-web`)** | **`effectcraft-cli mcp`** (nativo) |
| **Motion Graphics / VFX comerciales clientes** | **Adobe After Effects** (incl. Expresiones JS ES6+) + **Premiere Pro** | **DaVinci Resolve Studio** (Fusion/Color) | `@kumoproductions/mcp-aftereffects` + `premiere-pro-mcp` |
| **Limpiar silencios y retakes al instante** | **Open Cut Agent** (Premiere) o **`auto-editor`** | `LosslessCut` (recorte manual sin re-encode) | Puerto `3001` / CLI XML |
| **Visuales interactivos y audio-reactivos** | **TouchDesigner 2025+ (POPs + `Web Render TOP`)** + **StreamDiffusionTD** | Blender 5.x + Geometry Nodes / **Spout2** | **`TouchDesigner/TDMCP`** o **`Embody`** |
| **3D VFX, 3DGS y MoCap sin traje** | **Blender 5.x** + **GVHMR** + **`WiLoR-mini`** + `3dgs-render-blender-addon` | **ArtCraft Studio** (previs rápida) + **TRELLIS.2** | Oficial Blender MCP / `mcp-for-blender` / [`wilor_mano_to_blender_abc.py`](scripts/wilor_mano_to_blender_abc.py) |
| **Escalar 480p→1080p y pasar 16→32/60fps** | **SeedVR2 (3B/block-swap)** + **Practical-RIFE** | **FlashVSR** (con tiling) / VapourSynth `vs-mlrt` | ComfyUI (`mod_a_03`) / CLI |

---

## Hoja de Ruta Progresiva (Fase 1 → Fase 2.5)

- **Fase 1 + Pilares 08–10 + JS + Guías para Agentes (Completado):** Mapa integral de **10 pilares**, calibración estricta 3060 12GB / 32GB RAM / Windows 11, enfoque ArtCraft + Adobe + Animaciones JS + Camera Track 3D + OCIO/Audio/Face/OBS, `AGENTS.md`/`GEMINI.md`/`CLAUDE.md`, configs MCP verificadas, 3 Skills sincronizadas, scripts/shaders operativos y Radar Diario automatizado.
- **Fase 2 & 2.5 (Módulos Profundos):**
  1. **✅ Módulo A (Fase 2.5) — ComfyUI VFX, Fluido GPU Incompresible, PBR `SSDO`, Oclusión Z Continua & Workflow 4 (`33f` ➔ `167f`):** **Completado** en [`docs/modules/MODULE_A_COMFYUI_VFX_3060.md`](docs/modules/MODULE_A_COMFYUI_VFX_3060.md) con 3 templates API en [`workflows/comfyui/`](workflows/comfyui/README.md) y 5 motores CLI/Blender/CUDA ([`vfx_dual_matte_decontam.py`](scripts/vfx_dual_matte_decontam.py), [`vfx_ssdo_relight_16f.py`](scripts/vfx_ssdo_relight_16f.py), [`vfx_incompressible_fire_sim.py`](scripts/vfx_incompressible_fire_sim.py), [`wilor_mano_to_blender_abc.py`](scripts/wilor_mano_to_blender_abc.py), [`vfx_rd_metrics_eval.py`](scripts/vfx_rd_metrics_eval.py)).
  2. **Módulo B — Taller Práctico ArtCraft + Adobe Bridge:** *(Pendiente)* Compilar `effectcraft-cli.exe` / `filmcraft-cli.exe` en Windows 11 y crear un plugin propio UXP/CEP con `bolt-uxp`.
  3. **✅ Módulo C — TouchDesigner + Blender VFX en Vivo:** **Completado** en [`docs/modules/MODULE_C_TD_BLENDER_VFX.md`](docs/modules/MODULE_C_TD_BLENDER_VFX.md) con [`antigravity_td_blender_mcp.json`](mcps/antigravity_td_blender_mcp.json), [`blender_td_osc_bridge.py`](scripts/blender_td_osc_bridge.py) y [`setup_module_c_win11.ps1`](scripts/setup_module_c_win11.ps1).
