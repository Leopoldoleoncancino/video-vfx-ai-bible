# 01 · Generación de Video con IA Local (Perfil RTX 3060 12 GB + Ryzen 9 5900X + 32 GB RAM + Windows 11)

> **Regla de Oro de tu Hardware:** Tu RTX 3060 tiene **12 GB de VRAM** (excelente para su gama gracias a los 12 GB frente a tarjetas de 8 GB), pero tu techo real de estabilidad en Windows 11 son los **32 GB de RAM del sistema** (~22–24 GB libres tras Windows y apps abiertas). Sin cuantización (`GGUF` / `FP8` / `INT8`), los text encoders modernos (`UMT5-XXL`, `Gemma 4 12B`) + pesos BF16 provocan *OOM* o intercambio masivo al archivo de paginación.

---

## 1. Mapa de Modelos Viables en RTX 3060 12 GB + 32 GB RAM

| Modelo / Familia | Repo Oficial (Nov 2026) | Pesos recomendados para 12 GB / 32 GB | VRAM pico aprox. | Velocidad orientativa (3060 12GB) | Mejor caso de uso |
|---|---|---|---|---|---|
| **Wan 2.2 TI2V-5B** | [`Wan-Video/Wan2.2`](https://github.com/Wan-Video/Wan2.2) (★18,759 · Apache-2.0) | FP8 / GGUF Q6_K o Q8_0 | ~8–10 GB | Rápido (~2–5 min / 5s 480p–720p) | Iteración diaria T2V / I2V con alta coherencia |
| **Wan 2.2 MoE (14B activos / 27B total)** | [`Wan-Video/Wan2.2`](https://github.com/Wan-Video/Wan2.2) | **GGUF `Q4_K_M` / `Q5_K_M`** (`ComfyUI-GGUF`) o `INT8 mmgp` (`Wan2GP`) | ~7–9.5 GB (con offload) | Medio–Lento (~8–15 min / 5s 480p) | Máxima calidad cinemática de movimiento y física |
| **Wan 2.1 1.3B / VACE 1.3B** | [`ali-vilab/VACE`](https://github.com/ali-vilab/VACE) (★4,067 · Apache-2.0) | FP16 / BF16 nativo o FP8 | ~5–7 GB | Muy rápido (~1–3 min) | Inpainting, outpainting, reference-to-video, control |
| **LTX-2.3 / LTX-2.5** | [`Lightricks/LTX-2`](https://github.com/Lightricks/LTX-2) (★10,296 · Apache-2.0) & [`LTX-Desktop`](https://github.com/Lightricks/LTX-Desktop) (★2,294) | **GGUF `Q3_K_M` / `Q4_K_M`** + text encoder cuantizado | ~9–11.5 GB ⚠️ (vigilar RAM 32 GB) | Rápido con versión *Distilled* / 2-stage | Video **con audio sincronizado nativo** y multi-shot |
| **HunyuanVideo-1.5 (8.3B)** | [`Tencent-Hunyuan/HunyuanVideo-1.5`](https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5) (★4,609) | FP8 / GGUF Q4–Q5 con atención SSTA | ~9–11 GB | Medio | Planos largos con buena adherencia a texto bilingüe |
| **FramePack (Hunyuan backbone)** | [`lllyasviel/FramePack`](https://github.com/lllyasviel/FramePack) (★17,366 · Apache-2.0) | Built-in memory-packed (~6 GB VRAM mín.) | ~6–8 GB | Estable en clips largos | Image-to-Video largo (10–60s) anti-drift en GPUs 12 GB |
| **SkyReels-V2** | [`SkyworkAI/SkyReels-V2`](https://github.com/SkyworkAI/SkyReels-V2) (★7,821) | Variantes 1.3B / 14B cuantizadas | ~6–11 GB | Medio | Planos cinematográficos continuos (diffusion forcing) |
| **InfiniteTalk** | [`MeiGen-AI/InfiniteTalk`](https://github.com/MeiGen-AI/InfiniteTalk) (★8,430 · Apache-2.0) | FP8 / GGUF | ~8–11 GB | Medio | Avatares y *lip-sync* de duración ilimitada (I2V y V2V) |
| **EchoMimic v3 (1.3B)** | [`antgroup/echomimic_v3`](https://github.com/antgroup/echomimic_v3) (★1,126 · Apache-2.0) | BF16 / FP8 | ~6–8 GB | Rápido | Animación multimodal de cuerpo/rostro desde audio |

> **Qué NO intentar correr en local sin cuantización extrema en 3060 12GB + 32GB RAM:** pesos BF16 sin comprimir de LTX-2.5 22B ni el text encoder completo Gemma 4 12B FP16 junto con editores pesados (Premiere + Chrome + Blender abiertos). Usa siempre versiones **GGUF Q4/Q5**, **FP8** o **INT8** con `mmgp`.

---

## 2. Los 2 Mejores Runners en Windows 11 para 12 GB VRAM

### A. Wan2GP (`deepbeepmeep/WanGP`) — El más fácil para "GPU Poor"
- **Repositorio:** [`deepbeepmeep/WanGP`](https://github.com/deepbeepmeep/WanGP) (★12,010)
- **Por qué brilla en 3060 12GB + 32GB RAM:** Integra el gestor de memoria **`mmgp`** y kernels `quanto` **INT8** que cargan solo las capas activas en VRAM y gestionan el streaming desde RAM sin saturar tus 32 GB.
- **Modelos soportados en una sola interfaz:** Wan 2.1/2.2, MiniMax H3, LTX-2/2.3/2.5, HunyuanVideo 1/1.5, LongCat, Kandinsky, LTXV, además de generación 3D (`Hunyuan3D 2.1`, `TRELLIS.2`) y audio (`Ace Step`, `Chatterbox`, `Qwen3 TTS`).
- **Configuración recomendada en Wan2GP para tu PC:**
  - **Memory Profile:** Perfil `3` o `4` (*Low VRAM + Fast CPU load* adaptado a 32 GB RAM; si genera OOM con LTX-2.5, bajar a perfil `4` / `5` con offload agresivo).
  - **Quantization:** `int8` (o `int8 + fp8` según soporte RTX 30xx Ampere; recuerda que Ampere **RTX 3060 NO tiene Tensor Cores FP8 nativos**, por lo que `INT8` / `GGUF` suelen ir igual o más estables que emular FP8).
  - **Attention:** `sage` (`SageAttention`) o `sdpa`.

### B. ComfyUI Modular — Máximo control VFX y nodos de producción
- **Core & Manager:** [`comfyanonymous/ComfyUI`](https://github.com/comfyanonymous/ComfyUI) / `Comfy-Org/ComfyUI`
- **Paquete obligatorio de Custom Nodes para tu 3060 12GB:**
  1. [`kijai/ComfyUI-WanVideoWrapper`](https://github.com/kijai/ComfyUI-WanVideoWrapper) (★6,818 · Apache-2.0) — BlockSwap, TeaCache, SageAttention, LoRAs, ControlNet, VACE, `WanVideoSetAttentionModeOverride`.
  2. [`city96/ComfyUI-GGUF`](https://github.com/city96/ComfyUI-GGUF) (★4,270 · Apache-2.0) — Imprescindible para cargar `Wan2.2-14B-Q4_K_M.gguf` o `UMT5-XXL-Q5_K_M.gguf` dentro de 12 GB + 32 GB.
  3. [`Lightricks/ComfyUI-LTXVideo`](https://github.com/Lightricks/ComfyUI-LTXVideo) (★4,269) — Nodos oficiales LTX-2.3 / LTX-2.5.
  4. [`kijai/ComfyUI-KJNodes`](https://github.com/kijai/ComfyUI-KJNodes) (★3,478 · GPL-3.0) — Utilidades de memoria (`CleanVRAMUsed`), máscaras y resizing.
  5. [`Kosinkadink/ComfyUI-VideoHelperSuite`](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite) (★1,923 · GPL-3.0) — Carga/exportación MP4, ProRes 4444 (alpha), secuencias PNG/EXR con control de FPS y audio.
  6. [`wuwukaka/ComfyUI-WanAnimatePlus`](https://github.com/wuwukaka/ComfyUI-WanAnimatePlus) (★427 · Apache-2.0) — Continuidad de clips largos y multi-referencia con Wan Animate.
  7. [`ModelTC/LightX2V`](https://github.com/ModelTC/LightX2V) (★3,011 · Apache-2.0) — Framework ligero de inferencia rápida y destilación step-count para video.

---

## 3. Optimización Específica Windows 11 + Ampere (RTX 3060) + Ryzen 9 5900X

1. **SageAttention + Triton en Windows 11:**
   - Instalar Triton precompilado para Windows desde [`woct0rdho/triton-windows`](https://github.com/woct0rdho/triton-windows) (★1,949 · MIT).
   - Instalar ruedas Windows de SageAttention desde [`woct0rdho/SageAttention`](https://github.com/woct0rdho/SageAttention) (★1,067 · Apache-2.0).
   - **Ganancia real:** ~25–45% más velocidad en Wan 2.2 y HunyuanVideo. *Tip:* si notas degradación en los primeros pasos con SageAttention, usa el nodo **`WanVideo Set Attention Mode Override`** para forzar `sdpa` en los primeros 2 pasos y `sage` en el resto.
2. **Flags de lanzamiento ComfyUI en tu 3060 12GB (`scripts/comfyui_3060_12gb_launch.bat`):**
   - Usa `--lowvram` solo si combinas text-encoder + upscaler en el mismo grafo; para flujos estándar Wan/LTX GGUF en 12GB suele rendir mejor `--normalvram --preview-method auto` combinado con **BlockSwap** (20–32 bloques a CPU en modelos 14B) y **Tiled VAE Decode** (tile size `256`–`512`).
   - En Ryzen 9 5900X (12 cores / 24 hilos), **desactiva Hardware-accelerated GPU scheduling** solo si ves cuelgues de Vulkan/DirectML, y cierra Premiere/AE/Chrome antes de un batch largo.
3. **Archivo de Paginación NVMe en Windows 11 (Truco clave para 32 GB RAM):**
   - Configura en tu SSD NVMe más rápido un `pagefile.sys` fijo o administrado con mínimo **32,768 MB (32 GB)** y máximo **65,536 MB (64 GB)** para absorber picos momentáneos al cargar sharded checkpoints de 20+ GB sin provocar *MemoryError* ni cierre de PyTorch.
4. **Truco del "Sweet Spot" de Duración + RIFE:**
   - En 3060 12GB, generar **81 frames (5s @ 16fps)** a **480p (`832x480`)** o **640x360 → SeedVR2 + Practical-RIFE x2 (32fps)** es entre **3x y 5x más rápido** que intentar generar 720p nativo a 30fps directamente dentro del DiT.

---

## 4. Control por Agentes IA (ComfyUI MCP)

- **Oficial:** [`Comfy-Org/comfy-mcp`](https://github.com/Comfy-Org/comfy-mcp) (★357) — 42 herramientas MCP sobre `comfy-cli>=1.14.0`; permite lanzar grafos, inspeccionar nodos, gestionar modelos y conectar con Comfy Cloud desde Antigravity/Claude/Cursor.
- **Comunidad:** [`filliptm/ComfyUI_FL-MCP`](https://github.com/filliptm/ComfyUI_FL-MCP) (★126 · MIT) — puente directo a tu servidor ComfyUI local (`127.0.0.1:8188`).
- Configs listas para copiar en [`mcps/`](../mcps/README.md).

---

## 5. Control Geométrico Avanzado, Trayectorias (`CoTracker3`/`ATI`) y Relighting en ComfyUI (12 GB VRAM)

Cuando generas efectos emisivos adheridos a anatomía (como fuego sobre una mano en movimiento, humo o fluidos con interacción de luz real), los flujos simples T2V/I2V rompen dedos o flotan desconectados del plano. En **RTX 3060 12 GB + 32 GB RAM** combina estas piezas **por fases secuenciales** (descargando VRAM entre etapas con `CleanVRAMUsed`):

### 5.1 Control Estructural Multi-Condición (`Wan2.1/2.2 VACE` + `Fun-Control`) `[TIGHT-12GB]`
- **Repositorios clave:** [`kijai/ComfyUI-WanVideoWrapper`](https://github.com/kijai/ComfyUI-WanVideoWrapper) y [`drozbay/ComfyUI-WanVaceAdvanced`](https://github.com/drozbay/ComfyUI-WanVaceAdvanced).
- **Inyección Depth + Normales + Máscara:** En lugar de generar fuego sobre fondo negro aislado, `Wan2.1_14B_VACE-Q4_K_M.gguf` o `Wan2.2-VACE-Fun-A14B` permiten condicionar la difusión con secuencias temporalmente consistentes de profundidad y normales (ver [Pilar 08](08-normal-passes-realtime-post.md)) junto a una máscara temporal suave que congela el fondo lejano (`mask = 0`) y limita la síntesis al sujeto y su zona inmediata de rebote lumínico.
- **Precaución con LoRAs aceleradoras en fuego/fluidos:** Las LoRAs destiladas de pocos pasos (ej. *CausVid*) tienden a empastar la micro-turbulencia de las llamas en manchas blandas. Para combustión hiperrealista, prioriza **18–24 pasos (`euler` / `dpmpp_2m`)**, `shift 5.0–7.0`, en ventanas solapadas a `480x848` con `BlockSwap` (20–32 bloques a CPU) + `SageAttention` y **Premiere/Blender cerrados**.

### 5.2 Trayectorias Explícitas (`CoTracker3` + `WanVideo ATI Tracks`) `[OK-12GB / TIGHT-12GB]`
- **Nodos de tracking denso:** [`s9roll7/comfyui_cotracker_node`](https://github.com/s9roll7/comfyui_cotracker_node) (Meta CoTracker3, incluye `PerlinNoiseCoordinateRandomizerNode` y `XYMotionAmplifierNode` — `[OK-12GB]` a `480p`) y [`aharley/alltracker`](https://github.com/aharley/alltracker).
- **Anclaje físico:** Extrae las trayectorias 2D de yemas de dedos, nudillos y muñeca e inyéctalas en `WanVideo ATI Tracks` (`Wan2_1-I2V-ATI-14B_fp8`, `[TIGHT-12GB]` con offload) para que las llamas o partículas hereden la inercia real en giros rápidos de cámara/mano sin despegarse.

### 5.3 Relighting Neuronal Temporal y Separación de Frecuencias (`Frequency Separation`)
- **Modelos para ComfyUI:**
  - **[`Alibaba-DAMO-Academy/Lumos-Custom`](https://github.com/alibaba-damo-academy/Lumos-Custom) (`UniLumos`):** Integrado en `ComfyUI-WanVideoWrapper` vía `WanVideoUniLumosEmbeds` (variante 1.3B basada en Wan 2.1 — `[TIGHT-12GB]` con `fp8`/offload y text encoder `umt5_xxl` cuantizado).
  - **[`smthemex/ComfyUI_Light_A_Video`](https://github.com/smthemex/ComfyUI_Light_A_Video):** Relighting *training-free* por *Progressive Light Fusion* compatible con AnimateDiff/IC-Light (`[OK-12GB]`), CogVideoX y Wan 2.1 (`[TIGHT-12GB]` / `[CLOUD / >24GB]` en 4090 si se corre BF16 sin offload).
  - **[`Aleafy/RelightVid`](https://github.com/Aleafy/RelightVid)** (`[TIGHT-12GB]` en chunks cortos) y **`IC-Light V2`** (`[OK-12GB]` en SD1.5 con [`huchenlei/ComfyUI-IC-Light-Native`](https://github.com/huchenlei/ComfyUI-IC-Light-Native); `[TIGHT-12GB]` en Flux cuantizado).
- **Regla Crítica de Producción (No Reemplazar Piel/Tela Directa):** La salida RGB directa de un modelo de relighting suele suavizar poros, huellas dactilares, uñas o hilos de ropa. Extrae únicamente la **baja/media frecuencia lumínica (`Light Ratio Pass`)** en espacio lineal y multiplícala sobre las altas frecuencias intactas del plate original, diferenciando piel de tela mediante un **matte dual** (ver [Doc 02 §3.1](02-rotoscoping-matting-chroma-depth.md#31-matting-dual-por-material-regla-anti-sangrado-de-glowrelight-ok-12gb)):

```python
# Referencia: Frequency Separation Relighting (Light Ratio Pass) en espacio lineal
# Conserva 100% poros, uñas e hilos del plate original mientras transfiere el rebote de luz IA.
import cv2
import numpy as np


def apply_ai_relight_ratio(
    plate_lin: np.ndarray,
    relit_ai_lin: np.ndarray,
    matte_skin: np.ndarray,
    matte_fabric: np.ndarray,
    sigma_low: float = 18.0,
    eps: float = 1e-3,
) -> np.ndarray:
    plate_low = cv2.GaussianBlur(plate_lin, (0, 0), sigmaX=sigma_low)
    relit_low = cv2.GaussianBlur(relit_ai_lin, (0, 0), sigmaX=sigma_low)
    light_ratio = np.clip((relit_low + eps) / (plate_low + eps), 0.25, 4.5)

    # Atenúa ganancia difusa en tela oscura mate para evitar sangrado plano naranja/gris
    material_gain = matte_skin[..., None] * 1.0 + matte_fabric[..., None] * 0.25
    blended_ratio = 1.0 + (light_ratio - 1.0) * material_gain
    return plate_lin * blended_ratio


def extract_vace_residual_fire(
    plate_lin: np.ndarray,
    vace_out_lin: np.ndarray,
    warm_bias_threshold: float = 0.04,
) -> np.ndarray:
    """Extrae solo emisión y luz cálida añadida por VACE/I2V preservando fondo/piel base."""
    delta = np.maximum(vace_out_lin - plate_lin, 0.0)
    lum = 0.2126 * delta[..., 0] + 0.7152 * delta[..., 1] + 0.0722 * delta[..., 2]
    mask = np.clip((lum - warm_bias_threshold) / 0.15, 0.0, 1.0)[..., None]
    return delta * mask
```
