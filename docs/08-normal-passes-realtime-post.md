# 08 · Generación de Capa de Normales: Tiempo Real GPU y Postproducción VFX

> **Calibración:** NVIDIA **RTX 3060 · 12 GB VRAM** *(Ampere)* · **Ryzen 9 5900X** · **32 GB RAM** · **Windows 11**  
> **Respuesta corta:** Mientras **Z-Depth** mide *distancia* a la cámara (`1 canal`), la **Capa de Normales (Surface Normal Pass)** codifica la *orientación 3D exacta* `(Nx, Ny, Nz)` de cada píxel (`3 canales RGB`), indispensable para **relighting físico, reflejos, bordes especulares y ControlNet geométrico** sin reconstruir toda la escena.

---

## 1. Regla Matemática Crítica (Antes de Tocar Cualquier Herramienta)

El **90 % de los errores** al pasar un *Normal Pass* entre TouchDesigner, Blender, ComfyUI, After Effects o DaVinci Resolve ocurren por mezclar convenciones de ejes o espacio de color:

| Propiedad | Estándar VFX / IA Recomendado (`3060 Pipeline`) | Cuándo cambiarlo y cómo convertir |
|---|---|---|
| **Espacio de Coordenadas** | **Camera / View Space** *(normales relativas a la lente actual)* | Estándar de **NormalCrafter, Lotus, StableNormal, DSINE, MoGe, DAViD, AE `Normality`** y **Resolve `ReLight`**. Si tu cámara 3D se mueve y proyectas luces fijas del mundo, usa **World Space**. *(Nunca uses Tangent Space UV para relighting de pantalla).* |
| **Convención Y (Verde `G`)** | **OpenGL (`+Y` arriba)** | Usado por **Blender, TouchDesigner, Nuke, Resolve Fusion, NormalCrafter, Lotus, MoGe y DAViD**. Si exportas a/desde **DirectX (`-Y` arriba: Unreal, Substance DX, 3ds Max)**, invierte solo el canal verde: `G = 1.0 - G` (rango `0..1`) o `Ny = -Ny` (float `-1..1`). |
| **Rango y Espacio de Color** | **EXR 16-bit Half / 32-bit Float Lineal (`Raw / Non-Color`)** | En `float` puro los vectores viven en `[-1, +1]`. En PNG/JPG/RGB estándar se empaquetan como `RGB = (N × 0.5) + 0.5` (`[0, 1]`). **NUNCA apliques curva sRGB/Gamma ni compresión H.264 8-bit** si harás relighting físico: destrozará la longitud unitaria (`‖N‖ != 1`) y causará *banding*. |

> **Fórmula universal de seguridad antes de iluminar (GLSL / Compositor):**  
> Si lees un Normal Map empaquetado `[0, 1]`, decodifícalo en lineal: `N = normalize(rgb * 2.0 - 1.0)`. Si además viene de DirectX, aplica `N.y = -N.y`.

---

## 2. Generación en Tiempo Real (<1–25 ms GPU en RTX 3060 12 GB)

En vivo (**TouchDesigner / Blender / OBS**) tienes **3 caminos** según si la fuente es geometría 3D real o cámara/video vivo:

