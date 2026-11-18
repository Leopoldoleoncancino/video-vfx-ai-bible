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

## 3. Video como Código (*Programmatic Motion Graphics*)

| Framework | Repo | Stars | Cuándo usarlo en lugar de After Effects |
|---|---|---|---|
| **Remotion** | [`remotion-dev/remotion`](https://github.com/remotion-dev/remotion) | **74,117** | Gráficos de datos, UI/SaaS demos, subtítulos dinámicos y videos masivos generados desde APIs/JSON usando **React + TypeScript** (los agentes IA escriben código TSX casi perfecto!). *(Nota: licencia custom gratuita para individuos y equipos pequeños; revisar si superas umbral empresarial).* |
| **Motion Canvas** | [`motion-canvas/motion-canvas`](https://github.com/motion-canvas/motion-canvas) | 20,045 | **100% MIT**, enfocado a diagramas técnicos y animaciones vectoriales sincronizadas con línea de tiempo visual en TypeScript. |

---

## 4. Video Super-Resolution (VSR) & Frame Interpolation (Optimizado para 12 GB VRAM)

> **Por qué esto duplica la potencia de tu RTX 3060 12 GB:**  
> Generar un clip en `Wan 2.2` o `LTX-2.3` directamente a 1080p @ 30fps tarda 3–5× más o da OOM. Si generas a **`832x480 @ 16fps`** y luego aplicas **SeedVR2 / FlashVSR+** + **Practical-RIFE**, obtienes calidad 1080p/2K/60fps nítida en una fracción del tiempo.

| Herramienta | Repo Oficial | Stars | Técnica | Configuración recomendada para 3060 12GB + 32GB RAM |
|---|---|---|---|---|
| **SeedVR2 (ICLR 2026)** | [`IceClear/SeedVR2`](https://github.com/IceClear/SeedVR2) + [`ComfyUI-SeedVR2_VideoUpscaler`](https://github.com/numz/ComfyUI-SeedVR2_VideoUpscaler) | 937 / **3,000** | **Restauración por difusión adversarial en 1 solo paso** | Usa modelo **3B** (o 7B con `block_swap` activado hacia tus 32 GB RAM) + `batch_size` conservador (`5`–`9` frames por ventana temporal) y `color_correction: lab` para evitar shift cromático. |
| **FlashVSR / FlashVSR+ (CVPR 2026)** | [`OpenImagingLab/FlashVSR`](https://github.com/OpenImagingLab/FlashVSR) & [`FlashVSR_Plus`](https://github.com/OpenImagingLab/FlashVSR_Plus) | 1,979 / 250 | **Streaming VSR de 1 paso** con atención híbrida dispersa | El repo oficial `FlashVSR+` apunta 4K untiled en 24 GB VRAM; en **12 GB + 32 GB RAM** limita la salida a **1080p con tiling / CPU offload** (ver nodos comunitarios ComfyUI-FlashVSR). |
| **Practical-RIFE** | [`hzwer/Practical-RIFE`](https://github.com/hzwer/Practical-RIFE) | 1,049 | Flujo óptico neuronal RIFE (`v4.25` / `v4.26`) | Consume **<2 GB VRAM**, interpola `16fps → 32fps` o `24fps → 48/60fps` prácticamente en tiempo real en la 3060 sin deformar rostros en movimientos moderados. |
