# GEMINI.md — Instrucciones para Google Antigravity & Gemini Agents

Al trabajar sobre `Leopoldoleoncancino/video-vfx-ai-bible`:

1. **Lee obligatoriamente [`AGENTS.md`](AGENTS.md) y [`README.md`](README.md)** antes de proponer modelos, nodos, shaders, animaciones o comandos MCP.
2. **Puntos de entrada rápidos de Producción VFX (Fase 2.5):**
   - **Módulo A (ComfyUI `sm_86` + Fluido GPU Incompresible + PBR `SSDO` + Oclusión Z Continua + `33f ➔ 167f`):** [`docs/modules/MODULE_A_COMFYUI_VFX_3060.md`](docs/modules/MODULE_A_COMFYUI_VFX_3060.md) · [`scripts/vfx_incompressible_fire_sim.py`](scripts/vfx_incompressible_fire_sim.py) · [`workflows/comfyui/README.md`](workflows/comfyui/README.md) · [`Workflow 4 · Ruta G`](workflows/END_TO_END_PIPELINES.md#workflow-4--fuego--energía-hiperrealista-adherido-a-anatomía-con-capa-de-normales-7-rutas-comparadas--rd-33f--167f).
   - **Módulo C (TouchDesigner + Blender Live):** [`docs/modules/MODULE_C_TD_BLENDER_VFX.md`](docs/modules/MODULE_C_TD_BLENDER_VFX.md).
3. **Carga el skill adecuado según el dominio** desde [`skills/`](skills/) (o desde tu directorio global `~/.gemini/skills/`):
   - [`video-vfx-3060-12gb-local`](skills/video-vfx-3060-12gb-local/SKILL.md) — hardware RTX 3060 12 GB `sm_86` / 32 GB RAM / Win 11, 10 pilares, **Módulo A Fase 2.5** (`VRAM_Debug`, `vfx_incompressible_fire_sim.py`, `SSDO` MIP Area-Light, `WiLoR-mini` MANO Estanco, `vfx_rd_metrics_eval.py` Gates 0–3) & **Módulo C**, y offload JS en CPU.
   - [`artcraft-adobe-vfx-bridge`](skills/artcraft-adobe-vfx-bridge/SKILL.md) — ArtCraft (FilmCraft/EffectCraft), Adobe (Premiere/After Effects MCP/UXP/CEP), Lottie, ProRes 4444 Alpha, EXR lineal y animaciones JS.
   - [`daily-vfx-radar`](skills/daily-vfx-radar/SKILL.md) — auditoría diaria con [`RADAR_DAILY.md`](RADAR_DAILY.md) y [`scripts/daily_radar.py`](scripts/daily_radar.py).
4. **Configuración MCP específica de Antigravity:** para `TouchDesigner/TDMCP` usa **siempre `"serverUrl": "http://127.0.0.1:13316/mcp"`** (nunca `"url"` ni `localhost`). Usa la plantilla [`mcps/antigravity_td_blender_mcp.json`](mcps/antigravity_td_blender_mcp.json).
5. **Regla de verificación:** antes de recomendar novedades posteriores a la fecha del repositorio, revisa primero [`RADAR_DAILY.md`](RADAR_DAILY.md) y valida enlaces/kernels reales en `docs/` antes de escribir código o configs.
