# CLAUDE.md — Instrucciones para Claude Code & Claude Desktop

Cuando leas o trabajes sobre `Leopoldoleoncancino/video-vfx-ai-bible`:

1. **Punto de entrada obligatorio:** lee [`AGENTS.md`](AGENTS.md) y [`README.md`](README.md) completos antes de responder o generar código.
2. **Respeta el perfil físico del usuario:** NVIDIA **RTX 3060 12 GB VRAM (Ampere, sin FP8 Tensor Core)** · **Ryzen 9 5900X** · **32 GB RAM (~22–24 GB libres en Windows 11)**. Usa GGUF `Q4_K_M`/`Q5_K_M` o INT8 (`mmgp`), evita cargar dos apps GPU pesadas simultáneamente y descarga motion graphics a **JavaScript / Rust** cuando no requieran difusión.
3. **Navega directo al documento correcto:**
   - Video IA Local: [`docs/01-local-ai-video-12gb-32gb.md`](docs/01-local-ai-video-12gb-32gb.md)
   - Roto, Matting, Depth & Relighting: [`docs/02-rotoscoping-matting-chroma-depth.md`](docs/02-rotoscoping-matting-chroma-depth.md)
   - ArtCraft (Rust + MCP): [`docs/03-artcraft-deep-dive.md`](docs/03-artcraft-deep-dive.md)
   - Adobe (Premiere / AE MCP + UXP/CEP): [`docs/04-adobe-video-deep-dive.md`](docs/04-adobe-video-deep-dive.md)
   - TouchDesigner (`TDMCP`, `Embody`, POPs, `Web Render TOP`): [`docs/05-touchdesigner-realtime.md`](docs/05-touchdesigner-realtime.md) & [`docs/modules/MODULE_C_TD_BLENDER_VFX.md`](docs/modules/MODULE_C_TD_BLENDER_VFX.md)
   - Blender, 3DGS, MoCap & Resolve: [`docs/06-blender-3d-vfx-compositing.md`](docs/06-blender-3d-vfx-compositing.md)
   - NLEs Open-Source, CLI, **Animaciones JS**, VSR & RIFE: [`docs/07-opensource-nles-cli-upscaling.md`](docs/07-opensource-nles-cli-upscaling.md)
   - **Capa de Normales (Tiempo Real + Post)**: [`docs/08-normal-passes-realtime-post.md`](docs/08-normal-passes-realtime-post.md)
4. **Plantillas MCP para Claude:** usa `"url"` HTTP estándar o STDIO en [`mcps/win11_unified_mcp_config.json`](mcps/win11_unified_mcp_config.json) y [`mcps/artcraft_adobe_mcp.json`](mcps/artcraft_adobe_mcp.json) (y para `TouchDesigner/TDMCP` recuerda IPv4 `127.0.0.1:13316` + *Inline Images base64*).
5. **Estado actualizado:** consulta [`RADAR_DAILY.md`](RADAR_DAILY.md) y [`changelog/DAILY_LOG.md`](changelog/DAILY_LOG.md) antes de asumir versiones de modelos o releases.
