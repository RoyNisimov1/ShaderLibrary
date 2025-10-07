#version 330 core

// -------------------------------------------------------------------
// UNIFORMS (Inputs from Python/ModernGL)
// -------------------------------------------------------------------

// The texture we are sampling from.
uniform sampler2D tex; 

// Time in seconds, updated every frame by the host application.
uniform float time; 

// The texture coordinates passed from the vertex shader (typically 0.0 to 1.0).
in vec2 uvs; 

// -------------------------------------------------------------------
// OUTPUT
// -------------------------------------------------------------------

// The final color output to the framebuffer.
out vec4 fragColor;


void main() {
    // 1. Center the coordinates (-1.0 to 1.0 range, accounting for aspect ratio)
    // You should ensure 'res' matches your canvas size in Python for perfect circular warping.
    vec2 res = vec2(800.0, 600.0); 
    vec2 p = (uvs * 2.0 - 1.0) * res / res.y; 
    
    // 2. Calculate Distance and Angle (Polar Coordinates)
    float angle = atan(p.y, p.x); // Angle from the center
    float radius = length(p);      // Distance from the center
    
    // 3. Create the Complex Warping Field 'f'
    // This value 'f' now acts as the intensity and direction factor for the uvs offset.
    
    // Base wave (swirl and pulse)
    float f = sin(angle * 5.0 + time * 0.5) * 0.2; 
    
    // Layer 2: A fast, tight swirl that moves outward over time
    f += sin(radius * 10.0 + angle * 8.0 - time * 1.5) * 0.1;
    
    // Layer 3: A slow, broad movement that modulates the first two
    f += sin(radius * 3.0 - time * 0.2) * 0.3;
    
    // Add time and radius into the mix for overall movement
    f += time * 0.1;
    f += radius * 0.2;
    
    // 4. Transform Warping Field 'f' into a uvs Offset
    float offsetStrength = 0.04; // Controls how strong the warp is (0.0 means no warp)
    
    // Use 'f' to generate smooth, swirling x and y offsets.
    vec2 offset = vec2(
        sin(f * 5.0) * cos(time * 0.5), // X offset
        cos(f * 5.0) * sin(time * 0.7)  // Y offset
    ) * offsetStrength;
    
    // 5. Apply the offset to the original uvss and sample the texture.
    vec2 distorteduvs = uvs + offset;

    // Correct for tiling/wrapping issues if the uvss go outside [0, 1]
    distorteduvs = fract(distorteduvs); 

    vec4 textureColor = texture(tex, distorteduvs);
    
    // 6. Apply a dark vignette/falloff effect at the edges for presentation
    float vignetteFactor = smoothstep(2.0, 0.8, radius); 
    
    // 7. Output the final, warped color.
    fragColor = vec4(textureColor.rgb * vignetteFactor, 1.0);
}