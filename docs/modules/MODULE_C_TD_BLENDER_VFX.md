# Módulo C (Fase 2) · TouchDesigner (`TDMCP` + `Embody` + `StreamDiffusionTD`) + Blender VFX en Vivo

> **Hardware Calibrado:** NVIDIA **RTX 3060 12 GB VRAM** *(Ampere)* · AMD **Ryzen 9 5900X** · **32 GB RAM** · **Windows 11**  
> **Host Agente Principal:** **Google Antigravity** (`agy` / IDE) conectando TouchDesigner + Blender por MCP.

---

## 1. Mapa de Arquitectura en Vivo y Presupuesto RTX 3060 (12 GB VRAM / 32 GB RAM)

Con **12 GB de VRAM** y **~22–24 GB de RAM libre** en Windows 11, **el error #1 es intentar correr MoCap + Blender Cycles + StreamDiffusionTD + TouchDesigner POPs pesados al mismo tiempo**. Divide el trabajo en **3 Modos Operativos** probados:

| Modo Operativo | Apps GPU Activas Simultáneamente | Consumo VRAM Estimado | Consumo RAM | Rendimiento Esperado |
|---|---|---|---|---|
| **Modo 1 · Difusión 3D Guiada (Tiempo Real)** | **Blender (Viewport Solid/Workbench/EEVEE Ligero + `TextureSharing` Spout)** ➔ **TouchDesigner (`Spout In TOP` + `StreamDiffusionTD SD-Turbo TRT` + `depth_tensorrt`)** | ~1.5 GB (Blender) + ~6.0–7.5 GB (TD + TRT `512x512`) = **~8.5–9.5 GB** ✅ | ~11–14 GB | **15–25 FPS** en vivo (`cuda-link` GPU-zero-copy) |
| **Modo 2 · MoCap Sin Marcadores ➔ Rig Blender** | **Paso A (Solo MoCap):** `RGBMoCap` / **`GVHMR`** (`HTD+FootMR+HandFlow`).<br>**Paso B (Solo 3D):** **Blender (`mcp-for-blender`)** importando FBX/BVH o `.blend` | Paso A: **~4.2 GB VRAM** ✅<br>Paso B: **~2–5 GB VRAM** ✅ | Paso A: ~6.9 GB<br>Paso B: ~8–12 GB | 100% seguro sin OOM ni swap a disco |
| **Modo 3 · Escena 3DGS + Partículas POPs GPU** | **TouchDesigner `2025.33230+` (`Point File In POP` + POPs GPU)** y/o **Blender (`Kiri 3DGS Render`)** sincronizados vía OSC/glTF | **~3–7 GB VRAM** según nº de splats (cuidado con `Shift+D` duplicados en Blender) | ~10–15 GB | **30–60 FPS** en TouchDesigner POPs GPU |

> ⚠️ **Regla física Windows 11 (Graphics GPU Preference):**  
> Asegúrate en **Configuración de Windows → Sistema → Pantalla → Gráficos** de que tanto `TouchDesigner.exe` como `blender.exe` usen la **NVIDIA GeForce RTX 3060 (Alto rendimiento)**; si una usa GPU distinta en sistemas multi-GPU, Spout2 dará error `80070057` / textura negra.

---

## 2. TouchDesigner + Antigravity: `TDMCP` (Oficial) vs `Embody / Envoy`

Ambos requieren **TouchDesigner `2025.33230` o superior** (la rama que introduce POPs estables y compatibilidad oficial MCP).

