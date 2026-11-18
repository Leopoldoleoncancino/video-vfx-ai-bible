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
   │       + Relit-LiVE (video completo) o Fusion Relight [puerto Normals] / AE Normality (32-bpc)
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

## Workflow 4 · Fuego / Energía Hiperrealista Adherido a Anatomía con Capa de Normales (6 Rutas Comparadas — Sin Ganador Prematuro)

Marco de referencia R&D para efectos emisivos sobre manos/cuerpo en rotación donde la luz, las sombras interdigitales y el bloqueo sobre ropa oscura deben respetar geometría real sin caer en el antipatrón de *"brillo radial 2D sangrando sobre tela"*.

### Paso 0 Común · "Geometry, Matte Dual & Tracking Bus" (Siempre 16-bit Float / EXR)
> **Regla crítica:** Nunca exportes máscaras, mapas de profundidad ni normales en MP4 8-bit `yuv420p` (genera *stair-stepping* especular y bloques); usa **OpenEXR 16F/32F lineal** (`Camera Space`, **OpenGL `+Y` arriba**, ver [Pilar 08](../docs/08-normal-passes-realtime-post.md)) o `ProRes 4444` Straight Alpha para mattes.

1. **Matte Dual por Material `[OK-12GB]`:** `SAM 2.1 / SAM 3` (prompts separados: piel vs ropa/manga) ➔ `MatAnyone 2` o `VideoMaMa` (preservando *motion blur* e hilos sueltos, [Doc 02 §3.1](../docs/02-rotoscoping-matting-chroma-depth.md#31-matting-dual-por-material-regla-anti-sangrado-de-glowrelight-ok-12gb)).
2. **Depth Temporal `[OK-12GB]`:** `Video Depth Anything` (Small/Base) o `DAViDHuman.tox`.
3. **Capa de Normales (según necesidad):** `DAViDNormals.tox` (~10 ms GPU en vivo), `NormalCrafter --max-res 512` (~6 GB VRAM, coherencia temporal de video), `Lotus / Lotus-2` (`flux_empty_embed.pt`) o malla 3D `WiLoR / Dyn-HaMR`.
4. **Tracking `[OK-12GB]`:** `CoTracker3` / `AllTracker` o `MediaPipe` + orientación de palma/dorso.

### Paso 1 · Comparativa Neutral de las 6 Rutas (Perfil 3060 12 GB / 32 GB RAM)

| Ruta | Tag Hardware | Stack Principal | Cómo Resuelve Oclusión + Relighting | Trade-off Clave |
|---|---|---|---|---|
| **Ruta A · ComfyUI Híbrido** | `[TIGHT-12GB]` | `Wan 2.1/2.2 VACE` o `ATI` (`CoTracker3`) + `UniLumos` / `Light-A-Video` + `SeedVR2 3B` | Trayectorias + máscara en VACE; relighting aplicado vía **Frequency Separation (`Light Ratio`)** ([Doc 01 §5](../docs/01-local-ai-video-12gb-32gb.md#5-control-geométrico-avanzado-trayectorias-cotracker3ati-y-relighting-en-comfyui-12-gb-vram)) para preservar poros/hilos. | Exige ejecución por fases (`CleanVRAMUsed`) y cerrar Premiere/Blender por el techo de 32 GB RAM. |
| **Ruta B · Relighting Analítico PBR** | `[OK-12GB]` | Shader GLSL / Python Float32 con Normales `16F` + `Depth` | Multi-emisor (5–6 luces en yemas/palma), BRDF por matte (`roughness` piel `0.34` vs tela `0.88`), SSS de borde + **Screen-Space Depth Raymarch Shadows (`SSDO`)** ([Doc 02 §3.3](../docs/02-rotoscoping-matting-chroma-depth.md#33-por-qué-nl-solo-no-basta-sombras-raymarched-en-depth-ssdo--ggx--sss)). | Ultra rápido y 100% determinista; la calidad del sombreado depende directo de la limpieza de Normales y Depth. |
| **Ruta C · 3D Físico Puro (Blender)** | `[OK-12GB]` / `[TIGHT-12GB]` | `WiLoR` / `Dyn-HaMR` (MANO `.abc`) + Blender 4.5 `Mantaflow` / `OpenVDB` + Cycles | Malla MANO con `Holdout` da oclusión dedo-a-dedo exacta; **Multi-Layer OpenEXR** (`VL_Fire_Occluded`, `VL_Hand_Lit / VL_Hand_Ambient` *Light Ratio*, `Normal`, `Vector`, [Doc 06 §5](../docs/06-blender-3d-vfx-compositing.md#5-simulación-física-de-fuego-openexr-multi-layer--compositing-lineal-acescg--agx)). | Máxima precisión física y sombras reales; exige bake en Ryzen 9 5900X + render Cycles OptiX. |
| **Ruta D · Real-Time 60 FPS (TD)** | `[OK-12GB]` | TouchDesigner `POPs` + `DAViDNormals.tox` + `Fluid TOP` + GLSL | Fluido advectado por MediaPipe + deflexión por normales + `POPs` chispas GPU + shader 6 luces + `SSDO` en `32-bit Float TOP` ([Doc 05 §5](../docs/05-touchdesigner-realtime.md#5-relighting-pbr-multi-luz-ssdo--fuego-gpu-en-vivo-a-60-fps-ok-12gb)). | Interactivo a 60 FPS sin esperas de render; menor detalle micro-turbulento que Cycles/placas reales salvo que se pase por difusión/upscale. |
| **Ruta E · Stock Fuego 4K + Tracking** | `[OK-12GB]` | Placas reales de fuego sobre negro + `CoTracker3` / `AllTracker` + `Practical-RIFE` | Deformación no-rígida anclada a puntos de dedos, retiming `RIFE` ([Doc 07 §4.1](../docs/07-opensource-nles-cli-upscaling.md#41-orden-óptico-en-vfx-híbrido-stock-4k--practical-rife--seedvr2--re-grain-ok-12gb)), oclusión 3D y relighting por normales. | Cero alucinaciones IA y combustión 100% real con bajo uso de VRAM; limitado a los ángulos del stock elegido. |
| **Ruta F · Inverse Rendering + Diffusion** | `[TIGHT-12GB]` / `[CLOUD / >24GB]` | `DiffusionRenderer` (`comfyui-materia`) o `RGB-X` + `Wan VACE` Residual | Descompone `Albedo + Normal + Roughness + Irradiance` para relight PBR o extrae solo el residuo en `VACE` (**Difference-Keyed Residual Blending**). | Captura reflejos complejos en objetos del fondo (escritorio/vidrio/impresora); modelos pesados exigen chunks cortos y tiling en 12 GB. |

### Paso 2 Final Obligatorio · Compositing Óptico Lineal (`ACEScg` / `AgX`) + Protocolo de Benchmark R&D
1. Componer siempre en **espacio lineal (`16F/32F`)**: `Plate (De-grain) → Relight por material → Fuego Back → Sujeto Reiluminado → Fuego Front → Exponential Multi-Radius Glow → Red Halation → Heat Shimmer → ACES/AgX Tone Map → Re-grain & MTF Match` ([Doc 06 §5.3](../docs/06-blender-3d-vfx-compositing.md#53-orden-estricto-del-compositing-óptico-lineal-acescg--linear-rec709)).
2. **Protocolo de Benchmark R&D (Para comparar rutas empíricamente sin sesgos):**
   - Medir **VRAM pico (`<= 11.2 GB`)**, **RAM libre en Windows 11**, **tiempo/frame (`s/f`)**.
   - Auditar 4 criterios físicos en frames clave (`f00`, `mid`, `peak`, `end`): **(1)** cero sangrado difuso en ropa oscura opaca, **(2)** sombreado cilíndrico con oclusión entre dedos + especular selectivo en piel, **(3)** ausencia de clipping amarillo pastel en altas luces, y **(4)** coherencia temporal sin *boiling* en normales ni desfase MTF/grano frente al plate original.
