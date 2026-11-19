# Módulo A (Fase 2) · ComfyUI VFX Híbrido, Relighting PBR (`SSDO`), HDR Lineal & Workflow 4 (R&D `33f` ➔ `167f`)

> **Hardware Calibrado:** NVIDIA **RTX 3060 · 12 GB VRAM** *(`sm_86` Ampere, SIN FP8 Tensor Core nativo)* · AMD **Ryzen 9 5900X** *(12C / 24T)* · **32 GB DDR4** *(~22–24 GB libres reales en Windows 11)*  
> **Plantillas ComfyUI API JSON:** [`workflows/comfyui/README.md`](../../workflows/comfyui/README.md) · **Scripts CLI/Blender:** [`scripts/`](../../scripts/)  
> **Caso Objetivo de Referencia (Workflow 4):** Plano vertical handheld POV (`478×850`, `167 frames`, `~30 fps`) de una mano con manga negra deshilachada girando de palma a dorso frente a un escritorio blanco/impresora con fuego hiperrealista.

---

## 1. Reglas Duras de Kernel & VRAM en RTX 3060 (`sm_86`) + Windows 11

Antes de lanzar nodos de difusión, matting o normales sobre una toma real en **Windows 11 + 12 GB VRAM + 32 GB RAM**, aplica estas reglas verificadas directamente en el código fuente de los repositorios objetivo:

