# 11 · Usos Prácticos: TouchDesigner Visual, Distorsiones Analógicas, Webcam, Instalaciones & Workflows Reales

> **Hardware Calibrado:** NVIDIA **RTX 3060 12 GB VRAM** *(Ampere `sm_86`)* · AMD **Ryzen 9 5900X** · **32 GB RAM** · **Windows 11**  
> **Versión Base TD:** TouchDesigner **2025.31550+ / 2025.33230+** (POPs GPU, `Web Render TOP` Chromium 132.0, `cuda-link`, `TDMCP`).  
> **Propósito:** Recetas reproducibles paso a paso —desde espejos analógicos CRT/VHS y *datamosh* en webcam hasta relighting PBR `SSDO`, instalaciones multicámara, puente zero-copy `cuda-link` y checklist anti-nodos-rojos de ComfyUI.

---

## Mapa Rápido de las 8 Recetas

| # | Receta | Clasificación Hardware | VRAM Estimada | Uso Principal |
|---|---|---|---|---|
| **1** | Espejo Analógico CRT / VHS + Sangrado NTSC (`GLSL TOP` 16F) | `[OK-12GB]` | ~0.3–0.6 GB | Estética analógica 60 FPS en webcam / video |
| **2** | Feedback Líquido + Optical Flow + Datamosh en Webcam | `[OK-12GB]` | ~0.5–1.0 GB | Estelas líquidas y *datamosh* interactivo |
| **3** | Ecos Temporales al BPM + Slit-Scan con Oclusión Real | `[OK-12GB]` | ~1.5–2.5 GB | Visuales musicales sincronizados sin perder beats |
| **4** | Silueta de Partículas `POPs` + Raymarching GLSL (`MediaPipe`) | `[OK-12GB]` | ~1.5–2.5 GB | Control gestual *pinch* con webcam sin hardware |
| **5** | Relighting PBR en Vivo (`DAViD Normals` + `OCIO` + `SSDO`) | `[OK-12GB]` | ~2.0–3.2 GB | Iluminación física audio-reactiva hacia OBS |
| **6** | Instalación Multicámara (`Orbbec / Kinect / OAK-D`) + `Web Render TOP` | `[OK-12GB]` | ~1.5–3.5 GB | Instalaciones interactivas + overlays JS 60 FPS |
| **7** | Puente Zero-Copy `TD ↔ Python IA` (`cuda-link` + `StreamDiffusionTD`) | `[OK-12GB]` | ~5.5–7.5 GB | Difusión GPU en vivo sin copia CPU |
| **8** | Workflows ComfyUI / E-Commerce / VFX & Checklist Anti-Nodos-Rojos | `[OK-12GB]` / `[TIGHT-12GB]` | ~6.0–11.5 GB | Producción ComfyUI estable en Win 11 `sm_86` |

---

## Receta 1 · Espejo Analógico CRT / VHS + Sangrado NTSC (`GLSL TOP` 16-bit Float) `[OK-12GB]`

Ideal para convertir cualquier webcam o entrada de video en un monitor CRT/VHS realista a **60 FPS** con consumo mínimo de VRAM.

### 1.1 Topología de Nodos en TouchDesigner
1. **`Video Device In TOP`** *(720p/1080p @ 30–60 FPS)* o **`Spout In TOP`** *(ver nota de webcam compartida abajo)*.
2. **`Resolution TOP`** *(opcional, `1280x720`, Pixel Format: **`16-bit Float (RGBA)`** para evitar banding en el sangrado de croma)*.
3. **`GLSL TOP`** *(Pixel Format: `16-bit Float (RGBA)`, Input 0 conectado)*.
   - En la pestaña **Vectors / Uniforms** del `GLSL TOP` declara:
     - `uTime` → `absTime.seconds`
     - `uCurvature` → `0.18` *(curvatura de tubo CRT)*
     - `uTrackingSpeed` → `0.35` *(velocidad de banda VHS)*
     - `uTrackingAmp` → `0.018` *(desgarro horizontal de tracking)*
     - `uChromaShift` → `3.5` *(desfase horizontal de croma NTSC en píxeles)*
     - `uScanlineStrength` → `0.28`
     - `uGrainAmount` → `0.06`
4. **`Null TOP`** (`out_crt_vhs`) para salida o monitoreo.

