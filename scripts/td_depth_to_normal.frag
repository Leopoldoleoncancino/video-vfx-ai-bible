// TouchDesigner GLSL TOP — Depth Map -> Camera-Space Normal Map (<1 ms GPU)
//
// Convierte un Z-Depth en tiempo real (ej. `Depth TOP`, `Depth Anything 2/3` en td-native-inference
// o `BlenderDepth` vía Spout2) en un Normal Map OpenGL (+Y) o DirectX (-Y) sin costo de otro modelo IA.
//
// USO EN TOUCHDESIGNER:
// 1. Conecta tu textura Depth (monocromática, idealmente 16-bit/32-bit float) a la Entrada 0 del `GLSL TOP`.
// 2. En Common del GLSL TOP -> `Pixel Format`: 16-bit float (RGBA) o 32-bit float (RGBA).
// 3. Ajusta dos uniforms en la pestaña Vectors:
//    - `uStrength`: ~4.0 a 18.0 (intensidad del relieve según escala de tu escena Z)
//    - `uFlipY`: `0.0` para OpenGL (+Y arriba: Blender/TD/Resolve/AE Normality), `1.0` para DirectX (-Y arriba)
//    - `uNearIsWhite`: `1.0` si blanco = cerca (Depth Anything / Blender Mist inverso), `0.0` si negro = cerca.

uniform float uStrength;    // Default recomendado: 8.0
uniform float uFlipY;       // 0.0 = OpenGL (+Y), 1.0 = DirectX (-Y)
uniform float uNearIsWhite; // 1.0 = blanco cerca (Depth Anything), 0.0 = blanco lejos

out vec4 fragColor;

float sampleHeight(vec2 uv) {
    float d = texture(sTD2DInputs[0], uv).r;
    // Altura relativa hacia la cámara: valor alto = más cerca.
    return (uNearIsWhite > 0.5) ? d : (1.0 - d);
}

void main() {
    vec2 px = uTD2DInputs[0].res.xy; // (1/width, 1/height)

    // Filtro Sobel 3x3 para suavizar escalonamiento de cuantización en maps de 8-bit/ONNX
    // En TouchDesigner UV(0,0) está abajo-izquierda, por lo que +px.y es ARRIBA.
    float tl = sampleHeight(vUV.st + vec2(-px.x,  px.y));
    float tc = sampleHeight(vUV.st + vec2(  0.0,  px.y));
    float tr = sampleHeight(vUV.st + vec2( px.x,  px.y));
    float ml = sampleHeight(vUV.st + vec2(-px.x,   0.0));
    float mr = sampleHeight(vUV.st + vec2( px.x,   0.0));
    float bl = sampleHeight(vUV.st + vec2(-px.x, -px.y));
    float bc = sampleHeight(vUV.st + vec2(  0.0, -px.y));
    float br = sampleHeight(vUV.st + vec2( px.x, -px.y));

    float dHdx = (tr + 2.0 * mr + br) - (tl + 2.0 * ml + bl);
    float dHdy = (tl + 2.0 * tc + tr) - (bl + 2.0 * bc + br);

    float strength = (uStrength > 0.0001) ? uStrength : 8.0;
    // Normal de z = h(x,y): (-dh/dx, -dh/dy, 1) -> OpenGL (+X derecha, +Y arriba, +Z hacia lente)
    vec3 n = normalize(vec3(-dHdx * strength, -dHdy * strength, 1.0));

    if (uFlipY > 0.5) {
        n.y = -n.y;
    }

    vec3 packedRGB = n * 0.5 + 0.5;
    fragColor = TDOutputSwizzle(vec4(packedRGB, 1.0));
}
