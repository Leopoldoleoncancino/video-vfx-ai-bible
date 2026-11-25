---
name: video-vfx-3060-12gb-local
description: >
  Selecciona, optimiza y depura pipelines locales de generación de video IA, rotoscopia, matting,
  capa de normales, camera tracking 3D, color OCIO/ACES 2.0, audio/Foley IA, OBS Spout2, TouchDesigner/Blender en vivo,
  VSR y offload JS ajustados estrictamente al hardware RTX 3060 12 GB VRAM + Ryzen 9 5900X + 32 GB RAM en Windows 11.
---

# Video & VFX Local Optimization Skill (RTX 3060 12 GB / 32 GB RAM / Win 11)

## Cuándo aplicar este skill
Actívalo siempre que el usuario pida instalar, elegir modelos, construir flujos de ComfyUI/Wan2GP,
rotoscopiar, sacar capa de normales, hacer camera tracking 3D, configurar color OCIO, generar Foley/subtítulos/TTS, conectar TouchDesigner + Blender + OBS, simular fluidos/fuego GPU o hacer upscaling/motion local en Windows 11.

## Reglas Duras de Hardware (NO romper)
1. **Límite de VRAM (12 GB GDDR6 Ampere `sm_86`):**
   - La RTX 3060 **NO tiene FP8 Tensor Cores nativos (`sm_86 < 8.9`)**: prohibido activar `fp8_fast` o `torch.compile` sobre `e4m3fn` en `WanVideoModelLoader`; usa `base_precision="bf16"`, `quantization="disabled"`, `attention_mode="sageattn"`/`"sdpa"`, pesos **GGUF (`Q3_K_M` 8.64 GB / `Q4_K_S` 10.55 GB / `Q5_K_M`)** o **`INT8` (`quanto`/`mmgp`)**.
   - Nunca mantengas dos modelos de difusión/VLM pesados residentes en VRAM al mismo tiempo: ejecuta por fases secuenciales con **`VRAM_Debug` (`unload_all_models=true`, `empty_cache=true`, `gc_collect=true`)** y ajusta `"max_mem_frames": 5` en `comfy-matanyone2/config.py`.
2. **Límite de RAM del Sistema (32 GB — ~22–24 GB libres reales en Windows 11):**
   - Evita dejar residente `UMT5-XXL FP16` (~9.5 GB) o `Gemma` en RAM junto a expertos A14B: usa **`WanVideoTextEncodeCached` (`use_disk_cache=true`)**, versiones **GGUF Q4/Q5** (o `flux_empty_embed.pt` en `Lotus-2`) y cierra Premiere, AE, Blender pesado y Chrome antes de batches largos (fija Pagefile NVMe >=32 GB).
3. **Estrategia de Resolución, FPS & Pruebas R&D (`33f -> 167f` con 4 Gates Cuantitativos):**
   - En planos de fuego/VFX sobre anatomía, ejecuta primero el recorte crítico de **33 frames** (`job_33f`) validando los **4 Gates cuantitativos** con **`scripts/vfx_rd_metrics_eval.py`**:
     * **Gate 0:** `‖N‖ ∈ [0.99, 1.01]`, `fringe_delta_l < 0.03` en hilos negros (`vfx_dual_matte_decontam.py`).
     * **Gate 1:** ganancia en puño negro `<= 1.15x`, contraste SSDO `>= 3.5:1` (`invert_normal_y=True` con `NormalCrafter`) y escritorio blanco **`CIEDE2000 <= 1.5`**.
     * **Gate 2:** pico HDR lineal `>= 4.0`, **`pastel_yellow_clip_pct <= 1.0%`**, **`salmon_wash_pct <= 2.0%`** (usando **Stephen Hill ACES Filmic RRT+ODT** o **`PyOpenColorIO AgX Punchy`** + `compose_hdr_on_plate_srgb`, nunca `m_inset` simple) y ruido/MTF `±12%`.
     * **Gate 3 (Acoplamiento Movimiento↔Fuego):** `lag_correlation >= 0.45` y `mean_wake_deflection_px >= 1.2 px` entre `v_hand_world = v_hand_screen - v_cam` y la estela de la pluma superior (rechazando fuegos procedurales *stateless* rígidos).
   - Para I2V/T2V general, genera en `640x360` o `832x480` a `16 fps` (81 frames ≈ 5s), escala con **SeedVR2 (3B + `block_swap`)** o **FlashVSR** (tiling) y duplica FPS al final con **Practical-RIFE** *antes* de añadir el grano final.