> 💡 **Nota Windows 11 — Webcam compartida (`Spout2` / OBS):**  
> Windows 11 bloquea el dispositivo UVC físico para una sola aplicación a la vez. Si quieres usar la misma webcam simultáneamente en TouchDesigner, OBS o Zoom/Discord:
> - **Opción A (Recomendada, 0 ms):** Captura la cámara en TouchDesigner (`Video Device In TOP`) y envíala por **`Spout Out TOP`** (`TD_Cam_Out`) hacia OBS usando **`obs-spout2-plugin`** (ver [Pilar 10](10-color-ocio-audio-face-obs.md)).
> - **Opción B:** Captura la cámara en OBS y envía `OBS_Spout` hacia TouchDesigner (`Spout In TOP`), o usa la *OBS Virtual Camera* si necesitas compatibilidad UVC estándar.

### 1.2 Código GLSL Completo para TouchDesigner (`GLSL TOP`)

```glsl
// TouchDesigner GLSL TOP — Espejo Analógico CRT / VHS + Sangrado NTSC (16-bit Float)
// Input 0: sTD2DInputs[0]
uniform float uTime;
uniform float uCurvature;        // ej. 0.18
uniform float uTrackingSpeed;    // ej. 0.35
uniform float uTrackingAmp;      // ej. 0.018
uniform float uChromaShift;      // ej. 3.5 (píxeles)
uniform float uScanlineStrength; // ej. 0.28
uniform float uGrainAmount;      // ej. 0.06

out vec4 fragColor;

float hash12(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

vec2 barrelDistort(vec2 uv, float k) {
    vec2 centered = uv * 2.0 - 1.0;
    float r2 = dot(centered, centered);
    centered *= 1.0 + k * r2 + (k * 0.5) * r2 * r2;
    return centered * 0.5 + 0.5;
}

vec3 rgb2yiq(vec3 c) {
    return vec3(
        dot(c, vec3(0.299,  0.587,  0.114)),
        dot(c, vec3(0.596, -0.274, -0.322)),
        dot(c, vec3(0.211, -0.523,  0.312))
    );
}

vec3 yiq2rgb(vec3 yiq) {
    return vec3(
        dot(yiq, vec3(1.0,  0.956,  0.621)),
        dot(yiq, vec3(1.0, -0.272, -0.647)),
        dot(yiq, vec3(1.0, -1.106,  1.703))
    );
}

void main() {
    vec2 res = uTD2DInfos[0].res.zw;      // (width, height)
    vec2 texel = uTD2DInfos[0].res.xy;    // (1/width, 1/height)

    // 1. Curvatura CRT
    vec2 uv = barrelDistort(vUV.st, uCurvature);

    // Máscara de borde de tubo CRT
    if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) {
        fragColor = TDOutputSwizzle(vec4(0.0, 0.0, 0.0, 1.0));
        return;
    }

    // 2. Banda de tracking VHS móvil + jitter horizontal por línea
    float bandPos = fract(uTime * uTrackingSpeed);
    float bandDist = abs(uv.y - bandPos);
    float trackingBand = smoothstep(0.09, 0.0, bandDist);
    float lineNoise = (hash12(vec2(floor(uv.y * res.y), floor(uTime * 24.0))) - 0.5) * 2.0;
    uv.x += trackingBand * lineNoise * uTrackingAmp;
    uv.x += (hash12(vec2(uv.y * 120.0, uTime)) - 0.5) * 0.0018;

    // 3. Sangrado NTSC (luma nítida, croma I/Q desenfocada y desfasada horizontalmente)
    vec3 colCenter = texture(sTD2DInputs[0], uv).rgb;
    float yLuma = rgb2yiq(colCenter).x;

    vec2 cOffset = vec2(uChromaShift * texel.x, 0.0);
    vec3 yiqLeft  = rgb2yiq(texture(sTD2DInputs[0], clamp(uv - cOffset, 0.001, 0.999)).rgb);
    vec3 yiqRight = rgb2yiq(texture(sTD2DInputs[0], clamp(uv + cOffset * 1.5, 0.001, 0.999)).rgb);
    float iChroma = mix(yiqLeft.y, yiqRight.y, 0.65);
    float qChroma = mix(yiqLeft.z, yiqRight.z, 0.35);

    vec3 col = yiq2rgb(vec3(yLuma, iChroma, qChroma));

    // Ruido blanco sutil dentro de la banda de tracking VHS
    float snow = hash12(uv * res + uTime * 60.0);
    col = mix(col, vec3(snow), trackingBand * 0.35);

    // 4. Scanlines CRT + subpixel grille ligero
    float scan = sin(uv.y * res.y * 3.14159265) * 0.5 + 0.5;
    col *= 1.0 - uScanlineStrength * (1.0 - scan);

    // 5. Grano analógico temporal + viñeta CRT
    float grain = (hash12(uv * res * 0.5 + fract(uTime * 17.3) * 100.0) - 0.5) * uGrainAmount;
    col += grain;

    vec2 vigUV = uv * (1.0 - uv.yx);
    float vig = pow(clamp(vigUV.x * vigUV.y * 16.0, 0.0, 1.0), 0.18);
    col *= vig;

    fragColor = TDOutputSwizzle(vec4(max(col, 0.0), 1.0));
}
```

