---
name: artcraft-adobe-vfx-bridge
description: >
  Orquesta flujos híbridos de edición, motion graphics y automatización entre ArtCraft Studio / FilmCraft / EffectCraft
  (Rust + MCP + Lottie/JSON) y Adobe Premiere Pro / After Effects (MCP + UXP/CEP + ProRes 4444).
---

# ArtCraft ↔ Adobe Hybrid Production Bridge Skill

## Matriz de Decisión Rápida
- **Prototipado rápido por código/agente, versionado en Git o exportación Web/Lottie:** usa **EffectCraft** (`effectcraft-cli mcp --bridge 9877`, formato `.ecproj` + `.lottie` nativo) y **FilmCraft** (`filmcraft-cli mcp --bridge 127.0.0.1:9876`).
- **Previs de planos 3D/2D con modelos IA o posing:** usa **ArtCraft Studio** (`storytold/artcraft`).
- **Entrega comercial final, Color/Lumetri, MOGRTs complejos o plugins terceros:** usa **Adobe Premiere Pro** (`leancoderkavy/premiere-pro-mcp` o `Open Cut Agent`) y **After Effects** (`@kumoproductions/mcp-aftereffects` por sus operaciones con Undo atómico y preview frame IPC).

## Reglas de Intercambio Limpio (Sin Halos ni Desfases)
1. **Canales Alpha entre IA / EffectCraft / After Effects / Premiere:**
   - Exporta siempre **ProRes 4444 (`yuva444p10le`, Alpha Straight / Unmatted)** o secuencias **EXR 16-bit half-float / PNG 16-bit**.
   - En After Effects verifica `Interpret Footage -> Alpha: Straight - Unmatted`.
2. **Motion Vectorial Reversible:**
   - Genera motion procedural en **EffectCraft** (o **Remotion** / **Motion Canvas**), exporta **Lottie JSON (`.json` / `.lottie`)** e impórtalo en AE, o usa `@kumoproductions/mcp-aftereffects` para crear Shape Layers nativos agrupados en un solo paso Undo.
3. **Advertencia de Paridad:**
   - Nunca asumas que FilmCraft o EffectCraft abren archivos `.prproj` / `.aep` ni cargan plugins `.aex`/OpenFX propietarios: cuando necesites abrir proyectos de clientes Adobe, quédate en Adobe o exporta XML/OTIO (`OpenTimelineIO`) + renders stem.
