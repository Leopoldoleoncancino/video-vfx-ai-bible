# Pipelines End-to-End (Del Guion / Toma Cruda al Master Final en tu PC Local)

Estas arquitecturas conectan todas las herramientas de la Biblia respetando el límite físico de **12 GB VRAM + 32 GB RAM en Windows 11** (evita abrir dos apps GPU pesadas simultáneamente en los pasos de difusión).

---

## Workflow 1 · Plano VFX IA Híbrido (Live-Action + Inserción / Rotoscopia + Relighting)

Ideal para reemplazar croma verde, borrar equipos de rodaje y componer un personaje o criatura IA dentro de video real grabado con cámara.

```
[Toma Real MP4/MOV]
   ├──▶ 1. PySceneDetect / LosslessCut ──▶ Recorte exacto del plano útil (cero re-compresión)
   │
   ├──▶ 2. (Si hay objetos/sombras por borrar)
   │       SAM 2.1 (máscara) ──▶ EffectErase (objeto + sombra/reflejo) o ProPainter (cables rígidos)
   │
   ├──▶ 3. (Para extraer sujeto sin Green Screen)
   │       SAM 3 (texto/clic) ──▶ MatAnyone 2 (alpha pelo/tela) ──▶ Export ProRes 4444 Straight Alpha
   │
   ├──▶ 4. (Pases de profundidad, NORMALES e iluminación)
   │       Video Depth Anything (Z-Depth) + NormalCrafter --max-res 512 / Lotus-2 (Normal EXR 16F OpenGL +Y)
   │       + UniLumos 1.3B (Freq. Separation) / SSDO PBR (scripts/vfx_ssdo_relight_16f.py) o Fusion Relight / AE Normality [32-bpc]
   │       (Relit-LiVE solo en Cloud >=24 GB VRAM)
   │
   └──▶ 5. Compositing Final (elige ruta según proyecto):
           ├── Ruta A (Comercial/Plugins): After Effects (Normality 32-bpc) + Premiere Pro (Dynamic Link)
           ├── Ruta B (3D/CG): Blender 5.x (cámara + 3DGS + Normal AOV)
           └── Ruta C (Ágil/Lottie/Código): EffectCraft / DaVinci Resolve + MCP
```

---

## Workflow 2 · Generación Cinemática Local Rápida (3060 12GB Sweet Spot)

Evita renders eternos de 45 minutos por un clip fallido siguiendo la regla **Draft Low-Res ➔ Upscale 1-Step ➔ Interpolar FPS**:

1. **Previs y Staging (0 VRAM pesada):** Diseña la composición 3D/pose del plano en **ArtCraft Studio** o **Blender (`mcp-for-blender`)** y exporta el *keyframe inicial* (o mapa de profundidad/normal/canny).
2. **Generación Base (Cierra Premiere/Blender):**
   - **Opción A (Con audio sincronizado y multi-shot):** **LTX-2.3 / LTX-2.5 GGUF Q3/Q4** o **Wan2GP (`mmgp`)**.
   - **Opción B (Máxima física/calidad sin audio):** **Wan 2.2 MoE GGUF `Q4_K_M`** (o `5B FP8` para pruebas rápidas) a **`832x480` · 81 frames (~5s @ 16fps)** con **SageAttention + TeaCache**.
   - **Opción C (Plano continuo >15s desde imagen):** **`FramePack`** (6–8 GB VRAM, sin drift temporal).
3. **Limpieza & Escalado:**
   - Pasa el clip por **`SeedVR2` (3B o 7B con block swap)** en ComfyUI para llevar de `480p → 1080p/2K` en 1 paso recuperando piel, ojos y grano fino.
4. **Fluidez:**
   - Corre **`Practical-RIFE` (`x2`)** para pasar de `16fps → 32fps` (o conformar a `24fps`/`30fps`).
5. **Montaje Final:**
   - Ensambla en **Premiere Pro (`premiere-pro-mcp`)**, **FilmCraft** (`filmcraft-cli mcp`) o **DaVinci Resolve (`davinci-resolve-mcp`)**.

---

