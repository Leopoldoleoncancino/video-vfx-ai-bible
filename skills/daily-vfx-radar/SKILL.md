---
name: daily-vfx-radar
description: >
  Ejecuta la auditoría diaria del radar de Video IA, VFX, Capa de Normales, Camera Tracking 3D,
  Color OCIO, Audio/Foley IA, OBS MCP, Animaciones JS, ArtCraft, Adobe MCPs, TouchDesigner y Blender,
  filtrando novedades reales por viabilidad en RTX 3060 12 GB + 32 GB RAM + Windows 11.
---

# Daily Video & VFX Radar Skill

## Flujo de Ejecución Diario (`/automation`)
1. **Leer estado más reciente:** inspecciona `AGENTS.md`, `RADAR_DAILY.md` y `data/radar_latest.json` (o ejecuta `python3 scripts/daily_radar.py`).
2. **Clasificar cada hallazgo nuevo según el perfil del usuario:**
   - `[OK-12GB]` Corre nativo, GGUF/INT8 o CPU/WebGL cómodo en RTX 3060 12 GB + Ryzen 9 5900X + 32 GB RAM.
   - `[TIGHT-12GB]` Viable solo con BlockSwap / Tiling / `480p`–`512px` (`NormalCrafter --max-res 512`, `MapAnything minibatch_size=1`) / cierre de otras apps.
   - `[CLOUD / >24GB]` Supera 12 GB VRAM o 32 GB RAM reales; marcar claramente como referencia o nube, no para correr diario en la 3060.
3. **Prioridades Obligatorias de Vigilancia (10 Pilares + JS):**
   - Releases en `storytold/*` (`artcraft`, `filmcraft`, `effectcraft`, `anicraft`, `photocraft`, `lightcraft`, `texturecraft`, `materialcraft`, `soundcraft`).
   - Servidores MCP / UXP / CEP de Adobe (`premiere-pro-mcp`, `mcp-aftereffects`, `opencutagent`, `bolt-uxp`) y OBS (`obs-mcp`, `obs-spout2-plugin`).
   - Ecosistema TouchDesigner (`TDMCP`, `Embody`, `POPs`, `StreamDiffusionTD`, `td-native-inference`).
   - Ecosistema Blender / VFX / Normales / Tracking 3D / ComfyUI EXR (`WanVideoWrapper`, `Lumos-Custom`, `radiance`, `ComfyUI-ACES-IO`, `MatteDesk`, `WiLoR-mini`, `mcp-for-blender`, `vfx-agent-toolkit`, `MatAnyone2`, `sam3`, `EffectErase`, `NormalCrafter`, `StableNormal`, `Lotus`, `MoGe`, `DAViD`, `Depth-Anything-3`, `vggt`, `Pi3`, `co-tracker`, `alltracker`, `SeedVR2`, `FlashVSR`).
   - Color & Audio IA (`OpenColorIO`, `MMAudio`, `whisperX`, `chatterbox`, `F5-TTS`, `kokoro`, `LivePortrait`, `DeepFilterNet`).
   - Video-as-Code & Animaciones JS (`remotion`, `motion-canvas`, `GSAP`, `three.js`, `rive-wasm`).
4. **Regla de Calidad y Mantenimiento del Repo:**
   - Nunca agregues enlaces sin verificar que existen ni inventes tasas de FPS o requisitos de VRAM.
   - Mantén alineados `AGENTS.md`, `README.md`, `changelog/DAILY_LOG.md` y valida sintaxis JSON (`mcps/*.json`, `data/*.json`, `workflows/comfyui/*.json`), Python (`scripts/*.py`) y enlaces/tablas Markdown antes de hacer commit.
