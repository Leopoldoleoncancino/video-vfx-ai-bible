# 10 · Color (OCIO / ACES 2.0 / AgX), Audio IA, Face VFX & OBS Studio

> **Calibración:** NVIDIA **RTX 3060 · 12 GB VRAM** · **Ryzen 9 5900X** *(12C / 24T)* · **32 GB RAM** · **Windows 11**  
> **Brecha que cierra este pilar:** Un plano con gran rotoscopia o 3D falla al instante si mezcla **sRGB 8-bit quemado contra 32-bit lineal**, tiene **audio plano sin Foley ni subtítulos exactos**, sufre **flicker en rostro** o no captura bien desde/hacia **OBS Studio**. Aquí tienes las cuatro piezas transversales de acabado profesional en local.

---

## 1. Gestión de Color Unificada: `OpenColorIO`, `ACES 2.0` & `AgX`

Cuando combinas clips IA de **ComfyUI** (`sRGB` 8-bit), renders de **Blender**, visuales en **TouchDesigner**, pasadas **Normal EXR** (`Raw/Non-Color`) y timeline en **DaVinci Resolve / After Effects**, trabajar sin **OpenColorIO (`OCIO`)** provoca pieles radioactivas, neones recortados (*clipping*) y halos al mezclar alphas.

| Herramienta / Entorno | Repositorio / Soporte | Regla de Oro en Pipeline Híbrido 3060 |
|---|---|---|
| **`OpenColorIO` & `colour-science`** | [`AcademySoftwareFoundation/OpenColorIO`](https://github.com/AcademySoftwareFoundation/OpenColorIO) (★2,143 · BSD-3-Clause) · [`colour-science/colour`](https://github.com/colour-science/colour) (★2,697 · BSD-3-Clause) | Estándar industrial para configuraciones `.ocio` compartidas (`ACES 2.0` / `AgX`). Usa siempre espacios **lineales** para iluminación, normales y desenfoque (*motion blur / glow*). |
| **Blender 4.0 – 5.x+** | Nativo en *Render Properties → Color Management* | **AgX** es estándar desde Blender 4.0 y **Blender 5.0+ añade `ACES 2.0`** integrado de serie. ⚠️ Marca explícitamente mapas **Z-Depth, Roughness y Normal Passes** como **`Non-Color` / `Raw`** para no alterar sus vectores. |
| **TouchDesigner (2025+)** | **`OpenColorIO TOP`** nativo | Todos los TOPs de TD operan internamente en espacio **lineal** salvo configuración inversa; al meter video sRGB 8-bit o renders IA, pasa por `OpenColorIO TOP` (`sRGB - Texture ➔ Linear / ACEScg`) antes de componer glows/relighting, y convierte de regreso al final para monitor/Spout/OBS. |
| **DaVinci Resolve Studio** | Project Settings → `ACEScct` / **`ACES 2.0`** (`RGBA 32-bit float`) | En **Fusion Page**, verifica que cada secuencia EXR de `NormalCrafter`, `Lotus-2` o Blender entre en **Bypass / Raw** sin LUT aplicado, y aplica el View Transform (`ACES 2.0` / `Rec.709`) únicamente al final del flujo hacia salida. |
| **ComfyUI / VFX Scripts** | [`FXTD-Studios/radiance`](https://github.com/FXTD-Studios/radiance) (`RadianceACES2OutputTransformFull` / `RadianceEXRMultiPart`), [`BISAM20/ComfyUI-ACES-IO`](https://github.com/BISAM20/ComfyUI-ACES-IO) (`ACESIOConfig` / `ACESIOEXRSaver`), [`oumad/ComfyUI_Gear`](https://github.com/oumad/ComfyUI_Gear) y [`Code2Collapse/ComfyUI-CustomNodePacks`](https://github.com/Code2Collapse/ComfyUI-CustomNodePacks) (`VideoComparerC2C` / `FrequencySeparateMEC`) | Exporta pases técnicos (`Depth`, `Normal`, `Matte`) en **EXR 16F/32F lineal** fuera de sRGB. ⚠️ En `FrequencyCombineMEC`, el resultado se recorta a `[0, 1]` SDR: calcula la multiplicación/glow HDR `>1.0` en lineal ([Módulo A](modules/MODULE_A_COMFYUI_VFX_3060.md) · [`vfx_ssdo_relight_16f.py`](../scripts/vfx_ssdo_relight_16f.py)) antes de aplicar el View Transform `ACES 2.0` / `AgX`. |

---

## 2. Audio IA Local, Foley Sincronizado, Stems & Subtítulos (0–8 GB VRAM)

Un video VFX sin sonido físico ni diálogos limpios pierde la mitad de su realismo. Casi toda esta suite corre **simultáneamente o en segundos** aprovechando los **24 hilos del Ryzen 9 5900X** o consumiendo `<8 GB` de la RTX 3060:

### A. Foley & Video-to-Audio Sincronizado
- **[`hkchengrex/MMAudio`](https://github.com/hkchengrex/MMAudio)** (★2,323 · código MIT / pesos `CC-BY-NC-4.0`) `[OK-12GB]`
  - **Qué hace:** Genera efectos de sonido (**Foley** realistas: pasos, vidrios, motor, viento, impactos) **sincronizados frame a frame con la acción del video** mediante `Synchformer` (25 FPS) + `CLIP` (8 FPS) + texto opcional.
  - **Consumo real:** El modelo por defecto **`large_44k_v2`** consume únicamente **~6 GB VRAM en modo 16-bit (`fp16`)**, corriendo rápido y holgado en la **RTX 3060 12 GB**. *(Nota licencia: pesos bajo `CC-BY-NC-4.0`, revisar en proyectos comerciales de clientes).*

### B. Transcripción Exacta a Nivel de Palabra & Diarización
- **[`SYSTRAN/faster-whisper`](https://github.com/SYSTRAN/faster-whisper)** (★26,854 · MIT) + **[`m-bain/whisperX`](https://github.com/m-bain/whisperX)** (★25,463 · BSD-2-Clause) `[OK-12GB]`
  - **Qué hace:** Whisper clásico tiene marcas de tiempo imprecisas por frase; **WhisperX** combina VAD + backend `faster-whisper` (`<8 GB VRAM` en `large-v2/v3`) + **alineamiento forzado por fonemas (`wav2vec2`)** + diarización de hablantes (`--diarize`).
  - **Uso estrella con JS / Remotion / Premiere:** Ejecuta `whisperx audio.wav --model large-v2 --highlight_words True` para exportar JSON/SRT **palabra por palabra** con precisión de milisegundos, perfecto para generar subtítulos animados estilo *karaoke* directo en **Remotion / After Effects**.

### C. Separación de Stems & Limpieza de Ruido / Eco
| Herramienta | Repo & Licencia | Hardware / Notas | Uso Principal |
|---|---|---|---|
| **Python Audio Separator** | [`nomadkaraoke/python-audio-separator`](https://github.com/nomadkaraoke/python-audio-separator) (★1,499 · MIT) | GPU CUDA (~2–4 GB) o CPU | Envoltorio CLI/Python unificado para **UVR / MDX-Net / RoFormer / Demucs**: separa voz, batería, bajo, música, eco y reverb con calidad de estudio. |
| **Demucs** | [`facebookresearch/demucs`](https://github.com/facebookresearch/demucs) (★10,416 · MIT) | GPU ~2–3 GB o CPU | Separación rápida en 4/6 stems (`htdemucs`) para aislar diálogos o extraer pista musical limpia antes de `auto-editor` / montajes. |
| **ClearerVoice-Studio** | [`modelscope/ClearerVoice-Studio`](https://github.com/modelscope/ClearerVoice-Studio) (★4,630 · Apache-2.0) | GPU ligero / CPU | Suite open-source para **mejora de habla, eliminación de ruido complejo, dereverberación y separación de voces**. |
| **DeepFilterNet (`DeepFilterNet3`)** | [`Rikorose/DeepFilterNet`](https://github.com/Rikorose/DeepFilterNet) (★5,048 · MIT/Apache) | **CPU 5900X en tiempo real** | Supresión de ruido y ruido de sala ultrarrápida a 48 kHz sin gastar nada de VRAM de la RTX 3060 (ideal en batch CLI o plugins LADSPA/PipeWire/OBS). |

### D. Voces Locales & Clonación Emocional (TTS)
- **[`resemble-ai/chatterbox`](https://github.com/resemble-ai/chatterbox)** (★27,910 · MIT) `[OK-12GB]` — TTS open-source líder con **control de expresividad/emoción** y clonación *zero-shot* desde pocos segundos de audio limpio.
- **[`SWivid/F5-TTS`](https://github.com/SWivid/F5-TTS)** (★15,618 · MIT) `[OK-12GB]` — Basado en *Flow Matching*, rápido en RTX 3060 (<6 GB VRAM) con soporte sólido de clonación multilingüe incluyendo español.
- **[`hexgrad/kokoro`](https://github.com/hexgrad/kokoro)** (★10,227 · Apache-2.0) `[OK-12GB · Ultra-ligero]` — **Solo 82M de parámetros**; corre a velocidad récord tanto en la RTX 3060 como en CPU para locuciones borrador, bots o prototipado rápido en **Remotion / ArtCraft**.

---

## 3. Face VFX, Re-enactment de Retratos & Restauración Facial

> ⚠️ **Advertencia técnica de calidad:** Los swaps cuadro-por-cuadro clásicos (`inswapper_128`) suelen delatar baja resolución y parpadeo temporal si no se restauran ni estabilizan. Úsalos siempre con los límites claros de abajo.

1. **[`KlingAIResearch/LivePortrait`](https://github.com/KlingAIResearch/LivePortrait)** (★19,529 · antes `KwaiVGI`) `[OK-12GB]`
   - **Para qué brilla en VFX:** No es solo para animar fotos: en postproducción real sirve para **corregir mirada desviada a cámara (`Retargeting Eye Gaze`), arreglar parpadeos incómodos, ajustar sonrisa/gestos o transferir actuación facial exacta** en planos reales conservando iluminación original (~4–8 GB VRAM, incluye instalador Windows).
2. **[`Gourieff/ComfyUI-ReActor`](https://github.com/Gourieff/ComfyUI-ReActor)** (★1,409 · GPL-3.0) + **[`sczhou/CodeFormer`](https://github.com/sczhou/CodeFormer)** (★18,253) `[OK-12GB]`
   - **Limitaciones honestas:** El modelo base `inswapper_128.onnx` genera solo `128×128 px`, por lo que requiere restauración obligatoria con **`CodeFormer`** (peso fidelidad `0.7–0.8` para no plastificar piel) o **`GPEN-BFR-512`**. En videos largos el tiempo promedio ronda `1–2 s/frame` y puede aparecer *flicker* en giros pronunciados de perfil (>45°). Para planos parlantes generados desde cero con lip-sync limpio, prefiere **`InfiniteTalk`** o **`EchoMimic v3`** ([Pilar 01](01-local-ai-video-12gb-32gb.md)).

---

## 4. OBS Studio como Puente Grabador/Transmisor GPU (`Spout2`) + Control por Agente (`OBS MCP`)

Cuando trabajas con **TouchDesigner**, **StreamDiffusionTD**, **Blender EEVEE en vivo** o **Web Render TOP**, **OBS Studio** deja de ser "solo streaming" y se convierte en tu **grabador NVENC en tiempo real sin cuello de botella CPU** y conmutador de escenas controlable por IA:

- **[`obsproject/obs-studio`](https://github.com/obsproject/obs-studio)** (★79,700 · GPL-2.0) + **[`Off-World-Live/obs-spout2-plugin`](https://github.com/Off-World-Live/obs-spout2-plugin)** (★1,124 · GPL-2.0) `[OK-12GB]`
  - **Por qué `obs-spout2-plugin` supera a `SpoutCam` y captura de ventana:** Permite **importar y exportar texturas Direct3D 11 compartidas en memoria GPU sin pasar por CPU**, sin el límite `1920×1080` de `SpoutCam`, soportando **4K / canal Alfa / filtros por escena (`Spout Output Settings`)**.
  - **Bidireccional real:**
    - *TD / Blender ➔ OBS:* Captura visuales generativos 60 FPS en OBS usando **`Spout2 Capture`**, grabando a disco con hardware **NVENC (RTX 3060)** sin robar núcleos de IA.
    - *OBS ➔ TouchDesigner:* Envía la escena mezclada de OBS como textura Spout de vuelta a TouchDesigner para aplicar shaders o difusión en vivo.
- **Servidores MCP para OBS Studio (`WebSocket v5` puerto `4455`):**
  1. **[`royshil/obs-mcp`](https://github.com/royshil/obs-mcp)** (★167 · GPL-2.0): Servidor Node rápido (`npx -y obs-mcp@latest`). Activa en OBS *Herramientas → Ajustes del servidor WebSocket → Habilitar servidor WebSocket* (`4455`) y define `OBS_WEBSOCKET_PASSWORD` en tu config MCP ([ver `mcps/win11_unified_mcp_config.json`](../mcps/win11_unified_mcp_config.json)).
  2. **[`xDarkzx/OBS_MCP`](https://github.com/xDarkzx/OBS_MCP)** (★29 · Apache-2.0): Implementación extendida en Python (`148 herramientas` cubriendo filtros, transiciones, mezclador de audio, escenas y perfiles de grabación/replay buffer).

---

## 5. Checklist de Decisión Rápida

- *"Los neones o reflejos de mi render/IA se queman feo al unirlos en Premiere o Resolve"* ➔ Trabaja lineal con **OCIO (`ACES 2.0` o `AgX`)**, mantén tus Normal/Depth passes en **`Non-Color / Raw`** EXR 16F, y usa `OpenColorIO TOP` al entrar a TouchDesigner.
- *"Necesito efectos de sonido perfectamente sincronizados al frame para mi clip hecho con Wan/LTX"* ➔ **`hkchengrex/MMAudio`** (`large_44k_v2`, ~6 GB VRAM fp16).
- *"Quiero subtítulos palabra por palabra y limpiar el eco de mi micrófono sin tocar la GPU"* ➔ **`DeepFilterNet`** (CPU 5900X) ➔ **`whisperX --highlight_words True`** ➔ JSON hacia **Remotion / AE**.
- *"Necesito grabar mi canvas 60 FPS de TouchDesigner sin pérdidas y controlando escenas con el agente IA"* ➔ **`obs-spout2-plugin`** (Direct3D 11 GPU zero-copy) + **`royshil/obs-mcp`** en puerto `4455`.
