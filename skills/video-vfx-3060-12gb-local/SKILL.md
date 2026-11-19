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
rotoscopiar, sacar capa de normales, hacer camera tracking 3D, configurar color OCIO, generar Foley/subtítulos/TTS, conectar TouchDesigner + Blender + OBS o hacer upscaling/motion local en Windows 11.

## Reglas Duras de Hardware (NO romper)
1. **Límite de VRAM (12 GB GDDR6 Ampere `sm_86`):**
   - La RTX 3060 **NO tiene FP8 Tensor Cores nativos (`sm_86 < 8.9`)**: prohibido activar `fp8_fast` o `torch.compile` sobre `e4m3fn` en `WanVideoModelLoader`; usa `base_precision="bf16"`, `quantization="disabled"`, `attention_mode="sageattn"`/`"sdpa"`, pesos **GGUF (`Q3_K_M` 8.64 GB / `Q4_K_S` 10.55 GB / `Q5_K_M`)** o **`INT8` (`quanto`/`mmgp`)**.
   - Nunca mantengas dos modelos de difusión/VLM pesados residentes en VRAM al mismo tiempo: ejecuta por fases secuenciales con **`VRAM_Debug` (`unload_all_models=true`, `empty_cache=true`, `gc_collect=true`)** y ajusta `"max_mem_frames": 5` en `comfy-matanyone2/config.py`.
2. **Límite de RAM del Sistema (32 GB — ~22–24 GB libres reales en Windows 11):**
   - Evita dejar residente `UMT5-XXL FP16` (~9.5 GB) o `Gemma` en RAM junto a expertos A14B: usa **`WanVideoTextEncodeCached` (`use_disk_cache=true`)**, versiones **GGUF Q4/Q5** (o `flux_empty_embed.pt` en `Lotus-2`) y cierra Premiere, AE, Blender pesado y Chrome antes de batches largos (fija Pagefile NVMe >=32 GB).
3. **Estrategia de Resolución, FPS & Pruebas R&D (`33f -> 167f`):**
   - En planos de fuego/VFX sobre anatomía, ejecuta primero el recorte crítico de **33 frames** validando Gates cuantitativos con **`scripts/vfx_rd_metrics_eval.py`** (`CIEDE2000 <= 1.5` en fondo blanco, ganancia puño negro `<= 1.15x`, contraste SSDO `>= 3.5:1`, pico HDR lineal `>= 4.0`, ruido/MTF `±12%`) antes de escalar a 167+ frames.
   - Para I2V/T2V general, genera en `640x360` o `832x480` a `16 fps` (81 frames ≈ 5s), escala con **SeedVR2 (3B + `block_swap`)** o **FlashVSR** (tiling) y duplica FPS al final con **Practical-RIFE** *antes* de añadir el grano final.
4. **Regla Offload JS/CPU & Pases Lineales:**
   - Si una pieza es HUD, texto cinético, gráfico de datos o 3D ligero WebGL, renderízala con **JavaScript (`Remotion` ProRes 4444 Alpha, `Motion Canvas`, `GSAP`, `Three.js` + Playwright)** en los 24 hilos del Ryzen 9 5900X o en vivo vía **`Web Render TOP`** (TD `2025.31550+`) en lugar de gastar VRAM de difusión.
   - Mantén pases técnicos (`Normal`, `Depth`, `Roughness`) siempre como **`Non-Color / Raw` EXR 16F/32F lineal** fuera de curvas gamma sRGB. **NO uses `FrequencyCombineMEC` sobre fuego HDR `>1.0`** porque recorta a `[0, 1]` SDR; compone la suma/multiplicación HDR en lineal antes del Tone Map `ACES 2.0` / `AgX`.

