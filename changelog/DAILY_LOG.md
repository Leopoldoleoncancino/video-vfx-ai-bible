# Changelog Diario — Biblia Video IA & VFX

Este archivo registra hitos iniciales y cada hallazgo agregado por el pipeline diario `/automation`.

---

## 2026-11-18 — Edición Fundacional (Fase 1 Completa)

- **Perfil Fijado:** NVIDIA RTX 3060 12 GB VRAM · AMD Ryzen 9 5900X · 32 GB RAM · Windows 11.
- **Pilares Documentados (7 módulos):**
  - `docs/01-local-ai-video-12gb-32gb.md`: Wan 2.2 (5B/14B GGUF), LTX-2.3/2.5 + LTX-Desktop, HunyuanVideo 1.5, FramePack, VACE, Wan2GP (`mmgp`), ComfyUI (`GGUF`, `SageAttention`, `triton-windows`), InfiniteTalk & EchoMimic v3.
  - `docs/02-rotoscoping-matting-chroma-depth.md`: MatAnyone 2 (CVPR 2026), SAM 3, VideoMaMa (CVPR 2026), ComfyUI-RMBG, EffectErase (CVPR 2026), ProPainter, Video Depth Anything, DepthCrafter, Relit-LiVE (SIGGRAPH 2026).
  - `docs/03-artcraft-deep-dive.md`: Enfoque profundo ArtCraft Studio (`storytold/artcraft`) + 17 Rust Crafting Apps (`FilmCraft`, `EffectCraft`, `AniCraft`, `PhotoCraft`, `LightCraft`, `TextureCraft`, `MaterialCraft`, `SoundCraft`, etc.), `.mcp.json` nativo y evaluación honesta de paridad alpha frente a Adobe.
  - `docs/04-adobe-video-deep-dive.md`: Premiere Pro Object Mask & Media Intelligence, MCPs (`premiere-pro-mcp`, `Adobe_Premiere_Pro_MCP`, `opencutagent`, `@kumoproductions/mcp-aftereffects`, `Dakkshin/after-effects-mcp`), frameworks Hyper Brew (`bolt-uxp`, `bolt-cep`, `bolt-express`).
  - `docs/05-touchdesigner-realtime.md`: TouchDesigner 2025+ POPs/POPX, oficial `TouchDesigner/TDMCP` + `TDMCPSkills` (soporte Antigravity), `Embody/Envoy` (TDXN YAML), `touchdesigner-mcp`, `td-mcp-rs`, `StreamDiffusionTD`, `ComfyUI-TD`, `MediaPipe-TD`, Spout2/NDI.
  - `docs/06-blender-3d-vfx-compositing.md`: Oficial Blender MCP (5.1/5.2+), `mcp-for-blender`, `vfx-agent-toolkit`, `ComfyUI-BlenderAI-node`, `TRELLIS.2`, `Hunyuan3D 2.1`, 3DGS (`Kiri-Innovation`, `gsplat`, `spark`), MoCap (`GVHMR`, `FreeMoCap`), `davinci-resolve-mcp`, `Natron`, `OpenTimelineIO`.
  - `docs/07-opensource-nles-cli-upscaling.md`: `OpenCut`, `LosslessCut`, `Shotcut`, `Kdenlive`, aviso Olive pausado, `auto-editor`, `PySceneDetect`, `MoviePy`, `VapourSynth + vs-mlrt`, `Remotion`, `Motion Canvas`, `SeedVR2`, `FlashVSR/FlashVSR+`, `Practical-RIFE`.
- **Automatización Diaria Activa:** GitHub Actions (`.github/workflows/daily-radar.yml`) + `scripts/daily_radar.py` + Guía `/automation` en `automation/ANTIGRAVITY_DAILY_AUTOMATION.md`.
