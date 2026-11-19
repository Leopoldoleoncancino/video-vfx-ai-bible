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
| **[`zhuxing0/Relit-LiVE`](https://github.com/zhuxing0/Relit-LiVE)** (★128 · **SIGGRAPH 2026** · Apache-2.0) `[CLOUD / >24GB]` | **Re-iluminación de video consistente** + mapa de entorno por frame | **⚠️ Requiere GPU ≥24 GB VRAM** en inferencia estándar (no corre nativo cómodo en 12 GB); para local en 3060 usa **`UniLumos 1.3B`** (`Frequency Separation` en [Módulo A](modules/MODULE_A_COMFYUI_VFX_3060.md)) o relighting PBR analítico [`scripts/vfx_ssdo_relight_16f.py`](../scripts/vfx_ssdo_relight_16f.py). |
| **[`sbharadwajj/genlit`](https://github.com/sbharadwajj/genlit)** & **IC-Light** `[OK-12GB]` | Re-iluminación desde referencia / HDRI | Ideal para re-iluminar *stills* clave o tarjetas 2.5D antes de animarlas con I2V. |

> 👉 **¿Buscas Capa de Normales (Surface Normal Pass) en tiempo real GPU y postproducción?** Consulta el capítulo dedicado **[`docs/08-normal-passes-realtime-post.md`](08-normal-passes-realtime-post.md)** con **NormalCrafter (`--max-res 512`), `Lotus / Lotus-2`, `StableNormal`, `MoGe-2/3`, `DAViDNormals.tox` (~10 ms en TouchDesigner)**, Blender Camera-Space AOV + convenciones OpenGL `+Y` vs DirectX `-Y`.

### 3.1 Matting Dual por Material + Descontaminación `pymatting` `[OK-12GB]`
Un error común en compositing VFX es generar un único alpha para todo el sujeto (ej. mano + manga de chaqueta oscura). Si aplicas el mismo *Light Wrap*, *Roughness* y ganancia de relighting a la piel y a la tela negra mate, o conservas el halo blanco del fondo entre hilos deshilachados, la luz cálida sangra como una mancha plana sobre la ropa.
- **Solución + Herramienta Lista ([`scripts/vfx_dual_matte_decontam.py`](../scripts/vfx_dual_matte_decontam.py)):** Ejecuta dos prompts/máscaras independientes en `SAM 2.1 / SAM 3` (`SegmentC2C`) → refina ambos con `MatAnyone 2` *(ajusta `"max_mem_frames": 5` en `comfy-matanyone2/config.py` en 12 GB)* o [`fishfinger44/MatteDesk`](https://github.com/fishfinger44/MatteDesk) (`handoff/comfy/custom_nodes/ComfyUI-MatAnyone2-Keyframes`: **`ForegroundDecontaminate`** + **`EdgeCleanup`**) resolviendo $I = \alpha F + (1 - \alpha) B$:
  1. **`matte_skin`** (piel/dedos/uñas): recibe *Roughness* bajo–medio (`0.30–0.42`), respuesta especular **GGX** pronunciada (`F0 = 0.028`) y *Subsurface Scattering* cálido en bordes finos.
  2. **`matte_fabric`** (campera/puño/ropa mate): recibe *Roughness* alto (`0.80–0.92`), difusión muy atenuada (`~0.14×`) y cero brillo especular de piel, limpiando antes hilos claros contaminados por el fondo.

### 3.2 Descomposición Intrínseca PBR (`Inverse Rendering`)
Para descomposición en canales PBR (`Albedo + Normal + Roughness + Metallic + Irradiance`), ten presente los requisitos reales en **RTX 3060 12 GB + 32 GB Win 11**:
- **[`nv-tlabs/DiffusionRenderer`](https://github.com/nv-tlabs/DiffusionRenderer)**, **[`NicholaiVogel/comfyui-materia`](https://github.com/NicholaiVogel/comfyui-materia)**, [`eggsbenedicto/DiffusionRenderer-ComfyUI`](https://github.com/eggsbenedicto/DiffusionRenderer-ComfyUI) y **[`dreamrec/UniVidX_ComfyUI`](https://github.com/dreamrec/UniVidX_ComfyUI)** **`[CLOUD / >24GB]`** *(en video local 12 GB / Win 11)* — demandan **22–48+ GB VRAM** / **35–64 GB RAM** (y dependencias orientadas a Linux como `nvdiffrast` / `transformer-engine`). Resérvalos para nube o referencia.
- **[`leob03/ComfyUI-rgbx`](https://github.com/leob03/ComfyUI-rgbx)** (`RGB -> X` y `X -> RGB`) y **[`zju3dv/IntrinsicAnything`](https://github.com/zju3dv/IntrinsicAnything)** **`[TIGHT-12GB]`** — ejecutables localmente **solo por keyframes aislados** (p. ej. calibrar albedo/roughness de la mesa/mano) descargando modelos previos con `VRAM_Debug (unload_all_models=true)`.

### 3.3 Por Qué `N·L` Solo No Basta: Sombras Raymarched en Depth (`SSDO`) + GGX + SSS
Usar las normales de [Pilar 08](08-normal-passes-realtime-post.md) únicamente con `max(dot(N, L), 0)` hace que la luz de una llama en la punta de un dedo atraviese mágicamente otros dedos doblados o ilumine la cara opuesta del puño. Para física creíble en **16F/32F lineal**, usa la versión completa de producción con **16 pasos R2/Blue-Noise, Cook-Torrance GGX, bilateral Z-smoothing y caída `1/d²` en [`scripts/vfx_ssdo_relight_16f.py`](../scripts/vfx_ssdo_relight_16f.py)** (y teoría completa en [Módulo A](modules/MODULE_A_COMFYUI_VFX_3060.md)):
1. **Visibilidad $V(p, L) \in [0, 1]$ por *Screen-Space Depth Raymarch* (`SSDO`):** Muestrear 16 pasos con jitter temporal sobre el mapa de profundidad `16F` normalizado con `depth_scale = 0.35`.
2. **Especular Microfacet (Cook-Torrance GGX) modulado por Material:** Piel con `roughness ~ 0.34` vs tela con `roughness ~ 0.88`.
3. **Subsurface Scattering (`SSS`) Rasante:** Tinte rojo-ámbar en bordes delgados (`(1.0 - N·V)^2.5`) solo donde `matte_skin > 0`.

```python
# Referencia Vectorizada (NumPy Float32): Relighting Multi-Luz PBR + Screen-Space Depth Shadows (SSDO)
# Consume Normal Pass OpenGL +Y y Depth 16F (ver docs/08). Nunca usar MP4 8-bit comprimido para normal_rgb/depth_map.
import numpy as np


def compute_normal_relight_pass(
    albedo_lin: np.ndarray,
    normal_rgb: np.ndarray,
    depth_map: np.ndarray,
    matte_skin: np.ndarray,
    matte_fabric: np.ndarray,
    lights_uvz: list[tuple[float, float, float, float]],  # (u, v, z, strength)
    fire_color_lin: tuple[float, float, float] = (1.0, 0.38, 0.06),
    radius_uv: float = 0.55,
    invert_normal_y: bool = False,
    shadow_steps: int = 8,
    depth_bias: float = 0.018,
) -> np.ndarray:
    h, w = depth_map.shape
    N = normal_rgb.astype(np.float32) * 2.0 - 1.0
    if invert_normal_y:
        N[..., 1] = -N[..., 1]
    N = N / np.maximum(np.linalg.norm(N, axis=-1, keepdims=True), 1e-5)

    uu, vv = np.meshgrid(
        np.linspace(0.0, 1.0, w, dtype=np.float32),
        np.linspace(0.0, 1.0, h, dtype=np.float32),
    )
    roughness = np.where(matte_skin > 0.5, 0.34, 0.88).astype(np.float32)
    spec_weight = (matte_skin * 0.45 + matte_fabric * 0.04).astype(np.float32)
    diff_weight = (matte_skin * 1.0 + matte_fabric * 0.22).astype(np.float32)
    fire_col = np.array(fire_color_lin, dtype=np.float32)[None, None, :]
    sss_col = np.array([1.0, 0.16, 0.02], dtype=np.float32)[None, None, :]

    ndotv = np.clip(N[..., 2], 0.0, 1.0)
    total_light = np.zeros_like(albedo_lin, dtype=np.float32)

    for lu, lv, lz, l_strength in lights_uvz:
        dx = lu - uu
        dy = lv - vv
        dz = lz - depth_map
        dist = np.sqrt(dx * dx + dy * dy + dz * dz) + 1e-5
        lx, ly, lz_dir = dx / dist, dy / dist, dz / dist

        atten = np.clip(1.0 - dist / max(radius_uv, 1e-3), 0.0, 1.0) ** 2
        vis = np.ones((h, w), dtype=np.float32)
        for s in range(1, shadow_steps + 1):
            t = s / float(shadow_steps + 1)
            sx = np.clip((uu + dx * t) * (w - 1), 0, w - 1).astype(np.int32)
            sy = np.clip((vv + dy * t) * (h - 1), 0, h - 1).astype(np.int32)
            ray_z = depth_map + dz * t
            vis = np.where(depth_map[sy, sx] > (ray_z + depth_bias), vis * 0.35, vis)

        ndotl = np.clip(N[..., 0] * lx + N[..., 1] * ly + N[..., 2] * lz_dir, 0.0, 1.0)
        hx, hy, hz = lx, ly, lz_dir + 1.0
        hlen = np.sqrt(hx * hx + hy * hy + hz * hz) + 1e-5
        ndoth = np.clip((N[..., 0] * hx + N[..., 1] * hy + N[..., 2] * hz) / hlen, 0.0, 1.0)
        shininess = np.where(roughness < 0.5, 64.0, 10.0)
        spec = (ndoth ** shininess) * spec_weight
        sss = ((1.0 - ndotv) ** 2.5) * np.clip(ndotl * 0.5 + 0.5, 0.0, 1.0) * matte_skin

        contrib = fire_col * (ndotl * diff_weight + spec)[..., None] + sss_col * (sss * 0.35)[..., None]
        total_light += contrib * (atten * vis * l_strength)[..., None]

    return albedo_lin + albedo_lin * total_light + total_light * 0.05
```

---

## 4. Pipeline Batch Recomendado para Tu PC (Sin Colapsar VRAM)

En [`scripts/batch_matting_pipeline.py`](../scripts/batch_matting_pipeline.py) tienes un esqueleto listo para procesar clips en secuencia **paso a paso** (sin tener dos modelos gigantes cargados al mismo tiempo en los 12 GB):
1. **Desglose:** PySceneDetect o FFmpeg divide el clip largo en planos o secuencias PNG (`%05d.png`).
2. **Máscara + Matte:** SAM 2.1 / SAM 3 genera máscara guía ➔ MatAnyone 2 produce la secuencia Alpha.
3. **Empaquetado VFX sin pérdida de bordes:** FFmpeg genera **ProRes 4444 (`yuva444p10le`)** listo para arrastrar a **Premiere, After Effects, FilmCraft, EffectCraft o DaVinci Resolve** sin halos negros (*premultiplied fringes*).
