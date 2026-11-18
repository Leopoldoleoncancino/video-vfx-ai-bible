# 07 · NLEs Open-Source, CLI Pipelines, Video-as-Code, VSR (Upscaling) & RIFE

Para acelerar tu producción local en **Windows 11 + RTX 3060 12 GB + Ryzen 9 5900X**, el secreto es **no renderizarlo todo dentro del modelo de difusión**: genera clips base más cortos/compactos, recorta sin pérdida y termina con **VSR de 1 paso + RIFE**.

---

## 1. Editores NLE Open-Source y Utilidades de Corte

| Herramienta | Repo Oficial | Stars | Licencia | Estado & Mejor Uso |
|---|---|---|---|---|
| **OpenCut** | [`OpenCut-app/OpenCut`](https://github.com/OpenCut-app/OpenCut) | **98,843** | MIT | La gran explosión 2025–2026: alternativa open-source limpia estilo CapCut orientada a web/desktop privado. |
| **LosslessCut** | [`mifi/lossless-cut`](https://github.com/mifi/lossless-cut) | **46,167** | GPL-2.0 | **Imprescindible:** corta, une y re-empaqueta streams (ProRes, MP4, MKV, audio stems) a velocidad de disco duro sin re-codificar ni perder un bit. |
| **Shotcut** | [`mltframework/shotcut`](https://github.com/mltframework/shotcut) | 15,722 | GPL-3.0 | NLE multiplataforma sólido basado en MLT con filtros GPU/LUTs y timeline estable en Windows 11. |
| **Kdenlive** | [`KDE/kdenlive`](https://github.com/KDE/kdenlive) | 6,140 | GPL-3.0 | Completo NLE multipista con proxies NVENC, tracking OpenCV integrado, subtítulos locales Whisper/Vosk y keyframing avanzado. |
| **FilmCraft** | [`storytold/filmcraft`](https://github.com/storytold/filmcraft) | 18,548 | Apache-2.0 | Nueva generación en **Rust puro** con MCP nativo (ver [Doc 03](03-artcraft-deep-dive.md)). |
| ⚠️ **Olive** | *(Pausado)* | — | GPL-3.0 | **Advertencia:** desarrollo detenido desde finales de 2024; evita iniciar flujos nuevos dependientes de él. |

---

## 2. Automatización por CLI & Scripting (Ryzen 9 5900X 24 Hilos + NVENC)

| Herramienta | Repo | Stars | Qué automatiza |
|---|---|---|---|
| **auto-editor** | [`WyattBlue/auto-editor`](https://github.com/WyattBlue/auto-editor) | 5,986 | Elimina silencios, pausas y fragmentos sin movimiento mediante umbrales configurables y **exporta `.xml` directo para Premiere Pro, DaVinci Resolve, Shotcut o Kdenlive** (sin recomprimir!). |
| **PySceneDetect** | [`Breakthrough/PySceneDetect`](https://github.com/Breakthrough/PySceneDetect) | 5,569 | Detecta automáticamente todos los cambios de plano de un video largo y los divide en clips numerados listos para enviar por lote a `MatAnyone 2`, `SeedVR2` o `EffectErase`. |
| **MoviePy** | [`Zulko/moviepy`](https://github.com/Zulko/moviepy) | 15,166 | Automatización Python de montajes repetitivos, composiciones de texto, audio y exportación programática. |
| **VapourSynth + `vs-mlrt`** | VapourSynth / vs-mlrt | — | Motor frame-server multihilo brutal para tu **5900X** + ejecución de redes TensorRT/ONNX (RIFE, RealESRGAN, DPIR) sobre GPU en pipelines masivos. |
| **FFmpeg (NVENC + ProRes)** | ffmpeg.org (builds `gyan.dev` en Windows) | — | Compresión rápida H.265/H.264 con hardware **NVENC RTX 3060**, proxies ligeros, y conversión de secuencias PNG/EXR a **ProRes 4444 con canal alpha**. Ver [`scripts/ffmpeg_nvenc_prores_helpers.ps1`](../scripts/ffmpeg_nvenc_prores_helpers.ps1). |

---

## 3. Video como Código & Animaciones JavaScript (*Offline* ProRes 4444 y *Tiempo Real* 60 FPS)

Usar **JavaScript / TypeScript / WebGL** para motion graphics e interfaces animadas encaja perfecto con tu PC porque **renderiza usando los 24 hilos del Ryzen 9 5900X + WebGL ligero sin ocupar los 12 GB VRAM de tus modelos de difusión**. Además, los agentes IA generan código JS/TSX/GLSL con precisión altísima.

### A. Ecosistema Verificado de Librerías JS para Video & VFX

| Framework / Librería | Repo Oficial (Verificado Nov 2026) | Stars | Licencia | Cuándo usarlo en lugar de After Effects o Blender |
|---|---|---:|---|---|
| **Three.js** + **React Three Fiber** | [`mrdoob/three.js`](https://github.com/mrdoob/three.js) · [`pmndrs/react-three-fiber`](https://github.com/pmndrs/react-three-fiber) | **118,845** / **33,817** | MIT | Escenas 3D ligeras en WebGL, shaders GLSL, cámaras de datos, Gaussian Splatting web (`storytold/spark`) y **pases de Normales/Depth en vivo** dentro de Chromium / TouchDesigner. |
| **Anime.js** | [`juliangarnier/anime`](https://github.com/juliangarnier/anime) | **74,887** | MIT | Motor v4 modular y ultra-rápido para animar SVG, DOM, Web Animation API (WAAPI) y valores numéricos de HUDs o subtítulos cinéticos. |
| **Remotion** | [`remotion-dev/remotion`](https://github.com/remotion-dev/remotion) | **74,125** | Custom *(gratis uso personal y equipos ≤3 personas)* | Estándar **React + TypeScript ➔ video determinista frame-a-frame**. Ideal para gráficos de datos, UI/SaaS demos, subtítulos dinámicos y batches desde JSON/APIs. |
| **Lottie (`lottie-web`)** | [`airbnb/lottie-web`](https://github.com/airbnb/lottie-web) | **32,512** | MIT | Reproducción vectorial `.json` / `.lottie` ultra-ligera compatible de ida y vuelta con **EffectCraft** y **After Effects (Bodymovin)**. |
| **GSAP** *(GreenSock)* | [`greensock/GSAP`](https://github.com/greensock/GSAP) | **30,895** | Licencia estándar GSAP *(uso web/gratis según términos)* | Coreografías SVG/HTML complejas (`Timeline`, `MorphSVG`, `SplitText`, física de resorte) con control milimétrico de *easing*. |
| **p5.js** | [`processing/p5.js`](https://github.com/processing/p5.js) | **24,396** | LGPL-2.1 | Arte generativo 2D/3D procedural, partículas y tipografía algorítmica lista para grabar o conectar a audio en vivo. |
| **Motion Canvas** | [`motion-canvas/motion-canvas`](https://github.com/motion-canvas/motion-canvas) | **20,045** | MIT | **100% MIT**, editor visual + generadores TypeScript para diagramas técnicos, tutoriales de código y explicadores sincronizados con audio. |
| **Theatre.js** | [`theatre-js/theatre`](https://github.com/theatre-js/theatre) | **13,055** | Apache-2.0 | Añade **timeline visual con curvas de Bézier e inspector de keyframes** encima de **Three.js / R3F / DOM** directo en el navegador. |
| **Rive (`rive-wasm`)** | [`rive-app/rive-wasm`](https://github.com/rive-app/rive-wasm) | **1,029** | MIT | Animaciones vectoriales con **State Machines interactivas** (reaccionan en vivo a señales OSC/CHOP o clic sin re-renderizar video). |

---

### B. 3 Formas Reales de Sacar Animaciones JS a tu Pipeline VFX / Live

1. **Postproducción Sin Pérdida en Premiere, After Effects, Resolve o FilmCraft (`ProRes 4444 Alpha`):**
   - **Con Remotion (comando exacto con transparencia real):** deja `<AbsoluteFill>` sin color de fondo sólido y renderiza directo a 10-bit `4:4:4:4`:
     ```bash
     npx remotion render MyComp out/overlay.mov --codec=prores --prores-profile=4444 --image-format=png --pixel-format=yuva444p10le
     ```
   - **Con GSAP / Three.js / Anime.js / Motion Canvas:** evita grabadores antiguos en desuso (ej. `timecut`) y usa exportación de secuencia PNG RGBA desde Motion Canvas o un script **Playwright** con avance determinista de reloj (`requestAnimationFrame` controlado frame a frame + `page.screenshot({ omitBackground: true })`), empaquetado con [`ConvertTo-ProRes4444Alpha`](../scripts/ffmpeg_nvenc_prores_helpers.ps1).
   - **Tip Adobe:** en After Effects verifica `Interpret Footage → Alpha: Straight - Unmatted` (o premultiplied según tu fondo CSS/canvas) para cero bordes negros.

2. **Tiempo Real a 60 FPS en TouchDesigner (`Web Render TOP` — Sin Pre-render):**
   - TouchDesigner `2025.31550+` incorpora **Chromium 132.0** con **`Use Shared Textures`** en Windows (`Web Render TOP`).
   - Carga tu HTML/Vite local con **GSAP, Three.js, Rive, Lottie o p5.js** y fondo CSS `background: transparent` (`rgba(0,0,0,0)`): TouchDesigner recibe el **canal Alpha real GPU a 60 FPS** para enviarlo directo a `Composite TOP`, **StreamDiffusionTD** o HUDs reactivos vía **WebSocket / OSC** desde tus CHOPs.
   - *(Gotcha Windows 11):* si usas dos `Web Render TOP` al mismo tiempo, asigna un **`User Cache Directory` distinto a cada uno** o el segundo lanzará error de bloqueo de caché Chromium.

3. **Puente Nativo Dentro de After Effects & EffectCraft:**
   - **After Effects moderno** ejecuta **JavaScript ES6+** de serie en su motor de **Expresiones** (mucho más limpio que ExtendScript clásico): los agentes IA pueden escribir expresiones reactivas de inercia, *overshoot*, contadores o rigs de texto directamente sobre capas AE.
   - **EffectCraft** ([`storytold/effectcraft`](03-artcraft-deep-dive.md)) ejecuta expresiones JS sobre JSON declarativo `.ecproj` y exporta/importa `.lottie` sin necesitar navegador headless.

---

## 4. Video Super-Resolution (VSR) & Frame Interpolation (Optimizado para 12 GB VRAM)

> **Por qué esto duplica la potencia de tu RTX 3060 12 GB:**  
> Generar un clip en `Wan 2.2` o `LTX-2.3` directamente a 1080p @ 30fps tarda 3–5× más o da OOM. Si generas a **`832x480 @ 16fps`** y luego aplicas **SeedVR2 / FlashVSR+** + **Practical-RIFE**, obtienes calidad 1080p/2K/60fps nítida en una fracción del tiempo.

| Herramienta | Repo Oficial | Stars | Técnica | Configuración recomendada para 3060 12GB + 32GB RAM |
|---|---|---|---|---|
| **SeedVR2 (ICLR 2026)** | [`IceClear/SeedVR2`](https://github.com/IceClear/SeedVR2) + [`ComfyUI-SeedVR2_VideoUpscaler`](https://github.com/numz/ComfyUI-SeedVR2_VideoUpscaler) | 937 / **3,000** | **Restauración por difusión adversarial en 1 solo paso** | Usa modelo **3B** (o 7B con `block_swap` activado hacia tus 32 GB RAM) + `batch_size` conservador (`5`–`9` frames por ventana temporal) y `color_correction: lab` para evitar shift cromático. |
| **FlashVSR / FlashVSR+ (CVPR 2026)** | [`OpenImagingLab/FlashVSR`](https://github.com/OpenImagingLab/FlashVSR) & [`FlashVSR_Plus`](https://github.com/OpenImagingLab/FlashVSR_Plus) | 1,979 / 250 | **Streaming VSR de 1 paso** con atención híbrida dispersa | El repo oficial `FlashVSR+` apunta 4K untiled en 24 GB VRAM; en **12 GB + 32 GB RAM** limita la salida a **1080p con tiling / CPU offload** (ver nodos comunitarios ComfyUI-FlashVSR). |
| **Practical-RIFE** | [`hzwer/Practical-RIFE`](https://github.com/hzwer/Practical-RIFE) | 1,049 | Flujo óptico neuronal RIFE (`v4.25` / `v4.26`) | Consume **<2 GB VRAM**, interpola `16fps → 32fps` o `24fps → 48/60fps` prácticamente en tiempo real en la 3060 sin deformar rostros en movimientos moderados. |