4. **Gotchas Reales de Windows 11 + ComfyUI Portable (`python_embeded -s`):**
   - `MatAnyone2` falla en `pip install` por bug de `hatchling` (`matanyone2/config/__init__.py` duplicado) ➔ copiar carpeta `matanyone2/` directo a `python_embeded\Lib\site-packages\`.
   - `transformers 5.9.0` lanza `KeyError: 'flash_attn'` en `import_utils.py` con stubs ➔ usar `.get("flash_attn", [])`.
   - `python_embeded -s` ignora `--user` ➔ instalar `OpenEXR`, `PyOpenColorIO`, `pymatting` siempre con `--target python_embeded\Lib\site-packages`.
5. **Regla Offload JS/CPU & Pases Lineales:**
   - Si una pieza es HUD, texto cinético, catálogo de indumentaria o 3D ligero WebGL, renderízala con **JavaScript (`Remotion` ProRes 4444 Alpha, `Motion Canvas`, `GSAP`, `Three.js` + Playwright)** en los 24 hilos del Ryzen 9 5900X o en vivo vía **`Web Render TOP`** (TD `2025.31550+`) en lugar de gastar VRAM de difusión.
   - Mantén pases técnicos (`Normal`, `Depth`, `Roughness`) siempre como **`Non-Color / Raw` EXR 16F/32F lineal** fuera de curvas gamma sRGB. **NO uses `FrequencyCombineMEC` sobre fuego HDR `>1.0`** porque recorta a `[0, 1]` SDR.

## Selección Rápida por Caso de Uso
- **Facilidad / Multi-modelo "GPU Poor":** `Wan2GP` (`deepbeepmeep/WanGP`) con motor `mmgp` + `INT8`.
- **Video con Audio nativo:** `LTX-2.3` / `LTX-2.5` cuantizado (`GGUF Q3_K_M/Q4_K_M`) o `LTX-Desktop`.
- **Planos I2V largos (>10s anti-drift):** `FramePack` (`lllyasviel/FramePack`).
- **Rotoscopia de cabello/tela & Matte Dual:** `SAM 2 / SAM 3` (`SegmentC2C`) ➔ `MatAnyone 2` (`max_mem_frames=5`) ➔ `MatteDesk` (`ForegroundDecontaminate`) / `scripts/vfx_dual_matte_decontam.py` ➔ **ProRes 4444 Straight Alpha**.
- **Borrado de objetos + sombras + reflejos:** `EffectErase` (`FudanCVL/EffectErase`) o `ProPainter` (para cables/marcas rígidas).
- **Camera Tracking 3D / Matchmoving / Point Tracking:** Video largo IA ➔ `Depth-Anything-3` (`DA3-Streaming`) o `Pi3X` (`disable_multimodal()`) o `VGGT-1B` (export `COLMAP`); oclusiones ➔ `CoTracker3` / `AllTracker`; matchmoving sub-píxel ➔ Blender Tracker / `COLMAP` (GLOMAP integrado; `colmap/glomap` deprecated); 1 foto ➔ `perarnia/fSpy`.
- **Capa de Normales (Tiempo Real <25 ms):** `DAViDNormals.tox` (~10 ms en `td-native-inference` ➔ `Relight.tox`), TouchDesigner MRT GLSL (`scripts/td_mrt_normal_pass.frag`), Blender View/World Normal AOV (`scripts/blender_normal_pass_setup.py`) vía **Spout2** o Depth-to-Normal (`scripts/td_depth_to_normal.frag`).
- **Capa de Normales (Postproducción VFX):** `NormalCrafter --max-res 512` (~6 GB, `VizClickNormalCrafter` + `VizClickNormalTemporalStabilizer`), `Lotus` SD2.1 (~4–8 GB batch rápido), `Lotus-2` FLUX GGUF (~8–11 GB micro-detalle en stills), `StableNormal-turbo` + `StableDelight` (~6–9 GB), `MoGe-2/3`, `DeepBump`. Exportar **Camera Space OpenGL `+Y` arriba en EXR 16F/32F lineal** (`FXTD-Studios/radiance` / `ComfyUI-ACES-IO`).
- **Color OCIO (`ACES 2.0` / `AgX`):** Blender 5 (`ACES 2.0`/`AgX - Punchy`) · TouchDesigner (`OpenColorIO TOP`: `sRGB - Texture ➔ Linear`) · DaVinci Resolve (`ACEScct` / `ACES 2.0`) · ComfyUI (`RadianceACES2OutputTransformFull`; *RUDRA checkpoint es no-comercial*) · Python (`aces_hill_filmic_tonemap` / `ocio_agx_tonemap` + `compose_hdr_on_plate_srgb` en `scripts/vfx_ssdo_relight_16f.py`).
- **Audio IA, Foley & Subtítulos:** Foley frame-synced ➔ `hkchengrex/MMAudio` (~6 GB fp16, pesos `CC-BY-NC-4.0`); subtítulos word-sync ➔ `WhisperX` (`<8 GB`); limpieza CPU gratis ➔ `DeepFilterNet`; stems ➔ `python-audio-separator` / `Demucs`; TTS ➔ `Chatterbox` / `F5-TTS` / `Kokoro` (82M).
- **Face VFX & OBS Live:** Retoque/mirada natural ➔ `KlingAIResearch/LivePortrait` (~4–8 GB); swap ➔ `ReActor` + `CodeFormer` (`0.7–0.8`, advertencia 128px); captura GPU 60 FPS ➔ `obs-spout2-plugin` + `royshil/obs-mcp` (`4455`).
- **TouchDesigner + Blender en Vivo (Módulo C & Pilar 11):** `TouchDesigner/TDMCP` (`http://127.0.0.1:13316/mcp`, `"serverUrl"` en Antigravity) + `TDMCPSkills` (19 `td-*` skills) o `Embody/Envoy` (TDXN YAML); separa Modos VRAM 1 (`Spout2` + `StreamDiffusionTD` + `cuda-link`), 2 (`GVHMR` ~4.2 GB ➔ Blender `mcp-for-blender`) y 3 (POPs + 3DGS). Para **8 recetas listas** (CRT/VHS GLSL, Optical Flow Datamosh, Ecos BPM + `DAViDHuman`, MediaPipe + `POPs`, Relighting `SSDO` ➔ OBS, `Orbbec`/`TDOAK` + `Web Render TOP`, `cuda-link` y Checklist Anti-Nodos-Rojos ComfyUI), consulta `docs/11-usos-practicos-touchdesigner-vfx.md`.
- **Fuego / Energía VFX sobre Anatomía, Fluido GPU Incompresible & Relighting PBR (Módulo A Fase 2.5 / `Workflow 4 · Ruta G & B`):**
  1. **Bus Común `16F` (`~60s/33f`):** `vfx_dual_matte_decontam.py` (`matte_skin` vs `matte_fabric`) + `NormalCrafter 512px` + `DepthAnything V2`/`DA3`.
  2. **Simulación Física con Inercia Real (Gate 3):**
     - **Opción GPU Directa (`< 1 GB VRAM`, `< 1 min`):** **`scripts/vfx_incompressible_fire_sim.py`** (Navier-Stokes incompresible con proyección de presión **Red-Black SOR**, compensación de cámara `RANSAC Homography` / LK, advección **BFECC clamped**, *Vorticity Confinement*, lenguas *Curl* advectadas, chispas Lagrangianas y **Oclusión Z-Buffer Continua Front/Back**). Alternativas compatibles: `taichi-dev/taichi` / `tum-pbs/PhiFlow`.
     - **Opción 3D Volumétrica (`Ruta C`):** **`scripts/wilor_mano_to_blender_abc.py --enable-mantaflow`** (cierra el borde abierto de la muñeca MANO con `cap_open_mesh_watertight` para emisión superficial continua `velocity_factor=1.25` + shader **Lámina Fina Blackbody `Density=0.02`** + `Proxy_Black_Cuff` colisionador, o exportación `.abc` hacia **JangaFX EmberGen / LiquiGen** `[OK-12GB]`). **Nunca emitir desde esferas sueltas en landmarks.**
  3. **Relighting PBR Acoplado + Motion Blur `180°` + Tone Map sin Lavado Salmón:** **`scripts/vfx_ssdo_relight_16f.py`** (`invert_normal_y=True`, pirámide MIP `build_fire_irradiance_pyramid` + `extract_dynamic_lights_from_fire`, `apply_velocity_motion_blur` `shutter=0.5` y `compose_hdr_on_plate_srgb` con Stephen Hill ACES / `PyOpenColorIO AgX Punchy`).
- **Aceleración Windows:** `woct0rdho/triton-windows` + `woct0rdho/SageAttention` + `TeaCache`.