## Selección Rápida por Caso de Uso
- **Facilidad / Multi-modelo "GPU Poor":** `Wan2GP` (`deepbeepmeep/WanGP`) con motor `mmgp` + `INT8`.
- **Video con Audio nativo:** `LTX-2.3` / `LTX-2.5` cuantizado (`GGUF Q3_K_M/Q4_K_M`) o `LTX-Desktop`.
- **Planos I2V largos (>10s anti-drift):** `FramePack` (`lllyasviel/FramePack`).
- **Rotoscopia de cabello/tela & Matte Dual:** `SAM 2 / SAM 3` (`SegmentC2C`) ➔ `MatAnyone 2` (`max_mem_frames=5`) ➔ `MatteDesk` (`handoff/comfy/custom_nodes/ComfyUI-MatAnyone2-Keyframes`: `ForegroundDecontaminate`) / `scripts/vfx_dual_matte_decontam.py` ➔ **ProRes 4444 Straight Alpha**.
- **Borrado de objetos + sombras + reflejos:** `EffectErase` (`FudanCVL/EffectErase`) o `ProPainter` (para cables/marcas rígidas).
- **Camera Tracking 3D / Matchmoving / Point Tracking:** Video largo IA ➔ `Depth-Anything-3` (`DA3-Streaming`) o `Pi3X` (`disable_multimodal()`) o `VGGT-1B` (export `COLMAP`); oclusiones ➔ `CoTracker3` / `AllTracker`; matchmoving sub-píxel ➔ Blender Tracker / `COLMAP` (GLOMAP integrado; `colmap/glomap` deprecated); 1 foto ➔ `perarnia/fSpy`.
- **Capa de Normales (Tiempo Real <25 ms):** `DAViDNormals.tox` (~10 ms en `td-native-inference` ➔ `Relight.tox`), TouchDesigner MRT GLSL (`scripts/td_mrt_normal_pass.frag`), Blender View/World Normal AOV (`scripts/blender_normal_pass_setup.py`) vía **Spout2** o Depth-to-Normal (`scripts/td_depth_to_normal.frag`).
- **Capa de Normales (Postproducción VFX):** `NormalCrafter --max-res 512` (~6 GB, `VizClickNormalCrafter` + `VizClickNormalTemporalStabilizer`), `Lotus` SD2.1 (~4–8 GB batch rápido), `Lotus-2` FLUX GGUF (~8–11 GB micro-detalle en stills), `StableNormal-turbo` + `StableDelight` (~6–9 GB), `MoGe-2/3`, `DeepBump`. Exportar **Camera Space OpenGL `+Y` arriba en EXR 16F/32F lineal** (`FXTD-Studios/radiance` / `ComfyUI-ACES-IO`).
- **Color OCIO (`ACES 2.0` / `AgX`):** Blender 5 (`ACES 2.0`/`AgX`) · TouchDesigner (`OpenColorIO TOP`: `sRGB - Texture ➔ Linear`) · DaVinci Resolve (`ACEScct` / `ACES 2.0`) · ComfyUI (`RadianceACES2OutputTransformFull`; *RUDRA checkpoint es no-comercial*).
- **Audio IA, Foley & Subtítulos:** Foley frame-synced ➔ `hkchengrex/MMAudio` (~6 GB fp16, pesos `CC-BY-NC-4.0`); subtítulos word-sync ➔ `WhisperX` (`<8 GB`); limpieza CPU gratis ➔ `DeepFilterNet`; stems ➔ `python-audio-separator` / `Demucs`; TTS ➔ `Chatterbox` / `F5-TTS` / `Kokoro` (82M).
- **Face VFX & OBS Live:** Retoque/mirada natural ➔ `KlingAIResearch/LivePortrait` (~4–8 GB); swap ➔ `ReActor` + `CodeFormer` (`0.7–0.8`, advertencia 128px); captura GPU 60 FPS ➔ `obs-spout2-plugin` + `royshil/obs-mcp` (`4455`).
- **TouchDesigner + Blender en Vivo (Módulo C):** `TouchDesigner/TDMCP` (`http://127.0.0.1:13316/mcp`, `"serverUrl"` en Antigravity) + `TDMCPSkills` (19 `td-*` skills) o `Embody/Envoy` (TDXN YAML); separa Modos VRAM 1 (`Spout2` + `StreamDiffusionTD`), 2 (`GVHMR` ~4.2 GB ➔ Blender `mcp-for-blender`) y 3 (POPs + 3DGS).
- **Fuego / Energía VFX sobre Anatomía & Relighting PBR (Módulo A / `Workflow 4 · Ruta G`):** Separa siempre `matte_skin` vs `matte_fabric` (`vfx_dual_matte_decontam.py`), aplica **`vfx_ssdo_relight_16f.py`** (*SSDO 16-step R2* + *Cook-Torrance GGX* + *SSS* + caída `1/d²` en `16F/32F` lineal `ACEScg`/`AgX`), usa `CoTracker3` → `WanVideo ATI Tracks`, `UniLumos 1.3B` (`FrequencySeparateMEC linear=true` para LF-Ratio) o `VACE-Fun-A14B` (`Q3_K_M`/`Q4_K_S`, templates `workflows/comfyui/mod_a_01..03.json`) o malla **MANO** (`warmshao/WiLoR-mini` vía `scripts/wilor_mano_to_blender_abc.py` — evitar `Dyn-HaMR` en Win 11, nota `MANO_RIGHT.pkl` NC) → Blender Mantaflow/VDB OpenEXR. *(Aviso `[CLOUD / >24GB]`: `Relit-LiVE`, `DiffusionRenderer`/`comfyui-materia`/`UniVidX` en video largo superan 12 GB / 32 GB Win 11).*
- **Aceleración Windows:** `woct0rdho/triton-windows` + `woct0rdho/SageAttention` + `TeaCache`.