### 1.3 Librerías Listas para Arrastrar (`.tox`)
- **[`kevinraymond/touchdesigner-effects`](https://github.com/kevinraymond/touchdesigner-effects):** Incluye componentes `.tox` listos de **`VHS + CRT`** y **`film_stock`** (halación + grano fílmico), ideales si prefieres nodos modulares listos sin escribir GLSL desde cero.
- **[`aaronmylespereira/TD-Toxes`](https://github.com/aaronmylespereira/TD-Toxes):** Incluye presets `.tox` de **`Datamosh`** y **`Circuit Bending`** para combinar degradación digital con tu espejo analógico.

---

## Receta 2 · Feedback Líquido + Optical Flow + Datamosh en Webcam `[OK-12GB]`

Convierte el movimiento de tu mano o cuerpo frente a la webcam en **estelas líquidas viscosas** o **Datamosh puro** congelando píxeles donde no hay movimiento.

### 2.1 Cadena Exacta de Nodos
1. **`Video Device In TOP`** (`1280x720`, 30/60 FPS) → **`Flip TOP`** *(Flip X = On para modo espejo natural)*.
2. **`Optical Flow TOP`** conectado al `Flip TOP`: calcula el campo de velocidad `(R = u, G = v)` en GPU.
3. **`Blur TOP`** *(Filter Size: `6–10`, Pixel Format: **`16-bit Float (RGBA)`**)*: suaviza los vectores de flujo para evitar bloques ruidosos.
4. **`Feedback TOP`** *(Pixel Format: **`16-bit Float (RGBA)`**)*:
   - Target TOP: apunta al **`Composite TOP`** final de la cadena de feedback.
   - Pulsa **Pulse** en *Reset* (o conecta un `Keyboard In CHOP` tecla `r` a *Reset Pulse*) para reiniciar el lienzo.
5. **`Displace TOP`**:
   - Input 0 (Source): `Feedback TOP`
   - Input 1 (Displace): `Blur TOP` (Optical Flow suavizado)
   - **Displace Weight:** **`0.018`** (tanto en X como en Y) · **UV Offset:** `0.5` *(si `Optical Flow` está centrado en `0`, ajusta `Displace` Source Midpoint a `0.0`)* · **Extend:** `Mirror` o `Clamp`.
6. **`Level TOP`**:
   - **Opacity:** **`0.965`** *(decaimiento exponencial suave de la estela; `0.985` para colas largas, `0.92` para respuesta rápida)*.
7. **`Composite TOP`**:
   - Input 0: `Level TOP` (estela desplazada)
   - Input 1: `Flip TOP` (video vivo)
   - **Operand:** `Over` / `Maximum` / `Screen` *(o mezcla con un `Key` / `DAViDHuman.tox` alpha)*.

### 2.2 Truco Datamosh Puro (`Threshold TOP` sobre Magnitud de Flujo)
Para lograr el efecto clásico de **Datamosh** (el fondo se congela y los píxeles viejos son arrastrados solo por las zonas en movimiento):
1. Conecta el **`Optical Flow TOP`** a un **`Math TOP`**:
   - *Combine Channels:* **`Length`** (calcula $\sqrt{u^2 + v^2}$).
2. Conecta ese `Math TOP` a un **`Threshold TOP`**:
   - *Threshold:* **`0.025`** (ajusta según iluminación de tu webcam), *Softness:* `0.01`.
   - Esto genera una máscara blanca **solo donde hay movimiento nuevo**.
3. Usa esa máscara en un **`Matte TOP`** (o **`Composite TOP`**) para inyectar el `Flip TOP` actual únicamente en los píxeles en movimiento, mientras que el resto de la imagen sigue leyendo del **`Feedback TOP` + `Displace TOP`** sin limpiar el buffer (`Level Opacity = 1.0`).

---

## Receta 3 · Ecos Temporales al BPM + Slit-Scan con Oclusión Real `[OK-12GB]`

Proyecta múltiples ecos pasados de tu silueta al ritmo de la música **por detrás de tu cuerpo real** (sin tapar al sujeto en primer plano).

### 3.1 Ruta A · `.tox` Listo + Oclusión Humana Real
1. Descarga **`temporal_resonator.tox`** desde [`kevinraymond/touchdesigner-effects`](https://github.com/kevinraymond/touchdesigner-effects).
2. Conecta tu cámara (`1280x720`) en paralelo a:
   - **`temporal_resonator.tox`** (genera los ecos rítmicos acumulados).
   - **`DAViDHuman.tox`** de [`cacheflowe/td-native-inference`](https://github.com/cacheflowe/td-native-inference) (~21 ms GPU en RTX 3060, extrae *Depth + Normals + Alpha Matte* del cuerpo sin green screen).
3. Compón en un **`Over TOP`** / **`Composite TOP`**:
   - **Foreground (Input 0):** Cámara multiplicada por el Matte de `DAViDHuman.tox` *(el sujeto vivo en primer plano)*.
   - **Background (Input 1):** Salida de `temporal_resonator.tox`.
   - Resultado: los ecos temporales nacen y fluyen **por detrás del cuerpo** con recorte limpio en cabello y hombros.

### 3.2 Ruta B · Alternativa 100% Nativa (`Texture 3D TOP` + `Time Machine TOP` + `Count CHOP`)
Si quieres construir tu propio *Slit-Scan* o buffer temporal sin dependencias externas:
1. **`Texture 3D TOP`** *(Pixel Format: **`16-bit Float (RGBA)`**, Cache Size: `64` o `120` slices; en `1280x720` × 64 slices `16F` ocupa ~440 MB VRAM — muy cómodo en 12 GB)*. Activa **Prefill** / modo circular.
2. **`Time Machine TOP`**:
   - Input 0: `Texture 3D TOP`
   - Input 1 (Offset Map): un **`Ramp TOP`** (Slit-Scan lineal vertical/horizontal) o **`Noise TOP`** (Slit-Scan orgánico líquido).
3. **Patrón Seguro de Pulso + Contador (`Count CHOP`) para NO perder beats:**
   - **Nunca** dispares eventos usando `if val == 1:` en Python porque el reloj de frames puede saltar el pico exacto.
   - Usa **`Audio Analysis` / `Beat CHOP`** → **`Trigger CHOP`** *(Attack `0.005s`, Sustain `0`, Release `0.08s`)* → **`Logic CHOP`** *(Convert Input: `Off When Outside Bounds` o `Rising Edge`)* → **`Count CHOP`** *(Increment on `Off to On`, Limit: `Loop Min/Max` entre `0` y `3` para 4 tiempos)*.
   - Enlaza el `Count CHOP` al índice de capa de un **`Switch TOP`** o al offset de fase del `Time Machine TOP`.

---

## Receta 4 · Silueta de Partículas `POPs` + Raymarching GLSL con Manos (`MediaPipe`) `[OK-12GB]`

Controla campos de fuerza **POPs** en GPU y shaders **Raymarching GLSL** usando únicamente tus manos frente a la webcam.

### 4.1 Tracking de Manos Estable + Detección de *Pinch*
1. Descarga e integra **`MediaPipe.tox`** de [`torinmb/mediapipe-touchdesigner`](https://github.com/torinmb/mediapipe-touchdesigner) (~1–2 GB VRAM). Activa solo **Hand Tracking** (desactiva Face/Pose si no los usas para ahorrar ~400 ms de carga y VRAM).
2. Selecciona los landmarks clave con **`Select CHOP`** (por ejemplo `h1:thumb_tip_*` [landmark 4] y `h1:index_finger_tip_*` [landmark 8]).
3. **Anti-Jitter Obligatorio:** Pasa las coordenadas `tx, ty, tz` por un **`Filter CHOP`** (*Filter Type:* `Gaussian` o `One Euro` / `Lag CHOP` con `Lag = 0.04s`). Sin esto, las partículas vibrarán en reposo.
4. **Cálculo de *Pinch* (`Math CHOP` + `Logic CHOP`):**
   - Usa un **`Math CHOP`** (*Combine CHOPs:* `Subtract`) entre `thumb_tip` (`x,y,z`) e `index_finger_tip` (`x,y,z`).
   - Encadena otro **`Math CHOP`** (*Combine Channels:* **`Length`**) para obtener la distancia euclidiana 3D en tiempo real.
   - Pasa la distancia por un **`Logic CHOP`** (*Convert Input:* `Off When Outside Bounds`, `Bounds = [0.0, 0.045]`) → devuelve `1` cuando haces *pinch* y `0` cuando sueltas.

### 4.2 Conexión Hacia `POPs` GPU o Raymarching `GLSL TOP`
- **Hacia `POPs` (TD `2025.33230+`):**
  - Crea un **`Point Generator POP`** o **`Point File In POP`** (p. ej. 200,000 puntos GPU) → **`Force POP`** (o **`Transform POP`**).
  - Mapea `tx, ty, tz` del `Filter CHOP` al centro de atracción/repulsión del **`Force POP`**, y usa el canal *pinch* (`0`/`1`) para invertir la fuerza (atraer al hacer *pinch*, explotar al soltar).
  - Renderiza con **`Point Sprite MAT`** + **`Render TOP`**.
  - *(Si tienes licencia de **`POPX v1.5.0`**, puedes sustituir `Force POP` por los operadores físicos GPU de POPX y el **Aura Render Engine** para estelas volumétricas en tiempo real).*
- **Hacia `GLSL TOP` (Patrón `CHOP to TOP` 32-bit Float):**
  - Si quieres pasar los **21 landmarks de cada mano** (42 puntos) a un shader de **Raymarching** sin llenar 42 uniforms a mano:
  - Conecta los canales `x, y, z` al **`CHOP to TOP`** (*Data Format:* `RGB`, *Pixel Format:* **`32-bit Float (RGBA)`**, *Image Layout:* `Single Row`).
  - Conéctalo como **Input 1** (`sTD2DInputs[1]`) de tu `GLSL TOP` y léelo con `texelFetch(sTD2DInputs[1], ivec2(landmarkIndex, 0), 0).rgb`.
  - **Librería de Shaders Lista:** Explora los **98 archivos `.frag`** de [`Rikiya89/glsl_daily_practice`](https://github.com/Rikiya89/glsl_daily_practice) (raymarching SDF, campos de partículas y deformaciones GLSL listas para adaptar a `GLSL TOP`).

---

## Receta 5 · Relighting PBR en Vivo sobre Webcam (`DAViD Normals` + `OCIO` + `SSDO`) `[OK-12GB]`

Ilumina físicamente tu rostro y ropa en tiempo real con **sombras direccionales de profundidad (`SSDO`)**, specular GGX y respuesta audio-reactiva en espacio lineal, saliendo directo a OBS a 60 FPS.

### 5.1 Cadena Lineal Correcta (`OCIO` + `DAViD` + `SSDO`)
1. **Linealización Obligatoria (`OpenColorIO TOP`):**
   - Conecta `Video Device In TOP` → **`OpenColorIO TOP`**.
   - Configura **Input Space:** `sRGB - Texture` → **Output Space:** `Linear` *(o `ACEScg` según tu config `.ocio`)*, Pixel Format: **`16-bit Float (RGBA)`**.
   - *Por qué:* Calcular luz PBR sobre valores sRGB gamma-encoded produce sombras sucias y colores quemados.
2. **Inferencia de Normales y Matte (`~21 ms` en RTX 3060):**
   - Conecta el video original a **`DAViDNormals.tox`** (~10 ms GPU) y **`DAViDHuman.tox`** (~21 ms GPU, entrega Depth + Matte) de [`cacheflowe/td-native-inference`](https://github.com/cacheflowe/td-native-inference).
   - **Regla Crítica de Coordenadas:** `DAViDNormals` entrega normales OpenGL (`+Y` arriba). En el shader de pantalla (`vUV.st` donde `+Y` también va arriba en TD, o si tu Depth/Screen raymarch invierte el eje Y), verifica siempre el parámetro **`uInvertNormalY`** (`0.0` vs `1.0`) probando una luz cenital desde arriba: la frente y la parte superior de los hombros deben iluminarse primero.
3. **Shader `GLSL Multi TOP` (`SSDO` + Audio-Reactivo):**
   - Usa un **`GLSL Multi TOP`** (Pixel Format: **`32-bit Float (RGBA)`**) con los 4 inputs exactos del shader PBR documentado en [Pilar 05 §5](05-touchdesigner-realtime.md#shader-glsl-top-de-referencia-6-luces--screen-space-depth-shadows--material-dual):
     - `[0]` Plate Lineal (`OpenColorIO TOP`)
     - `[1]` `DAViDNormals.tox` (`16-bit Float`)
     - `[2]` Depth (`DAViDHuman.tox`)
     - `[3]` Matte (`DAViDHuman.tox` / dual matte)
   - Enlaza `uFireStrengths[0]` a un **`Audio Device In CHOP` → `Audio Spectrum CHOP` → `Analyze CHOP` (Average/RMS)** para que las luces de fuego/neón pulsen con los bajos.
4. **Tone Mapping y Salida a OBS:**
   - Antes de mostrar en pantalla SDR, pasa el `GLSL Multi TOP` por un **`OpenColorIO TOP`** inverso (`Linear → sRGB - Texture` con *Look: `AgX - Punchy`* o *ACES Filmic*) para comprimir los picos HDR sin lavado pastel.
   - Conecta a **`Spout Out TOP`** (`TD_Relight_Live`) y recíbelo en OBS con **`obs-spout2-plugin`** (0 ms, sin pérdida de FPS).

---

## Receta 6 · Instalación Multicámara (`Orbbec / Kinect / OAK-D`) + `Web Render TOP` `[OK-12GB]`

Arquitectura robusta para instalaciones interactivas con cámaras de profundidad y UI/HUDs en HTML/WebGL a 60 FPS.

### 6.1 Cámaras de Profundidad en Windows 11
- **Orbbec (Femto Bolt / Astra 2):** Usa **`Orbbec TOP`** + **`Orbbec Select TOP`** (para separar Color, Depth y Point Cloud).
  - ⚠️ **Nota SDK Windows 11:** Las series clásicas Astra/Astra Pro requieren **Orbbec SDK v1** instalado y no mezclar DLLs con SDK v2 (Femto Bolt/Gemini); verifica en el *Device Manager* de Windows que el driver USB3 esté activo.
- **Multicámara Calibrada (Kinect Azure / Femto Bolt / RealSense):** Usa **[`DarienBrito/TDXDepthCamMerger`](https://github.com/DarienBrito/TDXDepthCamMerger)** (verificado en **TD `2025.33070+`**), que fusiona múltiples nubes de puntos en un único espacio 3D GPU (`POPs`).
- **Luxonis OAK-D (PoE / USB3):** Usa el repo oficial **[`TouchDesigner/TDOAK`](https://github.com/TouchDesigner/TDOAK)**.
  - **Regla de Estabilidad:** Configura el hilo de captura en modo **`decode -> fill`** para evitar bloqueos del main thread de TouchDesigner cuando la cámara PoE pierde paquetes.
- **Visualización GPU:** Envía la nube fusionada directamente a **`Point File In POP` / `POPs`** para renderizar millones de puntos con `Point Sprite MAT` sin pasar por CPU.

### 6.2 `Web Render TOP` (Overlays JS/WebGL a 60 FPS) + Control MCP
- **`Web Render TOP` (Chromium 132.0 integrado):** Ejecuta interfaces **Three.js / GSAP / Rive / React** con `Background = Transparent` y `Use Shared Textures = On`.
  - ⚠️ **Regla Obligatoria Multi-Instancia:** Si abres **más de un `Web Render TOP`** en el mismo proyecto `.toe`, asigna un **`User Cache Directory` distinto** a cada operador (ej. `C:/TD_Cache/web1`, `C:/TD_Cache/web2`); de lo contrario, Chromium compartirá el lock de caché y la segunda instancia quedará en blanco o crasheará.
- **Control Remoto / Agente IA:**
  - Usa **`TouchDesigner/TDMCP`** (`http://127.0.0.1:13316/mcp` — ver [`MODULE_C`](modules/MODULE_C_TD_BLENDER_VFX.md)) o **[`eviscerations/touchdesigner-bridge-mcp`](https://github.com/eviscerations/touchdesigner-bridge-mcp)** para ajustar parámetros de instalación, leer `cookTime` y automatizar cambios de escena en vivo.

---

## Receta 7 · Puente Zero-Copy `TD ↔ Python IA` (`forkni/cuda-link` + `StreamDiffusionTD`) `[OK-12GB]`

Elimina el cuello de botella GPU→CPU→GPU cuando corres modelos PyTorch/TensorRT personalizados junto a TouchDesigner en Windows 11.

### 7.1 `forkni/cuda-link` (Memoria Compartida Directa CUDA ↔ TOP)
- **Repo:** [`forkni/cuda-link`](https://github.com/forkni/cuda-link) — permite compartir tensores PyTorch / CuPy directamente con `TOP`s de TouchDesigner mediante interop CUDA-Direct3D 11 (`WDDM` en Windows 11) sin copiar a RAM.
- **Requisitos exactos en tu PC:**
  - **TouchDesigner `2025.32820+`** (Windows 11).
  - **Python 3.11** (alineado con el Python embebido de TD `2025.x`).
  - Misma GPU NVIDIA (**RTX 3060 12 GB**) configurada en *Alto rendimiento* en Windows Graphics Settings.

### 7.2 `StreamDiffusionTD` (15–25 FPS en 12 GB VRAM) + Exportación a Post
1. Instala **StreamDiffusionTD v0.4.2** siguiendo [`MODULE_C §3`](modules/MODULE_C_TD_BLENDER_VFX.md#3-streamdiffusiontd-v042-en-rtx-3060-12-gb-configuración-óptima) (ya incluye `cuda-link` + `TensorRT 10.16`).
2. **Presupuesto VRAM Seguro (~5–7 GB VRAM):**
   - **Opción rápida (18–25 FPS):** `stabilityai/sd-turbo` o `SD 1.5 LCM` a `512x512`, `1–2 steps`, ControlNet **`depth_tensorrt`** (alimentado con Z-Depth de `DAViDHuman.tox` o Blender Spout2).
   - **Opción mayor detalle (10–14 FPS):** `SDXL-Turbo` compilado con TensorRT a `512x512` (~6.5–7.5 GB VRAM; **cierra** Blender/ComfyUI antes de activarlo).
3. **Exportación Maestra Hacia Offline (ArtCraft / Premiere / After Effects / Resolve):**
   - Graba la salida con **`Movie File Out TOP`**:
     - Para color + alpha limpio: **Apple ProRes 4444** (`yuva444p10le`) o **HAP Q Alpha**.
     - Para pases lineales (Normal / Depth / Relight HDR): secuencia **OpenEXR 16-bit Float** (`Zip` / `PIZ` lossless).

---

## Receta 8 · Workflows Prácticos ComfyUI / E-Commerce / VFX & Checklist Anti-Nodos-Rojos

Cuando pasas de tiempo real en TouchDesigner a generación/relighting offline en **ComfyUI** en tu **RTX 3060 12 GB (`sm_86`) + 32 GB RAM + Windows 11**, sigue esta lista para evitar nodos rojos, OOM y errores silenciosos.

### 8.1 Packs de Nodos Base Obligatorios
| Pack / Repo | Qué aporta | Gotcha Crítico en Windows 11 / RTX 3060 |
|---|---|---|
| [`Kosinkadink/ComfyUI-VideoHelperSuite`](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite) | `VHS_LoadVideo`, `VHS_VideoCombine` (ProRes/MP4/PNG) | **Nota NumPy 2.x:** si actualizaste paquetes y `VHS` o `cv2` falla al importar con error de ABI NumPy, fija `numpy<2.0` (`1.26.4`) o usa wheels compilados contra NumPy 2.x en `python_embeded`. |
| [`kijai/ComfyUI-KJNodes`](https://github.com/kijai/ComfyUI-KJNodes) | `VRAM_Debug`, `SetNode` / `GetNode`, utilidades de máscaras y tensores | **`SetNode` / `GetNode` son nodos virtuales solo-JS del cliente:** si exportas un workflow con `Set`/`Get` para ejecutarlo por API headless (`POST /prompt`), usa **Workflow → Export (API)** en la UI para que ComfyUI resuelva los enlaces virtuales; de lo contrario fallará el grafo en backend. |
| [`city96/ComfyUI-GGUF`](https://github.com/city96/ComfyUI-GGUF) | Carga `Q3_K_M` / `Q4_K_S` / `Q5_K_M` en 12 GB VRAM | **NO uses `Force/Set CLIP Device` fijado en `cuda:0`** junto a modelos 14B GGUF: provoca OOM inmediato al competir con los bloques DiT. Deja el Text Encoder en CPU o usa `WanVideoTextEncodeCached` con descarga automática. |
| [`rgthree/rgthree-comfy`](https://github.com/rgthree/rgthree-comfy) | `Fast Groups Bypasser`, `Power Lora Loader`, `Context` | Excelente para desactivar bloques pesados sin romper cables. Recuerda export API si usas sus nodos virtuales en scripts. |
| [`Fannovel16/comfyui_controlnet_aux`](https://github.com/Fannovel16/comfyui_controlnet_aux) | Preprocesadores Depth, Canny, DWPose, OpenPose | Si usas **DWPose / Depth**, ejecuta en fase separada o descarga modelos con **`VRAM_Debug` (`unload_all_models=true`)** antes de cargar el sampler principal. |
| [`cubiq/ComfyUI_IPAdapter_plus`](https://github.com/cubiq/ComfyUI_IPAdapter_plus) | Transferencia de identidad / estilo / iluminación | En 12 GB VRAM evita apilar más de 1–2 IPAdapters junto a ControlNet + Wan/FLUX sin *BlockSwap*. |
| `ComfyUI-Impact-Pack` + `Impact-Subpack` | `UltralyticsDetectorProvider`, `SAMDetector`, `Detailer` | Instala **ambos** (`Impact-Pack` e `Impact-Subpack`); muchos workflows de e-commerce/VFX fallan en rojo por faltar el *Subpack* (Ultralytics). |
| `ComfyUI-TeaCache` | Aceleración ~1.5–2× saltando pasos redundantes de difusión | Actívalo solo tras verificar la composición base (en movimientos rápidos puede suavizar micro-detalle). |

### 8.2 Dos Gotchas Críticos de Windows 11 + API ComfyUI
1. **Error en `/view` desde apps web externas (React / Remotion / Electron / Browser):**
   - En Windows 11, `aiohttp` puede corromper o truncar respuestas de archivos estáticos (`/view?filename=...`) por `sendfile`.
   - Solución en PowerShell **antes** de lanzar ComfyUI:
     ```powershell
     $env:AIOHTTP_NOSENDFILE = "1"
     ```
2. **Error `Node has no class_type` al enviar JSON a `POST /prompt`:**
   - Ocurre cuando envías el archivo guardado con *Save* (formato UI con `nodes`/`links`) en lugar del formato API.
   - Solución: En ComfyUI activa *Enable Dev mode Options* en Settings y usa siempre **`Workflow → Export (API)`** (o `Save (API Format)`).

### 8.3 Proyectos & Workflows Verificados (Clasificados para RTX 3060 12 GB)

| Proyecto / Repo | Caso de Uso | Clasificación Hardware | Notas de Ejecución en 3060 12 GB / 32 GB RAM |
|---|---|---|---|
| [`LuanVelo/fashion-pose-to-video`](https://github.com/LuanVelo/fashion-pose-to-video) | E-commerce moda: pose de referencia a video | **`[TIGHT-12GB]`** | Usa modelos cuantizados (`GGUF Q4`/`INT8`), `480p` (`832x480`), `Tiled VAE` y limpia VRAM entre DWPose y el sampler de video. |
| [`nftblackmagic/catvton-flux`](https://github.com/nftblackmagic/catvton-flux) | Virtual Try-On (cambio de prenda sobre FLUX) | **`[TIGHT-12GB]`** | Requiere pesos **FLUX GGUF (`Q4_K_S`/`Q4_K_M`)** + Text Encoder cuantizado (`T5 GGUF Q4`) para caber en 12 GB VRAM y ~22 GB RAM libres. |
| [`digitalinnovator/comfyui-production-workflows`](https://github.com/digitalinnovator/comfyui-production-workflows) | Colección de workflows modulares de producción | **`[OK-12GB]` / `[TIGHT-12GB]`** | Los flujos SDXL/ControlNet corren cómodos `[OK-12GB]`; los flujos FLUX/Wan requieren sustituir `FP16/FP8` por nodos `ComfyUI-GGUF` `[TIGHT-12GB]`. |
| [`D3voz/openjutsu`](https://github.com/D3voz/openjutsu) | Efectos VFX / anime / energía sobre video | **`[TIGHT-12GB]` / `[CLOUD / >24GB]`** | Viable en `[TIGHT-12GB]` recortando a `480p` + GGUF + `TeaCache`; sus presets `720p/1080p` nativos sin cuantizar superan los 12 GB (`[CLOUD / >24GB]`). |
| [`neuregex/freefield`](https://github.com/neuregex/freefield) | Workflows y utilidades experimentales ComfyUI | **`[OK-12GB]` / `[TIGHT-12GB]`** | Verificar en cada JSON que no cargue dos checkpoints simultáneos sin `VRAM_Debug` ni `fp8_fast` (`sm_86`). |
| [`ggvfx/comfyui-workflows`](https://github.com/ggvfx/comfyui-workflows) | Compositing VFX, relighting e integración en ComfyUI | **`[TIGHT-12GB]`** | Excelente referencia de estructura VFX; aplica las reglas de [Módulo A](modules/MODULE_A_COMFYUI_VFX_3060.md) (`Q3_K_M`/`Q4_K_S`, `invert_normal_y=True` si usa NormalCrafter). |
| [`dreamrec/UniVidX_ComfyUI`](https://github.com/dreamrec/UniVidX_ComfyUI) | Edición/generación unificada multi-tarea en video | **`[CLOUD / >24GB]`** | Su arquitectura unificada y contexto de video largo exceden cómodamente los 12 GB VRAM en inferencia estándar; úsalo como referencia o en nube >24 GB. |

---

## Siguientes Pasos Recomendados
- Para llevar el relighting y simulación física de fuego a calidad cine en offline (`33f ➔ 167f` con Gates 0–3): consulta [`docs/modules/MODULE_A_COMFYUI_VFX_3060.md`](modules/MODULE_A_COMFYUI_VFX_3060.md).
- Para conectar TouchDesigner + Blender en vivo por `Spout2`, `OSC` y `TDMCP`: consulta [`docs/modules/MODULE_C_TD_BLENDER_VFX.md`](modules/MODULE_C_TD_BLENDER_VFX.md).
