import pygame
import moderngl as mgl
import sys
import array
import math

# --- GLSL Shaders ---

# Vertex Shader: Used for both the Pixelation Pass and the CRT Pass.
VERTEX_SHADER_SOURCE = """
#version 330 core
in vec2 in_position;
in vec2 in_uv;
out vec2 v_uv;

// A 4x4 uniform matrix for transformation (e.g., translation)
uniform mat4 u_transform; 

void main() {
    // Apply the transformation matrix to the input position.
    gl_Position = u_transform * vec4(in_position, 0.0, 1.0);
    v_uv = in_uv;
}
"""

# Fragment Shader 1 (Pass 1): Pixelation Effect
PIXELATION_FRAGMENT_SHADER_SOURCE = """
#version 330 core
in vec2 v_uv;
uniform sampler2D u_texture;
uniform float u_pixel_count; 

out vec4 fragColor;

void main() {
    // 1. Calculate the pixel block coordinate (0 to u_pixel_count)
    vec2 pixel_coord = v_uv * u_pixel_count;

    // 2. Snap to the grid point
    vec2 snapped_coord = floor(pixel_coord);

    // 3. Scale back to the normalized UV range (0.0 to 1.0)
    vec2 pixelated_uv = snapped_coord / u_pixel_count;

    // 4. Sample the currently bound texture
    fragColor = texture(u_texture, pixelated_uv);
}
"""

# Fragment Shader 2 (Pass 2): CRT Effect
CRT_FRAGMENT_SHADER_SOURCE = """
#version 330 core
in vec2 v_uv;
uniform sampler2D u_texture;
uniform float u_exposure; // Repurposed to control Vignette/CRT strength

out vec4 fragColor;

void main() {
    // 1. Sample the texture color (this may be the output of the Pixelation Pass)
    vec4 sampled_color = texture(u_texture, v_uv);
    vec3 color = sampled_color.rgb;

    // --- CRT Effect Components ---

    // 2. Scanlines
    float scanline_frequency = 800.0;
    float scanline_factor = sin(v_uv.y * scanline_frequency * 3.14159) * 0.5 + 0.5;
    scanline_factor = mix(0.7, 1.0, scanline_factor); 

    // 3. Vignette
    vec2 center = v_uv - 0.5;
    float dist = dot(center, center) * 4.0; 
    float vignette = 1.0 - dist * u_exposure; 
    vignette = clamp(vignette, 0.0, 1.0);

    // 4. Combine effects and output
    vec3 final_color = color * vignette * scanline_factor;

    fragColor = vec4(final_color, sampled_color.a);
}
"""


# --- ModernGL Setup and Rendering Functions ---

def create_texture_from_surface(ctx, surface):
    """Converts a Pygame surface to a ModernGL texture."""
    texture = ctx.texture(
        surface.get_size(),
        3,  # 3 color components (RGB)
        pygame.image.tobytes(surface, 'RGB')
    )
    # Set to NEAREST filter to maintain sharp pixels for the CRT effect
    texture.filter = (mgl.NEAREST, mgl.NEAREST)
    return texture


def create_quad_vao(ctx, program, vertices):
    """
    Creates a VAO from a list of vertices.
    """
    # Indices for drawing two triangles (a quad)
    indices = [0, 1, 2, 2, 1, 3]

    # Convert Python list to byte buffers for the GPU
    vbo_data = array.array('f', vertices).tobytes()
    vbo = ctx.buffer(data=vbo_data)
    ibo_data = array.array('I', indices).tobytes()
    ibo = ctx.buffer(data=ibo_data)

    content = [
        # Format: 2 floats for position, 2 floats for UV
        (vbo, '2f 2f', 'in_position', 'in_uv'),
    ]

    return ctx.vertex_array(program, content, ibo)


def create_translation_matrix(tx, ty):
    """
    Creates a simple 4x4 translation matrix for 2D movement.
    """
    return [
        1.0, 0.0, 0.0, 0.0,  # Column 1
        0.0, 1.0, 0.0, 0.0,  # Column 2
        0.0, 0.0, 1.0, 0.0,  # Column 3
        tx, ty, 0.0, 1.0  # Column 4 (Translation vector)
    ]


# --- Main Game Loop ---

