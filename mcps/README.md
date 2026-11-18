# Plantillas MCP Verificadas para Windows 11 (Video, VFX, 3D, ArtCraft & Adobe)

Todos los bloques de esta carpeta han sido verificados contra los repositorios oficiales fuente en GitHub (Noviembre 2026). Adapta únicamente las rutas `C:\\...` a tu usuario de Windows 11.

> ⚠️ **Regla importante de VRAM/RAM (RTX 3060 12 GB + 32 GB RAM):**  
> No conectes ni dispares simultáneamente servidores que carguen modelos pesados en VRAM (p. ej. no lances ComfyUI Wan 2.2 mientras Premiere/After Effects/Blender y TouchDesigner tienen proyectos pesados abiertos). Usa perfiles MCP separados o cierra la app pesada previa.

---

## Inventario de Configs Incluidas

1. [`win11_unified_mcp_config.json`](win11_unified_mcp_config.json) — Plantilla maestra combinada (Blender, ComfyUI, TouchDesigner TDMCP, DaVinci Resolve, Premiere Pro, After Effects, EffectCraft, FilmCraft).
2. [`artcraft_adobe_mcp.json`](artcraft_adobe_mcp.json) — Perfil enfocado específicamente en **ArtCraft (EffectCraft/FilmCraft) + Adobe (Premiere/After Effects)**.

---

## Notas Rápidas de Activación en Windows 11

### 1. TouchDesigner Oficial (`TouchDesigner/TDMCP`)
- Requiere TouchDesigner **2025.33230+** con `TDMCP.tox` arrastrado a `/project1` y `Active = On`.
- Sirve **Streamable-HTTP** en `http://127.0.0.1:13316/mcp` (usa siempre `127.0.0.1`, nunca `localhost`).
- En GUI del componente, cambia `Install For` a **Antigravity** (o Claude Code / Codex) y pulsa **Install Skills** para poblar `.agents/skills/td-*`.
- Alternativa comunitaria avanzada con YAML Git diffs: [`dylanroscover/Embody`](https://github.com/dylanroscover/Embody) (Envoy autogenera su `.mcp.json` en tu carpeta de proyecto).

### 2. ArtCraft (`storytold/effectcraft` & `storytold/filmcraft`)
- Puedes correr en modo headless (`--demo`) para prototipar JSON/renders sin abrir ventana, o en modo conectado (`--bridge 9877` en EffectCraft / `--bridge 127.0.0.1:9876` en FilmCraft) para ver los cambios en tiempo real.
- Compila binarios Windows una vez (`cargo build --release`) para arranque instantáneo en lugar de `cargo run` cada vez.

### 3. Adobe After Effects (`kumoproductions/mcp-aftereffects` / `Dakkshin/after-effects-mcp`)
- Activa **Edit → Preferences → Scripting & Expressions → Allow Scripts to Write Files and Access Network**.
- En `Dakkshin/after-effects-mcp`, ejecuta `Window > mcp-bridge-auto.jsx` dentro de AE y marca `Auto-run commands`.
- En `@kumoproductions/mcp-aftereffects`, obtienes operaciones agrupadas en Undo atómico y preview single-frame por file IPC.

### 4. Adobe Premiere Pro (`leancoderkavy/premiere-pro-mcp` / `leonardogrig/opencutagent`)
- Instala el puente CEP (`MCPBridgeCEP.zxp`) o UXP y habilita `PlayerDebugMode = 1` en el registro `HKCU\Software\Adobe\CSXS.11` / `.12` para extensiones sin firmar.
- Si tu cliente MCP falla en `server/discover`, agrega `"env": {"PREMIERE_MCP_PROTOCOL_MODE": "legacy"}`.

### 5. Blender (`ahujasid/mcp-for-blender` o Oficial `blender.org/lab/mcp-server/`)
- Instala `uv` en Windows (`winget install astral-sh.uv`).
- Activa el add-on oficial de Blender Lab (Blender 5.1/5.2+) o `addon.py` en puerto `9876` para `uvx mcp-for-blender`.

### 6. ComfyUI (`Comfy-Org/comfy-mcp`)
- Instala `pip install comfy-cli comfy-mcp` dentro de tu venv de ComfyUI.
- Apunta `COMFY_BIN` hacia `C:\\AI\\ComfyUI\\venv\\Scripts\\comfy.exe`.

### 7. DaVinci Resolve (`samuelgursky/davinci-resolve-mcp`)
- Requiere **DaVinci Resolve Studio** (el scripting IPC externo está restringido en la versión gratuita).
- Configura `RESOLVE_SCRIPT_API` y `RESOLVE_SCRIPT_LIB` apuntando a `C:\\ProgramData\\Blackmagic Design\\DaVinci Resolve\\Support\\Developer\\Scripting`.