## Workflow 3 · Automatización Total de Video Híbrido (Premiere / EffectCraft / JS / TouchDesigner)

### Para YouTube / Talking-Head / Documental Técnico / Motion Graphics JS
1. **Corte automático de silencios y retakes:** **`Open Cut Agent`** (en vivo en Premiere) o **`auto-editor`** CLI exportando XML.
2. **Gráficos animados vectoriales, 3D WebGL y datos por código JS (0 GB VRAM IA):** Agente IA genera componentes en **Remotion** (`--codec=prores --prores-profile=4444 --pixel-format=yuva444p10le`), **Motion Canvas**, **GSAP / Three.js / Anime.js** (Playwright RGBA ➔ ProRes 4444 vía [`ConvertTo-ProRes4444Alpha`](../scripts/ffmpeg_nvenc_prores_helpers.ps1)) o proyectos JSON **`.ecproj` en EffectCraft** (`effectcraft-cli mcp`) exportando a `.lottie`.
3. **Avatares / Traducción Lip-Sync:** **`InfiniteTalk`** o **`EchoMimic v3` (1.3B)** cuando necesites tomas parlantes sincronizadas con un audio nuevo.

### Para Visuales Generativos / Escenario / Instalaciones en Vivo
1. **Esqueleto de nodos IA:** **`TouchDesigner/TDMCP`** (oficial, soporte directo Antigravity en `http://127.0.0.1:13316/mcp`) o **`Embody / Envoy`** (con TDXN YAML versionado en Git).
2. **Tracking, Normales en Vivo, HUDs JS & Física GPU:** **MediaPipe TD** + **`DAViDNormals.tox`** (~10 ms GPU en `td-native-inference` ➔ `Relight.tox`), **`Render TOP` MRT + `td_mrt_normal_pass.frag`** alimentando **POPs** en GPU, y **`Web Render TOP` (Chromium 132.0)** inyectando overlays **GSAP / Three.js / Rive / p5.js** transparentes a **60 FPS** vía CHOP/WebSocket.
3. **Difusión en vivo / puente:** **StreamDiffusionTD** (Turbo/LCM en 3060 guiado por Z-Depth o `BlenderNormals` vía **Spout2**) y grabación master ProRes / EXR 16F ([ver Pilar 08](../docs/08-normal-passes-realtime-post.md)).

---

## Workflow 4 · Fuego / Energía Hiperrealista Adherido a Anatomía con Capa de Normales (7 Rutas Comparadas + R&D `33f` ➔ `167f`)

Marco de referencia R&D para efectos emisivos sobre manos/cuerpo en rotación donde la luz, las sombras interdigitales y el bloqueo sobre ropa oscura deben respetar geometría real sin caer en el antipatrón de *"brillo radial 2D sangrando sobre tela"*.  
👉 **Manual profundo paso a paso, matemáticas y comandos:** [`docs/modules/MODULE_A_COMFYUI_VFX_3060.md`](../docs/modules/MODULE_A_COMFYUI_VFX_3060.md) y templates API en [`workflows/comfyui/`](comfyui/README.md).

### Paso 0 Común · "Geometry, Matte Dual & Tracking Bus" (Siempre 16-bit Float / EXR)
> **Regla crítica:** Nunca exportes máscaras, mapas de profundidad ni normales en MP4 8-bit `yuv420p` (genera *stair-stepping* especular y bloques); usa **OpenEXR 16F/32F lineal** (`Camera Space`, **OpenGL `+Y` arriba**, ver [Pilar 08](../docs/08-normal-passes-realtime-post.md)) o `ProRes 4444` Straight Alpha para mattes. Template ComfyUI: [`mod_a_01_step0_dual_matte_normal_exr.json`](comfyui/mod_a_01_step0_dual_matte_normal_exr.json).

