#version 460 core

in vec2 uvs;
uniform sampler2D tex;
uniform float u_exposure;    // Controls Vignette strength
uniform float u_rgb_shift;   // Controls horizontal displacement for Chromatic Aberration


out vec4 fragColor;

void main() {

    // 1. No Barrel Distortion: Use the input UV directly for sampling
    vec2 distorted_uv = uvs;

    // 2. Chromatic Aberration / RGB Subpixel Shift
    float shift_x = u_rgb_shift;

    // Sample R channel slightly left, B channel slightly right.
    float r = texture(tex, distorted_uv + vec2(-shift_x, 0.0)).r;
    float g = texture(tex, distorted_uv).g;
    float b = texture(tex, distorted_uv + vec2(shift_x, 0.0)).b;

    vec3 color = vec3(r, g, b);

    // 3. Scanlines (Horizontal only)
    float scanline_frequency = 400.0;
    float scanline_factor = sin(distorted_uv.y * scanline_frequency * 3.14159) * 0.5 + 0.5;
    scanline_factor = mix(0.6, 1.0, scanline_factor * scanline_factor);

    // 4. Vignette
    // Calculation remains the same, but centered on the flat plane
    vec2 center = distorted_uv - 0.5;
    float dist = dot(center, center) * 4.0;
    float vignette = 1.0 - dist * u_exposure;
    vignette = clamp(vignette, 0.0, 1.0);

    // 5. Combine effects and output
    vec3 final_color = color * vignette * scanline_factor;

    fragColor = vec4(final_color, texture(tex, uvs).a);
}