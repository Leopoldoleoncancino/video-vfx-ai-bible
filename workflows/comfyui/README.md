# Workflows ComfyUI · Módulo A (RTX 3060 12 GB `sm_86` + 32 GB RAM + Windows 11)

Plantillas **API-format JSON** (`class_type` + `inputs` verificados directamente contra el código fuente upstream de cada custom node) listas para enviarse por **ComfyUI API (`/prompt`)**, **`Comfy-Org/comfy-mcp`** / **`ComfyUI_FL-MCP`** o convertidas en carga de lotes de ComfyUI.

> ⚠️ **Regla Física RTX 3060 (`sm_86` Ampere) + 32 GB RAM:**  
> 1. **NUNCA** actives cuantizaciones `fp8_e4m3fn_fast` / `_scaled_fast` ni `WanVideoTorchCompileSettings` sobre `e4m3fn` (`sm < 8.9`, exclusivo Ada/Hopper). Usa `base_precision: "bf16"` (o `"fp16"`), `quantization: "disabled"`, `attention_mode: "sageattn"` (con `woct0rdho/triton-windows` + `woct0rdho/SageAttention`) o `"sdpa"`.  
> 2. **Cierra Premiere, After Effects, Blender pesado y Chrome** antes de ejecutar los JSON `02` o `03` (techo real ~22–24 GB RAM libres + `pagefile.sys` NVMe 32,768–65,536 MB).  
> 3. **Ejecución secuencial obligatoria:** Cada archivo incluye `VRAM_Debug` (`unload_all_models=true`) entre fases, o bien corre la generación VACE y el upscaler `SeedVR2 3B` como pasos separados si tu RAM física libre baja de 18 GB.

---

## Inventario de Templates & Dónde Cambiar Rutas (`[CAMBIAR_AQUI]`)

| Archivo JSON | Propósito en Workflow 4 (R&D `33f` ➔ `167f`) | VRAM / RAM Est. | Salida Principal |
|---|---|---|---|
| **[`mod_a_01_step0_dual_matte_normal_exr.json`](mod_a_01_step0_dual_matte_normal_exr.json)** | **Paso 0 (Geometry & Matte Bus):** `VHS_LoadVideoPath` (`frame_load_cap=33` para prueba) ➔ 2 prompts `SegmentC2C` (`piel/mano` vs `manga negra`) ➔ `MatAnyone2Run` dual ➔ `ForegroundDecontaminate` + `EdgeCleanup` ➔ `VRAM_Debug` (`unload_all_models=true`) ➔ `VizClickNormalCrafter` (`max_res_dimension=512`, `offload_after=true`) + `VizClickNormalTemporalStabilizer` ➔ **`RadianceEXRMultiPart`** (`16-bit Half Float` ZIP: `beauty`, `normal`, `matte_skin`, `matte_fabric`) + masks PNG. | ~6–9 GB VRAM *(secuencial)* | EXR multi-part lineal `16F` + `matte_skin` / `matte_fabric` limpios. |
| **[`mod_a_02_unilumos_freqsep_ciede_qc.json`](mod_a_02_unilumos_freqsep_ciede_qc.json)** | **Ruta A / G (Relight Neuronal Corto + QC):** Carga fg descontaminado + fondo neutro ➔ `WanVideoModelLoader` (`Wan2_1_UniLumos_1_3B_bf16.safetensors`, `2.84 GB`) + `WanVideoTextEncodeCached` (`umt5-xxl-enc-bf16.safetensors` con `use_disk_cache=true`, descarga automática) + `WanVideoUniLumosEmbeds` ➔ `WanVideoSampler` (`force_offload=true`) ➔ `FrequencySeparateMEC` (`Guided`, `Divide`, `Luminance`, `linear=True`) para extraer solo la **baja frecuencia lumínica** + **`VideoComparerC2C`** (`synced_player`, `CIEDE2000`/`SSIM`). | ~7–10 GB VRAM · ~15 GB RAM | `low_frequency` relit (para aplicar Light Ratio en lineal sin perder poros) + comparador A/B. |
| **[`mod_a_03_vace_fun_seedvr2_rudra_hdr.json`](mod_a_03_vace_fun_seedvr2_rudra_hdr.json)** | **Ruta A (VACE-Fun MoE Dual Expert) ➔ VSR `SeedVR2 3B` ➔ HDR/ACES 2.0:** `Wan2.2-VACE-Fun-A14B` (`HighNoise` ➔ `LowNoise` GGUF **`Q4_K_S` 10.55 GB** o **`Q3_K_M` 8.64 GB**, *evita `Q4_K_M` 11.64 GB*) + `WanVideoBlockSwap` (`blocks_to_swap=24`, `vace_blocks_to_swap=10`) + `WanVideoVACEEncode` (`strength=0.90`, control profundidad/normales + máscara de mano) ➔ `VRAM_Debug` (`unload_all_models=true`) ➔ `SeedVR2VideoUpscaler` (`3B`, `batch_size=5`, `color_correction="lab"`) ➔ `RadianceACES2OutputTransformFull` (`ACES 2.0 SDR`). | ~10.8–11.6 GB VRAM · **~20–23 GB RAM** (`[TIGHT-12GB]`) | Clip escalado HDR-ready o base para **Difference-Keyed Residual Blending** + finishing lineal. |

> ⚠️ **Regla Crítica de `FrequencyCombineMEC` vs HDR `> 1.0`:**  
> En `mod_a_02`, usamos `FrequencySeparateMEC` únicamente para extraer la capa **`low_frequency`** del relight y calcular el *Light Ratio* en **espacio lineal sin clamping** ([`scripts/vfx_ssdo_relight_16f.py`](../../scripts/vfx_ssdo_relight_16f.py), Blender Cycles EXR o Fusion/AE 32-bpc). **NO** uses `FrequencyCombineMEC` sobre fuego HDR porque clamps de ComfyUI Image (`[0, 1]`) recortarían los picos `> 1.0` de la llama causando clipping amarillo pastel.

