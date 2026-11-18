# 09 · Camera Tracking 3D, Matchmoving, Point Tracking & Fotogrametría Local

> **Calibración:** NVIDIA **RTX 3060 · 12 GB VRAM** *(Ampere)* · **Ryzen 9 5900X** *(12C / 24T)* · **32 GB RAM** · **Windows 11**  
> **Brecha que cierra este pilar:** Para insertar personajes 3D, 3DGS (`gsplat`), partículas TouchDesigner POPs o luces CG sobre una grabación cámara en mano, primero necesitas **recuperar la cámara 3D (`f`, FOV, traslación, rotación)** y **puntos 3D estables**. Hoy puedes hacerlo tanto con **tracking geométrico clásico (COLMAP/Blender)** como con **modelos IA feed-forward (`Depth Anything 3`, `VGGT`, `Pi3X`, `MapAnything`, `CoTracker3`)** que corren en tus **12 GB de VRAM**.

---

## 1. Mapa de Elección Rápida (¿Qué Herramienta Uso Hoy?)

| Necesidad VFX | Herramienta #1 en RTX 3060 12GB | Alternativa / Cuándo Cambiar | Export Directo a NLE/3D |
|---|---|---|---|
| **Camera Tracking + Depth + 3DGS desde video largo** | **[`Depth Anything 3`](https://github.com/ByteDance-Seed/Depth-Anything-3)** (`DA3-Streaming`) | [`VGGT-1B`](https://github.com/facebookresearch/vggt) (`COLMAP` format) | `.ply` 3DGS / Cámaras + Depth lineal |
| **Reconstrucción multi-vista libre de artefactos (12 GB)** | **[`Pi3X`](https://github.com/yyfz/Pi3)** (`disable_multimodal()`) | [`MapAnything`](https://github.com/facebookresearch/map-anything) (`minibatch_size=1`) | Nube de puntos métrica + Poses |
| **Point Tracking denso tras oclusiones (objetos/partes)** | **[`CoTracker3`](https://github.com/facebookresearch/co-tracker)** (Meta Research) | Tracker nativo de Blender / Fusion | Coordenadas 2D `(x, y)` + visibilidad (JSON/NPY/AE nulls) |
| **Matchmoving clásico de cine con precisión sub-píxel** | **`COLMAP`** ([`colmap/colmap`](https://github.com/colmap/colmap) · ya integra GLOMAP) + **Blender Motion Tracker** | **AliceVision Meshroom** (fotogrametría nodal) | `.abc` (Alembic), `.fbx`, `.usd`, `COLMAP sparse/dense` |
| **Calibración rápida de perspectiva con 1 foto/frame** | **[`fSpy`](https://github.com/perarnia/fSpy)** + **[`fSpy-Blender`](https://github.com/perarnia/fSpy-Blender)** | [`microsoft/MoGe`](https://github.com/microsoft/MoGe) (`MoGe-2/3` FOV) | Archivo `.fspy` ➔ Cámara exacta en Blender |
| **Normal + Height + Curvature desde textura/foto única** | **[`HugoTini/DeepBump`](https://github.com/HugoTini/DeepBump)** (Add-on Blender) | `StableDelight` (quitar brillos antes del PBR) | Nodos Blender PBR + Mapas 16-bit |

---

## 2. Reconstrucción 3D Feed-Forward + Camera Pose en Tiempo Record (IA Local)

Antes, recuperar cámara y geometría densa tomaba horas en SfM clásico y fallaba en paredes lisas o cielos abiertos. Esta nueva generación calcula **pose de cámara, mapa de profundidad consistente y geometría 3D en un solo paso** con la RTX 3060:

### A. `ByteDance-Seed/Depth-Anything-3` (`DA3` & `DA3-Streaming`) `[OK-12GB]`
- **Repo / Licencia:** [`ByteDance-Seed/Depth-Anything-3`](https://github.com/ByteDance-Seed/Depth-Anything-3) · ★6,709 · Apache-2.0
- **Qué aporta en VFX:** Predice **geometría consistente en espacio desde 1 o múltiples vistas**, **poses estimadas de cámara** e incluso salidas listas para **3D Gaussian Splatting (3DGS)** desde secuencia de video sin calibración previa.
- **Clave para 3060 12 GB + 32 GB RAM:**
  - Usa **`DA3-Streaming`** (`da3_streaming/`) para **videos largos** manteniendo consumo bajo de VRAM al procesar por ventanas con alineación global.
  - Combina modelos `DA3-Small` / `DA3-Base` / `DA3-Large-1.1` o `DA3-Metric-Large` según requieras distancia métrica real o máxima velocidad.

### B. `facebookresearch/vggt` (`VGGT-1B` · CVPR 2025 Best Paper) `[TIGHT-12GB]`
- **Repo / Licencia:** [`facebookresearch/vggt`](https://github.com/facebookresearch/vggt) · ★14,646 · Uso comercial permitido (revisar `LICENSE` excl. militar)
- **Qué aporta en VFX:** Visual Geometry Grounded Transformer que reconstruye en segundos parámetros extrínsecos/intrínsecos de cámara, profundidad, nube de puntos 3D y tracking 3D simultáneos.
- **Tip clave para 12 GB VRAM:**
  - Las optimizaciones de memoria eliminaron tensores intermedios redundantes; usa resolución moderada (`~518px`) o muestreo de **keyframes** + modo **`--anchors-only`** si solo necesitas poses de cámara y nubes de apoyo, además del script incluido para exportar **directamente en formato `COLMAP`** (con *Bundle Adjustment* opcional para refinar al milímetro en Blender / 3DGS).
  - *Nota `vggt-omega`:* la variante posterior CVPR '26 (~4.58 GB en 512 px) tiene pesos con acceso controlado (*gated*), por lo que **`VGGT-1B`** o **`DA3-Streaming`** siguen siendo el caballo de batalla abierto hoy.

### C. `yyfz/Pi3` (`Pi3X`) `[OK-12GB]`
- **Repo / Licencia:** [`yyfz/Pi3`](https://github.com/yyfz/Pi3) · ★2,265 · BSD-3-Clause
- **Por qué destacarlo en 3060 12 GB:** Arquitectura equivariante a permutaciones (no depende del frame de referencia inicial), elimina artefactos en cuadrícula, genera mapa de **confianza continua** y soporta **escala métrica aproximada** y condiciones opcionales de entrada (`example_mm.py`).
- **Ajuste obligatorio 12 GB VRAM:** Al instanciar para video/multi-vista estándar sin pistas multimodales adicionales, llama a `disable_multimodal()` para ajustar el consumo cómodo dentro de los **12 GB** sin desbordar RAM.

### D. `facebookresearch/map-anything` `[TIGHT-12GB]`
- **Repo / Licencia:** [`facebookresearch/map-anything`](https://github.com/facebookresearch/map-anything) · ★3,913 · Apache-2.0
- **Qué hace:** Framework universal de reconstrucción 3D métrica modular que soporta imágenes, profundidades parciales o poses COLMAP previas como entrada/evaluación.
- **Ajuste RTX 3060 12 GB:** Ejecuta con **`minibatch_size=1`** y secuencias recortadas de keyframes para mantener la memoria pico por debajo de 11 GB.

---

## 3. Point Tracking Denso: `facebookresearch/co-tracker` (`CoTracker3`) `[OK-12GB]`

Cuando el optical flow normal pierde un objeto porque alguien pasa por delante o el brazo gira, entra **`CoTracker3`**:

- **Repo:** [`facebookresearch/co-tracker`](https://github.com/facebookresearch/co-tracker) · ★5,206 · Modelo ligero *Transformer* entrenado con mil veces menos datos.
- **Ventaja VFX real:** Rastrea simultáneamente rejillas densas (o puntos manuales precisos) **a través de oclusiones totales**, reportando `(x, y)` y bandera binaria **`visibility`** frame a frame.
- **Casos de uso en Premiere / After Effects / Blender / ComfyUI:**
  1. Pegar gráficos **Remotion / HUDs JS** o texto sobre ropa en movimiento sin que floten.
  2. Alimentar máscaras punto-ancla hacia **`SAM 2 / SAM 3 ➔ MatAnyone 2`** en planos muy rápidos.
  3. Exportar trayectorias 2D limpias (`.npy` / `.json`) y convertirlas en **Null Objects en After Effects** mediante ExtendScript o `@kumoproductions/mcp-aftereffects`.

---

## 4. Pipeline Clásico & Fotogrametría PBR (`COLMAP`, `Meshroom`, `fSpy`, `Blender`, `DeepBump`)

La IA feed-forward es ideal para velocidad y geometría densa inicial, pero en **matchmoving de plano comercial con lentes distorsionadas o sets rígidos** el flujo clásico sigue siendo rey:

1. **`colmap/colmap` (★13,249 · ya incluye GLOMAP integrado)** `[OK-12GB + CPU 5900X]`
   - ⚠️ **Aviso de obsolescencia:** El repositorio separado [`colmap/glomap`](https://github.com/colmap/glomap) (★2,347) fue marcado como **`[DEPRECATED]`** porque **GLOMAP (Global SfM)** se fusionó directamente dentro del árbol principal de **`colmap/colmap`**. No instales el repo antiguo por separado.
   - **Rol en tu estación:** Reconstrucción SfM ultra rápida aprovechando los **24 hilos del Ryzen 9 5900X** + CUDA en la **RTX 3060**, generando la cámara exacta para entrenar **3D Gaussian Splatting (`gsplat` / Kiri Engine)** o importar vía Alembic/PLY a Blender.
2. **Blender Motion Tracking (`Movie Clip Editor`) ➔ Exportación Universal** `[OK-12GB]`
   - Rastrea marcadores físicos en plano real, resuelve distancia focal (`Focal Length` + distorsión radial K1/K2) hasta lograr **Solve Error < 0.5 px**, fija piso/origen y exporta:
     - **Hacia Unreal / Fusion / Nuke / TouchDesigner:** **Alembic (`.abc`)**, **FBX (`.fbx`)** o **USD (`.usda/.usdc`)** con la cámara animada y planos de sombra (*Shadow Catcher*).
3. **[`alicevision/Meshroom`](https://github.com/alicevision/Meshroom)** (★13,104) `[OK-12GB]`
   - Pipeline nodal de fotogrametría CUDA para convertir sesiones de fotos de objetos o locaciones en mallas limpias + texturas Albedo proyectadas listas para retopología o *Camera Projection* en Blender 5.x.
4. **[`perarnia/fSpy`](https://github.com/perarnia/fSpy)** (★2,633 · GPL-3.0) + **[`perarnia/fSpy-Blender`](https://github.com/perarnia/fSpy-Blender)** (★1,473 · GPL-3.0) `[OK-12GB]`
   - *(Nota: el propietario oficial en GitHub migró de `stuffmatic` a **`perarnia`**).*
   - Traza 2 o 3 pares de líneas paralelas de fuga sobre **un solo fotograma o pintura mate** y genera el archivo `.fspy` con FOV, rotación y punto principal óptico para montar una escena 3D exacta en Blender en menos de 2 minutos.
5. **[`HugoTini/DeepBump`](https://github.com/HugoTini/DeepBump)** (★1,431 · GPL-3.0) + **[`Stable-X/StableDelight`](https://github.com/Stable-X/StableDelight)** (★418) `[OK-12GB]`
   - **Delight + PBR en local:** Usa primero `StableDelight` (hermano de `StableNormal`) para quitar brillos especulares quemados de una foto real, y pásala por **DeepBump** dentro de Blender para sintetizar automáticamente **Normal Map + Height + Curvature** en canales PBR listos para EEVEE/Cycles o TouchDesigner.

---

## 5. Checklist Rápido de Elección

- *"Tengo un video cámara en mano de 6s y quiero cámara 3D + profundidad + 3DGS en minutos"* ➔ **`Depth-Anything-3` (`DA3-Streaming`)** o **`VGGT-1B`** (export `COLMAP` ➔ `gsplat` / Blender).
- *"Quiero pegar un título o partícula TouchDesigner a una mano que se tapa detrás de un objeto"* ➔ **`CoTracker3`**.
- *"Es una fotografía fija de arquitectura y necesito proyectar la cámara en Blender"* ➔ **`fSpy` + `fSpy-Blender`** (o **`MoGe-2/3`** si no hay líneas rectas visibles).
- *"Necesito precisión sub-píxel de lente cine y cero deslizamiento (`sliding`) para Shadow Catcher"* ➔ **Blender Motion Tracker** o **`COLMAP` (GLOMAP integrado)** ➔ Alembic `.abc` / USD.
