---
name: video-vfx-3060-12gb-local
description: >
  Selecciona, optimiza y depura pipelines locales de generación de video IA, rotoscopia, matting,
  VSR y VLM/VFX ajustados estrictamente al hardware RTX 3060 12 GB VRAM + Ryzen 9 5900X + 32 GB RAM en Windows 11.
---

# Video & VFX Local Optimization Skill (RTX 3060 12 GB / 32 GB RAM / Win 11)

## Cuándo aplicar este skill
Actívalo siempre que el usuario pida instalar, elegir modelos, construir flujos de ComfyUI/Wan2GP,
rotoscopiar o hacer upscaling local en su estación de trabajo Windows 11.

## Reglas Duras de Hardware (NO romper)
1. **Límite de VRAM (12 GB GDDR6 Ampere):**
   - La RTX 3060 NO tiene FP8 Tensor Cores nativos: prioriza pesos **GGUF (`Q4_K_M`, `Q5_K_M`, `Q6_K`)** o **`INT8` (`quanto`/`mmgp`)** antes que BF16 pesados.
   - Nunca mantengas dos modelos de difusión/VLM pesados residentes en VRAM al mismo tiempo: ejecuta por fases secuenciales o inserta limpieza de memoria (`CleanVRAMUsed`).
2. **Límite de RAM del Sistema (32 GB — ~22–24 GB libres reales en Windows 11):**
   - Evita cargar Text Encoders `UMT5-XXL FP16` (~9.5 GB) o `Gemma 4 12B FP16` junto a DiT 14B/22B sin cuantizar, o se saturará RAM y pagefile.
   - Usa versiones **GGUF Q4/Q5** para el text encoder y mantén cerrado Premiere, After Effects, Blender y navegadores con muchas pestañas antes de batches largos.
3. **Estrategia de Resolución & FPS ("Sweet Spot 3060"):**
   - Genera en `640x360` o `832x480` a `16 fps` (81 frames ≈ 5s).
   - Escala a 1080p/2K en 1 paso con **SeedVR2 (3B o 7B con block_swap)** o **FlashVSR** (con tiling).
   - Duplica FPS al final con **Practical-RIFE v4.25/4.26** (`16fps -> 32fps` o `24fps -> 48fps`).

## Selección Rápida por Caso de Uso
- **Facilidad / Multi-modelo "GPU Poor":** `Wan2GP` (`deepbeepmeep/WanGP`) con motor `mmgp` + `INT8`.
- **Video con Audio nativo:** `LTX-2.3` / `LTX-2.5` cuantizado (`GGUF Q3_K_M/Q4_K_M`) o `LTX-Desktop`.
- **Planos I2V largos (>10s anti-drift):** `FramePack` (`lllyasviel/FramePack`).
- **Rotoscopia de cabello/tela sin croma verde:** `SAM 2 / SAM 3` ➔ `MatAnyone 2` o `VideoMaMa` ➔ **ProRes 4444 Straight Alpha**.
- **Borrado de objetos + sombras + reflejos:** `EffectErase` (`FudanCVL/EffectErase`) o `ProPainter` (para cables/marcas rígidas).
- **Aceleración Windows:** `woct0rdho/triton-windows` + `woct0rdho/SageAttention` + `TeaCache`.
