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

Marco de referencia R&D para efectos emisivos sobre manos/cuerpo en rotación (`f88..f120`, giro `180°` palma→dorso) donde la inercia del fluido, la oclusión continua entre dedos, la luz acoplada a la llama y el bloqueo sobre ropa oscura deben respetar física real.  
👉 **Manual profundo Fase 2.5, resultados empíricos `33f`, troubleshooting Win 11 y ecuaciones:** [`docs/modules/MODULE_A_COMFYUI_VFX_3060.md`](../docs/modules/MODULE_A_COMFYUI_VFX_3060.md) y templates API en [`workflows/comfyui/`](comfyui/README.md).

### Paso 0 Común · "Geometry, Matte Dual & Tracking Bus" (Validado en Hardware Real: `~60 s` para `33f`, `~4.75 GB` pesos totales)
> **Regla crítica:** Nunca exportes máscaras, mapas de profundidad ni normales en MP4 8-bit `yuv420p`; usa **OpenEXR 16F/32F lineal** (`Camera Space`, **OpenGL `+Y` arriba**, ver [Pilar 08](../docs/08-normal-passes-realtime-post.md)) o `.npy` `float32`. Template ComfyUI: [`mod_a_01_step0_dual_matte_normal_exr.json`](comfyui/mod_a_01_step0_dual_matte_normal_exr.json).

1. **Matte Dual + Descontaminación `[OK-12GB]` (PASS Gate 0):** `SAM 2.1 / SAM 3` ➔ `MatAnyone 2` (`max_mem_frames=5`) ➔ [`scripts/vfx_dual_matte_decontam.py`](../scripts/vfx_dual_matte_decontam.py). En `job_33f` logró solapamiento piel/tela de **`0.015 %`** y reducción de halo blanco en hilos negros deshilachados del **`85.4 %`** (`0.154 → 0.0225` sRGB / `0.0113` lineal `16F`).
2. **Depth Temporal & Oclusión Z Continua `[OK-12GB]`:** `DepthAnything V2 ViT-L` + `DA3-Streaming` alimentando la visibilidad sigmoidal continua Front/Back (`compose_continuous_z_fire` en [`scripts/vfx_incompressible_fire_sim.py`](../scripts/vfx_incompressible_fire_sim.py), sin switch binario palma/dorso).
3. **Capa de Normales Estabilizada `[OK-12GB]`:** `VizClickNormalCrafter` (`--max-res 512`) + `VizClickNormalTemporalStabilizer` (`‖N‖ ∈ [0.9996, 1.0004]`, estabilidad temporal en fondo **`0.533°/frame`**). ⚠️ En SSDO en espacio de pantalla (`+Y` abajo), usar siempre **`invert_normal_y=True`** (activo por defecto en [`vfx_ssdo_relight_16f.py`](../scripts/vfx_ssdo_relight_16f.py)).
4. **Compensación de Cámara en Mano `[OK-12GB]`:** `RANSAC Homography` / Lucas-Kanade sobre fondo estático (`estimate_camera_motion_bg`) para aislar `v_hand_world = v_hand_screen - v_cam` antes de advectar el fluido.

### Paso 1 · Comparativa Neutral de las 7 Rutas (Perfil 3060 12 GB `sm_86` / 32 GB RAM Win 11)

