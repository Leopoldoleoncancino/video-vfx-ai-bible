# AGENTS.md — Guía Maestra de Lectura y Operación para Agentes IA

> **Propósito:** Este repositorio (`Leopoldoleoncancino/video-vfx-ai-bible`) es la base de conocimiento técnica viva del usuario para producir **Video IA Local, VFX, Motion Graphics, TouchDesigner, Blender y Automatización híbrida (ArtCraft + Adobe + JavaScript)** en su estación local **Windows 11**.

---

## 1. Reglas Duras de Hardware y Calidad (Leer Antes de Responder o Editar)

Toda recomendación, workflow, comando o código generado a partir de esta Biblia DEBE respetar el perfil físico de la estación de trabajo del usuario:

| Componente | Especificación | Regla Operativa Obligatoria para Agentes |
|---|---|---|
| **GPU** | **NVIDIA RTX 3060 · 12 GB VRAM** *(Ampere, sin FP8 Tensor Core nativo)* | Prioriza **`GGUF (Q4_K_M / Q5_K_M)`** o **`INT8` (`mmgp`)** + `SageAttention` + `Tiled VAE`. **Nunca** asumas 24 GB VRAM; **nunca** dejes dos modelos de difusión/VLM o dos apps GPU pesadas abiertas simultáneamente (ej. cerrar Premiere/AE/Blender pesado antes de difundir en ComfyUI o Wan2GP). |
| **CPU** | **AMD Ryzen 9 5900X** *(12C / 24T)* | Aprovecha CPU para BlockSwap, **Remotion / Playwright / FFmpeg**, **FilmCraft / EffectCraft (Rust)** y VapourSynth cuando la GPU esté ocupada en IA. |
| **RAM** | **32 GB DDR4** *(techo operativo real ~22–24 GB libres en Win 11)* | Evita Text Encoders `BF16/FP16` de 9–12 GB (`UMT5-XXL`, `T5`, `Gemma`) junto a modelos 14B sin cuantizar: usa versiones **GGUF Q4/Q5** o embeddings precalculados (`flux_empty_embed.pt` en Lotus-2). |
| **OS** | **Windows 11** | Usa `woct0rdho/triton-windows`, `woct0rdho/SageAttention`, `Spout2` en la misma GPU NVIDIA, `127.0.0.1` IPv4-only para `TDMCP` (no `localhost`) y rutas Windows escapadas en JSON (`C:\\...`). |

### Reglas de Honestidad Técnica
1. **No inventes** URLs de GitHub, números de stars, FPS o compatibilidades no verificadas en `docs/` o en [`RADAR_DAILY.md`](RADAR_DAILY.md).
2. **Clasifica claramente** cualquier novedad externa:
   - `[OK-12GB]` Corre cómodo en 12 GB VRAM + 32 GB RAM.
   - `[TIGHT-12GB]` Viable con GGUF / BlockSwap / Tiling / 480p y cerrando apps pesadas.
   - `[CLOUD / >24GB]` Solo referencia o nube; **no** recomendar para flujo diario local sin advertencia explícita.
3. **ArtCraft vs Adobe:** `FilmCraft` / `EffectCraft` **NO** abren archivos `.prproj` / `.aep` ni plugins `.aex` / OFX propietarios; el intercambio entre suites se hace vía **ProRes 4444 (`yuva444p10le` Straight Alpha)**, **EXR 16F/32F lineal**, **Lottie JSON/`.lottie`** o **OTIO/XML**.
4. **Reglas OCIO y Repos Deprecados:** Mantén pases técnicos (`Normal`, `Depth`) en `Non-Color/Raw` (OpenEXR lineal) fuera de curvas gamma sRGB; el antiguo `colmap/glomap` está **`[DEPRECATED]`** (ya integrado dentro de `colmap/colmap`).

---

## 2. Mapa de Contenidos del Repositorio (Índice Actualizado — 10 Pilares)

