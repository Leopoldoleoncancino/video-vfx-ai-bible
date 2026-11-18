---
name: video-vfx-3060-12gb-local
description: >
  Selecciona, optimiza y depura pipelines locales de generación de video IA, rotoscopia, matting,
  capa de normales, TouchDesigner/Blender en vivo, VSR y offload JS ajustados estrictamente al hardware
  RTX 3060 12 GB VRAM + Ryzen 9 5900X + 32 GB RAM en Windows 11.
---

# Video & VFX Local Optimization Skill (RTX 3060 12 GB / 32 GB RAM / Win 11)

## Cuándo aplicar este skill
Actívalo siempre que el usuario pida instalar, elegir modelos, construir flujos de ComfyUI/Wan2GP,
rotoscopiar, sacar capa de normales, conectar TouchDesigner + Blender o hacer upscaling/motion local en Windows 11.

## Reglas Duras de Hardware (NO romper)
1. **Límite de VRAM (12 GB GDDR6 Ampere):**
   - La RTX 3060 NO tiene FP8 Tensor Cores nativos: prioriza pesos **GGUF (`Q4_K_M`, `Q5_K_M`, `Q6_K`)** o **`INT8` (`quanto`/`mmgp`)** antes que BF16 pesados.
   - Nunca mantengas dos modelos de difusión/VLM pesados residentes en VRAM al mismo tiempo: ejecuta por fases secuenciales o inserta limpieza de memoria (`CleanVRAMUsed`).
2. **Límite de RAM del Sistema (32 GB — ~22–24 GB libres reales en Windows 11):**
   - Evita cargar Text Encoders `UMT5-XXL FP16` (~9.5 GB), `T5` o `Gemma 4 12B FP16` junto a DiT 14B/22B sin cuantizar, o se saturará RAM y pagefile.
   - Usa versiones **GGUF Q4/Q5** para el text encoder (o `flux_empty_embed.pt` en `Lotus-2`) y mantén cerrado Premiere, After Effects, Blender y navegadores con muchas pestañas antes de batches largos.
3. **Estrategia de Resolución & FPS ("Sweet Spot 3060"):**
   - Genera en `640x360` o `832x480` a `16 fps` (81 frames ≈ 5s).
   - Escala a 1080p/2K en 1 paso con **SeedVR2 (3B o 7B con block_swap)** o **FlashVSR** (con tiling).
   - Duplica FPS al final con **Practical-RIFE v4.25/4.26** (`16fps -> 32fps` o `24fps -> 48fps`).
4. **Regla Offload JS/CPU:**
   - Si una pieza es HUD, texto cinético, gráfico de datos o 3D ligero WebGL, renderízala con **JavaScript (`Remotion` ProRes 4444 Alpha, `Motion Canvas`, `GSAP`, `Three.js` + Playwright)** en los 24 hilos del Ryzen 9 5900X o en vivo vía **`Web Render TOP`** (TD `2025.31550+`) en lugar de gastar VRAM de difusión.

## Selección Rápida por Caso de Uso
- **Facilidad / Multi-modelo "GPU Poor":** `Wan2GP` (`deepbeepmeep/WanGP`) con motor `mmgp` + `INT8`.
- **Video con Audio nativo:** `LTX-2.3` / `LTX-2.5` cuantizado (`GGUF Q3_K_M/Q4_K_M`) o `LTX-Desktop`.
- **Planos I2V largos (>10s anti-drift):** `FramePack` (`lllyasviel/FramePack`).
- **Rotoscopia de cabello/tela sin croma verde:** `SAM 2 / SAM 3` ➔ `MatAnyone 2` o `VideoMaMa` ➔ **ProRes 4444 Straight Alpha**.
- **Borrado de objetos + sombras + reflejos:** `EffectErase` (`FudanCVL/EffectErase`) o `ProPainter` (para cables/marcas rígidas).
- **Capa de Normales (Tiempo Real <25 ms):** `DAViDNormals.tox` (~10 ms en `td-native-inference` ➔ `Relight.tox`), TouchDesigner MRT GLSL (`scripts/td_mrt_normal_pass.frag`), Blender View/World Normal AOV (`scripts/blender_normal_pass_setup.py`) vía **Spout2** o Depth-to-Normal (`scripts/td_depth_to_normal.frag`).
- **Capa de Normales (Postproducción VFX):** `NormalCrafter --max-res 512` (~6 GB, coherencia temporal de video), `Lotus` SD2.1 (~4–8 GB batch rápido), `Lotus-2` FLUX GGUF (~8–11 GB micro-detalle en stills), `StableNormal-turbo` (~6–9 GB baja varianza), `MoGe-2/3` (normales + depth métrico + FOV). Usar siempre **Camera Space, OpenGL `+Y` arriba, EXR 16F/32F lineal** (nunca H.264 8-bit para relighting en Resolve `ReLight` o AE `Normality`).
- **TouchDesigner + Blender en Vivo (Módulo C):** `TouchDesigner/TDMCP` (`http://127.0.0.1:13316/mcp`, `"serverUrl"` en Antigravity) + `TDMCPSkills` (19 `td-*` skills) o `Embody/Envoy` (TDXN YAML); separa Modos VRAM 1 (`Spout2` + `StreamDiffusionTD`), 2 (`GVHMR` ~4.2 GB ➔ Blender `mcp-for-blender`) y 3 (POPs + 3DGS).
- **Aceleración Windows:** `woct0rdho/triton-windows` + `woct0rdho/SageAttention` + `TeaCache`.
