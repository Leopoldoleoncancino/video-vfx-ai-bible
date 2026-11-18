# 04 · Enfoque Profundo: Adobe Video (Premiere Pro & After Effects — IA Nativa, MCPs, UXP/CEP y Puentes)

A diferencia de aplicaciones nativas en Rust como ArtCraft, automatizar **Adobe Premiere Pro** y **Adobe After Effects** en Windows 11 requiere entender sus **dos motores de extensibilidad** (**CEP + ExtendScript `.jsx`** clásico vs **UXP** moderno en Premiere) y cómo los **servidores MCP** se conectan por debajo.

---

## 1. Herramientas IA Nativas de Adobe (2025–2026) que YA Corren sin Plugins

Antes de añadir scripts pesados, aprovecha lo que Adobe integró nativamente en Desktop (2025.6–2026):

| Aplicación | Herramienta Nativa (2026) | Dónde vive | Caso de uso y límite real |
|---|---|---|---|
| **Premiere Pro** | **Object Mask Tool** | Barra de herramientas → Object Mask (hover rojo + Track) | Sustituye el 70% de máscaras simples (*texto detrás de sujeto*, *color selectivo*) sin enviar a After Effects. Para cabello fino o transparencia extrema, sigue siendo inferior a `MatAnyone 2` o `Roto Brush 3`. |
| **Premiere Pro** | **Media Intelligence** | Panel Search (búsqueda visual + transcripción local) | Indexa localmente tus horas de metraje sin subir video a la nube; ideal combinado con clips generados localmente en Wan/LTX. |
| **Premiere Pro** | **Generative Extend** & **Generative Remove (beta)** | Edge drag en timeline / Effect Controls | Usa nube Firefly (créditos); úsalo solo cuando necesites 1–2s extra de reacción sin querer renderizar otro plano en ComfyUI. |
| **After Effects** | **Roto Brush 3** + **Content-Aware Fill** | Layer Panel | Muy bueno en cortes limpios; si falla con reflejos/sombras de piso, usa [`FudanCVL/EffectErase`](https://github.com/FudanCVL/EffectErase) fuera de AE e importa el clean-plate. |

---

## 2. Ecosistema de Servidores MCP para Adobe (Verificados Nov 2026)

### A. Adobe Premiere Pro MCPs

1. **[`leancoderkavy/premiere-pro-mcp`](https://github.com/leancoderkavy/premiere-pro-mcp)** (★550 · v1.31.0 · MIT · `premiere-pro-mcp.com`)
   - **El más completo técnicamente hoy:** **453 herramientas**, *MOGRT Studio* con guardrails para After Effects, **puente híbrido CEP (`MCPBridgeCEP.zxp`) + UXP**, e inventarios reales de API Adobe (`adobe-api-inventory.json`).
   - **Protocolo moderno:** Usa TypeScript SDK v2 (especificación `2026-07-28` con HTTP/stdio + compatibilidad legacy `PREMIERE_MCP_PROTOCOL_MODE=legacy` si tu cliente no soporta `server/discover`).
2. **[`hetpatel-11/Adobe_Premiere_Pro_MCP`](https://github.com/hetpatel-11/Adobe_Premiere_Pro_MCP)** (★896 · MIT)
   - Popular y ligero para edición impulsada por agente (`premiere-pro-mcp` CLI + `.mcpb`).
3. **[`leonardogrig/opencutagent`](https://github.com/leonardogrig/opencutagent)** (**Open Cut Agent** · puerto `3001`)
   - Panel CEP + servidor Node diseñado específicamente para **edición de timeline en vivo: eliminar silencios y retakes automáticamente** desde el agente.
   - Instalación rápida: `npm run setup` + `npm start` (ocupa TCP `3001`, ver [`mcps/`](../mcps/README.md)).

### B. Adobe After Effects MCPs

1. **[`kumoproductions/mcp-aftereffects`](https://github.com/kumoproductions/mcp-aftereffects)** (★186 · MIT · `@kumoproductions/mcp-aftereffects` v0.3.2)
   - **Arquitectura más segura para producción:**
     - **Operaciones agrupadas en Undo atómico** (un `Ctrl+Z` revierte todo lo que hizo el agente).
     - Introspección profunda de proyecto/composiciones/capas/efectos/máscaras/expresiones.
     - **Importación y exportación de composiciones a JSON** (puente perfecto hacia EffectCraft/Git!).
     - **Render de preview single-frame por file IPC** para que el agente *vea* el frame antes de seguir.
2. **[`Dakkshin/after-effects-mcp`](https://github.com/Dakkshin/after-effects-mcp)** (★898 · MIT)
   - El servidor pionero más conocido: ejecuta comandos mediante ExtendScript via `Window > mcp-bridge-auto.jsx` (activar casilla *"Auto-run commands"*). Fácil de clonar y extender con tus propios `.jsx`.
   - También tiene forks mejorados como [`a-y-ibrahim/after-effects-mcp`](https://github.com/a-y-ibrahim/after-effects-mcp).

> ⚠️ **Regla crítica de seguridad en Windows 11 con CEP/ExtendScript MCPs:**  
> Para cargar extensiones CEP locales sin firmar en Windows 11 necesitas habilitar `PlayerDebugMode = 1` en el registro `HKEY_CURRENT_USER\Software\Adobe\CSXS.11` (y `.12`), y en After Effects activar **Edit → Preferences → Scripting & Expressions → Allow Scripts to Write Files and Access Network**.

---

## 3. Frameworks de Desarrollo de Plugins Propios (UXP & CEP — Hyper Brew)

Si quieres construir tus propios paneles de IA en Premiere Pro o After Effects (conectando directamente tu **ComfyUI local `127.0.0.1:8188`** o **Wan2GP** dentro de Adobe), utiliza los frameworks gratuitos de **Hyper Brew** (respaldados oficialmente por Adobe Developer Fund):

| Framework | Repo GitHub | Para qué sirve | Stack |
|---|---|---|---|
| **Bolt UXP** | [`hyperbrew/bolt-uxp`](https://github.com/hyperbrew/bolt-uxp) (★207 · MIT · v1.3) | Crear **plugins UXP modernos en Premiere Pro**, Photoshop, Media Encoder | Svelte / React / Vue + Vite + TypeScript + Sass + Hot Reload |
| **Bolt CEP** | [`hyperbrew/bolt-cep`](https://github.com/hyperbrew/bolt-cep) (★516 · MIT) | Crear **extensiones CEP en After Effects** y Premiere clásico (acceso completo a Node.js + ExtendScript) | Svelte / React / Vue + Vite + TS |
| **Bolt Express** | [`hyperbrew/bolt-express`](https://github.com/hyperbrew/bolt-express) (★10 · v1.2) | Add-ons para Adobe Express | Vite + TS + GitHub Actions packager |
| **AE Command IDs** | [`hyperbrew/after-effects-command-ids`](https://github.com/hyperbrew/after-effects-command-ids) | Referencia exacta de IDs numéricos para disparar menús ocultos de AE desde scripts/MCPs | JSON + Visor interactivo |

---

## 4. Workflows Puentes: Adobe ↔ IA Local (3060 12GB) ↔ ArtCraft

### Workflow A: ComfyUI / MatAnyone 2 ➔ After Effects sin Fringes (Halos)
1. En Premiere, exporta tu clip de origen o selecciona *"Reveal in Explorer"*.
2. Procesa fuera de Adobe (para liberar VRAM de la 3060!) usando **MatAnyone 2** o **ComfyUI SAM 3 + VideoMaMa**.
3. Guarda como **ProRes 4444 (`Straight / Unmatted`)** o secuencia **EXR 16-bit half-float**.
4. Importa en AE y **asegúrate en Interpret Footage → Alpha: Straight - Unmatted**.

### Workflow B: Edición de Guion/Retakes ➔ Render IA ➔ Montaje Final
1. Corre [`WyattBlue/auto-editor`](https://github.com/WyattBlue/auto-editor) o **`Open Cut Agent`** en Premiere para limpiar silencios y errores de cámara.
2. Exporta **FCP XML / OTIO** ([`OpenTimelineIO`](https://github.com/AcademySoftwareFoundation/OpenTimelineIO)) o selecciona los huecos (*B-roll slots*).
3. Genera insertos B-roll de 5s en **Wan2GP (`Wan 2.2`)** o **LTX-2.3** mientras Premiere está cerrado, escálalos con **SeedVR2** + **RIFE**, y vuelve a colocarlos automáticamente usando **`premiere-pro-mcp`**.

### Workflow C: Motion Procedural por Agente (EffectCraft / JavaScript / Lottie / AE)
1. Pide al agente que genere gráficos vectoriales/UI animados en **EffectCraft** (exporta `.lottie` / Lottie JSON), **Remotion** (`--codec=prores --prores-profile=4444 --pixel-format=yuva444p10le`), **Motion Canvas** o **GSAP / Three.js** (ver [Pilar 07](07-opensource-nles-cli-upscaling.md#3-video-como-c%C3%B3digo--animaciones-javascript-offline-prores-4444-y-tiempo-real-60-fps)).
2. Carga el Lottie JSON en After Effects vía plugins Lottie/Bodymovin, importa el MOV ProRes 4444 (`Straight - Unmatted`), o haz que `@kumoproductions/mcp-aftereffects` construya Shape Layers y **Expresiones JavaScript ES6+ nativas** de AE en un solo Undo atómico.