### Pilares Principales (`docs/`)
- **[`README.md`](README.md)** — Mapa maestro y matriz comparativa rápida *"¿Qué herramienta uso hoy en mi PC?"*.
- **[`docs/01-local-ai-video-12gb-32gb.md`](docs/01-local-ai-video-12gb-32gb.md)** — Generación de video IA local: Wan 2.2 (5B/14B GGUF), LTX-2.3/2.5 + LTX-Desktop, HunyuanVideo 1.5, FramePack, VACE, Wan2GP (`mmgp`), ComfyUI, InfiniteTalk, EchoMimic v3.
- **[`docs/02-rotoscoping-matting-chroma-depth.md`](docs/02-rotoscoping-matting-chroma-depth.md)** — Rotoscopia, matting, borrado con sombras y profundidad: MatAnyone 2, SAM 3, VideoMaMa, BiRefNet/RMBG, `MatteDesk` (`pymatting`), EffectErase, ProPainter, Video Depth Anything, DepthCrafter, [`vfx_ssdo_relight_16f.py`](scripts/vfx_ssdo_relight_16f.py) (*`Relit-LiVE` `[CLOUD / >24GB]`*).
- **[`docs/03-artcraft-deep-dive.md`](docs/03-artcraft-deep-dive.md)** — Suite completa ArtCraft (`storytold/artcraft`) + 17 Crafting Apps en Rust puro (`FilmCraft`, `EffectCraft`, `AniCraft`, `PhotoCraft`, `TextureCraft`, `MaterialCraft`, `SoundCraft`), `.mcp.json` nativo y paridad real vs Adobe.
- **[`docs/04-adobe-video-deep-dive.md`](docs/04-adobe-video-deep-dive.md)** — Premiere Pro & After Effects: Object Mask, Media Intelligence, MCPs (`premiere-pro-mcp`, `Adobe_Premiere_Pro_MCP`, `opencutagent`, `@kumoproductions/mcp-aftereffects`, `Dakkshin/after-effects-mcp`), `Bolt UXP/CEP` y expresiones JS ES6+.
- **[`docs/05-touchdesigner-realtime.md`](docs/05-touchdesigner-realtime.md)** — TouchDesigner 2025+: POPs/POPX GPU, `TouchDesigner/TDMCP` (oficial con soporte Antigravity), `Embody/Envoy` (TDXN YAML Git), `StreamDiffusionTD`, `ComfyUI-TD`, `td-native-inference` (`DAViD`), Spout2/NDI, shader `SSDO` 6 luces y **`Web Render TOP`** (Chromium 132.0 para animaciones JS a 60 FPS).
- **[`docs/06-blender-3d-vfx-compositing.md`](docs/06-blender-3d-vfx-compositing.md)** — Blender 4.5/5.x MCP oficial & comunitarios (`mcp-for-blender`, `vfx-agent-toolkit`), TRELLIS.2, Hunyuan3D 2.1, 3DGS (`Kiri-Innovation`, `gsplat`, `spark`), MoCap sin traje (`GVHMR`, `FreeMoCap`, `WiLoR-mini`), Mantaflow/EXR Multi-Layer, `davinci-resolve-mcp`, Natron y OpenTimelineIO.
- **[`docs/07-opensource-nles-cli-upscaling.md`](docs/07-opensource-nles-cli-upscaling.md)** — NLEs open-source (`OpenCut`, `LosslessCut`, `Shotcut`, `Kdenlive`), CLI (`auto-editor`, `PySceneDetect`, `MoviePy`, `VapourSynth + vs-mlrt`), **Video-as-Code & Animaciones JavaScript** (**`Remotion` ProRes 4444 Alpha, `Motion Canvas`, `Three.js/R3F`, `GSAP`, `Anime.js`, `Theatre.js`, `p5.js`, `Rive`, `lottie-web`, Playwright + `Web Render TOP`**), VSR (**`SeedVR2`**, **`FlashVSR`**) y **`Practical-RIFE`**.
- **[`docs/08-normal-passes-realtime-post.md`](docs/08-normal-passes-realtime-post.md)** — Capa de Normales: convención OpenGL `+Y` vs DX `-Y`, EXR 16F/32F lineal (`radiance`, `ACES-IO`), tiempo real (`DAViDNormals.tox` ~10 ms, TD MRT GLSL, Blender Spout2, Depth-to-Normal) y postproducción (`NormalCrafter --max-res 512`, `Lotus / Lotus-2`, `StableNormal-turbo`, `MoGe-2/3`, `DSINE`, Resolve `ReLight`, AE `Normality`).
- **[`docs/09-camera-tracking-matchmoving-3d.md`](docs/09-camera-tracking-matchmoving-3d.md)** — Camera Tracking 3D, Matchmoving & Fotogrametría: `Depth-Anything-3` (`DA3-Streaming`), `VGGT-1B` (export COLMAP), `Pi3X` (`disable_multimodal()`), `MapAnything` (`minibatch_size=1`), `CoTracker3`, `AllTracker`, `COLMAP` (con GLOMAP fusionado), `Meshroom`, `perarnia/fSpy` + `fSpy-Blender`, Blender `.abc`/`.fbx`/`.usd` y `DeepBump` + `StableDelight`.
- **[`docs/10-color-ocio-audio-face-obs.md`](docs/10-color-ocio-audio-face-obs.md)** — Color `OpenColorIO` (`ACES 2.0` / `AgX` en Blender 5, TD `OpenColorIO TOP`, ComfyUI `radiance` / `ACES-IO`, Resolve), Audio IA (`MMAudio` ~6 GB Foley, `WhisperX`/`faster-whisper` word-sync, `audio-separator`/`Demucs`, `ClearerVoice-Studio`/`DeepFilterNet`, `Chatterbox`/`F5-TTS`/`Kokoro`), Face VFX (`LivePortrait`, `ReActor` + `CodeFormer`) y OBS (`obs-spout2-plugin` + `royshil/obs-mcp` / `xDarkzx/OBS_MCP`).
- **[`docs/11-usos-practicos-touchdesigner-vfx.md`](docs/11-usos-practicos-touchdesigner-vfx.md)** — Usos Prácticos TD & Workflows Reales (8 recetas reproducibles): CRT/VHS GLSL 16F, Feedback + Optical Flow + Datamosh, Ecos BPM + `DAViDHuman` + `Time Machine TOP`, `MediaPipe` + `POPs` + Raymarching (`glsl_daily_practice`), Relighting PBR `SSDO` ➔ OBS, Multicámara (`Orbbec`/`TDOAK`/`TDXDepthCamMerger`) + `Web Render TOP`, Zero-Copy `cuda-link` + `StreamDiffusionTD`, y Checklist Anti-Nodos-Rojos ComfyUI / E-Commerce.

