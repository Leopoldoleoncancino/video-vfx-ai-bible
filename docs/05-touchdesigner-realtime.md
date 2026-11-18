# 05 · TouchDesigner (2025–2026): POPs, POPX, MCP Oficiales & IA en Tiempo Real

**TouchDesigner** dio su mayor salto arquitectónico en **2025–2026** con dos revoluciones simultáneas: el estreno de **POPs (Point Operators)** totalmente ejecutados en GPU y la llegada de **servidores MCP oficiales y comunitarios** con skills dedicadas para que agentes IA construyan, depuren y lean cook-times en vivo dentro del editor.

---

## 1. POPs & POPX (Computación de Partículas y Geometría 100% GPU)

- **TouchDesigner 2025.33230+ POPs:** Nueva familia de operadores de geometría/puntos ejecutada directamente en GPU compute shaders (evitando el clásico cuello de botella de CPU de los SOPs tradicionales). En tu **RTX 3060 12 GB**, puedes manipular millones de puntos, instanciación masiva y campos de fuerza en tiempo real a 60 FPS mientras liberas tu Ryzen 9 5900X.
- **POPX v1.5.0:** Colección comercial/especializada con ~99 operadores sobre POPs para simulaciones físicas GPU y **Aura Render Engine**.

---

## 2. Comparativa de Servidores MCP para TouchDesigner (Verificados Nov 2026)

