// TouchDesigner GLSL MAT (Pixel Shader) — Beauty + Normal AOV en 1 solo Render Pass (MRT)
//
// CONFIGURACION EN TOUCHDESIGNER (2025.33230+):
// 1. Render TOP -> pestaña "Advanced" / "Common":
//    - `# Of Color Buffers`: 2
//    - `Pixel Format`: 16-bit float (RGBA) o 32-bit float (RGBA) para precisión VFX sin banding.
// 2. GLSL MAT -> usa "Output Shader" en TouchDesigner como base para el Vertex Shader y
//    pega este código como Pixel Shader (100% compatible con iVert estándar, sin editar el Vertex Shader!).
// 3. Render Select TOP -> apunta `TOP` al `Render TOP` y pon `Color Buffer Index = 1` para sacar las Normales a 60 FPS!
//
// Por defecto exporta OpenGL Camera-Space Normal empaquetada [0, 1]: RGB = N * 0.5 + 0.5.
// Define `#define RAW_FLOAT_NORMALS 1` si quieres vectores [-1, +1] crudos en Color Buffer de 32-bit float.

#define RAW_FLOAT_NORMALS 0

uniform vec4 uBaseColor; // opcional (ej. vec4(0.85, 0.85, 0.85, 1.0))

in Vertex {
    vec4 color;
    vec3 worldSpacePos;
    vec3 worldSpaceNorm;
    flat int cameraIndex;
} iVert;

layout(location = 0) out vec4 oFragColor[TD_NUM_COLOR_BUFFERS];

void main() {
    TDCheckDiscard();

    vec3 nWorld = normalize(iVert.worldSpaceNorm);
    // Transforma normal de World Space -> Camera Space usando la matriz de cámara activa de TouchDesigner
    vec3 nCam   = normalize((uTDMats[iVert.cameraIndex].worldCam * vec4(nWorld, 0.0)).xyz);

    // Luz difusa mínima de preview para Buffer 0 (Beauty / puedes sustituirlo por TDLightingPBR)
    vec3 viewDir = normalize(uTDMats[iVert.cameraIndex].camInverse[3].xyz - iVert.worldSpacePos);
    float ndotv  = max(dot(nWorld, viewDir), 0.0);
    vec4 beauty  = vec4(iVert.color.rgb * (0.25 + 0.75 * ndotv), iVert.color.a);

    TDAlphaTest(beauty.a);
    oFragColor[0] = TDOutputSwizzle(beauty);

    // Buffer 1: Camera-Space Surface Normal (OpenGL +Y arriba)
    // Si prefieres World-Space para relighting fijo ante cámara en movimiento, reemplaza `nCam` por `nWorld`.
    if (TD_NUM_COLOR_BUFFERS > 1) {
        #if RAW_FLOAT_NORMALS
            oFragColor[1] = TDOutputSwizzle(vec4(nCam, beauty.a));
        #else
            vec3 packedNorm = nCam * 0.5 + 0.5;
            oFragColor[1] = TDOutputSwizzle(vec4(packedNorm, beauty.a));
        #endif
    }
}
