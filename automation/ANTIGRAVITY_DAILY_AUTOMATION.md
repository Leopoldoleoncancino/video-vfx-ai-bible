# Guía Completa de Automatización Diaria (`/automation`)

Esta guía implementa exactamente tu objetivo de **`/automation` diario** con una arquitectura híbrida en **3 capas** (sin depender de que tu PC esté encendido para recopilar noticias ni de recordar hacerlo a mano):

1. **Capa Cloud Automática (GitHub Actions — cero intervención manual):** [`daily-radar.yml`](../.github/workflows/daily-radar.yml) se ejecuta todos los días a las **12:00 UTC (06:00 AM CST)**, consulta GitHub + Hugging Face Hub, y actualiza [`RADAR_DAILY.md`](../RADAR_DAILY.md) y [`data/radar_latest.json`](../data/radar_latest.json).
2. **Capa Agéntica con Análisis Profundo (Antigravity `/automation`):** Un task programado en Antigravity (o ejecutado manualmente en la nube sobre tu proyecto) que lee `RADAR_DAILY.md`, evalúa compatibilidad real con **RTX 3060 12GB + Ryzen 9 5900X + 32GB RAM + Windows 11**, verifica nuevos MCPs/skills/releases de **ArtCraft** y **Adobe**, y abre un Pull Request o commit estructurado en los documentos `docs/`.
3. **Capa Local Windows 11 (Sync + Notificación en tu PC):** Un script/tarea programada en Windows 11 (`Task Scheduler`) que hace `git pull` cada mañana y deja tu copia local de `skills/` y `mcps/` sincronizada.

---

## Parte 1 — Cómo configurar la Automatización Nativa en Antigravity (`/automation`)

> **Nota de transparencia técnica:** Desde este agente remoto en VM no existe una herramienta CLI para registrar cron jobs en tu cuenta de Antigravity por ti; debes crear el task desde tu interfaz de **Antigravity → Automations / `/automation`** (1 minuto) usando los parámetros exactos de abajo.

### Configuración recomendada en Antigravity
- **Nombre de la tarea:** `Biblia Video IA & VFX — Radar Diario (3060 12GB)`
- **Repositorio conectado al proyecto:** `Leopoldoleoncancino/video-vfx-ai-bible`
- **Frecuencia (Schedule):** `Daily` (todos los días, sugerido `07:30 AM` hora local, 90 min después del GitHub Action de las 06:00 AM)
- **Plugins recomendados activos:** `github` (obligatorio), `gdocs` / `gdrive` (opcional si deseas resumen en Google Docs)

### Prompt exacto para copiar y pegar en `/automation`

```text
Ejecuta la actualización diaria de nuestra "Biblia de Herramientas de Video IA y VFX" en el repositorio conectado (Leopoldoleoncancino/video-vfx-ai-bible).

Contexto fijo de hardware y entorno:
- GPU: NVIDIA RTX 3060 12 GB VRAM
- CPU: AMD Ryzen 9 5900X | RAM: 32 GB | OS: Windows 11
- Prioridades especiales: ArtCraft (storytold/*, FilmCraft, EffectCraft, AniCraft, etc.), Adobe (Premiere Pro & After Effects MCP/UXP/CEP), TouchDesigner (TDMCP/Embody/POPs), Blender VFX/MCP, IA Video local cuantizada (GGUF/FP8/mmgp), Rotoscopia/Matting (MatAnyone 2, SAM 3, VideoMaMa), y Open Source CLI/VSR.

Pasos obligatorios:
1. Lee RADAR_DAILY.md y data/radar_latest.json (o ejecuta `python3 scripts/daily_radar.py` si tienen más de 24h de antigüedad).
2. Busca en la web/GitHub novedades de las últimas 24-48 horas sobre:
   - Nuevos modelos/pesos cuantizados aptos para <=12GB VRAM y <=32GB RAM (Wan, LTX, Hunyuan, FramePack, FlashVSR, SeedVR2, MatAnyone, SAM).
   - Releases y avances de paridad en storytold/artcraft, effectcraft y filmcraft.
   - Nuevos MCP servers, plugins UXP/CEP o skills para Adobe Premiere Pro, After Effects, TouchDesigner, Blender y DaVinci Resolve.
   - Nuevas versiones de Kdenlive, Shotcut, OpenCut, LosslessCut, auto-editor, Natron y ComfyUI nodes críticos.
3. Filtra cualquier herramienta que NO corra localmente en 12GB VRAM / 32GB RAM (márcala claramente como "Solo Cloud o >24GB VRAM / No viable en 3060 12GB sin cuantización extrema").
4. Actualiza la sección correspondiente en `docs/` y añade la ficha del día en `changelog/DAILY_LOG.md` con enlace verificado, licencia, requisito VRAM/RAM y si tiene MCP/CLI.
5. Si detectas una nueva config `.mcp.json` o script útil, añádelo a `mcps/` o `scripts/` y valida sintaxis JSON/Python.
6. Crea una rama `radar/YYYY-MM-DD`, haz commit de los cambios y abre un Pull Request (o haz push directo si estás autorizado) con un resumen ejecutivo de 5 puntos en español.
```

---

## Parte 2 — Activación de GitHub Actions en tu Repositorio

El workflow ya está incluido en [`.github/workflows/daily-radar.yml`](../.github/workflows/daily-radar.yml). Para probarlo hoy mismo sin esperar a mañana:
1. Entra a `https://github.com/Leopoldoleoncancino/video-vfx-ai-bible/actions`
2. Selecciona **Daily Video & VFX AI Radar** → **Run workflow** → ejecuta sobre `main`.
3. En ~30 segundos verás actualizado [`RADAR_DAILY.md`](../RADAR_DAILY.md).

*(Si GitHub desactiva Actions por inactividad después de 60 días sin commits manuales, un clic en "Enable workflow" lo reactiva).*

---

## Parte 3 — Sincronización Automática en Windows 11 (Tu PC Local)

Para tener siempre actualizada la Biblia, los scripts `.bat`/`.ps1` y las configuraciones MCP en tu PC con Windows 11, clona el repo y programa una tarea diaria en PowerShell:

```powershell
# 1. Clonar en tu carpeta de herramientas (una sola vez)
mkdir C:\Tools -Force
git clone https://github.com/Leopoldoleoncancino/video-vfx-ai-bible.git C:\Tools\video-vfx-ai-bible

# 2. Registrar tarea diaria en Windows Task Scheduler a las 08:00 AM
$Action = New-ScheduledTaskAction -Execute "git.exe" -Argument "-C C:\Tools\video-vfx-ai-bible pull --ff-only"
$Trigger = New-ScheduledTaskTrigger -Daily -At 8:00AM
Register-ScheduledTask -TaskName "SyncVideoVFXBible" -Action $Action -Trigger $Trigger -Description "Sincroniza diariamente la Biblia de Herramientas Video IA y VFX"
```

También puedes ejecutar el radar localmente en cualquier momento desde Windows:
```powershell
cd C:\Tools\video-vfx-ai-bible
python scripts\daily_radar.py
```
