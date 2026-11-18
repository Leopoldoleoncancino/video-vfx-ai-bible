---
name: artcraft-adobe-vfx-bridge
description: >
  Orquesta flujos híbridos de edición, motion graphics, animaciones JavaScript y automatización entre
  ArtCraft Studio / FilmCraft / EffectCraft (Rust + MCP + Lottie/JSON), JavaScript (Remotion/GSAP/Three.js/Web Render TOP)
  y Adobe Premiere Pro / After Effects (MCP + UXP/CEP + ProRes 4444 + EXR Normals).
---

# ArtCraft ↔ JavaScript ↔ Adobe Hybrid Production Bridge Skill

## Matriz de Decisión Rápida
- **Prototipado rápido por código/agente, versionado en Git o exportación Web/Lottie:** usa **EffectCraft** (`effectcraft-cli mcp --bridge 9877`, formato `.ecproj` + `.lottie` nativo) y **FilmCraft** (`filmcraft-cli mcp --bridge 127.0.0.1:9876`).
- **Motion graphics programático JS / HUDs / Gráficos de datos / 3D WebGL (0 GB VRAM IA):**
  - *Video offline con transparencia:* **Remotion** (`npx remotion render MyComp out/overlay.mov --codec=prores --prores-profile=4444 --image-format=png --pixel-format=yuva444p10le`) o **Motion Canvas** / **GSAP** / **Anime.js** / **Three.js + Theatre.js** capturados vía Playwright RGBA ➔ `ConvertTo-ProRes4444Alpha` (`scripts/ffmpeg_nvenc_prores_helpers.ps1`).
  - *Tiempo real 60 FPS en vivo:* carga HTML/CSS `background: transparent` con **GSAP / Three.js / Rive / Lottie / p5.js** dentro de **`Web Render TOP`** (Chromium 132.0 en TouchDesigner `2025.31550+`, asignando un *User Cache Directory* distinto por instancia).
- **Previs de planos 3D/2D con modelos IA o posing:** usa **ArtCraft Studio** (`storytold/artcraft`).
- **Entrega comercial final, Color/Lumetri, MOGRTs complejos o plugins terceros:** usa **Adobe Premiere Pro** (`leancoderkavy/premiere-pro-mcp` o `Open Cut Agent`) y **After Effects** (`@kumoproductions/mcp-aftereffects` por Undo atómico, preview frame IPC y generación de **Expresiones JavaScript ES6+ nativas**).

## Reglas de Intercambio Limpio (Sin Halos ni Ejes Invertidos)
1. **Canales Alpha entre IA / JS / EffectCraft / After Effects / Premiere:**
   - Exporta siempre **ProRes 4444 (`yuva444p10le`, Alpha Straight / Unmatted)** o secuencias **EXR 16-bit half-float / PNG 16-bit**.
   - En After Effects verifica `Interpret Footage -> Alpha: Straight - Unmatted`.
2. **Capas de Normales para Relighting entre Blender / IA / AE / Resolve:**
   - Usa **Camera / View Space**, convención **OpenGL (`+Y` arriba)** y **EXR 16F/32F lineal** (`Raw / Non-Color`). Nunca H.264 8-bit.
   - Si algún pase proviene de motor DirectX (`-Y`), invierte únicamente el verde (`G = 1.0 - G`). Compatible directo con DaVinci Resolve `ReLight` (puerto *Normals*) y After Effects `Normality` (32-bpc).
3. **Motion Vectorial Reversible:**
   - Genera motion procedural en **EffectCraft** (o **Remotion** / **Motion Canvas** / **lottie-web**), exporta **Lottie JSON (`.json` / `.lottie`)** e impórtalo en AE, o usa `@kumoproductions/mcp-aftereffects` para crear Shape Layers nativos agrupados en un solo paso Undo.
4. **Advertencia de Paridad:**
   - Nunca asumas que FilmCraft o EffectCraft abren archivos `.prproj` / `.aep` ni cargan plugins `.aex`/OpenFX propietarios: cuando necesites abrir proyectos de clientes Adobe, quédate en Adobe o exporta XML/OTIO (`OpenTimelineIO`) + renders stem.
