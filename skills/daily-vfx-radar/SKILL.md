---
name: daily-vfx-radar
description: >
  Ejecuta la auditoría diaria del radar de Video IA, VFX, ArtCraft, Adobe MCPs, TouchDesigner y Blender,
  filtrando novedades reales por viabilidad en RTX 3060 12 GB + 32 GB RAM + Windows 11.
---

# Daily Video & VFX Radar Skill

## Flujo de Ejecución Diario (`/automation`)
1. **Leer estado más reciente:** inspecciona `RADAR_DAILY.md` y `data/radar_latest.json` (o ejecuta `python3 scripts/daily_radar.py`).
2. **Clasificar cada hallazgo nuevo según el perfil del usuario:**
   - `[OK-12GB]` Corre nativo o GGUF/FP8/INT8 cómodo en RTX 3060 12 GB + 32 GB RAM.
   - `[TIGHT-12GB]` Viable solo con BlockSwap / Tiling / 480p / cierre de otras apps.
   - `[CLOUD / >24GB]` Supera 12 GB VRAM o 32 GB RAM reales; marcar claramente como referencia o nube, no para correr diario en la 3060.
3. **Prioridades Obligatorias de Vigilancia:**
   - Releases en `storytold/*` (`artcraft`, `filmcraft`, `effectcraft`, `anicraft`, `texturecraft`, `materialcraft`, `soundcraft`).
   - Servidores MCP / UXP / CEP de Adobe (`premiere-pro-mcp`, `mcp-aftereffects`, `opencutagent`, `bolt-uxp`).
   - Ecosistema TouchDesigner (`TDMCP`, `Embody`, `POPs`, `StreamDiffusionTD`).
   - Ecosistema Blender / VFX (`mcp-for-blender`, `vfx-agent-toolkit`, `MatAnyone2`, `sam3`, `EffectErase`, `SeedVR2`, `FlashVSR`).
4. **Regla de Calidad:**
   - Nunca agregues enlaces sin verificar que existen o no inventes tasas de FPS.
   - Mantén los archivos JSON en `mcps/` y scripts en `scripts/` sintácticamente validados antes de hacer commit.
