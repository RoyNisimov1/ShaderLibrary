import math
import sys

import pygame
import moderngl

from ShaderLIB.Shader import Shader
from ShaderLIB.ShaderChainer import ShaderChainer

from array import array

pygame.init()
SCREEN_SIZE = (1920, 1080)
display = pygame.display.set_mode(SCREEN_SIZE, pygame.OPENGL | pygame.DOUBLEBUF)
screen = pygame.Surface((SCREEN_SIZE[0], SCREEN_SIZE[1]), pygame.SRCALPHA)
ctx = moderngl.create_context()
ctx.enable(moderngl.BLEND)
ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)

color_texture = ctx.texture(SCREEN_SIZE, 4) # RGBA texture

# Create the framebuffer
fbo = ctx.framebuffer(
    color_attachments=[color_texture],
)


clock = pygame.time.Clock()


img2 = pygame.image.load("test_bg.jpg").convert()
pnois = pygame.transform.smoothscale(img2, SCREEN_SIZE)

default_pipline_shader = Shader("ShaderLIB/SHADERS/default_pipline_render_shader", ctx, screen_size=SCREEN_SIZE)
crt_shader = Shader("ShaderLIB/SHADERS/crt_shader", ctx, screen_size=SCREEN_SIZE)
bg_shader = Shader("ShaderLIB/SHADERS/bg_pnois_shader", ctx, screen_size=SCREEN_SIZE)
bg_shader2 = Shader("ShaderLIB/SHADERS/bg_noise_shader2", ctx, screen_size=SCREEN_SIZE)
pixalation_shader = Shader("ShaderLIB/SHADERS/pixalation_shader", ctx, screen_size=SCREEN_SIZE)

pixalation_normal_shader_chain = ShaderChainer([pixalation_shader, default_pipline_shader], ctx, SCREEN_SIZE)
bg_shaders = ShaderChainer([bg_shader, bg_shader2], ctx, SCREEN_SIZE)


fps = 60
running = True
delta_time = 0.1
t = 0
bg_color = (90, 158, 81)

while running:
    ctx.clear()
    fbo.clear()
    screen.fill((0, 0, 0, 1))
    t += delta_time
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    # default_pipline_shader.render(screen, (0, 0), fbo=fbo)

    # bg_shader.render(pnois, (0, 0), color=bg_color, darkness_mult=0.5,fbo=fbo)
    #
    # bg_shader2.render_texture(color_texture, flip_y=True, time=t)

    bg_shaders.render(pnois, (0, 0), fbo, [{"color": bg_color, "darkness_mult": 0.5}, {"time": t}])
    #pixalation_normal_shader_chain.render(screen, (0, 0), fbo, args_for_shaders=[{"pixelSize": 5}])

    #pixalation_shader.render_frame_buffer(fbo=fbo, pixelSize=1000)
    crt_shader.render_frame_buffer(fbo=fbo, u_rgb_shift=0.01)

    default_pipline_shader.render_texture(color_texture, flip_y=True)

    pygame.display.flip()

    delta_time = clock.tick(fps) / 1000
    delta_time = max(0.001, min(0.1, delta_time))

ctx.release()

pygame.quit()
sys.exit()