### Módulos Profundos (`docs/modules/`) & Workflows (`workflows/`)
- **[`docs/modules/HAND_FIRE_PBR_V6C_SPEC.md`](docs/modules/HAND_FIRE_PBR_V6C_SPEC.md)** — **Especificación Maestra `V6-C Cinema Suite` (Hand Fire Pipeline V1 ➔ V6-C):** Gates 0–3, separación ego-motion (`LK + RANSAC`), Navier-Stokes con frontera sólida de Brinkman + Poisson, render 3 capas (MacCormack clamped + ascuas $\omega \times r$ + Area Light PBR) y benchmarks reales RTX 3060 (`33f` en `73.1 s`, `~2.2 s/f`, `< 2.5 GB VRAM`).
- **[`docs/modules/MODULE_A_COMFYUI_VFX_3060.md`](docs/modules/MODULE_A_COMFYUI_VFX_3060.md)** — Manual completo Fase 2.5 para ComfyUI VFX en RTX 3060 `sm_86` (resultados empíricos `33f`, 4 fixes Win 11 ComfyUI Portable `python_embeded -s`, fix colorimétrico ACES Hill / OCIO AgX Punchy contra lavado salmón, **Solver GPU Navier-Stokes Incompresible `vfx_incompressible_fire_sim.py`**, malla MANO estanca `watertight`, oclusión Z continua, MIP Area-Light, motion blur `180°` y Gates R&D 0–3).
- **[`docs/modules/MODULE_C_TD_BLENDER_VFX.md`](docs/modules/MODULE_C_TD_BLENDER_VFX.md)** — Manual completo Fase 2 de TouchDesigner (`TDMCP` + 19 `td-*` skills / `Embody`) + Blender Spout2/OSC + StreamDiffusionTD + 3DGS + MoCap (`GVHMR`), con los 3 modos de presupuesto VRAM.
- **[`workflows/END_TO_END_PIPELINES.md`](workflows/END_TO_END_PIPELINES.md)** — 4 blueprints completos listos para ejecutar (VFX Híbrido, Sweet-Spot 480p→SeedVR2→RIFE, Automatización Híbrida JS/Adobe/ArtCraft/TD y **Workflow 4: Fuego/Energía sobre Anatomía — 7 Rutas Comparadas + `Ruta G` SOTA & Protocolo `33f ➔ 167f` con Gates 0–3**).
- **[`workflows/comfyui/`](workflows/comfyui/README.md)** — 3 plantillas ComfyUI API-format verificadas (`mod_a_01_step0_dual_matte_normal_exr.json`, `mod_a_02_unilumos_freqsep_ciede_qc.json`, `mod_a_03_vace_fun_seedvr2_rudra_hdr.json`).