| Proyecto | Repo Oficial | Stars | Arquitectura & Protocolo | Cuándo elegirlo |
|---|---|---|---|---|
| **Derivative TDMCP** *(Oficial)* | [`TouchDesigner/TDMCP`](https://github.com/TouchDesigner/TDMCP) + [`TDMCPSkills`](https://github.com/TouchDesigner/TDMCPSkills) (★107 / ★46) | 107 | `TDMCP.tox` nativo · **Streamable-HTTP MCP** en `http://127.0.0.1:13316/mcp` (requiere TD `2025.33230+`), **26 tools**, undo nativo, soporte oficial en GUI para **Antigravity**, Claude Code, Claude Desktop (`.mcpb`) y Codex. | **Tu opción #1 por defecto** si quieres estabilidad oficial, soporte de **Antigravity** en `.agents/skills/` con 1 clic (`Pulse Install Skills`) y captura visual del editor. |
| **Embody / Envoy** | [`dylanroscover/Embody`](https://github.com/dylanroscover/Embody) · [`docs`](https://dylanroscover.github.io/Embody/) (MIT) | 222 | `.tox` + **Envoy MCP (70 tools)** + puente `.mcp.json` STDIO + **TDXN** (formato YAML v2.1 para versionar `.toe` en Git!) + **Convoy** (LAN multi-máquina) + `.venv` aislado automático. | **Imprescindible para proyectos serios en Git** o multi-agente paralelo sobre la misma red TouchDesigner. |
| **TouchDesigner MCP** | [`8beeeaaat/touchdesigner-mcp`](https://github.com/8beeeaaat/touchdesigner-mcp) (MIT) | 638 | Puente Node.js (`touchdesigner-mcp-server` en npm) ↔ `WebServer DAT` dentro de TD. | Muy maduro para compatibilidad con versiones anteriores de TD o integraciones Node personalizadas. |
| **td-mcp-rs** *(Rust)* | [`Verbalize-public/td-mcp-rs`](https://github.com/Verbalize-public/td-mcp-rs) (MIT) | 6 | Daemon nativo en Rust + bandeja de sistema + `bootstrap.tox`, direccionamiento explícito entre múltiples instancias TD abiertas. | Si manejas varias instancias simultáneas de TouchDesigner (p. ej. show file vs sandbox de pruebas). |

> ⚠️ **Gotcha crítica en Windows 11 con `TouchDesigner/TDMCP`:**  
> El socket es **IPv4-only**: configura siempre `http://127.0.0.1:13316/mcp` y **NUNCA `http://localhost:13316/mcp`**, o recibirás `Connection refused`. Si usas Claude Desktop, activa **Inline Images (base64)** en la pestaña *Tune* del componente para que el modelo vea las capturas de tus TOPs.

---

## 3. Plugins de IA Generativa, Tracking e Interconexión en Tiempo Real

| Herramienta | Tipo / URL | VRAM (en 3060 12GB) | Uso práctico en tiempo real |
|---|---|---|---|
| **StreamDiffusionTD v0.4.2** (DotSimulate) | `.tox` (`https://dotsimulate.com/tools/streamdiffusiontd`, sobre [`cumulo-autumn/StreamDiffusion`](https://github.com/cumulo-autumn/StreamDiffusion) ★10,837) | ~5–8 GB (`sd-turbo` + TRT `512x512`) | Difusión interactiva en tiempo real (~15–25 FPS @ `512x512` en 3060 con `cuda-link` + `depth_tensorrt`) + modo remoto **RunPod** (*nota:* el antiguo servicio Daydream cerró el 13 nov 2026). |
| **ComfyUI-TD** | [`JiSenHua/ComfyUI-TD`](https://github.com/JiSenHua/ComfyUI-TD) (★167 · AGPL-3.0) | Según flujo ComfyUI | Streaming bidireccional de imágenes, video, modelos 3D, audio y texto entre ComfyUI y TouchDesigner. |
| **MediaPipe TouchDesigner** | [`torinmb/mediapipe-touchdesigner`](https://github.com/torinmb/mediapipe-touchdesigner) (★2,904 · MIT) | ~1–2 GB (GPU) | Tracking de manos, rostro y pose sin hardware externo (webcam) para controlar parámetros TOP/POP en tiempo real. |
| **TD Native Inference** | [`cacheflowe/td-native-inference`](https://github.com/cacheflowe/td-native-inference) | ~1–3 GB (GPU) | Nodos C++ ONNX/TensorRT nativos GPU sin copia CPU: incluye **`DAViDNormals.tox` (~10 ms GPU)** y **`DAViDHuman.tox` (~21 ms Depth+Normals+Matte)** + **`Relight.tox`** PBR. |
| **TouchDiffusion** | [`olegchomp/TouchDiffusion`](https://github.com/olegchomp/TouchDiffusion) (★306) | ~5–7 GB | Referencia open-source de StreamDiffusion en TD (sin mantenimiento activo reciente desde 2024; preferir StreamDiffusionTD o ComfyUI-TD para proyectos nuevos). |
| **Spout2 + NDI** | Integrados de serie en TD Windows (TOP `Spout In/Out`, `NDI In/Out`) | ~0 overhead | **Spout2** comparte texturas GPU en memoria directa a 0 ms entre **TouchDesigner ↔ Blender (`maybites/TextureSharing`) ↔ OBS ↔ Resolume**. **NDI** envía video alfa sobre LAN a Premiere/OBS. |
| **`Web Render TOP`** *(Nativo TD `2025.31550+`)* | Chromium 132.0 integrado + `Use Shared Textures` | ~0.2–1.5 GB según escena WebGL | Ejecuta **animaciones JavaScript (`GSAP`, `Three.js / R3F`, `Rive`, `Lottie`, `p5.js`)** con `background: transparent` a **60 FPS con alpha real** + control bidireccional **CHOP ↔ WebSocket/OSC** (**nota:** usa distinto *User Cache Directory* si abres más de uno; ver [Pilar 07](07-opensource-nles-cli-upscaling.md)). |

---

## 4. Pipeline Recomendado: TouchDesigner + IA Generativa en tu PC

1. **Pre-proceso en vivo (0 difusión pesada):** Usa **MediaPipe TD**, **Z-Depth / Normal Pass por Spout desde Blender**, **`Render TOP` MRT (`# Of Color Buffers = 2`)** o **`DAViDNormals.tox`** (~10 ms GPU), **`Web Render TOP`** (overlays HUD/Three.js/GSAP transparentes a 60 FPS) y **POPs** (`Point File In POP` para `.ply` 3DGS) en GPU.
2. **Estilización interactiva:** Pasa la textura por **StreamDiffusionTD** (`stabilityai/sd-turbo` en 1–2 steps con **TensorRT 10.16** + `depth_tensorrt` / Normal ControlNet) o envía frames clave vía **ComfyUI-TD**.
3. **Grabación Maestra para Post:** Captura mediante `Movie File Out TOP` en **ProRes 4444**, **HAP Q Alpha** o secuencias **EXR 16F** (si exportas Normal/Depth) para llevarlo limpio a **FilmCraft / Premiere / After Effects / EffectCraft**.

> 👉 **Guía práctica completa (Fase 2):** Sigue el paso a paso completo de TDMCP, Embody, StreamDiffusionTD y el puente Spout/OSC con Blender en [`docs/modules/MODULE_C_TD_BLENDER_VFX.md`](modules/MODULE_C_TD_BLENDER_VFX.md) y la guía dedicada de **Capa de Normales Tiempo Real + Post** en [`docs/08-normal-passes-realtime-post.md`](08-normal-passes-realtime-post.md).
