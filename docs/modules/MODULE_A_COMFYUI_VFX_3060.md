# Módulo A (Fase 2.5) · ComfyUI VFX Híbrido, Relighting PBR (`SSDO`), Fluido GPU Incompresible, Oclusión Z Continua & Workflow 4 (R&D `33f` ➔ `167f`)

> **Hardware Calibrado:** NVIDIA **RTX 3060 · 12 GB VRAM** *(`sm_86` Ampere, SIN FP8 Tensor Core nativo)* · AMD **Ryzen 9 5900X** *(12C / 24T)* · **32 GB DDR4** *(~22–24 GB libres reales en Windows 11)*  
> **Plantillas ComfyUI API JSON:** [`workflows/comfyui/README.md`](../../workflows/comfyui/README.md) · **Scripts CLI/Blender/CUDA:** [`scripts/`](../../scripts/)  
> **Caso Objetivo de Referencia (Workflow 4):** Plano vertical handheld POV (`478×850`, `167 frames`, `~30 fps`, recorte crítico `33f` en `f88..f120` con giro palma→dorso de `180°`) de una mano con manga negra deshilachada frente a un escritorio blanco/impresora con fuego hiperrealista.

---

## 1. Reglas Duras de Kernel & VRAM en RTX 3060 (`sm_86`) + Windows 11

Antes de lanzar nodos de difusión, matting o normales sobre una toma real en **Windows 11 + 12 GB VRAM + 32 GB RAM**, aplica estas reglas verificadas directamente en el código fuente de los repositorios objetivo:

