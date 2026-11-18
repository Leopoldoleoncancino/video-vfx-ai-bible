# 02 · Rotoscopia IA, Alpha Matting, Chroma Key, Limpieza de Objetos, Depth y Relighting

En VFX moderno ya no dependes únicamente de máscaras Bezier a mano ni de *croma verde perfecto*. El ecosistema open-source 2025–2026 corre en tu **RTX 3060 12 GB** y se divide en **5 capas especializadas** según el problema de producción.

---

## 1. Rotoscopia vs Alpha Matting vs Chroma Key (Cuándo usar cada uno)

| Herramienta / Repo | Categoría | Licencia | VRAM aprox. | Fortaleza clave frente a Roto Brush / Keylight |
|---|---|---|---|---|
| **[`pq-yang/MatAnyone2`](https://github.com/pq-yang/MatAnyone2)** (★945 · CVPR 2026 Highlight) + [`ComfyUI-MatAnyone`](https://github.com/FuouM/ComfyUI-MatAnyone) (★108) | **Video Alpha Matting** | Ver repo (Research/Custom) | ~6–10 GB (1080p OK en 12GB) | **Matte temporal pixel-level**: preserva cabellos sueltos, pelo translúcido y ropa con *Learned Quality Evaluator (MQE)*. |
| **[`facebookresearch/sam3`](https://github.com/facebookresearch/sam3)** (★12,334) | **Segmentación Video por Texto/Concepto** | Ver repo (Meta SAM License) | ~6–11 GB | Segmenta y trackea objetos por **prompt de texto** o clic; perfecto para máscaras binarias limpias multi-objeto. |
| **[`cvlab-kaist/VideoMaMa`](https://github.com/cvlab-kaist/VideoMaMa)** (★554 · CVPR 2026) | **Mask → Matte Generativo** | Ver repo | ~8–12 GB | Toma una máscara dura de SAM2/SAM3 y la convierte en un **alpha matte suave preservando motion blur real**. |
| **[`1038lab/ComfyUI-RMBG`](https://github.com/1038lab/ComfyUI-RMBG)** (★2,238) | **Suite Todo-en-Uno ComfyUI** | GPL-3.0 | ~4–10 GB | Integra en un solo paquete: **RMBG-2.0, VRMBG-3.0, BiRefNet, SDMatte, SAM 1/2/3, Florence-2, YOLOv8/11, Big-Lama, GroundingDINO**. |
| **[`kijai/ComfyUI-segment-anything-2`](https://github.com/kijai/ComfyUI-segment-anything-2)** (★1,221) & [`neverbiasu/ComfyUI-SAM2`](https://github.com/neverbiasu/ComfyUI-SAM2) (★265) | **SAM 2.1 Video Tracking** | Apache-2.0 | ~4–8 GB | Ligero, ultra rápido en 3060 12GB para generar máscaras base de sujetos o placas de clean-plate. |
| **[`ZhengPeng7/BiRefNet`](https://github.com/ZhengPeng7/BiRefNet)** (★4,423) | **Foreground Matting Alta Res** | MIT | ~4–8 GB | Brutal en siluetas finas frame a frame / 2K sin croma verde. |
| **[`PeterL1n/RobustVideoMatting`](https://github.com/PeterL1n/RobustVideoMatting)** (★9,620) | **Matting en Tiempo Real** | GPL-3.0 | ~2–4 GB | Corre a +30 FPS en tu 3060 para *virtual green screen* humano en OBS/TouchDesigner o batches masivos. |

> **Combo ganador para reemplazar un Croma tradicional o Roto Brush difícil:**  
> `SAM 2 / SAM 3` (te da la máscara inicial por clic o texto) ➔ `MatAnyone 2` o `VideoMaMa` (refina bordes, pelo y desenfoque de movimiento) ➔ exportas **ProRes 4444 (Straight Alpha)** o **Luma Matte PNG 16-bit** hacia After Effects / Premiere / EffectCraft / DaVinci Resolve.

---

## 2. Eliminación de Objetos, Cables, Sombras y Reflejos (Inpainting VFX)

| Proyecto | Especialidad | Base / VRAM en 3060 12GB | Cuándo elegirlo |
|---|---|---|---|
| **[`FudanCVL/EffectErase`](https://github.com/FudanCVL/EffectErase)** (★173 · **CVPR 2026 Highlight**) | **Borrado Effect-Aware (Objeto + Sombra + Reflejo)** | Basado en `Wan2.1-Fun-1.3B-InP` + `SAM2.1` (~8–11 GB VRAM con offload) | Cuando borras un trípode, micrófono o persona y **debes eliminar también su sombra en el piso o su reflejo en un vidrio**. |
| **[`sczhou/ProPainter`](https://github.com/sczhou/ProPainter)** (★7,080) | **Flujo Óptico + Transformer (Rápido)** | ~6–10 GB (segmentando por chunks de frames en 12GB) | Limpieza determinista sin alucinaciones de difusión: cables, marcas de tracking, logos en paredes rígidas. |
| **[`lixiaowen-xw/DiffuEraser`](https://github.com/lixiaowen-xw/DiffuEraser)** (★707 · Apache-2.0) | **Diffusion Inpainting Temporal** | ~8–11 GB | Fondos complejos o texturas orgánicas donde ProPainter deja borrosidad. |
| **[`ali-vilab/VACE`](https://github.com/ali-vilab/VACE)** (★4,067 · Apache-2.0) | **Edición Unificada (Relleno / Swap / Extend)** | Variante `1.3B` nativa o `14B` GGUF | Insertar elementos nuevos o reemplazar áreas enteras con coherencia lumínica. |

---

## 3. Video Depth (Z-Depth) & Relighting Físico

| Herramienta | Propósito VFX | Notas de uso en RTX 3060 12GB |
|---|---|---|
| **[`DepthAnything/Video-Depth-Anything`](https://github.com/DepthAnything/Video-Depth-Anything)** (★2,352 · CVPR 2025 Highlight · Apache-2.0) | **Depth Map temporalmente consistente** (sin parpadeo) | Usar variantes **Small / Base** para 1080p fluido en 12GB. Exporta mapas Z-Depth limpios para desenfoque *Lens Blur* real, niebla Z y partículas 3D en After Effects / Blender / TouchDesigner. |
| **[`Tencent/DepthCrafter`](https://github.com/Tencent/DepthCrafter)** (★1,602 · CVPR 2025 Highlight) | Depth por difusión para planos abiertos | Útil en escenas complejas con transparencias/reflejos donde los modelos discriminativos dudan (más pesado en VRAM; usar tiles/chunks cortos). |
| **[`zhuxing0/Relit-LiVE`](https://github.com/zhuxing0/Relit-LiVE)** (★128 · **SIGGRAPH 2026** · Apache-2.0) | **Re-iluminación de video consistente** + mapa de entorno por frame | Cambia la iluminación completa de un plano grabado en estudio para integrarlo en otra escena o plate 3D sin depender de pose de cámara previa. |
| **[`sbharadwajj/genlit`](https://github.com/sbharadwajj/genlit)** & **IC-Light** | Re-iluminación desde referencia / HDRI | Ideal para re-iluminar *stills* clave o tarjetas 2.5D antes de animarlas con I2V. |

---

## 4. Pipeline Batch Recomendado para Tu PC (Sin Colapsar VRAM)

En [`scripts/batch_matting_pipeline.py`](../scripts/batch_matting_pipeline.py) tienes un esqueleto listo para procesar clips en secuencia **paso a paso** (sin tener dos modelos gigantes cargados al mismo tiempo en los 12 GB):
1. **Desglose:** PySceneDetect o FFmpeg divide el clip largo en planos o secuencias PNG (`%05d.png`).
2. **Máscara + Matte:** SAM 2.1 / SAM 3 genera máscara guía ➔ MatAnyone 2 produce la secuencia Alpha.
3. **Empaquetado VFX sin pérdida de bordes:** FFmpeg genera **ProRes 4444 (`yuva444p10le`)** listo para arrastrar a **Premiere, After Effects, FilmCraft, EffectCraft o DaVinci Resolve** sin halos negros (*premultiplied fringes*).