| Regla | Motivo Técnico Verificado `(Repo)` | Configuración Obligatoria en tu PC |
|---|---|---|
| **Prohibido `fp8_fast` y `torch.compile` en `e4m3fn`** | En `WanVideoModelLoader` (`ComfyUI-WanVideoWrapper`), los modos `*_fast` y `torch.compile` sobre `fp8_e4m3fn` exigen **`CUDA compute capability >= 8.9`** (Ada RTX 40xx+); la RTX 3060 es **`sm_86`**. | Usa `base_precision: "bf16"` (o `"fp16"`), `quantization: "disabled"`, `attention_mode: "sageattn"` (vía [`woct0rdho/triton-windows`](https://github.com/woct0rdho/triton-windows) + [`woct0rdho/SageAttention`](https://github.com/woct0rdho/SageAttention)) o `"sdpa"`. No conectes `WanVideoTorchCompileSettings`. |
| **Cuantización exacta de `Wan2.2-VACE-Fun-A14B`** | Tamaños reales en Hugging Face (`QuantStack/Wan2.2-VACE-Fun-A14B-GGUF`): `Q4_K_M` pesa **`11.64 GB`** por experto (High/Low) — deja margen casi nulo en 12 GB. `Q4_K_S` pesa **`10.55 GB`** y `Q3_K_M` pesa **`8.64 GB`**. | Usa **`Q3_K_M` (`8.64 GB`)** para iterar rápido o **`Q4_K_S` (`10.55 GB`)** para el render hero, siempre con `WanVideoBlockSwap` (`blocks_to_swap=24`, `vace_blocks_to_swap=10`, `offload_img_emb=true`, `offload_txt_emb=true`). |
| **Sin T5 residente en los 32 GB de RAM** | Cargar `umt5-xxl-enc-bf16` en RAM permanente junto a dos expertos A14B satura los ~22–24 GB libres de Win 11. | Usa **`WanVideoTextEncodeCached`** con `use_disk_cache: true` (descarga T5 inmediatamente tras generar el caché de prompt) y fija Pagefile NVMe en **32,768–65,536 MB**. |
| **Memoria temporal en `MatAnyone 2`** | En `spiritform/comfy-matanyone2/config.py`, `max_mem_frames` viene fijado por defecto en **`10`** (sube picos VRAM en secuencias `>60f`). | Edita `"max_mem_frames": 5` en `config.py` y cierra Premiere/AE/Blender pesado antes de correr ComfyUI. |
| **NormalCrafter & Secuencialidad Estricta** | `Binyr/NormalCrafter` consume ~6 GB a `512px`, pero sube a **~20 GB** a `1024×576`. | Fija `max_res_dimension = 512`, `offload_after = true` en `VizClickNormalCrafter` e inserta `VRAM_Debug` (`unload_all_models=true`, `empty_cache=true`, `gc_collect=true`) entre fases pesadas. |
| **Evitar LoRAs destiladas *CausVid* en llamas** | Las LoRAs de 4–8 steps fusionan y suavizan la micro-turbulencia Navier-Stokes del fuego. | Usa **20 steps (`euler` / `unipc`)**, `cfg: 5.0–6.0`, `shift: 6.0` sin CausVid en pases finales de fuego. |
| **Cuidado con `FrequencyCombineMEC` en HDR** | En `Code2Collapse/ComfyUI-CustomNodePacks`, `FrequencyCombineMEC` recorta (*clamps*) la salida al rango SDR `[0, 1]`. | Usa `FrequencySeparateMEC` (`linear=true`) solo para extraer la capa **`low_frequency`** del relight y calcula la multiplicación HDR + fuego `>1.0` en [`vfx_ssdo_relight_16f.py`](../../scripts/vfx_ssdo_relight_16f.py), Blender Cycles o Fusion/AE 32-bpc. |

---

## 2. Arquitectura Física y Matemática (Erradicando las 5 Fallas de `v10`)

Cada defecto visible en iteraciones 2D/8-bit previas responde a una ecuación mal planteada. Aquí tienes la solución exacta implementada en los scripts de este repositorio:

### Falla #1 · Sangrado naranja sobre puño negro y halo blanco del escritorio
- **Causa:** Un único matte mezclado trata algodón negro deshilachado y piel semibrillante como un mismo material, mientras que los bordes semitransparentes conservan fondo blanco contaminante.
- **Solución Matemática + Código ([`scripts/vfx_dual_matte_decontam.py`](../../scripts/vfx_dual_matte_decontam.py)):**
  1. Dos prompts independientes (`SAM 3 ➔ MatAnyone 2`): **`matte_skin`** (`α_skin`) y **`matte_fabric`** (`α_fabric`).
  2. Descontaminación de borde resolviendo la ecuación lineal de matting:
     $$I = \alpha F + (1 - \alpha) B \implies F = \text{ML-Foreground}(I, \alpha, \lambda=10^{-5})$$
     mediante `pymatting.estimate_foreground_ml` (presente en `MatteDesk` [`ForegroundDecontaminate`](https://github.com/fishfinger44/MatteDesk)) o estimación multi-escala NumPy + recoloreado de hilos blancos residuales (`EdgeCleanup` / limpieza de bordes).
  3. Respuesta BRDF diferenciada por canal material:
     - **Piel (`α_skin`):** `roughness = 0.34`, Fresnel `F0 = 0.028`, ganancia difusa `1.0`, SSS activo.
     - **Manga negra (`α_fabric`):** `roughness = 0.88`, Fresnel `F0 = 0.015`, ganancia difusa `0.14` (cero tinte naranja plano; solo brillo rasante real donde `N·L > 0` y `V > 0`).

### Falla #2 · Falta de oclusión 3D entre dedos doblados y sombras de contacto
- **Causa:** Aplicar solo $\max(N \cdot L, 0)$ ignora si otro dedo o el pliegue de la palma bloquea físicamente la línea de vista hacia la llama.
- **Solución Matemática + Código ([`scripts/vfx_ssdo_relight_16f.py`](../../scripts/vfx_ssdo_relight_16f.py)):**
  - **Screen-Space Depth Raymarch (`SSDO`) de 16 pasos** sobre profundidad normalizada aspect-safe (`depth_scale = 0.35` en vertical `478×850`), muestreada con secuencia cuasi-aleatoria temporal **R2 / Blue-Noise** para evitar bandas horizontales:
    $$t_s = \frac{s + 0.2 + 0.6 \cdot J_{\text{R2}}(x, y, t)}{16}, \quad \text{hit} = \left(Z_{\text{obs}} - Z_{\text{ray}} > \epsilon_z\right) \land \left(Z_{\text{obs}} - Z_{\text{ray}} < 0.95 \cdot d_{\text{scale}}\right)$$
    seguido de un filtro bilateral guiado por profundidad que limpia ruido de muestreo respetando siluetas duras de dedos.
  - Si necesitas oclusión exacta incluso cuando un dedo ocluye otro en profundidad ambigua, refuerza con malla **MANO (`WiLoR-mini`) + Holdout** en Blender (`VL_Fire_Occluded`).

### Falla #3 · Normales sin *boiling*, especular GGX y Subsurface Scattering (SSS)
- **Causa:** Un normal map inferido a `512px` y re-escalado a `478×850` en `8-bit` pierde longitud unitaria ($\|N\| \neq 1$) y genera chispas de *boiling* temporal al rotar la mano.
- **Solución:**
  1. `VizClickNormalCrafter --max-res 512` ➔ `VizClickNormalTemporalStabilizer` (flujo óptico) ➔ Exportación **EXR 16F ZIP** en **Camera Space OpenGL `+Y` arriba**.
  2. **Joint Bilateral Guided Normal Refinement** guiado por luminancia del plate original (en [`vfx_ssdo_relight_16f.py`](../../scripts/vfx_ssdo_relight_16f.py)) + renormalización estricta $N = N / \max(\|N\|_2, 10^{-5})$.
  3. **Especular Microfacet Cook-Torrance GGX:**
     $$f_{\text{spec}} = \frac{D_{\text{GGX}}(N \cdot H, \alpha_r) \cdot F_{\text{Schlick}}(V \cdot H, F_0) \cdot G_{\text{Smith}}(N \cdot V, N \cdot L)}{4\,(N \cdot V)(N \cdot L)}$$
     con `α_r = roughness²`, destacando aceites naturales y nudillos sin plastificar el dorso ni encender la manga.
  4. **SSS cálido rasante:** $(1 - N \cdot V)^{2.5} \cdot \text{wrap}(N \cdot L) \cdot \alpha_{\text{skin}}$ teñido en ámbar-carmín (`[1.0, 0.14, 0.02]`).

### Falla #4 · Llamas sin turbulencia ni núcleo HDR `>1.0` (eliminando el amarillo pastel SDR)
- **Causa:** Sumar fuego encima de un plate `sRGB 8-bit [0, 1]` satura `[R=1.0, G=1.0, B=0.2]` en amarillo chicle plano y destruye la gradación física entre núcleo blanco incandescente y lenguas rojas turbulentas.
- **Solución:**
  - **Turbulencia física real** vía placas 4K sobre negro retimed con `Practical-RIFE` + deformación por `CoTracker3` (`Ruta E`), o simulación **Mantaflow Adaptive (`224–288`) + Wavelet Noise + Shader `Principled Volume` Blackbody (`1400K → 3200K`)** advectada por velocidad de dedos (`Ruta C`, [`scripts/wilor_mano_to_blender_abc.py`](../../scripts/wilor_mano_to_blender_abc.py)).
  - **Pipeline estrictamente Lineal HDR (`16F/32F`)** donde el núcleo del fuego alcanza `> 4.0–12.0` unidades lineales, permitiendo que **Exponential Multi-Radius Glow** (`4px` / `24px` / `96px`) y **Red Halation** trabajen antes del Tone Map **AgX** o **ACES 2.0** (`RadianceACES2OutputTransformFull`), desaturando naturalmente los picos hacia blanco crema sin amarillo pastel.

### Falla #5 · Desfase MTF/grano del teléfono y cambio cálido en escritorio blanco
- **Causa:** Las sombras o brillos globales en modelos de difusión tiñen la impresora y mesa blanca lejanas, y el fuego/VSR llega más nítido o más liso que el sensor CMOS real.
- **Solución:**
  - **Neutralidad de fondo (`CIEDE2000 <= 1.5`):** Atenuación espacial física `1 / (1 + k * d²)` con ventana de radio finito + máscara opcional de escritorio/profundidad métrica (`DA3-Streaming`) para limitar cualquier rebote cálido únicamente a los ~20–35 cm próximos a la mano.
  - **Orden óptico de grano y MTF:** Match de MTF (convolución Gaussiana ligera equivalente a la lente móvil, ~0.35–0.65 px) + `SeedVR2 3B` / `Practical-RIFE` **SIEMPRE antes** de inyectar grano de luminancia/croma medido sobre un parche neutro del plate original (`eval_highfreq_noise_match` en [`scripts/vfx_rd_metrics_eval.py`](../../scripts/vfx_rd_metrics_eval.py)).

---

## 3. Matriz Comparativa Honesta de las 7 Rutas + Evaluación 4DGS (Workflow 4)

> **Convención obligatoria:** Los datos acompañados de `(Repo)` provienen de código/repos verificados; las proyecciones de tiempo/RAM para **`478×850`, `167 frames`** en tu estación **RTX 3060 12 GB + Ryzen 9 5900X + 32 GB Win 11** se etiquetan como `(Est.)`.

| Ruta | Tag Hardware | VRAM Pico `(Repo / Est.)` | RAM Win 11 `(Est.)` | Tiempo `167f` `(Est.)` | Riesgo Temporal (*Boiling*) | Control Artístico | Puntos de Fallo Conocidos en Win 11 |
|---|---|---|---|---|---|---|---|
| **Ruta A · ComfyUI Híbrido** *(VACE-Fun A14B `Q3_K_M`/`Q4_K_S` + `CoTracker3` + `UniLumos 1.3B` LF + `SeedVR2 3B`)* | `[TIGHT-12GB]` | **~9.5–11.5 GB** *(BlockSwap `24/10`)* | **~20–23 GB** *(pagefile NVMe ≥32 GB obligatorio)* | **~35–65 min** *(en ventanas 33f–81f)* | Medio–Alto *(requiere Frequency Separation y Difference Keying)* | Medio *(prompt + máscaras/normales)* | OOM/swap si se corre VACE + SeedVR2 sin `VRAM_Debug` o con navegador/Adobe abiertos; prohibido `torch.compile` `e4m3fn` en `sm_86`. |
| **Ruta B · Relighting Analítico PBR** *(`vfx_ssdo_relight_16f.py`: Normales `16F` + Depth `16F` + SSDO 16-step + GGX + SSS + Matte Dual)* | `[OK-12GB]` | **~6.0 GB** *(solo en `NormalCrafter 512px` del Paso 0)*; **~0–1 GB** en el relight | **~8–12 GB** | **~4–8 min** total *(incl. Paso 0)* | Bajo *(si usas estabilizador temporal + filtro bilateral)* | **Máximo** *(curvas BRDF, luces UVZ, roughness exactos)* | La oclusión depende 100% de la limpieza del Z-Depth relativo y normales durante el giro rápido palma→dorso. |
| **Ruta C · 3D Físico en Blender** *(`WiLoR-mini` MANO `.npz`→`.abc` + Proxy Manga + `Mantaflow Adaptive 256` + Cycles OptiX EXR Multi-Layer)* | `[OK-12GB]` / `[TIGHT-12GB]` | **~2.5–6.0 GB** *(WiLoR + Cycles OptiX)* | **~12–18 GB** *(cache Mantaflow en Ryzen 5900X)* | **~18–40 min** *(bake CPU + Cycles ~2–4s/f)* | **Mínimo** *(geometría 3D + One-Euro filter)* | **Máximo** *(simulación física + Light Ratio exacto)* | `Dyn-HaMR` rompe en Win 11 (`mmcv==1.3.9` / `chumpy`); usar **`warmshao/WiLoR-mini`** (`MANO_RIGHT.pkl` es no-comercial). Si la rotación rápida estira vértices MANO, reforzar con matte real. |
| **Ruta D · Real-Time 60 FPS (TD)** *(`DAViDNormals.tox` ~10 ms + `POPs` + `Fluid TOP` + GLSL SSDO + `OpenColorIO TOP`)* | `[OK-12GB]` | **~3.5–6.0 GB** | **~8–12 GB** | **<10 s** *(tiempo real 30–60 FPS)* | Medio *(estabilización ONNX cuadro a cuadro)* | Alto en interacción / Medio en micro-turbulencia | `DAViD` segmenta humano completo sin distinguir bien manga deshilachada negra vs piel; menor micro-detalle de flama que Cycles o placas 4K. |
| **Ruta E · Placas Fuego 4K + Tracking** *(Elementos reales s/negro + `Practical-RIFE` + `CoTracker3`/`AllTracker` warp + Relight PBR)* | `[OK-12GB]` | **~2.5–5.0 GB** | **~8–12 GB** | **~8–15 min** | **Muy Bajo** | Alto *(librería de placas reales sin warping excesivo)* | Cuando la mano gira 180° (palma→dorso), el *warping* 2D no envuelve un dedo pasando por detrás de otro si no se corta la placa por capas Front/Back (`α_hand` + `Depth`). |
| **Ruta F · Inverse Rendering + Residuo** *(`DiffusionRenderer`/`comfyui-materia`/`UniVidX` vs `RGB-X`/`IntrinsicAnything` + VACE Residual)* | `[CLOUD / >24GB]` *(full video)* / `[TIGHT-12GB]` *(solo keyframes calibration)* | **~22–48 GB** `(Repo: DiffusionRenderer / comfyui-materia / UniVidX)`; **~10–11.5 GB** *(RGB-X por frame)* | **~24–64 GB** | **N/A local** en clips largos `(167f OOM / swap severo)` | Bajo–Medio | Medio–Alto *(extrae Albedo/Roughness del escritorio)* | Dependencias Linux-first (`nvdiffrast`, `transformer-engine`) en varios wrappers; usar **solo en frames clave de calibración PBR** con `RGB-X`/`IntrinsicAnything` o en Cloud. |
| **🏆 Ruta G · 7ª Vía Híbrida SOTA (Recomendada R&D)** *(`Paso 0` Completo ➔ Fuego Dual (`Ruta C` Mantaflow Blackbody `.exr` + chispas `Ruta E`) ➔ Relight PBR (`Ruta B` `SSDO` + `UniLumos` LF-Ratio opcional) ➔ `DA3` Desk Catcher + `ACES 2.0/AgX` + `MMAudio`)* | `[OK-12GB]` / `[TIGHT-12GB]` | **~6.0–9.0 GB** *(secuencial por fases, nunca juntas)* | **~12–17 GB** | **~22–45 min** | **Mínimo** *(física 3D + normales estabilizadas + plate 100% real en piel/tela)* | **Máximo** *(combina realismo de flama/luz con preservación absoluta de poros e hilos)* | Exige disciplina de ejecución secuencial y calibración de distancia mano↔escritorio (`DA3-Streaming`) para anclar el plano catcher. |

> **Evaluación de 4DGS / Relightable Gaussians (`[CLOUD / >24GB]`):**  
> Optimizar *4D Gaussian Splatting* o *Relightable 3D/4D Gaussians* a partir de **una única toma monocular handheld** en movimiento rápido (mano rotando + llama emisiva transparente que cambia de topología cada frame) falla geométricamente en las caras ocluidas de los dedos, alucina *floaters* sobre la manga negra y supera holgado los **12 GB VRAM / 32 GB RAM** durante la optimización por escena (`>20–40 min` con calidad inferior al plate directo). No es viable ni competitivo para este plano en local frente a **Ruta C / Ruta E / Ruta G**.

---

## 4. Sinergias Explotables con Pilares 09 y 10 en Workflow 4

1. **Camera Track 3D + Escala Métrica ([Pilar 09](../09-camera-tracking-matchmoving-3d.md)):**
   - **`ByteDance-Seed/Depth-Anything-3` (`DA3-Streaming` `[OK-12GB]`):** Extrae cámara handheld consistente y la distancia relativa real entre la mano y el escritorio blanco/impresora (`--desk-distance-m` en [`wilor_mano_to_blender_abc.py`](../../scripts/wilor_mano_to_blender_abc.py)), permitiendo situar el plano *Bounce Catcher* exacto en Blender o limitar la caída $1/d^2$ en SSDO sin manchar el fondo.
   - **`CoTracker3` / `AllTracker` (`[OK-12GB]`):** Trackea yemas, palma y nudillos incluso cuando quedan ocluidos en el giro de palma a dorso, conduciendo emisores de partículas/placas (`Ruta E`/`C`) y anclando las posiciones `lights_uvz` dinámicas del relighting analítico (`Ruta B`).
2. **Colorimetría Unificada `ACES 2.0` / `AgX` ([Pilar 10 §1](../10-color-ocio-audio-face-obs.md)):**
   - Todo pasa a **scene-linear** (`16F/32F`) al inicio (`sRGB → Linear`), los núcleos de fuego se componen en rango HDR no recortado (`> 4.0`) con glow exponencial y halación roja en lineal, y el **View Transform (`AgX` o `ACES 2.0 SDR`)** se aplica exclusivamente al final del pipeline (`RadianceACES2OutputTransformFull` o Blender Compositor).
3. **Audio/Foley Sincronizado al Frame ([Pilar 10 §2](../10-color-ocio-audio-face-obs.md)):**
   - **`hkchengrex/MMAudio` (`large_44k_v2`, ~6 GB VRAM fp16 `[OK-12GB]`):** Alimentando el master final de `167f` con prompt de combustión súbita + crepitación sutil de llama cerca del micrófono del teléfono genera Foley alineado con el pico del giro de mano *(nota: verificar licencia no comercial `CC-BY-NC-4.0` de los pesos antes de entregar a cliente comercial)*.

---

## 5. Plan de Experimentos R&D por Fases (`33f` Crítico ➔ `167f` Final)

**Regla de oro:** Prohibido renderizar los **167 frames** completos sin haber superado los 3 **Gates Cuantitativos** en el recorte crítico de **33 frames** (el intervalo exacto donde la mano gira palma→dorso frente a la manga y el escritorio).

### Tabla de Criterios Objetivos de Aceptación ([`scripts/vfx_rd_metrics_eval.py`](../../scripts/vfx_rd_metrics_eval.py))

| Gate | Fase | Métrica Exacta | Umbral de Aprobación | Falla que Previene |
|---|---|---|---|---|
| **Gate 0** | Paso 0 | `unit_norm_error`, `temporal_normal_l2`, `fringe_delta_l` | `‖N‖ ∈ [0.99, 1.01]`, bordes tela `ΔL < 0.03` tras descontaminar | Normales rotas 8-bit, *boiling* y halo blanco en manga negra (F1, F3). |
| **Gate 1** | A/B `33f` | `cuff_gain_ratio`, `ssdo_shadow_contrast`, `desk_ciede2000` | Ganancia en puño negro `<= 1.15×`, contraste oclusión `>= 3.5:1`, escritorio **`CIEDE2000 <= 1.5`** | Sangrado naranja en tela (F1), dedos sin sombra (F2), mesa teñida (F5b). |
| **Gate 2** | HDR/MTF `33f` | `hdr_linear_peak`, `pastel_clip_pct`, `mtf_noise_delta_pct` | Pico fuego lineal `>= 4.0` pre-tonemap, clipping pastel mínimo, ruido HF dentro de **`±12%`** frente al plate | Fuego plano pastel SDR (F4) y "parche PEGADO IA" más liso/nítido que el móvil (F5a). |

### Secuencia Ejecutable Paso a Paso en Windows 11

```powershell
# 0. Verificar entorno Win 11, sm_86, Pagefile >= 32 GB y bibliotecas Python
.\scripts\check_3060_env.ps1

# 1. Validar que los 4 motores locales pasan sus pruebas unitarias matemáticas antes de tocar metraje
python scripts/vfx_dual_matte_decontam.py --self-test
python scripts/vfx_ssdo_relight_16f.py --self-test
python scripts/wilor_mano_to_blender_abc.py --check
python scripts/vfx_rd_metrics_eval.py --self-test

# 2. Fase 0 (Recorte crítico 33f del giro palma->dorso):
#    Extrae secuencia PNG lossless + ejecuta ComfyUI template `mod_a_01_step0_dual_matte_normal_exr.json`
#    y pasa los mattes por descontaminación dual:
python scripts/vfx_dual_matte_decontam.py `
  --plate-dir job_33f/01_plate_lin `
  --skin-matte-dir job_33f/02_matte_skin `
  --fabric-matte-dir job_33f/02_matte_fabric `
  --out-dir job_33f/03_decontam

# 3. Fase 1A (Malla 3D MANO + Manga Proxy para Ruta C / Ruta G):
python scripts/wilor_mano_to_blender_abc.py --extract --frames-dir job_33f/01_plate_lin --track-npz job_33f/mano_track.npz --fps 30
# Dentro de Blender 4.5/5.x headless:
# blender --background --python scripts/wilor_mano_to_blender_abc.py -- --blender-build --track-npz job_33f/mano_track.npz --export-abc job_33f/mano_33f.abc --desk-distance-m 0.72

# 4. Fase 1B (Relight Analítico SSDO 16F + GGX + SSS):
python scripts/vfx_ssdo_relight_16f.py `
  --plate job_33f/03_decontam/fg_decontaminated/frame_00016.npy `
  --normal job_33f/04_normals/frame_00016.npy `
  --depth job_33f/05_depth/frame_00016.npy `
  --skin-matte job_33f/02_matte_skin/frame_00016.png `
  --fabric-matte job_33f/02_matte_fabric/frame_00016.png `
  --lights-json job_33f/lights_f00016.json `
  --out job_33f/06_relit/frame_00016.exr `
  --preview-png job_33f/06_relit/frame_00016_agx.png

# 5. Evaluar Gates 1 y 2 antes de escalar de 33f -> 167f:
python scripts/vfx_rd_metrics_eval.py `
  --plate-npy job_33f/01_plate_lin/frame_00016.npy `
  --comp-hdr-npy job_33f/07_comp_hdr/frame_00016.npy `
  --comp-tonemapped-npy job_33f/07_comp_hdr/frame_00016_agx.png `
  --normal-npy job_33f/04_normals/frame_00016.npy `
  --desk-roi 10 10 140 160 `
  --out-json job_33f/metrics_gate_report.json
```

Una vez superados **Gate 0, Gate 1 (`desk_ciede2000 <= 1.5`, `cuff_gain <= 1.15x`, `ssdo_contrast >= 3.5:1`) y Gate 2 (`hdr_linear_peak >= 4.0`, `mtf_noise ±12%`)** en los 33 frames del giro crítico, escala exactamente el ganador (**Ruta G** por defecto salvo derrota numérica frente a **Ruta E** o **Ruta A**) a los **167 frames** completos, realiza finishing óptico en Blender/Fusion/AE `32-bpc` y agrega opcionalmente Foley con `MMAudio`.