### Skills, MCPs, Scripts, Shaders y Radar (`skills/`, `mcps/`, `scripts/`, `automation/`)
- **`skills/`** *(cargar según tarea):*
  - [`skills/video-vfx-3060-12gb-local/SKILL.md`](skills/video-vfx-3060-12gb-local/SKILL.md)
  - [`skills/artcraft-adobe-vfx-bridge/SKILL.md`](skills/artcraft-adobe-vfx-bridge/SKILL.md)
  - [`skills/daily-vfx-radar/SKILL.md`](skills/daily-vfx-radar/SKILL.md)
- **`mcps/`** ([`mcps/README.md`](mcps/README.md)):
  - [`mcps/win11_unified_mcp_config.json`](mcps/win11_unified_mcp_config.json) (Claude Code / Cursor — incl. OBS Studio)
  - [`mcps/antigravity_td_blender_mcp.json`](mcps/antigravity_td_blender_mcp.json) (Google Antigravity con `"serverUrl"` para `TDMCP`)
  - [`mcps/artcraft_adobe_mcp.json`](mcps/artcraft_adobe_mcp.json) (ArtCraft + Adobe)
- **`scripts/`**:
  - Windows & Video: [`check_3060_env.ps1`](scripts/check_3060_env.ps1), [`comfyui_3060_12gb_launch.bat`](scripts/comfyui_3060_12gb_launch.bat), [`ffmpeg_nvenc_prores_helpers.ps1`](scripts/ffmpeg_nvenc_prores_helpers.ps1), [`batch_matting_pipeline.py`](scripts/batch_matting_pipeline.py), [`setup_module_c_win11.ps1`](scripts/setup_module_c_win11.ps1)
  - Módulo A PBR, Fluido Incompresible, MANO 3D Estanco & Gates 0–3: [`vfx_dual_matte_decontam.py`](scripts/vfx_dual_matte_decontam.py), [`vfx_ssdo_relight_16f.py`](scripts/vfx_ssdo_relight_16f.py), [`vfx_incompressible_fire_sim.py`](scripts/vfx_incompressible_fire_sim.py), [`wilor_mano_to_blender_abc.py`](scripts/wilor_mano_to_blender_abc.py), [`vfx_rd_metrics_eval.py`](scripts/vfx_rd_metrics_eval.py)
  - TouchDesigner + Blender + Normales: [`blender_td_osc_bridge.py`](scripts/blender_td_osc_bridge.py), [`blender_normal_pass_setup.py`](scripts/blender_normal_pass_setup.py), [`td_mrt_normal_pass.frag`](scripts/td_mrt_normal_pass.frag), [`td_depth_to_normal.frag`](scripts/td_depth_to_normal.frag)
  - Radar diario: [`daily_radar.py`](scripts/daily_radar.py)
- **Estado Vivo & Radar:** [`RADAR_DAILY.md`](RADAR_DAILY.md), [`data/radar_latest.json`](data/radar_latest.json), [`changelog/DAILY_LOG.md`](changelog/DAILY_LOG.md), [`automation/ANTIGRAVITY_DAILY_AUTOMATION.md`](automation/ANTIGRAVITY_DAILY_AUTOMATION.md).

---

## 3. Tabla de Enrutamiento Rápido para el Agente