1. **Matte Dual + Descontaminación `[OK-12GB]`:** `SegmentC2C` (SAM 3 prompts separados: piel vs manga negra) ➔ `MatAnyone 2` (`max_mem_frames=5`) ➔ `ForegroundDecontaminate`/`EdgeCleanup` o [`scripts/vfx_dual_matte_decontam.py`](../scripts/vfx_dual_matte_decontam.py) ([Doc 02 §3.1](../docs/02-rotoscoping-matting-chroma-depth.md#31-matting-dual-por-material--descontaminaci%C3%B3n-pymatting-ok-12gb)).
2. **Depth Temporal & Escala Métrica `[OK-12GB]`:** `DA3-Streaming` (distancia real mano↔escritorio + cámara) + `Video Depth Anything` (Small/Base).
3. **Capa de Normales:** `DAViDNormals.tox` (~10 ms GPU en vivo), `VizClickNormalCrafter` (`max_res_dimension=512` + `VizClickNormalTemporalStabilizer`) o malla 3D `WiLoR-mini` MANO ([`scripts/wilor_mano_to_blender_abc.py`](../scripts/wilor_mano_to_blender_abc.py)).
4. **Tracking `[OK-12GB]`:** `CoTracker3` / `AllTracker` o `MediaPipe` + orientación de palma/dorso.

### Paso 1 · Comparativa Neutral de las 7 Rutas (Perfil 3060 12 GB `sm_86` / 32 GB RAM Win 11)

| Ruta | Tag Hardware | Stack Principal | Cómo Resuelve Oclusión + Relighting | Trade-off Clave |
|---|---|---|---|---|
| **Ruta A · ComfyUI Híbrido** | `[TIGHT-12GB]` | `Wan2.2-VACE-Fun-A14B` (`Q3_K_M`/`Q4_K_S` + `BlockSwap`) + `CoTracker3` + `UniLumos 1.3B` + `SeedVR2 3B` | Trayectorias + normales/máscara en VACE (`mod_a_03`); relighting vía **Frequency Separation (`low_frequency`)** (`mod_a_02`) + *Difference-Keyed Residual Blending*. | Sin `fp8_fast`/`torch.compile` en `sm_86`; requiere `VRAM_Debug (unload_all_models=true)` y Pagefile ≥32 GB. |
| **Ruta B · Relighting Analítico PBR** | `[OK-12GB]` | [`scripts/vfx_ssdo_relight_16f.py`](../scripts/vfx_ssdo_relight_16f.py) (Normales `16F` + `Depth` + **SSDO 16-step R2**) | Multi-emisor (yemas/palma), BRDF **Cook-Torrance GGX** por matte (`roughness` piel `0.34` vs tela `0.88`), **SSS** de borde, caída `1/d²` y sombras SSDO ([Doc 02 §3.3](../docs/02-rotoscoping-matting-chroma-depth.md#33-por-qué-nl-solo-no-basta-sombras-raymarched-en-depth-ssdo--ggx--sss)). | Muy rápido (`~4–8 min` Est.) y 100% determinista; depende directo de la limpieza de Normales y Depth. |
| **Ruta C · 3D Físico Puro (Blender)** | `[OK-12GB]` / `[TIGHT-12GB]` | **`WiLoR-mini`** (MANO `.abc` + filtro One-Euro + proxy manga) + Blender 4.5 `Mantaflow` / `OpenVDB` + Cycles | Malla MANO + manga con `Holdout` dan oclusión 3D exacta; **Multi-Layer OpenEXR** (`VL_Fire_Occluded`, `VL_Hand_Lit / VL_Hand_Ambient` *Light Ratio*, [Doc 06 §5](../docs/06-blender-3d-vfx-compositing.md#5-simulación-física-de-fuego-openexr-multi-layer--compositing-lineal-acescg--agx)). | Máxima física 3D; usar `WiLoR-mini` (no `Dyn-HaMR` en Win 11) y respetar licencia NC de `MANO_RIGHT.pkl`. |
| **Ruta D · Real-Time 60 FPS (TD)** | `[OK-12GB]` | TouchDesigner `POPs` + `DAViDNormals.tox` + `Fluid TOP` + GLSL | Fluido advectado por MediaPipe + deflexión por normales + `POPs` chispas GPU + shader 6 luces + `SSDO` en `32-bit Float TOP` ([Doc 05 §5](../docs/05-touchdesigner-realtime.md#5-relighting-pbr-multi-luz-ssdo--fuego-gpu-en-vivo-a-60-fps-ok-12gb)). | Interactivo a 60 FPS sin esperas de render; menor micro-turbulencia que Cycles o placas 4K. |
| **Ruta E · Stock Fuego 4K + Tracking** | `[OK-12GB]` | Placas reales de fuego sobre negro + `CoTracker3` / `AllTracker` + `Practical-RIFE` | Deformación no-rígida anclada a dedos, retiming `RIFE` ([Doc 07 §4.1](../docs/07-opensource-nles-cli-upscaling.md#41-orden-óptico-en-vfx-híbrido-stock-4k--practical-rife--seedvr2--re-grain-ok-12gb)), capas Front/Back y relight PBR por normales. | Cero alucinaciones IA y combustión 100% real; exige dividir Front/Back para giros de 180°. |
| **Ruta F · Inverse Rendering + Residuo** | `[CLOUD / >24GB]` / `[TIGHT-12GB]` | `DiffusionRenderer` / `comfyui-materia` / `UniVidX` *(Cloud/≥24GB)* vs `ComfyUI-rgbx` / `IntrinsicAnything` *(solo keyframes)* | Descompone `Albedo + Normal + Roughness + Irradiance` para calibrar materiales o extraer residuo en VACE. | Video largo excede 12 GB VRAM / 32 GB RAM Win 11; útil solo en keyframes de calibración o nube. |
| **Ruta G · Híbrida SOTA R&D *(7ª Vía Recomendada)*** | `[OK-12GB]` / `[TIGHT-12GB]` | `Paso 0 Bus` + **Fuego Dual (`Ruta C` Mantaflow Blackbody + chispas `Ruta E`)** + **Relight (`Ruta B` SSDO + `UniLumos` LF-Ratio opcional)** + `DA3` Desk + `ACES 2.0/AgX` + `MMAudio` | Combina turbulencia Navier-Stokes HDR `>1.0` y Holdout 3D real (`MANO`) con relighting PBR determinista sobre poros e hilos 100% intactos del plate real, ejecutado secuencialmente. | Requiere disciplina por fases (~22–45 min Est. para 167f), pero elimina las 5 fallas de `v10` sin alucinaciones IA. |

*(Nota R&D: **4DGS / Relightable Gaussians** se clasifican como **`[CLOUD / >24GB]`** y no son competitivos aquí al entrenarse desde 1 sola cámara monocular handheld sobre fuego dinámico).*

### Paso 2 Final Obligatorio · Compositing Óptico Lineal (`ACEScg` / `AgX`) + Gates Cuantitativos (`33f` ➔ `167f`)
1. Componer siempre en **espacio lineal (`16F/32F`)**: `Plate (De-grain) → Relight por material → Fuego Back → Sujeto Reiluminado → Fuego Front → Exponential Multi-Radius Glow → Red Halation → Heat Shimmer → ACES 2.0 / AgX Tone Map → Re-grain & MTF Match` ([Doc 06 §5.3](../docs/06-blender-3d-vfx-compositing.md#53-orden-estricto-del-compositing-óptico-lineal-acescg--linear-rec709)).
2. **Protocolo de Gates R&D (Primero sobre recorte crítico de `33 frames` antes de escalar a `167f`):** ejecuta [`scripts/vfx_rd_metrics_eval.py`](../scripts/vfx_rd_metrics_eval.py) para validar:
   - **Gate 0:** `‖N‖ ∈ [0.99, 1.01]` y `fringe_delta_l < 0.03` en tela negra.
   - **Gate 1:** ganancia en puño negro `<= 1.15×`, contraste SSDO `>= 3.5:1` y neutralidad en escritorio blanco **`CIEDE2000 <= 1.5`**.
   - **Gate 2:** pico HDR de fuego lineal `>= 4.0` pre-tonemap (sin clipping amarillo pastel) y diferencia de ruido HF/MTF dentro de **`±12 %`** respecto al plate original (seguido de Foley opcional con `MMAudio`).