---

## Custom Nodes Requeridos y Notas de Instalación (Windows 11)

1. [`kijai/ComfyUI-WanVideoWrapper`](https://github.com/kijai/ComfyUI-WanVideoWrapper) — `WanVideoModelLoader`, `WanVideoBlockSwap`, `WanVideoTextEncodeCached`, `WanVideoVAELoader`, `WanVideoEncode`, `WanVideoUniLumosEmbeds`, `WanVideoVACEEncode`, `WanVideoSampler`, `WanVideoDecode`.
2. [`city96/ComfyUI-GGUF`](https://github.com/city96/ComfyUI-GGUF) — lectura de pesos GGUF (`Q3_K_M` / `Q4_K_S`) en `unet_gguf`.
3. [`kijai/ComfyUI-KJNodes`](https://github.com/kijai/ComfyUI-KJNodes) — `ImageResizeKJv2`, `VRAM_Debug` (`unload_all_models=true`, `empty_cache=true`, `gc_collect=true`).
4. [`Kosinkadink/ComfyUI-VideoHelperSuite`](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite) — `VHS_LoadVideoPath`, `VHS_VideoCombine`.
5. [`Code2Collapse/ComfyUI-CustomNodePacks`](https://github.com/Code2Collapse/ComfyUI-CustomNodePacks) — `SegmentC2C` (SAM 3 / 3.1), `FrequencySeparateMEC`, `VideoComparerC2C`.
6. [`spiritform/comfy-matanyone2`](https://github.com/spiritform/comfy-matanyone2) *(o [`pq-yang/MatAnyone2`](https://github.com/pq-yang/MatAnyone2))*: `LoadMatAnyone2Model`, `MatAnyone2Run`.  
   - 🔧 **Ajuste obligatorio 12 GB VRAM en `comfy-matanyone2/config.py`:** cambia `"max_mem_frames": 10` ➔ **`5`** antes de procesar secuencias largas (>60 frames) para mantener holgura VRAM.
7. [`fishfinger44/MatteDesk`](https://github.com/fishfinger44/MatteDesk) — **¡Ojo ruta exacta!** Copia la subcarpeta `handoff/comfy/custom_nodes/ComfyUI-MatAnyone2-Keyframes` dentro de `ComfyUI/custom_nodes/` para disponer de `ForegroundDecontaminate` (`pymatting`) y `EdgeCleanup`. (Alternativa CLI sin ComfyUI: [`scripts/vfx_dual_matte_decontam.py`](../../scripts/vfx_dual_matte_decontam.py)).
8. [`zuanfilm/ComfyUI-VizClick-NormalCrafter`](https://github.com/zuanfilm/ComfyUI-VizClick-NormalCrafter) — `VizClickNormalCrafter` (`max_res_dimension=512`), `VizClickNormalTemporalStabilizer`.
9. [`numz/ComfyUI-SeedVR2_VideoUpscaler`](https://github.com/numz/ComfyUI-SeedVR2_VideoUpscaler) — `SeedVR2LoadDiTModel`, `SeedVR2LoadVAEModel`, `SeedVR2VideoUpscaler`.
10. [`FXTD-Studios/radiance`](https://github.com/FXTD-Studios/radiance) — `RadianceEXRMultiPart`, `RadianceSDRToHDRUniversal`, `RadianceACES2OutputTransformFull` (y opcional [`BISAM20/ComfyUI-ACES-IO`](https://github.com/BISAM20/ComfyUI-ACES-IO)).

---

## Pesos Exactos Recomendados (Verificados en Hugging Face)

| Modelo / Rol | Repo Hugging Face | Archivo Recomendado 3060 12 GB | Tamaño | Nota de Licencia |
|---|---|---|---|---|
| **UniLumos Relight** | `Kijai/WanVideo_comfy` | `UniLumos/Wan2_1_UniLumos_1_3B_bf16.safetensors` | **2.84 GB** | Apache-2.0 *(ver repo base)* |
| **Wan 2.2 VACE-Fun (High/Low)** | `QuantStack/Wan2.2-VACE-Fun-A14B-GGUF` | `Wan2.2-VACE-Fun-A14B-high-noise-Q3_K_M.gguf` + `low-noise-Q3_K_M.gguf` *(o `Q4_K_S`)* | **8.64 GB** / **10.55 GB** *(evita `Q4_K_M` 11.64 GB)* | Apache-2.0 |
| **Wan VAE + T5** | `Kijai/WanVideo_comfy` | `Wan2_1_VAE_bf16.safetensors` + `umt5-xxl-enc-bf16.safetensors` | — | Usar con `WanVideoTextEncodeCached` (`use_disk_cache=true`) |
| **SeedVR2 3B VSR** | Auto-descarga de `SeedVR2LoadDiTModel` | `seedvr2_ema_3b_fp8_e4m3fn.safetensors` / `bf16` + VAE 3B tiled | ~3.4–6.8 GB | Apache-2.0 |
| **RUDRA SDR→HDR *(opcional)*** | `FXTD-Studios/radiance` *(RUDRA)* | Si usas modo `Recover`/`Hybrid`, descarga checkpoint RUDRA; si no está presente hace fallback a `Expand` | — | ⚠️ **Solo uso NO comercial** *(para comercial usa HDR nativo Cycles/Mantaflow o curva analítica `Expand`)* |