| Ruta | Tag Hardware | Stack Principal | Cómo Resuelve Física de Fuego + Oclusión + Relighting | Trade-off Clave |
|---|---|---|---|---|
| **Ruta A · ComfyUI Híbrido** | `[TIGHT-12GB]` | `Wan2.2-VACE-Fun-A14B` (`Q3_K_M`/`Q4_K_S` + `BlockSwap`) + `CoTracker3` + `UniLumos 1.3B` + `SeedVR2 3B` | Trayectorias + normales/máscara en VACE (`mod_a_03`); relighting vía **Frequency Separation (`low_frequency`)** (`mod_a_02`). | Sin `fp8_fast`/`torch.compile` en `sm_86`; requiere `VRAM_Debug (unload_all_models=true)` y Pagefile ≥32 GB. |
| **Ruta B · Fluido GPU Incompresible + Relight PBR** | `[OK-12GB]` | [`scripts/vfx_incompressible_fire_sim.py`](../scripts/vfx_incompressible_fire_sim.py) + [`scripts/vfx_ssdo_relight_16f.py`](../scripts/vfx_ssdo_relight_16f.py) | **Navier-Stokes Incompresible** (`Red-Black SOR` $\nabla^2 p = \nabla \cdot \mathbf{v}$) + `BFECC clamped` + Fase *Curl* advectada + chispas + **Oclusión Z continua** + **MIP Area-Light SSDO** (`5.48:1`, máx `36.07:1`) + Motion Blur `180°`. | Ultra rápido (`< 1 GB VRAM`, `< 1 min` para `167f` tras Paso 0), `CIEDE2000 = 0.000` en escritorio blanco y **PASS Gate 3** (`corr >= 0.45`). |
| **Ruta C · 3D Físico Puro (Blender / EmberGen)** | `[OK-12GB]` / `[TIGHT-12GB]` | **`WiLoR-mini` MANO Estanco** ([`wilor_mano_to_blender_abc.py`](../scripts/wilor_mano_to_blender_abc.py)) + `Mantaflow Adaptive 224` / `EmberGen` + Cycles | **Malla MANO con muñeca cerrada (`watertight`)** (`velocity_factor=1.25`, `surface_distance=0.012`) + shader **Lámina Fina Blackbody (`Density=0.02`)** + `Proxy_Black_Cuff` colisionador/Holdout. | **Prohibido emitir desde esferas en landmarks** (flota y genera nubes rojas); usar malla estanca + `.abc` `MeshSequenceCache`. |
| **Ruta D · Real-Time 60 FPS (TD)** | `[OK-12GB]` | TouchDesigner `POPs` + `DAViDNormals.tox` + `Fluid TOP` + GLSL | Fluido advectado por MediaPipe + deflexión por normales + `POPs` chispas GPU + shader 6 luces + `SSDO` en `32-bit Float TOP` ([Doc 05 §5](../docs/05-touchdesigner-realtime.md#5-relighting-pbr-multi-luz-ssdo--fuego-gpu-en-vivo-a-60-fps-ok-12gb)). | Interactivo a 60 FPS sin esperas de render; menor micro-turbulencia que Cycles o `Ruta B/G`. |
| **Ruta E · Stock Fuego 4K + Tracking** | `[OK-12GB]` | Placas reales de fuego sobre negro + `CoTracker3` / `AllTracker` + `Practical-RIFE` | Deformación no-rígida anclada a dedos, retiming `RIFE` ([Doc 07 §4.1](../docs/07-opensource-nles-cli-upscaling.md#41-orden-óptico-en-vfx-híbrido-stock-4k--practical-rife--seedvr2--re-grain-ok-12gb)), capas Z continuas Front/Back y relight PBR. | Cero alucinaciones IA y combustión 100 % real; combinar siempre con oclusión Z continua en giros de `180°`. |
| **Ruta F · Inverse Rendering + Residuo** | `[CLOUD / >24GB]` / `[TIGHT-12GB]` | `DiffusionRenderer` / `comfyui-materia` / `UniVidX` *(Cloud/≥24GB)* vs `ComfyUI-rgbx` / `IntrinsicAnything` *(solo keyframes)* | Descompone `Albedo + Normal + Roughness + Irradiance` para calibrar materiales o extraer residuo en VACE. | Video largo excede 12 GB VRAM / 32 GB RAM Win 11; útil solo en keyframes de calibración o nube. |
| **Ruta G · Híbrida SOTA R&D *(7ª Vía Recomendada)*** | `[OK-12GB]` | `Paso 0 Bus` (`~60s/33f`) + **Fuego Incompresible (`Ruta B` / `Ruta C` MANO Estanco)** + **Relight PBR acoplado a MIP Area-Light** + **Oclusión Z Continua** + **Stephen Hill ACES / OCIO AgX Punchy** + `MMAudio` | Erradica las 5 fallas de `v10` y supera los **4 Gates (`Gate 0..3`)**: lenguas sedosas con estela de *Karman* real, sombras interdigitales `5.48:1`, puño negro `1.004×`, escritorio blanco `CIEDE2000 = 0.000` y espectro hidrocarburo sin lavado salmón. | Corre 100 % local en `< 6 GB VRAM` secuenciales (`~5–8 min` para `167f` en modo GPU Solver). |

### Paso 2 Final Obligatorio · Tone Mapping sin Lavado Salmón (`ACES Hill` / `OCIO AgX Punchy`) + 4 Gates Cuantitativos (`33f` ➔ `167f`)
1. **Colorimetría HDR verificada:** No uses la aproximación `m_inset` simple sobre fuego HDR (`peak 8–14`), ya que inyecta Rojo en Azul y lava las llamas hacia salmón/blanco tiza. Usa **`aces_hill_filmic_tonemap` (Stephen Hill RRT+ODT)** o **`ocio_agx_tonemap` (`PyOpenColorIO` `Look: AgX - Punchy`)** junto con **`compose_hdr_on_plate_srgb`** (inversa analítica ACES sobre el plate) en [`scripts/vfx_ssdo_relight_16f.py`](../scripts/vfx_ssdo_relight_16f.py).
2. **Protocolo de 4 Gates R&D (Primero sobre `job_33f` antes de escalar a `167f`):** ejecuta [`scripts/vfx_incompressible_fire_sim.py`](../scripts/vfx_incompressible_fire_sim.py) y [`scripts/vfx_rd_metrics_eval.py`](../scripts/vfx_rd_metrics_eval.py) para validar:
   - **Gate 0:** `‖N‖ ∈ [0.99, 1.01]` y `fringe_delta_l < 0.03` en tela negra.
   - **Gate 1:** ganancia en puño negro `<= 1.15×`, contraste SSDO `>= 3.5:1` y escritorio blanco **`CIEDE2000 <= 1.5`**.
   - **Gate 2:** pico HDR `>= 4.0`, **`pastel_yellow_clip_pct <= 1.0 %`**, **`salmon_wash_pct <= 2.0 %`** y ruido HF/MTF dentro de **`±12 %`**.
   - **Gate 3 (Acoplamiento Movimiento↔Fuego):** **`lag_correlation >= 0.45`** y **`mean_wake_deflection_px >= 1.2 px`** entre $\mathbf{v}_{\text{hand, world}}$ y la estela de la pluma superior.