| Si el usuario te pide... | Lee primero | Skill / Recurso a usar |
|---|---|---|
| **Generar video IA local (T2V/I2V/Lip-sync/VSR)** | [`docs/01`](docs/01-local-ai-video-12gb-32gb.md) + [`docs/07`](docs/07-opensource-nles-cli-upscaling.md) | `video-vfx-3060-12gb-local` + `comfyui_3060_12gb_launch.bat` |
| **Rotoscopia, croma, borrado de sombras o Z-Depth** | [`docs/02`](docs/02-rotoscoping-matting-chroma-depth.md) | `video-vfx-3060-12gb-local` + `batch_matting_pipeline.py` + `vfx_dual_matte_decontam.py` |
| **Capa de Normales o relighting (vivo o post)** | [`docs/08`](docs/08-normal-passes-realtime-post.md) + [`MODULE_A`](docs/modules/MODULE_A_COMFYUI_VFX_3060.md) | `blender_normal_pass_setup.py`, `vfx_ssdo_relight_16f.py`, `td_mrt_normal_pass.frag`, `td_depth_to_normal.frag` |
| **Camera Tracking 3D, Matchmoving, Point Track o 3DGS** | [`docs/09`](docs/09-camera-tracking-matchmoving-3d.md) | `DA3-Streaming`, `VGGT-1B`, `Pi3X`, `CoTracker3`, `AllTracker`, `COLMAP`, `fSpy` |
| **Color ACES 2.0/AgX, Foley/STT/TTS, Face VFX o OBS** | [`docs/10`](docs/10-color-ocio-audio-face-obs.md) | `OpenColorIO`, `radiance`, `MMAudio`, `WhisperX`, `LivePortrait`, `obs-spout2-plugin`, `obs-mcp` |
| **Fuego / energía hiperrealista sobre anatomía (7 rutas · R&D `33f->167f`)** | [`MODULE_A`](docs/modules/MODULE_A_COMFYUI_VFX_3060.md) + [`Workflow 4`](workflows/END_TO_END_PIPELINES.md#workflow-4--fuego--energía-hiperrealista-adherido-a-anatomía-con-capa-de-normales-7-rutas-comparadas--rd-33f--167f) + [`workflows/comfyui/`](workflows/comfyui/README.md) | `Ruta G` (Paso 0 + `vfx_dual_matte_decontam.py` + `vfx_incompressible_fire_sim.py` + `vfx_ssdo_relight_16f.py` + `wilor_mano_to_blender_abc.py` + `vfx_rd_metrics_eval.py` + `mod_a_01..03.json`) |
| **TouchDesigner + Blender + StreamDiffusionTD + MCP** | [`docs/05`](docs/05-touchdesigner-realtime.md) + [`docs/06`](docs/06-blender-3d-vfx-compositing.md) + [`MODULE_C`](docs/modules/MODULE_C_TD_BLENDER_VFX.md) | `antigravity_td_blender_mcp.json` + `blender_td_osc_bridge.py` |
| **Recetas TD (CRT/VHS, Optical Flow, MediaPipe, `cuda-link`) & ComfyUI Anti-Nodos-Rojos** | [`docs/11`](docs/11-usos-practicos-touchdesigner-vfx.md) | 8 recetas reproducibles, `DAViDHuman.tox`, `cuda-link`, `VideoHelperSuite`/`KJNodes`/`GGUF` |
| **ArtCraft, EffectCraft, FilmCraft, Premiere o After Effects** | [`docs/03`](docs/03-artcraft-deep-dive.md) + [`docs/04`](docs/04-adobe-video-deep-dive.md) | `artcraft-adobe-vfx-bridge` + `artcraft_adobe_mcp.json` |
| **Animaciones JS, HUDs, 3D WebGL, Remotion o Motion Canvas** | [`docs/07 §3`](docs/07-opensource-nles-cli-upscaling.md#3-video-como-código--animaciones-javascript-offline-prores-4444-y-tiempo-real-60-fps) + [`docs/05`](docs/05-touchdesigner-realtime.md) | `Remotion` ProRes 4444 Alpha, `Web Render TOP`, `ffmpeg_nvenc_prores_helpers.ps1` |
| **Actualizar radar diario o auditar repos recientes** | [`RADAR_DAILY.md`](RADAR_DAILY.md) + [`automation/`](automation/ANTIGRAVITY_DAILY_AUTOMATION.md) | `daily-vfx-radar` + `python3 scripts/daily_radar.py` |

---

## 4. Checklist Antes de Hacer Commit en Este Repositorio

1. Si añadiste o modificaste **scripts Python**, valida `python3 -m py_compile ...` y sus pruebas rápidas (`--self-test` / `--check` / `--dry-run`).
2. Si modificaste configs en `mcps/`, datos en `data/` o workflows ComfyUI en `workflows/comfyui/`, valida que sean **JSON válido** (`json.load`) y referencias de nodos consistentes.
3. Verifica que **todas las rutas relativas Markdown** en `docs/`, `README.md`, `AGENTS.md`, `workflows/` y `skills/` apunten a archivos existentes y ninguna tabla tenga columnas rotas.
4. Si actualizas capacidades importantes o skills del repo, mantén alineados `README.md`, `AGENTS.md`, `changelog/DAILY_LOG.md` y la copia correspondiente dentro de `skills/*/SKILL.md`.
5. No hagas commit de archivos temporales, cachés (`__pycache__/`) ni medios pesados (`*.mp4`, `*.mov`, `*.exr`, `*.png`).
