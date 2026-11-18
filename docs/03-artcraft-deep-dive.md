# 03 · Enfoque Profundo: Ecosistema ArtCraft (Storytold — Suite Completa en Rust)

**ArtCraft** ([`getartcraft.com`](https://getartcraft.com/) · [`github.com/storytold`](https://github.com/storytold)) es el proyecto open-source más ambicioso de 2025–2026 para reescribir desde cero una suite creativa completa en **Rust puro** (sin dependencias pesadas de FFmpeg, renderizado por `wgpu`, binarios nativos + compilación WebAssembly, archivos JSON difeables en Git y **servidores MCP integrados directamente en las CLIs**).

---

## 1. ArtCraft Studio (El IDE Central de Staging 2D/3D + IA)

- **Repositorio:** [`storytold/artcraft`](https://github.com/storytold/artcraft) (★41,521 · Apache-2.0)
- **Qué es:** Entorno unificado (*Intentional Crafting Engine*) para directores, artistas 3D y cineastas que combina **staging 3D + composición 2D + generación IA**.
- **Capacidades clave de producción:**
  - **2D / 3D Compositing** nativo y **Mixed Asset Crafting** (combina imágenes, modelos 3D, poses y cámaras en la misma escena).
  - **Image to Location** (convierte una imagen conceptual en entorno navegable 3D) y **Image to 3D Mesh**.
  - **Character Posing** & **Character Identity Transfer** (consistencia de personaje entre planos con pose controlada).
  - **Background Removal** integrado.
- **Modelos integrados (62 proveedores/modelos cloud + bridging local):**
  - *Video Cloud:* Seedance 1.5/2.0, Kling 1.6–3.0, Veo 3/3.1, Sora 2, Vidu Q3, MiniMax H3.
  - *Imagen/3D/Audio:* Flux 3, Hunyuan 3D 2.0–3.1, Marble 1.1 / TripoSplat (`storytold/spark`), Suno, Seed Audio.
  - *Infraestructura AI y Skills de Storytold:* [`storytold/craft-ai-integrations`](https://github.com/storytold/craft-ai-integrations) (★173) y [`storytold/craft-skills`](https://github.com/storytold/craft-skills) (★18). El soporte nativo para gestor de modelos locales (Ollama / LM Studio / pesos locales) está en desarrollo activo (issue `#2152` en `storytold/artcraft`).

---

## 2. Catálogo Verificado de las 17+ Crafting Apps (`getartcraft.com/apps`)

Todas se gestionan unificadamente con **`ArtCraft Launcher`** ([`storytold/craft-launcher`](https://github.com/storytold/craft-launcher), ★5,476 · Apache-2.0):

### A. Aplicaciones Directas de Video, VFX, 3D, Foto y Audio

| App | Repositorio (Verificado API Nov 2026) | Stars | Licencia | Equivalente Tradicional | Lo que aporta a tu pipeline (MCP / Rust / Formatos) |
|---|---|---:|---|---|---|
| **FilmCraft** | [`storytold/filmcraft`](https://github.com/storytold/filmcraft) | 18,548 | Apache-2.0 | Premiere Pro / Resolve Edit | Codecs H.264/HEVC/ProRes/AAC en Rust puro (sin FFmpeg), aritmética entera exacta por frame, compositor GPU lineal, **MCP nativo** (`filmcraft-cli mcp --bridge 127.0.0.1:9876`). |
| **EffectCraft** | [`storytold/effectcraft`](https://github.com/storytold/effectcraft) | 8,949 | Apache-2.0 | After Effects | **308 efectos**, **38 blend modes**, 9 layer styles, expresiones JS, cámaras/luces 3D, Puppet pins, **Lottie JSON/`.lottie` bidireccional**, `.ecproj` difeable, **MobileSAM 40MB Roto Brush**, **MCP nativo** (`effectcraft-cli mcp --bridge 9877`). |
| **AniCraft** | [`storytold/anicraft`](https://github.com/storytold/anicraft) | 468 | Apache-2.0 | Animate / Toon Boom | Editor de animación 2D vectorial en Rust desde cero. |
| **PhotoCraft** | [`storytold/photocraft`](https://github.com/storytold/photocraft) | 80,276 | Apache-2.0 | Photoshop | Edición raster profesional de clean-plates, matte paintings y texturas. |
| **LightCraft** | [`storytold/lightcraft`](https://github.com/storytold/lightcraft) | 16,160 | Apache-2.0 | Lightroom | Revelado RAW / DNG no destructivo y catalogación local rápida. |
| **TextureCraft** | [`storytold/texturecraft`](https://github.com/storytold/texturecraft) | 689 | Apache-2.0 | Substance 3D Painter | Flujo de pintura de texturas 3D directo sobre mallas. |
| **MaterialCraft** | [`storytold/materialcraft`](https://github.com/storytold/materialcraft) | 411 | Apache-2.0 | Substance 3D Designer | Diseñador nodal de materiales PBR en Rust. |
| **SoundCraft** | [`storytold/soundcraft`](https://github.com/storytold/soundcraft) | 4,449 | Apache-2.0 | Audition / Reaper | DAW *clean-room* multipista en Rust para stems y SFX de video. |

### B. Resto de la Suite + Motor "Craft Anything"

| App | Repo | Stars | Equivalente |
|---|---|---:|---|
| **Craft Anything** | [`storytold/craft-anything`](https://github.com/storytold/craft-anything) | 36,814 | Meta-framework y análisis arquitectónico para crear software *clean-room* |
| **PdfCraft** | [`storytold/pdfcraft`](https://github.com/storytold/pdfcraft) | 21,120 | Acrobat / Lector & editor PDF |
| **WordCraft** | [`storytold/wordcraft`](https://github.com/storytold/wordcraft) | 18,237 | Word / Procesador de texto (guiones/escaletas) |
| **VectorCraft** | [`storytold/vectorcraft`](https://github.com/storytold/vectorcraft) | 11,885 | Illustrator / Gráficos vectoriales |
| **CADCraft** | [`storytold/cadcraft`](https://github.com/storytold/cadcraft) | 8,256 | AutoCAD / Dibujo técnico 2D/3D para escenografía |
| **GridCraft** | [`storytold/gridcraft`](https://github.com/storytold/gridcraft) | 7,645 | Excel / Hoja de cálculo (budgets/tracking de VFX) |
| **DesignCraft** | [`storytold/designcraft`](https://github.com/storytold/designcraft) | 5,322 | InDesign / Maquetación (pitch decks y lookbooks) |
| **FigCraft** | [`storytold/figcraft`](https://github.com/storytold/figcraft) | 5,142 | Figma / Diseño UI/HUD para motion graphics |
| **DeckCraft** | [`storytold/deckcraft`](https://github.com/storytold/deckcraft) | 4,868 | PowerPoint / Pitch presentaciones |

---

## 3. Deep-Dive en Automation & MCP: FilmCraft + EffectCraft

Lo que hace única a esta suite frente a **Adobe** es que **la automatización por agentes IA no es un parche por COM/ExtendScript**, sino parte del núcleo:

### EffectCraft `.mcp.json` (Verificado directamente del repo)
```json
{
  "mcpServers": {
    "effectcraft": {
      "command": "cargo",
      "args": ["run", "--quiet", "--release", "-p", "effectcraft-cli", "--", "mcp", "--demo"]
    },
    "effectcraft-app": {
      "command": "cargo",
      "args": ["run", "--quiet", "--release", "-p", "effectcraft-cli", "--", "mcp", "--bridge", "9877"]
    }
  }
}
```
*(Si ya compilaste el binario en Windows `effectcraft-cli.exe`, reemplaza `cargo run ...` por la ruta directa al `.exe` para arranque instantáneo).*

### FilmCraft `.mcp.json` (Verificado directamente del repo)
```json
{
  "mcpServers": {
    "filmcraft": {
      "command": "target/release/filmcraft-cli.exe",
      "args": ["mcp", "--bridge", "127.0.0.1:9876"]
    },
    "filmcraft-headless": {
      "command": "target/release/filmcraft-cli.exe",
      "args": ["mcp", "--demo"]
    }
  }
}
```

### Flujo real en Windows 11 con Antigravity / Claude Code
1. Un agente genera un motion graphic procedural en archivo declarativo **`.ecproj`** o scripts CLI (`effectcraft-cli script` / herramienta MCP `run_script`) ➔ exporta directo a **Lottie JSON** o secuencia de video con alpha.
2. **FilmCraft** ensambla el montaje en headless CLI o vivo sobre la UI en el puerto `9876` con **0 frames de desfase** gracias a su matemática entera de tiempos.
3. Todo el proyecto vive en **Git** con diffs legibles (`.ecproj`, scripts Rust/JS) — imposible con `.aep` o `.prproj` binarios sin convertir.

---

## 4. Evaluación Honesta de Madurez (Noviembre 2026): ArtCraft vs Adobe

> **No caigas en el hype ciego:** Aunque sus cifras en GitHub y su diseño en Rust son sobresalientes, en noviembre de 2026 **FilmCraft y EffectCraft están en desarrollo acelerado (etapa alpha / *clean-room* WIP)**:

| Criterio | FilmCraft & EffectCraft (Hoy Nov 2026) | Adobe Premiere & After Effects (Hoy Nov 2026) |
|---|---|---|
| **Nivel de Paridad / Madurez** | FilmCraft (~56% paridad objetivo); EffectCraft (~45% readiness operativa / ~91% de features rastreadas en su matriz `target-app-parity.md`). | 100% estándar industrial consolidado para entrega comercial y agencias. |
| **Archivos Propietarios** | **NO abre** `.aep`, `.prproj`, `.mogrt` ni `.psb` con paridad completa (soporta estándares abiertos y Lottie). | Nativo `.aep` / `.prproj` / MOGRTs / Dynamic Link. |
| **Plugins Terceros (.aex / OFX)** | Sin soporte para plugins compilados de Adobe/BorisFX/Red Giant/VideoCopilot. | Ecosistema inmenso de plugins GPU y hardware comercial. |
| **Velocidad de Iteración AI/MCP** | **Imbatible:** CLI nativa headless, JSON diffable, Lottie bidireccional, MCP en puerto dedicado desde el día 1. | Requiere puentes externos (Node + CEP/UXP + `.jsx`) con fricciones ocasionales de permisos/UI. |
| **Costo & Licenciamiento** | **Apache-2.0** (100% gratis, sin suscripción, tu propio código). | Suscripción Creative Cloud mensual. |

### Estrategia Recomendada en Tu PC Local (Híbrida)
- **Usa ArtCraft Studio** para previsualización 3D/2D con modelos de última generación, poses y diseño de escenas.
- **Usa EffectCraft** para motion graphics vectoriales exportables a **Lottie** / web, o experimentos MCP de composición rápida sin pagar licencias ni abrir el pesado AE.
- **Usa PhotoCraft / LightCraft / SoundCraft / TextureCraft** como reemplazos ligeros sin suscripción en tareas concretas.
- **Conserva Premiere Pro + After Effects** como estación maestra cuando necesites clientes corporativos, plugins comerciales, rotoscopia en timeline o entregas broadcast estrictas.