def run_game():
    pygame.init()

    size = (800, 400)
    pygame.display.set_caption("ModernGL Shader Chaining (Pixelation -> CRT)")
    screen = pygame.display.set_mode(size, pygame.OPENGL | pygame.DOUBLEBUF)

    ctx = mgl.create_context()

    # --- Shader Programs ---
    crt_program = ctx.program(
        vertex_shader=VERTEX_SHADER_SOURCE,
        fragment_shader=CRT_FRAGMENT_SHADER_SOURCE,
    )
    pixelation_program = ctx.program(
        vertex_shader=VERTEX_SHADER_SOURCE,
        fragment_shader=PIXELATION_FRAGMENT_SHADER_SOURCE,
    )

    # --- 1. Create Pygame Surfaces (The Data) ---
    SURFACE_WIDTH, SURFACE_HEIGHT = 400, 400

    # Surface 1: Blue and Red Pattern (Used for Chained Effect)
    surface1 = pygame.Surface((SURFACE_WIDTH, SURFACE_HEIGHT))
    surface1.fill((100, 100, 255))
    pygame.draw.circle(surface1, (255, 50, 50), (100, 100), 80)
    pygame.draw.rect(surface1, (255, 255, 255), (200, 250, 150, 100))

    # Surface 2: Green and Yellow Pattern (Used for CRT Only Effect)
    surface2 = pygame.Surface((SURFACE_WIDTH, SURFACE_HEIGHT))
    surface2.fill((100, 255, 100))
    pygame.draw.line(surface2, (255, 255, 0), (0, 0), (SURFACE_WIDTH, SURFACE_HEIGHT), 10)
    pygame.draw.polygon(surface2, (255, 150, 0), [(50, 300), (350, 300), (200, 50)])

    # --- 2. Create ModernGL Textures from Surfaces ---
    texture1 = create_texture_from_surface(ctx, surface1)
    texture2 = create_texture_from_surface(ctx, surface2)

    # --- 3. FBO Setup (The Intermediate Target) ---
    # FBO size should match the screen area we want to cover (the left half, in this case)
    fbo_texture = ctx.texture((size[0] // 2, size[1]), components=3)
    fbo_texture.filter = (mgl.NEAREST, mgl.NEAREST)
    fbo = ctx.framebuffer(color_attachments=[fbo_texture])

    # --- 4. Base VAO Geometry ---

    # VAO 1: Left Half (X: -1.0 to 0.0). Used for both Pass 1 (FBO) and Pass 2 (Screen)
    vertices1 = [
        -1.0, -1.0, 0.0, 1.0,  # Bottom-Left
        -1.0, 1.0, 0.0, 0.0,  # Top-Left
        0.0, -1.0, 1.0, 1.0,  # Bottom-Right
        0.0, 1.0, 1.0, 0.0,  # Top-Right
    ]
    # We use the CRT program here so the VAO knows the attribute locations
    # for the final rendering pass.
    vao1 = create_quad_vao(ctx, crt_program, vertices1)

    # VAO 2: Right Surface - Small square (Moving object, CRT only)
    quad_size = 0.6
    x_start, x_end = -quad_size / 2, quad_size / 2
    y_start, y_end = -quad_size / 2, quad_size / 2

    vertices2 = [
        x_start, y_start, 0.0, 1.0,  # Bottom-Left
        x_start, y_end, 0.0, 0.0,  # Top-Left
        x_end, y_start, 1.0, 1.0,  # Bottom-Right
        x_end, y_end, 1.0, 0.0,  # Top-Right
    ]
    vao2 = create_quad_vao(ctx, crt_program, vertices2)

    # --- Shader Uniform Setup ---
    crt_strength = 0.7
    crt_program['u_exposure'] = crt_strength
    crt_program['u_texture'] = 0

    pixelation_program['u_pixel_count'] = 40.0  # Fixed pixelation amount
    pixelation_program['u_texture'] = 0

    IDENTITY_MATRIX = create_translation_matrix(0.0, 0.0)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

            # Allow dynamic CRT strength control via mouse wheel
            if event.type == pygame.MOUSEWHEEL:
                crt_strength += event.y * 0.05
                crt_strength = max(0.0, min(1.0, crt_strength))  # Clamp between 0 and 1
                crt_program['u_exposure'] = crt_strength
                pygame.display.set_caption(f"CRT Strength (Vignette): {crt_strength:.2f}")

        # --- ANIMATION: Calculate Movement ---
        time = pygame.time.get_ticks() / 1000.0

        x_offset = 0.5 + 0.25 * math.sin(time * 1.5)
        y_offset = 0.0 + 0.5 * math.cos(time * 0.8)

        transform2 = create_translation_matrix(x_offset, y_offset)

        # --- Rendering Loop ---
        ctx.clear(0.1, 0.1, 0.1)
        ctx.enable(mgl.BLEND)

        # =======================================================
        # 1. CHAINED PASS: Render Left Half (Pixelation -> CRT)
        # =======================================================

        # --- Pass 1: Pixelation (Input: texture1, Output: fbo) ---
        fbo.use()
        fbo.clear(0.0, 0.0, 0.0)  # Clear the FBO content

        # CORRECTED: Set program via ctx.program
        ctx.program = pixelation_program
        pixelation_program['u_transform'].write(array.array('f', IDENTITY_MATRIX))
        texture1.use(0)
        # Render the full left quad geometry into the FBO
        vao1.render(mgl.TRIANGLE_STRIP)

        # --- Pass 2: CRT (Input: fbo_texture, Output: screen) ---
        ctx.screen.use()  # Switch render target back to the screen

        # CORRECTED: Set program via ctx.program
        ctx.program = crt_program
        crt_program['u_transform'].write(array.array('f', IDENTITY_MATRIX))
        fbo_texture.use(0)  # The FBO's texture is now the input for the CRT shader
        # Render the full left quad geometry to the screen
        vao1.render(mgl.TRIANGLE_STRIP)

        # =======================================================
        # 2. STANDARD PASS: Render Right Half (CRT Only)
        # =======================================================

        # --- Draw Surface 2 (Moving Square - CRT Only) ---
        # Uses texture2 as input
        # CORRECTED: Set program via ctx.program
        ctx.program = crt_program
        crt_program['u_transform'].write(array.array('f', transform2))
        texture2.use(0)  # Use the original texture2 as input
        vao2.render(mgl.TRIANGLE_STRIP)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    run_game()