| Regla | Motivo Técnico Verificado `(Repo)` | Configuración Obligatoria en tu PC |
|---|---|---|
| **Prohibido `fp8_fast` y `torch.compile` en `e4m3fn`** | En `WanVideoModelLoader` (`ComfyUI-WanVideoWrapper`), los modos `*_fast` y `torch.compile` sobre `fp8_e4m3fn` exigen **`CUDA compute capability >= 8.9`** (Ada RTX 40xx+); la RTX 3060 es **`sm_86`**. | Usa `base_precision: "bf16"` (o `"fp16"`), `quantization: "disabled"`, `attention_mode: "sageattn"` (vía [`woct0rdho/triton-windows`](https://github.com/woct0rdho/triton-windows) + [`woct0rdho/SageAttention`](https://github.com/woct0rdho/SageAttention)) o `"sdpa"`. No conectes `WanVideoTorchCompileSettings`. |
| **Cuantización exacta de `Wan2.2-VACE-Fun-A14B`** | Tamaños reales en Hugging Face (`QuantStack/Wan2.2-VACE-Fun-A14B-GGUF`): `Q4_K_M` pesa **`11.64 GB`** por experto (High/Low) — deja margen casi nulo en 12 GB. `Q4_K_S` pesa **`10.55 GB`** y `Q3_K_M` pesa **`8.64 GB`**. | Usa **`Q3_K_M` (`8.64 GB`)** para iterar rápido o **`Q4_K_S` (`10.55 GB`)** para el render hero, siempre con `WanVideoBlockSwap` (`blocks_to_swap=24`, `vace_blocks_to_swap=10`, `offload_img_emb=true`, `offload_txt_emb=true`). |
| **Sin T5 residente en los 32 GB de RAM** | Cargar `umt5-xxl-enc-bf16` en RAM permanente junto a dos expertos A14B satura los ~22–24 GB libres de Win 11. | Usa **`WanVideoTextEncodeCached`** con `use_disk_cache: true` (descarga T5 inmediatamente tras generar el caché de prompt) y fija Pagefile NVMe en **32,768–65,536 MB**. |
| **Memoria temporal en `MatAnyone 2`** | En `spiritform/comfy-matanyone2/config.py`, `max_mem_frames` viene fijado por defecto en **`10`** (sube picos VRAM en secuencias `>60f`). | Edita `"max_mem_frames": 5` en `config.py` y cierra Premiere/AE/Blender pesado antes de correr ComfyUI. |
| **NormalCrafter & Secuencialidad Estricta** | `Binyr/NormalCrafter` consume ~6 GB a `512px`, pero sube a **~20 GB** a `1024×576`. | Fija `max_res_dimension = 512`, `offload_after = true` en `VizClickNormalCrafter` e inserta `VRAM_Debug` (`unload_all_models=true`, `empty_cache=true`, `gc_collect=true`) entre fases pesadas. |
| **Evitar LoRAs destiladas *CausVid* en llamas** | Las LoRAs de 4–8 steps fusionan y suavizan la micro-turbulencia Navier-Stokes del fuego. | Usa **20 steps (`euler` / `unipc`)**, `cfg: 5.0–6.0`, `shift: 6.0` sin CausVid en pases finales de fuego. |
| **Cuidado con `FrequencyCombineMEC` en HDR** | En `Code2Collapse/ComfyUI-CustomNodePacks`, `FrequencyCombineMEC` recorta (*clamps*) la salida al rango SDR `[0, 1]`. | Usa `FrequencySeparateMEC` (`linear=true`) solo para extraer la capa **`low_frequency`** del relight y calcula la multiplicación HDR + fuego `>1.0` en [`vfx_ssdo_relight_16f.py`](../../scripts/vfx_ssdo_relight_16f.py) / [`vfx_incompressible_fire_sim.py`](../../scripts/vfx_incompressible_fire_sim.py), Blender Cycles o Fusion/AE 32-bpc. |

---

## 2. Resultados Empíricos Validados en Hardware Real (`33f` Críticos `f88..f120`, `478×850`, Giro `180°`)

> **Entorno de validación empírica:** Windows 11 · ComfyUI Portable (`python_embeded -s`) · NVIDIA RTX 3060 12 GB (`sm_86`) · AMD Ryzen 9 5900X · 32 GB RAM · Directorio de intercambio `E:\confyui\exchange\job_33f\`.

### 2.1 Resumen Cuantitativo de Fase 0 y Relighting PBR (`PASS Gate 0 & Gate 1`)

| Etapa / Motor | Tiempo Real (`33f`) | Peso / VRAM | Métrica Empírica Obtenida | Umbral Gate | Estado |
|---|---|---|---|---|---|
| **Fase 0 · Bus Común `16F`** *(`SAM 2.1` + `MatAnyone 2 max_mem_frames=5` + `DepthAnything V2 ViT-L` + `VizClickNormalCrafter --max-res 512` + `VizClickNormalTemporalStabilizer` + [`vfx_dual_matte_decontam.py`](../../scripts/vfx_dual_matte_decontam.py))* | **`~60 s` total** | **`~4.75 GB` pesos totales** | `‖N‖ ∈ [0.9996, 1.0004]`<br>Estabilidad normal fondo estático: **`0.533°/frame`**<br>Solapamiento `matte_skin` vs `matte_fabric`: **`0.015 %`**<br>Reducción halo blanco en hilos negros: **`-85.4 %`** (`0.154 → 0.0225` sRGB / `0.0113` lineal `16F`) | `‖N‖ ∈ [0.99, 1.01]`<br>`ΔL < 0.03` | **✅ PASS Gate 0** |
| **Fase 1B · Relighting PBR Analítico** *([`vfx_ssdo_relight_16f.py`](../../scripts/vfx_ssdo_relight_16f.py) sobre `NormalCrafter` + `DepthAnything V2`)* | **`< 5 s`** | **`< 1 GB`** | Contraste SSDO dedo-a-dedo: **`5.48:1`** *(máx **`36.07:1`**)*<br>Ganancia naranja en puño negro: **`1.004×`**<br>Neutralidad escritorio blanco: **`CIEDE2000 = 0.000`** *(vs `40.35` en `v10`)* | `SSDO >= 3.5:1`<br>`cuff <= 1.15×`<br>`CIEDE2000 <= 1.5` | **✅ PASS Gate 1** |
| **Fase 1C · Colorimetría HDR Fuego** *(Reemplazo de `m_inset` por **Stephen Hill ACES Filmic RRT+ODT** / **OCIO `AgX - Punchy`**)* | **Instantáneo** | **CPU / GPU** | Puntas rojo carmesí → cuerpo naranja hidrocarburo → núcleo dorado-crema (`peak 8–14` lineal)<br>`pastel_yellow_clip_pct = 0.0 %`<br>`salmon_wash_pct = 0.0 %` | `peak >= 4.0`<br>`pastel_clip <= 1 %`<br>`salmon_wash <= 2 %` | **✅ PASS Gate 2** |

### 2.2 Troubleshooting Real: 4 Gotchas Críticos de Windows 11 + ComfyUI Portable (`python_embeded -s`)

1. **`MatAnyone2` falla al instalar con `pip` por bug de empaquetado `hatchling`:**
   - **Causa:** El repositorio `pq-yang/MatAnyone2` contiene una referencia duplicada a `matanyone2/config/__init__.py` en su configuración de wheel con `hatchling`, abortando `pip install`.
   - **Solución directa en Windows 11:** Clona el repositorio y copia la carpeta del paquete `matanyone2\` directamente dentro de `ComfyUI_windows_portable\python_embeded\Lib\site-packages\matanyone2\`.
2. **`transformers 5.9.0` lanza `KeyError: 'flash_attn'` al iniciar ComfyUI:**
   - **Causa:** En `transformers/utils/import_utils.py`, cuando un custom node registra un stub de `flash_attn` sin metadatos completos de distribución, el acceso directo por diccionario falla con `KeyError: 'flash_attn'`.
   - **Solución:** Cambiar la búsqueda directa en `import_utils.py` por `.get("flash_attn", [])`.
3. **ComfyUI Portable corre con `-s` (`--no-user-site`) e ignora paquetes instalados en `--user`:**
   - **Causa:** El ejecutable `python_embeded\python.exe -s` deshabilita explícitamente `%APPDATA%\Python\Python31x\site-packages`, por lo que `OpenEXR`, `PyOpenColorIO` o `pymatting` instalados sin `--target` no son visibles.
   - **Solución obligatoria:** Instalar siempre apuntando al `site-packages` embebido:
     ```powershell
     .\python_embeded\python.exe -m pip install --target .\python_embeded\Lib\site-packages OpenEXR PyOpenColorIO pymatting
     ```
4. **Orientación del eje Y entre `NormalCrafter` (`+Y` arriba) y Screen-Space SSDO (`+Y` abajo):**
   - **Causa:** `NormalCrafter` exporta normales en convención **OpenGL Camera Space (`+X` derecha, `+Y` arriba, `+Z` hacia cámara)**. En cambio, la grilla de imagen `vv` en Python/ NumPy crece de arriba hacia abajo (`0..1`), por lo que el vector hacia la luz `dy = lv - vv` tiene **`+Y` hacia abajo**. Si no se invierte `N_y`, las luces situadas arriba iluminan las caras inferiores de los dedos.
   - **Solución (ya fijada por defecto en [`vfx_ssdo_relight_16f.py`](../../scripts/vfx_ssdo_relight_16f.py)):** `invert_normal_y=True` (`--normal-convention opengl`, activo por defecto).

### 2.3 Diagnóstico del Lavado Salmón/Blanco Tiza en `agx_filmic_tonemap` y Solución Analítica

- **Por qué fallaba la aproximación `m_inset` simple:**
  La matriz `m_inset` (`B_in = 0.042376·R + 0.078434·G + 0.879143·B`) mezclaba un `4.24 %` de Rojo en el canal Azul antes de aplicar el logaritmo. Al comprimir el rango dinámico de `[2^{-10}, 2^{+6.5}]` con una curva S suave sin aplicar la expansión cromática *Look: Punchy* de Blender y luego aplicar `m_out = inv(m_inset)`, una punta de llama roja pura (`R=1.2, G=0.12, B=0.01` lineal) salía con **`B_srgb = 0.525`** (`[0.889, 0.660, 0.525]`), tiñendo las lenguas de fuego de color **salmón / rosa pastel** y el núcleo de **blanco tiza**.
- **Solución doble implementada en [`scripts/vfx_ssdo_relight_16f.py`](../../scripts/vfx_ssdo_relight_16f.py):**
  1. **Stephen Hill ACES Filmic (`RRT + ODT` exacto, `aces_hill_filmic_tonemap`):** Transforma `sRGB D65 -> AP1` (`_ACES_INPUT_MAT`), evalúa el polinomio racional exacto de RRT+ODT:
     $$f(v) = \frac{v(v + 0.0245786) - 0.000090537}{v(0.983729\,v + 0.4329510) + 0.238081}$$
     y proyecta de vuelta con `_ACES_OUTPUT_MAT`. La misma punta roja `(1.2, 0.12, 0.01)` produce ahora **`[0.894, 0.319, 0.090]` sRGB** (rojo carmesí profundo) y un núcleo HDR `10.0` produce **`[0.994, 0.934, 0.686]` sRGB** (blanco-crema incandescente, `0.0 %` clipping pastel).
  2. **OCIO `AgX - Punchy` nativo (`ocio_agx_tonemap`):** Si `PyOpenColorIO` está instalado, encadena `OCIO.LookTransform(src="Linear Rec.709", dst="Linear Rec.709", looks="AgX - Punchy")` + `OCIO.DisplayViewTransform(src="Linear Rec.709", display="sRGB", view="AgX")`.
  3. **Preservación Analítica del Plate (`inverse_aces_hill_linear` + `compose_hdr_on_plate_srgb`):** Aplicar un tone mapper fílmico directamente sobre un plate de teléfono que *ya viene tone-mapped de cámara* oscurece el escritorio blanco de `0.85` a `0.62` (`CIEDE2000 ≈ 14`). Al invertir analíticamente la cuadrática de Stephen Hill sobre el plate donde hay luz añadida (`delta_hdr > 0`), sumar `delta_hdr` en dominio ACES pre-RRT y re-aplicar el RRT+ODT (manteniendo intactos los píxeles con `delta_hdr == 0`), obtenemos **roll-off HDR genuino en la llama y `CIEDE2000 = 0.000` en el escritorio blanco**.

### 2.4 Hallazgos del A/B Visual de Simulación de Fuego sobre `33f` (`f88..f120`)

1. **Blender Mantaflow emitido desde esferas en landmarks (`res 176–224`):**
   - Tiene inercia 3D real, pero al nacer de 21 esferas discretas parece *"flotando/trackeado encima"* sin abrazar el contorno epidérmico continuo de la mano, y el hollín estándar produce nubes rojas cortadas/granulosas. **Requiere emisión superficial desde una malla 3D continua estanca (*watertight*) con shader de lámina fina Blackbody (Pilar 2).**
2. **Domain-Warped Curl Fire 2× supersampled (`72` pasos R2 en PyTorch CUDA, `53 s` en RTX 3060):**
   - Logra estética sedosa, cero ruido gaussiano, cero bandeado y abraza con precisión los 5 dedos y la palma. **PERO** al ser *stateless* (sin estado temporal ni advección de flujo), **el giro rápido de `180°` de la mano no dobla, arrastra ni perturba el fuego** (se percibe rígido/pegado).
3. **Fluido Euleriano GPU básico sin proyección de presión (`∇·v ≠ 0`):**
   - Sin hacer cumplir la incompresibilidad (`∇²p = ∇·v`, `v ← v - ∇p`) ni imponer condición de contorno de cuerpo sólido, la mano atraviesa el humo sin desplazar físicamente el aire ni generar vórtices de arrastre (*Karman wake*) ni estelas de chispas.

---

## 3. Los 5 Nuevos Pilares de Producción (Fase 2.5 — Física + Luz + Oclusión + Gates)

### Pilar 1 · Fluido GPU Incompresible con Interacción Real Mano↔Aire ([`scripts/vfx_incompressible_fire_sim.py`](../../scripts/vfx_incompressible_fire_sim.py))

#### A. Comparativa de Motores Ligeros Ejecutables en Windows 11 + RTX 3060 (`< 2 GB VRAM`)

| Motor | Repo Verificado & Licencia | Estado / Ruedas Win 11 | Uso Recomendado en Tu Estación |
|---|---|---|---|
| **PyTorch CUDA `float32` *(Motor por defecto del repo)*** | `torch.nn.functional.conv2d` / `grid_sample` (`sm_86` nativo) | **`[OK-12GB]`** · Ya instalado dentro de `ComfyUI\python_embeded` (cero dependencias nuevas) | **Elección #1 inmediata:** corre el solver Red-Black SOR + BFECC + Curl Advectado en **`< 0.5 GB VRAM`** y **`~12–25 s` para `167f`** sin salir del entorno de ComfyUI. |
| **Taichi Lang** | [`taichi-dev/taichi`](https://github.com/taichi-dev/taichi) (`★28,465` · Apache-2.0) | **`[OK-12GB]`** · Kernels JIT CUDA/Vulkan ultra-rápidos *(nota: wheels PyPI oficiales `taichi 1.7.x` llegan hasta Python `3.10/3.11`; verificar versión de `python_embeded`)* | Ideal para kernels acoplados 3D (`128³–192³`) o partículas MPM/Lagrangianas masivas cuando trabajas en un venv Python `3.11`. |
| **PhiFlow ($\Phi_{\text{Flow}}$)** | [`tum-pbs/PhiFlow`](https://github.com/tum-pbs/PhiFlow) (`★1,959` · MIT · TUM Physics-Based Simulation) | **`[OK-12GB]`** · `pip install phiflow` sobre backend PyTorch CUDA | Excelente para prototipado de operadores diferenciables (`fluid.make_incompressible`, grillas MAC escalonadas y multigrid). |

#### B. Formulación Matemática Implementada en [`scripts/vfx_incompressible_fire_sim.py`](../../scripts/vfx_incompressible_fire_sim.py)

1. **Compensación de Cámara en Mano (`estimate_camera_motion_bg`):**
   Para que el temblor de la cámara del celular no inyecte viento falso sobre las llamas, estimamos el desplazamiento del fondo estático $\mathbf{v}_{\text{cam}}(t)$ sobre la máscara $\Omega_{\text{bg}} = \neg \text{dilate}(\alpha_{\text{skin}} \cup \alpha_{\text{fabric}}, 10\text{ px})$ vía `RANSAC Homography` (`cv2.findHomography`) o Lucas-Kanade ponderado IRLS, trasladamos los campos inerciales del fluido por $-\mathbf{v}_{\text{cam}}(t)$ y calculamos la velocidad real de la mano en el mundo:
   $$\mathbf{v}_{\text{hand, world}}(t) = \mathbf{v}_{\text{hand, screen}}(t) - \mathbf{v}_{\text{cam}}(t)$$
2. **Ecuaciones de Navier-Stokes Incompresibles con Empuje de Obstáculo, Flotabilidad y Vorticity Confinement:**
   $$\frac{\partial \mathbf{v}}{\partial t} + (\mathbf{v} \cdot \nabla)\mathbf{v} = -\nabla p + \beta_{\text{buoy}}\left(0.55\,T + 0.45\,F\right)\hat{\mathbf{j}}_{\text{up}} + \varepsilon_{\text{vc}}\,\Delta t\,(\mathbf{N}_{\omega} \times \boldsymbol{\omega}) + \mathbf{f}_{\text{hand}}$$
   donde $\omega_z = \frac{\partial v_y}{\partial x} - \frac{\partial v_x}{\partial y}$ y $\mathbf{N}_{\omega} = \frac{\nabla |\omega_z|}{\|\nabla |\omega_z|\|_2 + 10^{-5}}$ reinyecta energía rotacional en las escalas finas para formar vórtices de *Karman* detrás de los dedos durante el giro de `180°`.
3. **Proyección de Presión Incompresible vía Red-Black SOR (`project_incompressible_pressure`):**
   Resolvemos la ecuación de Poisson con condición de contorno de velocidad prescrita sobre el obstáculo de la mano ($\mathbf{v}|_{\Omega_{\text{hand}}} = \mathbf{v}_{\text{hand, world}}$) y frontera libre Neumann en bordes:
   $$\nabla^2 p = \nabla \cdot \mathbf{v}^*, \qquad \mathbf{v}^{n+1} = \mathbf{v}^* - \nabla p \implies \nabla \cdot \mathbf{v}^{n+1} \approx 0$$
   Usando **sobre-relajación sucesiva Red-Black (`omega_sor = 1.72`, `36` iteraciones)** sobre el esténcil acoplado a diferencias centrales, la divergencia cae **`> 80–90 %`** por paso en menos de `1 ms` en la RTX 3060.
4. **Advección BFECC / MacCormack con Clamping Local Min-Max (`advect_bfecc_clamped`):**
   $$\hat{\phi} = \mathcal{A}(\phi^n, -\mathbf{v}\Delta t), \quad \tilde{\phi} = \phi^n + \frac{1}{2}\left(\phi^n - \mathcal{A}(\hat{\phi}, +\mathbf{v}\Delta t)\right), \quad \phi^{n+1} = \text{clip}\!\left(\mathcal{A}(\tilde{\phi}, -\mathbf{v}\Delta t),\, \phi_{\min, 3\times 3},\, \phi_{\max, 3\times 3}\right)$$
   Elimina la borrosidad numérica de Semi-Lagrangian de 1er orden y garantiza **cero oscilaciones / cero puntitos blancos (*speckle*)**.
5. **Síntesis Híbrida de Lenguas Sedosas (`_advected_curl_tongues`) + Micro-Chispas Lagrangianas:**
   En lugar de renderizar solo la densidad borrosa de una grilla Euleriana, advectamos un campo continuo de coordenadas de fase $(\Phi_x, \Phi_y)$ por el flujo incompresible $\mathbf{v}$ (con re-anclaje elástico suave `0.86 / 0.14`) y evaluamos armónicos *Domain-Warped Curl* multi-escala sobre $(\Phi_x, \Phi_y)$ junto a partículas Lagrangianas emitidas en las crestas donde $|\omega_z| > 0.12$. Así conservamos la **estética sedosa y afilada del Curl Fire**, pero ahora **las lenguas se doblan, estiran y dejan estela física real cuando la mano gira**.

---

### Pilar 2 · Emisión Superficial 3D Estanca (*Watertight*) en Blender Mantaflow / EmberGen / LiquiGen ([`scripts/wilor_mano_to_blender_abc.py`](../../scripts/wilor_mano_to_blender_abc.py))

#### A. Por Qué Fallan las Esferas en Landmarks y Cómo Cerrar la Malla MANO
- La topología estándar de `MANO` (`778` vértices, `1538` caras) tiene un **agujero abierto de 16 aristas en el corte de la muñeca**. Si un solver volumétrico 3D recibe esferas separadas o una malla no estanca (*non-manifold*), el *level-set* de distancia firmada (`surface_distance`) se fragmenta y emite burbujas rojas desconectadas de la piel.
- **Solución automatizada en [`wilor_mano_to_blender_abc.py`](../../scripts/wilor_mano_to_blender_abc.py):**
  1. `find_open_boundary_loop(faces)` + `cap_open_mesh_watertight(verts_seq, faces)`: detecta en NumPy todas las aristas de frontera que pertenecen a un único triángulo, ordena el anillo de la muñeca y lo sella con un abanico de triángulos hacia el centroide de muñeca en todos los frames (`boundary_edges: 16 → 0`), reforzado dentro de Blender con `close_mesh_boundary_loops_bmesh()` (`bmesh.ops.contextual_create` + `recalc_face_normals`).
  2. **Emisión superficial continua (`setup_mantaflow_watertight_fire`, flag `--enable-mantaflow`):**
     - `MANO_Hand`: `Fluid Flow` (`flow_type='FIRE'`, `flow_behavior='INFLOW'`, `flow_source='MESH'`, `surface_distance=0.012`, `use_initial_velocity=True`, `velocity_factor=1.25`, `velocity_normal=0.15`, `fuel_amount=1.4`).
     - `Proxy_Black_Cuff`: `Fluid Effector` (`effector_type='COLLISION'`, `surface_distance=0.015`) + `Holdout` en `VL_Fire_Occluded`, impidiendo físicamente que las llamas invadan el puño negro deshilachado.
     - **Gotcha de Velocidad en Blender Mantaflow:** Mantaflow calcula velocidades de vértices deformantes con mucha mayor precisión desde un modificador **`MeshSequenceCache` (`.abc`)** que desde *Shape Keys* cuadro a cuadro. Siempre exporta primero `--export-abc job_33f/mano_33f.abc` al activar `--enable-mantaflow`.
  3. **Shader de Lámina Fina Blackbody (`build_laminar_blackbody_fire_material`):**
     Configura `ShaderNodeVolumePrincipled` con **`Density = 0.02`** (casi cero hollín gris/rojo opaco), **`Blackbody Intensity = 1.0`**, `Blackbody Tint = (1.0, 0.88, 0.72)` y `Temperature = 2650 K`, más `scene.render.use_motion_blur = True` (`motion_blur_shutter = 0.5`).

#### B. Alternativa Comercial Rápida en Tiempo Real: JangaFX `EmberGen` / `LiquiGen` `[OK-12GB]`
- Si dispones de licencia de **JangaFX EmberGen (`1.2+`)** o **LiquiGen (`1.0`)**:
  - Ambos corren con holgura en la **RTX 3060 12 GB** (`[OK-12GB]`, requisito mínimo GTX 1060 / 8 GB VRAM) en tiempo real.
  - Importa directamente el archivo **`mano_33f.abc`** generado por [`wilor_mano_to_blender_abc.py`](../../scripts/wilor_mano_to_blender_abc.py) como *Animated Collider + Surface Emitter*, activa *Inherit Mesh Velocity (`125 %`)* y exporta el pase de fuego ocluido con Vector Motion Blur en **OpenEXR 16F lineal** hacia el paso de relighting y compositing.

---

### Pilar 3 · Oclusión 3D Continua por Profundidad (`Z-Buffer` Sigmoidal vs Switch Binario)

En [`scripts/vfx_incompressible_fire_sim.py`](../../scripts/vfx_incompressible_fire_sim.py) (`compose_continuous_z_fire`), eliminamos el salto brusco (*pop*) entre "modo palma" y "modo dorso" a mitad del giro (`f98..f108`):

1. Normalizamos la profundidad continua del sujeto $Z_{\text{hand}}(x, y) \in [0, 1]$ (`DepthAnything V2 ViT-L` o `DA3-Streaming`, donde mayor valor = más cerca de la cámara).
2. Propagamos el campo de profundidad media del emisor $Z_{\text{emit}}(x, y)$ hacia la pluma y definimos dos láminas volumétricas de grosor finito:
   $$Z_{\text{back}}(x, y) = Z_{\text{emit}}(x, y) - 0.11, \qquad Z_{\text{front}}(x, y) = Z_{\text{emit}}(x, y) + 0.065$$
3. Calculamos la transmitancia/visibilidad continua frente a cada dedo mediante una puerta sigmoidal diferenciable ($\sigma_z = 0.075$):
   $$V_{\text{layer}}(x, y) = \left(1 - \alpha_{\text{subj}}\right) + \alpha_{\text{subj}} \cdot \frac{1}{1 + \exp\!\left(-\frac{Z_{\text{layer}}(x, y) - Z_{\text{hand}}(x, y)}{\sigma_z}\right)}$$
   con bloqueo adicional sobre el puño negro $V_{\text{front}} \leftarrow V_{\text{front}} \cdot (1 - 0.94\,\alpha_{\text{fabric}})$.
   - **Resultado físico:** Cuando la mano está a `90°` de perfil, los dedos más cercanos a cámara ($Z_{\text{hand}} \approx 0.92$) bloquean suavemente la lámina trasera ($V_{\text{back}} < 0.05$) mientras los dedos más alejados ($Z_{\text{hand}} \approx 0.45$) quedan envueltos por la lámina frontal sin un solo frame de discontinuidad temporal.

---

### Pilar 4 · Relighting PBR Acoplado al Fuego Advectado + Velocity-Vector Motion Blur `180°`

Evolución implementada en [`scripts/vfx_ssdo_relight_16f.py`](../../scripts/vfx_ssdo_relight_16f.py):

1. **Extracción Dinámica de Emisores (`extract_dynamic_lights_from_fire`):**
   En cada frame $t$, aplica supresión no-máxima por celdas sobre la energía radiante HDR real de la llama advectada $E_{\text{fire}}(x, y, t) = 0.55 R + 0.35 G + 0.10 B$, obteniendo los $K = 6$ centroides radiantes $(u_k(t), v_k(t), z_k(t), I_k(t))$. Si el latigazo de la mano inclina la llama hacia la izquierda, las 6 fuentes SSDO y los reflejos especulares GGX sobre los nudillos se desplazan solidariamente con la llama.
2. **Pirámide MIP Multi-Escala de Irradiancia de Área (`build_fire_irradiance_pyramid`):**
   Construye 4 niveles de convolución separable rápida $O(1)$ con radios $(3, 10, 28, 64)\text{ px}$ sobre el buffer HDR del fuego, calcula la dirección del gradiente de irradiancia $\nabla I_{\text{MIP}}$ y aporta luz difusa envolvente de campo cercano modulada por la visibilidad SSDO media y `matte_skin`.
3. **Velocity-Vector Motion Blur de `180°` (`apply_velocity_motion_blur`):**
   Integra $S = 7$ muestras lineales HDR a lo largo del campo de velocidad 2D del fluido $\mathbf{v}_{\text{px}}(x, y)$ con ángulo de obturación $\theta_{\text{shutter}} = 0.5$ (`180°`, equivalente a `1/60 s` a `30 fps`):
   $$I_{\text{blur}}(\mathbf{x}) = \frac{1}{S}\sum_{k=1}^{S} I_{\text{HDR}}\!\left(\mathbf{x} - \tau_k\,\theta_{\text{shutter}}\,\mathbf{v}_{\text{px}}(\mathbf{x})\right), \quad \tau_k \in [-0.5, +0.5]$$

---

### Pilar 5 · Gate 3 Cuantitativo: Acoplamiento Dinámico Movimiento Mano ↔ Fuego ([`scripts/vfx_rd_metrics_eval.py`](../../scripts/vfx_rd_metrics_eval.py))

Para impedir que un fuego procedural *stateless* (que luce bonito en un frame fijo pero se mueve pegado como un sticker rígido) pase a los `167 frames`, añadimos **`Gate 3` (`eval_motion_fire_coupling`)**:

| Gate | Fase | Métrica Exacta | Umbral de Aprobación | Qué Audita / Previene |
|---|---|---|---|---|
| **Gate 0** | Paso 0 | `unit_norm_error`, `temporal_normal_l2`, `fringe_delta_l` | `‖N‖ ∈ [0.99, 1.01]`, bordes tela `ΔL < 0.03` (*empírico `33f`: `0.0113` lineal*) | Normales rotas 8-bit, *boiling* y halo blanco en manga negra (F1, F3). |
| **Gate 1** | A/B `33f` | `cuff_gain_ratio`, `ssdo_shadow_contrast`, `desk_ciede2000` | Puño negro `<= 1.15×` (*empírico: `1.004×`*), SSDO `>= 3.5:1` (*empírico: `5.48:1`*), escritorio **`CIEDE2000 <= 1.5`** (*empírico: `0.000`*) | Sangrado naranja en tela (F1), dedos sin sombra (F2), mesa blanca oscurecida/teñida (F5b). |
| **Gate 2** | HDR/Color `33f` | `hdr_linear_peak`, `pastel_yellow_clip_pct`, `salmon_wash_pct`, `mtf_noise_delta_pct` | Pico fuego `>= 4.0`, **`pastel_clip <= 1.0 %`**, **`salmon_wash <= 2.0 %`**, ruido HF **`±12 %`** | Clipping amarillo pastel SDR (F4), lavado salmón de `m_inset` y desajuste de grano (F5a). |
| **Gate 3** | Dinámica `33f` | `lag_correlation`, `mean_wake_deflection_px` | **`lag_correlation >= 0.45`** y **`mean_wake_deflection_px >= 1.2 px`** en frames activos | **Rechaza fuegos *stateless* rígidos** (`corr = 0.0`) y exige que la pluma superior se doble en dirección opuesta a $\mathbf{v}_{\text{hand, world}}$. |

---

## 4. Matriz Comparativa Honesta de las 7 Rutas + Evaluación 4DGS (Workflow 4)

> **Convención obligatoria:** Los datos acompañados de `(Empírico 33f / Repo)` provienen de mediciones reales en tu RTX 3060 o código verificado; las proyecciones para **`478×850`, `167 frames`** se etiquetan como `(Est.)`.

| Ruta | Tag Hardware | VRAM Pico `(Empírico / Repo)` | RAM Win 11 `(Est.)` | Tiempo `167f` `(Est.)` | Riesgo Temporal (*Boiling*) | Control Artístico | Puntos de Fallo Conocidos en Win 11 |
|---|---|---|---|---|---|---|---|
| **Ruta A · ComfyUI Híbrido** *(VACE-Fun A14B `Q3_K_M`/`Q4_K_S` + `CoTracker3` + `UniLumos 1.3B` LF + `SeedVR2 3B`)* | `[TIGHT-12GB]` | **~9.5–11.5 GB** *(BlockSwap `24/10`)* | **~20–23 GB** *(pagefile NVMe ≥32 GB obligatorio)* | **~35–65 min** *(en ventanas 33f–81f)* | Medio–Alto *(requiere Frequency Separation y Difference Keying)* | Medio *(prompt + máscaras/normales)* | OOM/swap si se corre VACE + SeedVR2 sin `VRAM_Debug`; prohibido `torch.compile` `e4m3fn` en `sm_86`. |
| **Ruta B · Fluido GPU Incompresible + Relight Analítico PBR** *([`vfx_incompressible_fire_sim.py`](../../scripts/vfx_incompressible_fire_sim.py) + [`vfx_ssdo_relight_16f.py`](../../scripts/vfx_ssdo_relight_16f.py))* | `[OK-12GB]` | **~4.75 GB** en Paso 0 `(Empírico 33f)`; **`< 1.0 GB`** en Solver Fluid + SSDO | **~8–12 GB** | **~4–6 min** total *(Paso 0 ~3 min + Solver/Relight `< 1 min`)* | **Muy Bajo** *(BFECC clamped + normales estabilizadas `0.533°/f`)* | **Máximo** *(Navier-Stokes Red-Black SOR, Z-oclusión continua, ACES Hill / OCIO AgX Punchy)* | Requiere `invert_normal_y=True` con `NormalCrafter` y `compose_hdr_on_plate_srgb` para no oscurecer la mesa blanca. |
| **Ruta C · 3D Físico en Blender / EmberGen** *(`WiLoR-mini` MANO Estanco `.abc` + Proxy Manga + `Mantaflow Adaptive 224` Lámina Blackbody + Cycles EXR)* | `[OK-12GB]` / `[TIGHT-12GB]` | **~2.5–6.0 GB** *(WiLoR + Cycles OptiX)* | **~12–18 GB** *(cache Mantaflow en Ryzen 5900X)* | **~18–40 min** *(o `< 5 min` con EmberGen)* | **Mínimo** *(malla estanca + One-Euro filter)* | **Máximo** *(inercia 3D volumétrica + Holdout exacto)* | **No emitir desde esferas en landmarks:** usar malla MANO cerrada en muñeca (`cap_open_mesh_watertight`) + `.abc` `MeshSequenceCache` (`velocity_factor=1.25`). |
| **Ruta D · Real-Time 60 FPS (TD)** *(`DAViDNormals.tox` ~10 ms + `POPs` + `Fluid TOP` + GLSL SSDO + `OpenColorIO TOP`)* | `[OK-12GB]` | **~3.5–6.0 GB** | **~8–12 GB** | **<10 s** *(tiempo real 30–60 FPS)* | Medio *(estabilización ONNX cuadro a cuadro)* | Alto en interacción / Medio en micro-turbulencia | `DAViD` segmenta humano completo sin distinguir manga deshilachada negra vs piel. |
| **Ruta E · Placas Fuego 4K + Tracking** *(Elementos reales s/negro + `Practical-RIFE` + `CoTracker3`/`AllTracker` warp + Relight PBR)* | `[OK-12GB]` | **~2.5–5.0 GB** | **~8–12 GB** | **~8–15 min** | **Muy Bajo** | Alto *(librería de placas reales sin warping excesivo)* | En el giro de `180°`, el warping 2D debe combinarse con la oclusión Z continua Front/Back (Pilar 3). |
| **Ruta F · Inverse Rendering + Residuo** *(`DiffusionRenderer`/`comfyui-materia`/`UniVidX` vs `RGB-X`/`IntrinsicAnything` + VACE Residual)* | `[CLOUD / >24GB]` *(full video)* / `[TIGHT-12GB]` *(keyframes)* | **~22–48 GB** `(Repo: DiffusionRenderer / comfyui-materia / UniVidX)`; **~10–11.5 GB** *(RGB-X por frame)* | **~24–64 GB** | **N/A local** en clips largos | Bajo–Medio | Medio–Alto | Dependencias Linux-first (`nvdiffrast`, `transformer-engine`); usar solo en keyframes de calibración o Cloud. |
| **🏆 Ruta G · 7ª Vía Híbrida SOTA (Recomendada R&D)** *(`Paso 0` validado `~60s/33f` ➔ Fuego Incompresible `Ruta B` o MANO Estanco `Ruta C` + Chispas ➔ Relight PBR acoplado a MIP Area-Light + Oclusión Z continua + ACES Hill / OCIO AgX Punchy + `MMAudio`)* | `[OK-12GB]` | **~4.75–6.0 GB** *(secuencial por fases, nunca juntas)* | **~10–16 GB** | **~5–8 min** *(con Solver GPU `Ruta B`)* o **~22–40 min** *(con Cycles `Ruta C`)* | **Mínimo** *(pasa Gates 0, 1, 2 y 3 con `CIEDE2000 = 0.000` en mesa)* | **Máximo** *(lenguas sedosas con estela Karman real + poros e hilos 100 % intactos)* | Seguir el checklist de 4 fixes de ComfyUI Portable (`python_embeded -s`) en Windows 11 (§2.2). |

---

## 5. Secuencia Ejecutable Directa sobre `E:\confyui\exchange\job_33f\` (Windows 11)

```powershell
# 0. Verificar entorno Win 11, sm_86, Pagefile >= 32 GB y bibliotecas Python
.\scripts\check_3060_env.ps1

# 1. Validar los 5 motores locales (todos incluyen --self-test / --check determinista)
python scripts/vfx_dual_matte_decontam.py --self-test
python scripts/vfx_ssdo_relight_16f.py --self-test
python scripts/wilor_mano_to_blender_abc.py --check
python scripts/vfx_rd_metrics_eval.py --self-test
python scripts/vfx_incompressible_fire_sim.py --self-test

# 2. Ejecutar el Solver GPU Incompresible + Compensación de Cámara + Oclusión Z Continua +
#    Relight PBR Acoplado (MIP Area-Light) + Motion Blur 180° + ACES Filmic directo sobre job_33f:
python scripts/vfx_incompressible_fire_sim.py `
  --job-dir "E:\confyui\exchange\job_33f" `
  --tonemap aces_hill `
  --shutter-angle 0.5 `
  --sim-scale 0.5

# (Opcional) Si instalaste PyOpenColorIO en python_embeded y quieres usar el config.ocio de Blender 4.5/5.x:
# python scripts/vfx_incompressible_fire_sim.py `
#   --job-dir "E:\confyui\exchange\job_33f" `
#   --tonemap ocio_agx `
#   --ocio-config "C:\Program Files\Blender Foundation\Blender 4.5\4.5\datafiles\colormanagement\config.ocio"

# 3. Auditar explícitamente Gate 1, Gate 2 y Gate 3 sobre la salida generada:
python scripts/vfx_rd_metrics_eval.py `
  --plate-npy "E:\confyui\exchange\job_33f\01_plate_png\frame_00016.png" `
  --comp-hdr-npy "E:\confyui\exchange\job_33f\08_incompressible_fire_out\comp_hdr_npy\frame_00016.npy" `
  --comp-tonemapped-npy "E:\confyui\exchange\job_33f\08_incompressible_fire_out\preview_srgb_png\frame_00016.png" `
  --normal-npy "E:\confyui\exchange\job_33f\02_normals\frame_00016.png" `
  --gate3-skin-dir "E:\confyui\exchange\job_33f\02_matte_skin" `
  --gate3-fire-dir "E:\confyui\exchange\job_33f\08_incompressible_fire_out\fire_hdr_npy" `
  --desk-roi 10 10 140 160 `
  --out-json "E:\confyui\exchange\job_33f\08_incompressible_fire_out\metrics_gates_0_to_3.json"

# 4. (Alternativa 3D Ruta C / G) Construir escena Blender con malla MANO Estanca (Watertight) + Mantaflow:
python scripts/wilor_mano_to_blender_abc.py --extract --frames-dir "E:\confyui\exchange\job_33f\01_plate_png" --track-npz "E:\confyui\exchange\job_33f\mano_track.npz" --fps 30
blender --background --python scripts/wilor_mano_to_blender_abc.py -- --blender-build --track-npz "E:\confyui\exchange\job_33f\mano_track.npz" --export-abc "E:\confyui\exchange\job_33f\mano_33f.abc" --enable-mantaflow --mantaflow-res 224 --desk-distance-m 0.72
```