| Método en Tiempo Real | Fuente | Latencia / FPS en 3060 12GB | VRAM Extra | Ventaja y Límite Honesto |
|---|---|---|---|---|
| **A. TouchDesigner `Render TOP` MRT + `GLSL MAT`** | Escena 3D nativa TD (SOPs / POPs / 3DGS) | **<1 ms · 60 FPS** | ~0 MB extra | Saca **Beauty + Normals** en un solo render usando `# Of Color Buffers >= 2` + **`Render Select TOP` (`Index 1`)**. Cero costo de doble cámara. |
| **B. Blender 4.5/5.x ➔ Spout2 (`TextureSharing`)** | Escena Blender en vivo | **<1 ms (GPU zero-copy) · 30–60 FPS** | ~1.5 GB total | Envía View Layer / Override **`VFX_Normal_CameraSpace_OpenGL`** (o AOV) por `Spout Sender` hacia `Spout In TOP` en TouchDesigner (**0 ms de latencia IA**). |
| **C. `DAViDNormals.tox` / `DAViDHuman.tox`** ([`cacheflowe/td-native-inference`](https://github.com/cacheflowe/td-native-inference)) | Webcam / Video humano en vivo | **~10 ms** *(solo Normals)* / **~21 ms** *(Depth + Normals + Matte)* | ~1.5–2.5 GB | **Modelo C++ ONNX/TensorRT nativo GPU de Microsoft (`microsoft/DAViD`, MIT)**. Estima forma 3D humana real (rostro, pliegues de ropa, brazos) a ~45–95 FPS. *El fondo no tiene geometría válida: enmascara siempre con `DAViD Matte`.* |
| **D. Depth ➔ `Normal TOP` / GLSL Sobel** ([`td_depth_to_normal.frag`](../scripts/td_depth_to_normal.frag)) | Webcam + Depth Anything 2/3, Kinect o Render Depth | **<1 ms · 60 FPS** | ~0 MB *(solo shader)* | **El truco más rápido** para escenas completas (no solo humanos): calcula gradiente `dZ/dx, dZ/dy` en GPU sobre el **Depth Map TensorRT**. Con filtro bilateral/blur ligero evita ruido en bordes. |
| **E. `Normal TOP` sobre Luminancia RGB** (Shader 2D) | Video / Textura 2D | **<0.5 ms · 60 FPS** | ~0 MB | Convierte brillo 2D en mapa de altura (*height field*). **Atención:** una camisa negra o sombra pintada se vuelve "hundida"; úsalo solo para micro-relieve de textura o *emboss* estilizado. |
| **F. `MoGe-2` ONNX (`vits-normal` 35M / `vitb-normal` 104M)** ([`microsoft/MoGe`](https://github.com/microsoft/MoGe)) | Escenas generales abiertas | **~15–45 ms** *(según resolución ONNX/TRT)* | ~1–2.5 GB | Exportado oficialmente a **ONNX dinámico** (`Ruicheng/moge-2-vits-normal-onnx`). Da **normales + depth métrico + FOV** de habitaciones/objetos completos (ideal si creas un `OnnxTOP` propio o preproceso rápido). |

### Combo Pro en TouchDesigner (Del `MODELS.md` de `td-native-inference`)
- **Forma + Micro-detalle en vivo:** Usa **`DAViD Normals`** (`~10 ms`) para la volumetría 3D real del cuerpo/rostro (resistente a luces planas o estampados) + una capa sutil pasa-altos de **`Normal TOP`** (sobre luminancia muy suavizada) renormalizada en GLSL ➔ envíalo al componente **`Relight.tox`** (GGX PBR lineal con luces que siguen manos de MediaPipe!).
- **¿Y `StreamDiffusionTD`?** En vivo (15–25 FPS @ `512x512` con `sd-turbo` + TensorRT 10.16), úsalo **consumiendo** el Normal Map o Depth Map desde Blender / `DAViD` / `td_depth_to_normal.frag` dentro del segundo input TOP (**ControlNet**). *No* intentes generar normal maps por difusión dentro de `StreamDiffusionTD` a 60 FPS: los modelos de difusión geométrica son flujos de postproducción.

> 👉 Plantillas shader listas en el repo:
> - **MRT Color Buffer GLSL MAT:** [`scripts/td_mrt_normal_pass.frag`](../scripts/td_mrt_normal_pass.frag)
> - **Depth-to-Normal OpenGL/DX Sobel Suavizado:** [`scripts/td_depth_to_normal.frag`](../scripts/td_depth_to_normal.frag)
> - **Setup automático Blender (Camera & World Normal + AOVs):** [`scripts/blender_normal_pass_setup.py`](../scripts/blender_normal_pass_setup.py)

---

## 3. Generación en Postproducción VFX (IA Local en RTX 3060 12 GB + 32 GB RAM)

En postproducción buscas **cero parpadeo temporal** en clips de video o **precisión sub-milimétrica (pelos, pliegues, tela)** en stills clave y batches de ComfyUI.

### A. Matriz de Herramientas Postproducción (Verificada Nov 2026)

| Herramienta / Repo | Licencia | VRAM Real en RTX 3060 12GB | Velocidad aprox. | Cuándo elegirlo (y Regla Anti-OOM) |
|---|---|---|---|---|
| **[`Binyr/NormalCrafter`](https://github.com/Binyr/NormalCrafter)** (ICCV 2025) + **[`ComfyUI-VizClick-NormalCrafter`](https://github.com/zuanfilm/ComfyUI-VizClick-NormalCrafter)** / **[`ComfyUI-NormalCrafterWrapper`](https://github.com/AIWarper/ComfyUI-NormalCrafterWrapper)** | MIT / Apache-2.0 | **`~6 GB` @ `512×256` (`--max-res 512`)** ⚠️ *`1024×576` pide ~20 GB!* | ~1–2 s/frame en ventanas | **Tu #1 para VIDEO con coherencia temporal.** Basado en video diffusion priors. Incluye nodo opcional *VizClick Normal Temporal Stabilizer* (flujo óptico). **Regla 3060:** mantén `max_res_dimension = 512` (o `640` máximo con `decode_chunk_size = 2..4`), `window_size = 14–20`, `time_step_size = 10` (solape) y `offload_after = true`. |
| **`Lotus` (SD2.1)** ([`EnVision-Research/Lotus`](https://github.com/EnVision-Research/Lotus) · [`1038lab/ComfyUI-Lotus-2`](https://github.com/1038lab/ComfyUI-Lotus-2) · [`kijai/ComfyUI-Lotus`](https://github.com/kijai/ComfyUI-Lotus)) | Apache-2.0 / GPL-3.0 | **~4–8 GB** (`~1.7 GB` pesos) | **~1.5 s / frame** | **Mejor relación velocidad/calidad para batches de frames o previews.** Un solo paso determinista, carga rápida, cero congestión de los 32 GB de RAM. |
| **`Lotus-2` (FLUX.1-dev + LoRA 1.43 GB)** ([`1038lab/ComfyUI-Lotus-2`](https://github.com/1038lab/ComfyUI-Lotus-2)) | Apache-2.0 / GPL-3.0 | **~8–11 GB** *(con FLUX **GGUF `Q4_K_M`/`FP8`**)* | **~13 s / frame** | **Máximo micro-detalle en stills / placas 2.5D / cabello y encaje.** Usa vector precalculado `flux_empty_embed.pt` (2 MB, ¡sin cargar 10 GB de T5 CLIP!). **Tip crítico:** usa `steps=1` en superficies lisas, pero sube a **`steps=2..4`** en pelo rizado/pelaje para borrar la cuadrícula de latentes `2×2` de FLUX. |
| **[`Stable-X/StableNormal`](https://github.com/Stable-X/StableNormal)** (`-turbo`) + `ComfyUI-StableXWrapper` | Apache-2.0 | **~6–9 GB** | **~1.1–2.3 s** (`turbo` warm) | **Mínima varianza estocástica** entre ejecuciones; la variante `StableNormal_turbo` es ~10× más rápida manteniendo nitidez superior en bordes. Útil combinar con **`StableDelight`** (del mismo repo) para remover brillos especulares. |
| **[`microsoft/MoGe`](https://github.com/microsoft/MoGe)** (`MoGe-2` / **`MoGe-3`** ago '26) | Ver repo (Microsoft) | **~2–5 GB (`MoGe-2` 35M–331M)** / ~6–9 GB (`MoGe-3 vitl` 370M) | **~60 ms** (`ViT-L` FP16 en 3090) | El mejor cuando necesitas **Normales + Depth métrico + FOV + Nube de puntos 3D** consistentes para proyectar en Blender/Nuke. *(Nota: `MoGe-3` requiere `FlexGEMM`/Triton → usa `woct0rdho/triton-windows` en Win 11).* |
| **[`Fannovel16/comfyui_controlnet_aux`](https://github.com/Fannovel16/comfyui_controlnet_aux)** (`DSINE`, `Metric3D`, `BAE`) | Apache-2.0 | **~1.5–4 GB** | **<0.2–0.5 s / frame** | Preprocesadores feed-forward ligeros (`DSINE-NormalMapPreprocessor`, `Metric3D-NormalMapPreprocessor`). Ideales para condicionar ControlNet rápido sin esperar difusión. |
| **[`huawei-bayerlab/marigold-v2`](https://github.com/huawei-bayerlab/marigold-v2-0)** ([`ComfyUI-Marigold-v2`](https://github.com/visualbruno/ComfyUI-Marigold-v2)) | Apache-2.0 | **⚠️ Límite duro en 3060 / 32GB RAM** | Lento por streaming de pesos | Basado en **Qwen-Image-Edit-2509 (20B DiT)** en 4-bit + LoRA (`~1.8 GB`). Aun en GGUF `Q3_K_M/Q4_K_M` (`9.8–13.1 GB`), supera holgado los 12 GB con activaciones y presiona los **22–24 GB de RAM libre** si tienes otras apps abiertas. Resérvalo **solo para stills héroe con ComfyUI Weight Streaming** y navegador/Premiere cerrados. |

> 💡 **Alternativa comercial NLE Windows (si ya pagas suite):** `Normal Scanner` (Blaze AI / aescripts) ofrece estimación de normales enfocada en video y cuerpo humano directo dentro de After Effects, aunque los modelos open-source arriba (`NormalCrafter`, `DAViD`, `Lotus-2`) te dan control total, salida EXR 32-bit sin marcas y automatización CLI/ComfyUI.

---

## 4. Pipeline Completo: Del Normal Pass al Relighting Final en VFX

### 1. En ComfyUI ➔ Exportación Sin Pérdida (`EXR Lineal`)
- Evita guardar tu Normal Pass como MP4 H.264 de 8-bit si lo usarás para iluminación o reflejos (la compresión 4:2:0 genera bloques en degradados suaves de caras/telas).
- Exporta secuencia **OpenEXR 16-bit Half Float** (ComfyUI nativo soporta `Save EXR` / nodes 32-bit EXR) o **PNG 16-bit** en espacio lineal.
- En videos procesados con `NormalCrafter --max-res 512`, puedes preservar el detalle de bordes escalando con método bicúbico suave + **renormalización por píxel** (`N = normalize(N)`) y un *guided filter* ligero guiado por el plate original HD.

### 2. En DaVinci Resolve Studio (Color & Fusion `ReLight FX`)
- **En Color Page (2 nodos rápidos):** El nodo `Relight` trae estimador interno de superficie, pero si lo usas:
  1. Nodo 1 (`Surface Map`): activa **Output Surface Map** y activa **Node Cache > On** (`Playback > Render Cache > User`) para no recalcular cada frame.
  2. Nodo 2 (`Lighting`): cambia **Surface Map → Use Input 2** y conecta el RGB del Nodo 1 al segundo input verde.
- **Para precisión VFX real (Fusion Page):** Crea tu Normal Pass superior con **`NormalCrafter` / `Lotus-2` / Blender EXR** y conéctalo directo al **puerto verde (`Normals`)** del nodo **`Relight [RLT]`** en Fusion (junto con `MediaIn` en entrada naranja y un `Magic Mask` / `MatAnyone 2` alpha en la entrada azul para no contaminar el fondo).

### 3. En Adobe After Effects (`32-bpc` Linear)
- Cambia el proyecto a **`32 bpc (Float)`** (`Project Settings -> Color`) y marca **Interpret Footage → Preserve RGB** en tu secuencia de Normales.
- **Con `Normality` (plugin):** Conecta el Normal Pass + (opcional) Z-Depth de `Video Depth Anything` + **Luces 3D reales de After Effects** para keyframear luces direccionales, rim lights y especulares GGX reactivos a tu cámara 3D.
- **Sin plugins (Expresión / Cálculo Canal):** Con `CC Glass` (solo relieve estilizado) o mediante `Shift Channels` + `Arithmetic` (`Channel Combiner`) calculando `max(0, dot(N, L))` para crear una máscara de *Rim Light* aditiva instantánea (`Screen` / `Add`) sobre tu `Colorista / Lumetri`!

### 4. En Blender (`Cycles / EEVEE` ➔ Compositor / TouchDesigner)
- Ejecuta **`scripts/blender_normal_pass_setup.py`** (o pídelo vía Blender MCP): crea el View Layer con AOV **`VFX_CamNormal`** (Camera Space OpenGL `[0..1]`), **`VFX_WorldNormal`** y el material override **`VFX_Normal_CameraSpace_OpenGL`** listo para transmitir directo por **`Spout Sender` (`TextureSharing`)** hacia TouchDesigner o **ControlNet Normal** en `StreamDiffusionTD` / ComfyUI sin tiempo de render extra.

---

## 5. Checklist de Decisión Rápida ("¿Cuál Uso Hoy?")

- **"Estoy haciendo visuales interactivos en vivo con persona frente a cámara en TouchDesigner"** ➔ **`DAViDNormals.tox`** (o **`DAViDHuman.tox`** si también quieres depth + matte) en `td-native-inference` (~10–21 ms) ➔ `components/Relight.tox` (o shader multi-luz con **SSDO** y material dual en [`docs/05 §5`](05-touchdesigner-realtime.md#5-relighting-pbr-multi-luz-ssdo--fuego-gpu-en-vivo-a-60-fps-ok-12gb)).
- **"Necesito guiar IA en vivo (`StreamDiffusionTD`) o luces TD desde una escena Blender a 60 FPS"** ➔ Override **`VFX_Normal_CameraSpace_OpenGL`** en Blender ➔ **`Spout2` (`BlenderNormals`)** (0 ms IA).
- **"Necesito re-iluminar un clip grabado real en Resolve/AE sin que parpadee"** ➔ **`NormalCrafter --max-res 512`** (~6 GB VRAM, `ComfyUI-VizClick-NormalCrafter` + Temporal Stabilizer) ➔ EXR 16F ➔ **Fusion `Relight` (puerto verde)** o **AE `Normality` (32-bpc)**.
- **"Necesito máxima definición de cabello, pliegues y relieve en un frame héroe o placa 2.5D"** ➔ **`Lotus-2 (FLUX GGUF)`** con `steps=2..4` (o **`StableNormal-turbo`** si quieres ~2s).
- **"Quiero que la IA saque Normales + Depth + Ángulo de cámara para proyectar un set en 3D"** ➔ **`MoGe-2`** (`vitb/vitl-normal`) o **`MoGe-3`**.
- **"Necesito oclusión dedo-a-dedo exacta, sombras de contacto sin sangrado en ropa oscura o albedo/roughness separado"** ➔ Combina este Normal Pass con **Matting Dual (`piel` vs `tela`) + Depth Raymarch (`SSDO`)** o **Inverse Rendering (`DiffusionRenderer` / `RGB-X`)** en [`docs/02`](02-rotoscoping-matting-chroma-depth.md#31-matting-dual-por-material-regla-anti-sangrado-de-glowrelight-ok-12gb), o reconstruye malla 3D MANO con **`WiLoR` / `Dyn-HaMR`** + compositing lineal `ACEScg`/`AgX` en [`docs/06`](06-blender-3d-vfx-compositing.md#5-simulación-física-de-fuego-openexr-multi-layer--compositing-lineal-acescg--agx).