### Opción A · `TouchDesigner/TDMCP` + `TDMCPSkills` (Recomendado por Defecto en Antigravity)
- **Repos:** [`TouchDesigner/TDMCP`](https://github.com/TouchDesigner/TDMCP) (26 tools, Streamable-HTTP `http://127.0.0.1:13316/mcp`, Undo nativo) + [`TouchDesigner/TDMCPSkills`](https://github.com/TouchDesigner/TDMCPSkills) (19 skills oficiales).
- **Por qué elegirlo:** Integración oficial de Derivative con soporte explícito para **`Antigravity (agy)`** y guardado de imágenes de salida (`view_operator`) para que el agente *vea* por qué un render TOP está negro.

#### Instalación Paso a Paso (5 minutos):
1. Descarga `TDMCP.tox` desde [GitHub Releases de TDMCP](https://github.com/TouchDesigner/TDMCP/releases) y arrástralo dentro de tu proyecto (p. ej. `/project1/TDMCP`).
2. En la pestaña **MCP** del componente:
   - Activa **Active = On**.
   - En **Install For**, selecciona **Antigravity**.
   - Deja **Install Scope = Local** *(si vas a ejecutar `agy --print` en scripts headless, cambia a **User** para que vayan a `~/.gemini/config/skills/`)*.
3. Registra el servidor en Antigravity (usa **siempre `127.0.0.1`**, nunca `localhost`, porque el socket es IPv4-only):
   - **Vía CLI Antigravity:**
     ```bash
     agy mcp add touchdesigner http://127.0.0.1:13316/mcp
     ```
   - **O manualmente en `~/.gemini/config/mcp_config.json`** *(¡OJO! Antigravity exige la clave `"serverUrl"`, NO `"url"`)*:
     ```json
     {
       "mcpServers": {
         "touchdesigner": {
           "serverUrl": "http://127.0.0.1:13316/mcp"
         }
       }
     }
     ```
4. Pulsa el botón **Install Skills** en el componente `TDMCP`. Esto descarga automáticamente las **19 skills oficiales `td-*`** en `.agents/skills/` (o `~/.gemini/config/skills/`):
   `td-build-planning`, `td-pop-family`, `td-top-family`, `td-chop-family`, `td-sop-family`, `td-dat-family`, `td-mat-family`, `td-glsl-shaders`, `td-geometry-instancing`, `td-comp-architecture`, `td-python-extension`, `td-lister-ui`, `td-node-layout`, `td-network-cleanup`, `td-performance-check`, `td-review-network`, `td-general`, `td-working-mode`, `td-colab`.
5. Al enviar el primer prompt, TouchDesigner mostrará un modal de consentimiento: haz clic en **Allow**.

---

### Opción B · `dylanroscover/Embody` + `Envoy` (Para Proyectos Serios en Git / 70 Tools / Multi-Instancia)
- **Repo:** [`dylanroscover/Embody`](https://github.com/dylanroscover/Embody) (`Envoy` en puerto `127.0.0.1:9870`, puente STDIO `.embody/envoy-bridge.py`, formato YAML **TDXN** y **Convoy** LAN).
- **Por qué elegirlo:** Además de **70 herramientas MCP**, externaliza tus operadores y redes enteras en archivos **`.tdxn` (YAML legible por Git e IAs)** y el puente STDIO permite a Antigravity **lanzar, reiniciar o cambiar de instancia de TouchDesigner incluso antes de abrir el `.toe`**.
- **Configuración automática para Antigravity:**
  1. Arrastra `Embody.tox` (o parte de `starter/Embody-starter.toe`) a tu proyecto.
  2. Sigue el **Setup Wizard**, elige **Antigravity** y activa **Envoy Enable**.
  3. Embody escribe automáticamente **`.agents/mcp_config.json`** en la raíz de tu proyecto usando su puente STDIO (`envoy-bridge.py`), además de mantener bloques actualizados en `AGENTS.md` / `GEMINI.md`.
  4. Atajos clave dentro de TouchDesigner: `lctrl + lctrl` (etiquetar nodo para externalizar a disco), `Ctrl + Shift + U` (actualizar archivos en disco), `Ctrl + Shift + E` (exportar red entera a `.tdxn`).

> 💡 **¿Puedo tener TDMCP y Embody instalados?**  
> Técnicamente escuchan en puertos distintos (`13316` vs `9870`), pero en un mismo proyecto `.toe` usa **uno solo a la vez** para evitar que dos agentes compitan modificando el grafo. Usa `TDMCP` para exploración rápida y visuales con las 19 `td-*` skills; usa `Embody` cuando quieras **Git roundtrip (`.tdxn`)**, código GLSL/Python externalizado en VS Code o multi-máquina con **Convoy**.  
> *(Alternativa multi-instancia en Rust: [`Verbalize-public/td-mcp-rs`](https://github.com/Verbalize-public/td-mcp-rs); alternativa Node/WebServer DAT clásica para versiones <2025: [`8beeeaaat/touchdesigner-mcp`](https://github.com/8beeeaaat/touchdesigner-mcp)).*

---

## 3. StreamDiffusionTD v0.4.2 en RTX 3060 12 GB (Configuración Óptima)

[`StreamDiffusionTD`](https://dotsimulate.com/docs/streamdiffusiontd/install) (`v0.4.2`, sobre `cumulo-autumn/StreamDiffusion`) permite estilización generativa en tiempo real manteniendo los frames dentro de la GPU mediante **`cuda-link`** (sin ir y volver por CPU).

### Pasos exactos de instalación (Windows 11 + RTX 3060):
1. Arrastra `streamdiffusiontd_latest.tox` en TouchDesigner e inicia sesión.
2. En la pestaña **Install**:
   - **Base Folder:** apunta a una carpeta vacía y corta sin espacios (ej. `C:\AI\SDTD`).
   - **Step 1 · Download StreamDiffusion:** descarga los commits fijos (`SDTD_040_stable` / `SDTD_042_installer`).
   - **Step 2 · Install StreamDiffusion:** crea el `.venv` en **CUDA 12.8** + PyTorch `2.11.0+cu128` + `cuda-link`.
   - **Step 3 · Install TensorRT:** instala **TensorRT 10.16** (`tensorrt_cu12`), **obligatorio** para ControlNet, IP Adapter y StreamV2V.

### Receta Segura de Parámetros para 12 GB VRAM (15–25 FPS estables):
- **Modelo Base:** `stabilityai/sd-turbo` (o SD 1.5 LCM). *Evita SDXL Turbo si vas a compartir VRAM con Blender simultáneamente.*
- **Acceleration:** `tensorrt` (compila el engine una sola vez; tarda 2–5 min la primera corrida).
- **Resolución:** **`512x512`** (si necesitas `1024x576` para formato 16:9, mejor genera a `512x288` / `512x512` y escala después con **Topaz / ComfyUI / GLSL Sharpen + Lanczos** en TD).
- **Steps / Denoising:** `1` a `2` steps (`t_index_list` corto).
- **ControlNet Guiado por Blender (El secreto VFX):**
  - Usa **`depth_tensorrt`** en lugar de `depth` estándar: consume **~60% menos tiempo/VRAM** en preprocesamiento! O mejor aún: **saca el Z-Depth directo de Blender por Spout** y desactiva el preprocesador neuronal de TD (0 ms de costo!).
- **IP Adapter:** déjalo desactivado salvo que lo necesites; con TensorRT queda compilado (*baked*) en el engine (decídelo antes de hacer *Build Engine*).
- ⚠️ **Aviso de plataforma (Nov 2026):** El servicio nube **Daydream** cerró el **13 de noviembre de 2026**; si necesitas más FPS para un evento en vivo, `v0.4.2` incorpora modo remoto con **RunPod**.

> **Alternativa modular ComfyUI:** Si prefieres enviar prompts o frames pesados a Wan/Flux sin compilar engines TRT, usa [`JiSenHua/ComfyUI-TD`](https://github.com/JiSenHua/ComfyUI-TD) (streaming bidireccional) o [`cacheflowe/td-native-inference`](https://github.com/cacheflowe/td-native-inference) (nodos C++ nativos ONNX/MediaPipe dentro de TD), junto con [`torinmb/mediapipe-touchdesigner`](https://github.com/torinmb/mediapipe-touchdesigner) (~1–2 GB VRAM).

---

## 4. Blender 4.5 / 5.x MCP en Antigravity (Opciones Verificadas)

> ⚠️ **Regla de Puerto Único (`localhost:9876`):** Nunca habilites dos add-ons MCP distintos apuntando al puerto `9876` en la misma instancia de Blender al mismo tiempo. Elige **una** de estas tres rutas según tu flujo:

| Opción | Repo / Fuente | Ventaja Clave para Módulo C | Configuración en Windows 11 + Antigravity |
|---|---|---|---|
| **1. Community Standard** (`mcp-for-blender`) | [`ahujasid/mcp-for-blender`](https://github.com/ahujasid/mcp-for-blender) (★34,936 · MIT) | Detección automática de **Antigravity**, PolyHaven, Sketchfab, Hyper3D y ejecución directa `bpy`. | En PowerShell:<br>`winget install --id=astral-sh.uv -e`<br>`uvx mcp-for-blender setup` *(elige Antigravity e instala `addon.py`)*. |
| **2. Ultra Granular + VLM Loop** (`blender-mcp-ultra`) | [`carlosh7/blender-mcp`](https://github.com/carlosh7/blender-mcp) (MIT) | **248 herramientas tipadas** (GeoNodes, Shader Nodes, Física, Rigging, EEVEE visual feedback), blocklist AST de seguridad y 479 tests E2E. | `pip install blender-mcp-ultra` + instalar `blender_mcp_ultra.zip` en Blender `Preferences > Add-ons` + añadir `blender-mcp-server` en `mcp_config.json`. |
| **3. Oficial Blender Lab MCP** | [`blender.org/lab/mcp-server/`](https://www.blender.org/lab/mcp-server/) | Oficial de Blender Foundation para **Blender 5.1 / 5.2+**. | Descargar extensión oficial + paquete `.mcpb` y referenciarlo en **Agent Manager → Manage MCP Servers → View raw config**. |

> 🔧 **Gotcha Windows (`invalid trailing data`):** Si usas algún fork de Blender MCP antiguo con Antigravity en Windows y ves errores de JSON corrupto por stdio (`\r\n` vs `\n`), asegúrate de estar usando las versiones actualizadas (`mcp-for-blender` actual, `carlosh7/blender-mcp`, o [`kc0ed/Blender-MCP-For-Antigravity`](https://github.com/kc0ed/Blender-MCP-For-Antigravity)) que fuerzan modo binario en `stdin/stdout`.

---

## 5. El Puente en Vivo: Blender ↔ TouchDesigner (`Spout2` + `OSC` + `POPs 3DGS`)

### A. Texturas en Tiempo Real por GPU (`Spout2` en Windows 11) — La Verdad Técnica

No todas las direcciones de Spout rinden igual en Blender. Conoce el diseño correcto para lograr **30–60 FPS sin trabar Blender**:

1. **Dirección Rápida (GPU Zero-Copy ✅): `Blender ➔ Spout Sender ➔ TouchDesigner Spout In TOP`**
   - Instala [`maybites/TextureSharing`](https://github.com/maybites/TextureSharing/releases) (`v9.1.1+`, soporta **Blender 5.x+**) en **Edit → Preferences → Add-ons → Install from Disk** y pulsa instalar `SpoutGL` dentro de las preferencias del add-on.
   - Selecciona tu **Cámara** en Blender → Panel **Camera Properties → Share texture** → tipo **Spout** → Sender Name: `BlenderCam01`.
   - En TouchDesigner crea un **`Spout In TOP`** y elige `BlenderCam01`. Latencia práctica: **<1 ms en la misma RTX 3060**.
   - **Superpoder VFX (Z-Depth / Normal / Clay ControlNet en Vivo):** Crea una segunda cámara o View Layer en Blender con material override **Mist/Depth** o **Normal** enviando `BlenderDepth` por Spout hacia TouchDesigner, conéctalo directo al input ControlNet de **StreamDiffusionTD** (o a mapas UV/desplazamiento en GLSL/POPs) y **tendrás IA generativa guiada en tiempo real por geometría 3D animada de Blender**.

2. **Dirección Lenta (Limitación Documentada ⚠️): `TouchDesigner Spout Out TOP ➔ Blender Texture/Viewport`**
   - Tanto `maybites/TextureSharing` (Receiver) como [`fonotipooo/blender-video-input`](https://github.com/fonotipooo/blender-video-input) (`v0.3.1-beta`) tienen un cuello de botella inherente a la API Python de Blender: `bpy.data.images.pixels` **copia la textura desde GPU hacia CPU y de regreso** (unos pocos FPS a resolución alta; `blender-video-input` limita por defecto a `Half` y `Max FPS = 15`).
   - **Cuándo usar Blender Receiver:** para previsualizar mapeos arquitectónicos en escena (`blender-video-input`), iluminar reflexiones ambientales aproximadas o probar texturas animadas a `512x512 @ 12-15fps`.
   - **Cuándo NO usarlo:** si necesitas composición final a 60 FPS combinando tu render 3D + la IA de StreamDiffusionTD, envía **ambas capas por Spout hacia TouchDesigner (o OBS `obs-spout2-plugin`)** y haz el compositing final en GPU en TouchDesigner!

---

### B. Sincronización Bidireccional de Cámara & Controles (`OSC`)

Incluimos en este repositorio el script listo para usar [`scripts/blender_td_osc_bridge.py`](../../scripts/blender_td_osc_bridge.py):
- Añade un panel **TD Bridge (OSC)** en el **N-panel (`N`)** de la Vista 3D de Blender.
- Envía a `127.0.0.1:9000` (UDP) la posición `(tx, ty, tz)`, rotación Euler en grados `(rx, ry, rz)`, longitud focal (`focal`) y el frame actual de tu cámara activa en cada tick de timer (~30–60 Hz) usando únicamente la biblioteca estándar de Python (`socket` + `struct`, **sin instalar `pip install python-osc` dentro del Python de Blender**!).
- En TouchDesigner, simplemente crea un **`OSC In CHOP`** (Network Port `9000`, Active `On`) y enlázalo con un **`Camera COMP`** o con **`Transform POP` / `StreamDiffusionTD` prompts**.

---

### C. 3D Gaussian Splatting Compartido (`.ply` en Blender + TouchDesigner POPs)

1. Genera o descarga tu captura `.ply` 3DGS (p. ej. con [`nerfstudio-project/gsplat`](https://github.com/nerfstudio-project/gsplat) acelerado en tu RTX 3060).
2. **En TouchDesigner (`2025.33230+`):**
   - Crea un **`Point File In POP`** y apunta al `.ply` (o `.gsz`). TouchDesigner auto-detecta automáticamente los atributos 3DGS (`Sh`, `Scale`, `Rotate`, `Color`) directamente en GPU *(no necesitas el antiguo `gsLoader` de la Palette)*.
   - Aplica ruido curl, audio-reactividad o físicas GPU con **Transform POP / Noise POP / Force POP**.
   - *(Tip Pro: actualiza a `2025.33230+`; versiones `2025.33070` tuvieron un bug de lectura en algunos `.ply` antiguos ya corregido en `33230`).*
3. **En Blender (4.5 / 5.x):**
   - Instala [`Kiri-Innovation/3dgs-render-blender-addon`](https://github.com/Kiri-Innovation/3dgs-render-blender-addon/releases) para editar, recortar y proyectar sombras EEVEE sobre el mismo `.ply`.
   - ⚠️ *Límite 12 GB VRAM:* En Blender (`Render mode`), cada duplicado `Shift+D` de un Splat empaqueta otro set completo en VRAM; usa instancias con cuidado en escenas grandes.

---

## 6. Markerless MoCap (`GVHMR` / `RGBMoCap`) ➔ Blender Rig ➔ TouchDesigner

Graba un video con tu celular o cámara (incluso **con cámara en movimiento** gracias a las coordenadas *Gravity-View* de GVHMR) y llévalo a un rig limpio en Blender:

### Ruta 1 · Suite Visual Windows Todo-en-Uno (Recomendada): `toyxyz/toyxyz_RGBMocap`
- **Repo:** [`toyxyz/toyxyz_RGBMocap`](https://github.com/toyxyz/toyxyz_RGBMocap) (Windows 11, soporta **GVHMR**, **FlowHMR**, **ExMR**, **MAMMA**, **PromptHMR** + **PEAR** captura en vivo).
- **Huella medida real:** **GVHMR + HTD + FootMR + HandFlow = ~4.20 GiB VRAM / ~6.87 GiB RAM** (sobra más de la mitad de tu RTX 3060 12 GB y tus 32 GB RAM).
- **Flujo exacto:**
  1. Clona `toyxyz_RGBMocap` y ejecuta **`install.cmd`** (prepara entornos aislados + Blender 4.5 + FFmpeg).
  2. Abre **`RGBMoCap.cmd`**, selecciona **GVHMR** (o **FlowHMR** con `Low Memory = 2.77 GiB VRAM`) y descarga modelos en **Model Manager** *(recuerda aceptar licencia y colocar `SMPLX_NEUTRAL.npz` en `models/body_models/smplx/`)*.
  3. Activa **HTD Refine + FootMR + HandFlow** (para dedos y tobillos) ➔ pulsa **Reconstruct 3D**.
  4. Corrige deslizamiento de pies en la línea de tiempo con **Apply Correction**.
  5. Importa tu personaje (**Mixamo FBX, VRM o PMX**) con **File → Import Character → Retarget** o exporta directo **File → Export → Blender / FBX / BVH**.

### Ruta 2 · CLI Directo (`zju3dv/GVHMR`) o Multi-Webcam (`FreeMoCap`)
- **CLI GVHMR:** `python tools/demo/demo.py --video=mi_toma.mp4 -s` *(usa `-s` solo si tu cámara está estática en trípode; omite `-s` si la cámara se mueve para activar SimpleVO)*.
- **Multi-Webcam USB (aprovechando los 24 hilos del Ryzen 9 5900X):** [`freemocap/freemocap`](https://github.com/freemocap/freemocap) + [`freemocap_blender_addon`](https://github.com/freemocap/freemocap_blender_addon).

### Llevar la Animación de Blender hacia TouchDesigner
- Exporta desde Blender como **`.glb` / `.gltf`** e impórtalo con **`glTF In COMP`** en TouchDesigner (mantiene huesos, cámaras y materiales), o transmite los puntos/articulaciones en vivo mediante el script OSC o exporta secuencia de malla a **`.pop`** (`File Out POP` / Alembic).

---

## 7. Checklist de Arranque Rápido (Ejecuta en Tu PC Windows 11)

1. Ejecuta el asistente de verificación incluido en el repo:
   ```powershell
   cd C:\Tools\video-vfx-ai-bible
   .\scripts\setup_module_c_win11.ps1
   ```
2. Abre **Blender** (con add-on MCP + `TextureSharing` + `scripts\blender_td_osc_bridge.py` cargados) y **TouchDesigner 2025.33230+** (con `TDMCP.tox` activo en `127.0.0.1:13316/mcp` y **Install Skills** ejecutado para Antigravity).
3. Prueba estos **4 Prompts Maestro** en Antigravity:
   - **Prompt 1 (TDMCP):** *"Inspect my TouchDesigner project and verify my `td-*` skills. Inside `/project1/live_vfx`, build a `Spout In TOP` receiving `BlenderCam01`, pass it through an edge-glow GLSL + `Blur TOP`, and show me `view_operator` of the final `null1`."*
   - **Prompt 2 (Blender MCP):** *"Connect to my Blender scene, set up a low-poly sci-fi stage around `(0,0,0)` with EEVEE fast lighting, attach the active camera to a smooth 240-frame orbit track, and verify frame count."*
   - **Prompt 3 (Híbrido Blender Z-Depth ➔ StreamDiffusionTD):** *"In Blender, duplicate my active camera into a depth-pass camera with `TextureSharing` Spout sender `BlenderDepth`. In TouchDesigner, wire `Spout In TOP` (`BlenderDepth`) into my `StreamDiffusionTD` ControlNet depth input and switch `ControlNet` mode to `depth_tensorrt`."*
   - **Prompt 4 (3DGS POPs):** *"In TouchDesigner `/project1`, create a `Point File In POP` pointing to `C:/Assets/scan.ply`, connect a `Noise POP` driven by an `Audio Spectrum CHOP` (`audio_react`), and check `get_cook_performance` to confirm we stay under 16 ms frame time."*
