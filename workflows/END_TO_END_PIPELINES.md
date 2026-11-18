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

## Workflow 3 · Automatización Total de Video Híbrido (Premiere / EffectCraft / TouchDesigner)

### Para YouTube / Talking-Head / Documental Técnico
1. **Corte automático de silencios y retakes:** **`Open Cut Agent`** (en vivo en Premiere) o **`auto-editor`** CLI exportando XML.
2. **Gráficos animados vectoriales/datos por código:** Agente IA genera componentes en **Remotion** o proyectos JSON **`.ecproj` en EffectCraft** (`effectcraft-cli mcp`) exportando a `.lottie` / ProRes 4444 alpha.
3. **Avatares / Traducción Lip-Sync:** **`InfiniteTalk`** o **`EchoMimic v3` (1.3B)** cuando necesites tomas parlantes sincronizadas con un audio nuevo.

### Para Visuales Generativos / Escenario / Instalaciones en Vivo
1. **Esqueleto de nodos IA:** **`TouchDesigner/TDMCP`** (oficial, soporte directo Antigravity en `http://127.0.0.1:13316/mcp`) o **`Embody / Envoy`** (con TDXN YAML versionado en Git).
2. **Tracking, Normales en Vivo & Física GPU:** **MediaPipe TD** + **`DAViDNormals.tox`** (~10 ms GPU en `td-native-inference` ➔ `Relight.tox`) o **`Render TOP` MRT + `td_mrt_normal_pass.frag`** alimentando **POPs** en GPU.
3. **Difusión en vivo / puente:** **StreamDiffusionTD** (Turbo/LCM en 3060 guiado por Z-Depth o `BlenderNormals` vía **Spout2**) y grabación master ProRes / EXR 16F ([ver Pilar 08](../docs/08-normal-passes-realtime-post.md)).
