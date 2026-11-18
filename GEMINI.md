# GEMINI.md — Instrucciones para Google Antigravity & Gemini Agents

Al trabajar sobre `Leopoldoleoncancino/video-vfx-ai-bible`:

1. **Lee obligatoriamente [`AGENTS.md`](AGENTS.md) y [`README.md`](README.md)** antes de proponer modelos, nodos, shaders, animaciones o comandos MCP.
2. **Carga el skill adecuado según el dominio** desde [`skills/`](skills/) (o desde tu directorio global `~/.gemini/skills/`):
   - [`video-vfx-3060-12gb-local`](skills/video-vfx-3060-12gb-local/SKILL.md) — hardware RTX 3060 12 GB / 32 GB RAM / Win 11, 10 pilares: modelos locales, roto/matting, Módulo C TD/Blender, Pilar 08 normales, Pilar 09 Camera Tracking 3D, Pilar 10 OCIO/Audio/Face/OBS y offload JS en CPU.
   - [`artcraft-adobe-vfx-bridge`](skills/artcraft-adobe-vfx-bridge/SKILL.md) — ArtCraft (FilmCraft/EffectCraft), Adobe (Premiere/After Effects MCP/UXP/CEP), Lottie, ProRes 4444 Alpha, EXR lineal y animaciones JS.
   - [`daily-vfx-radar`](skills/daily-vfx-radar/SKILL.md) — auditoría diaria con [`RADAR_DAILY.md`](RADAR_DAILY.md) y [`scripts/daily_radar.py`](scripts/daily_radar.py).
3. **Configuración MCP específica de Antigravity:** para `TouchDesigner/TDMCP` usa **siempre `"serverUrl": "http://127.0.0.1:13316/mcp"`** (nunca `"url"` ni `localhost`). Usa la plantilla [`mcps/antigravity_td_blender_mcp.json`](mcps/antigravity_td_blender_mcp.json).
4. **Regla de verificación:** antes de recomendar novedades posteriores a la fecha del repositorio, revisa primero [`RADAR_DAILY.md`](RADAR_DAILY.md) y valida enlaces reales antes de escribir docs o configuraciones.
