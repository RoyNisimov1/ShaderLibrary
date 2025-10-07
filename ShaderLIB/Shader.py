import moderngl
import pygame
import os
from array import array

class Shader:

    DEFAULT_SHADER_DIR = "ShaderLIB/SHADERS/default_pipline_render_shader"

    VERTEX_SHADER_PREFIX = "vertex_shader.glsl"
    FRAGMENT_SHADER_PREFIX = "fragment_shader.glsl"

    # Prefixes for identifying types
    SAMPLE2D_PREFIX = "sample2D_"

    def __init__(self, shader_dir_loc: str, ctx: moderngl.Context, screen_size = (1920, 1080)):
        self.dir_loc = shader_dir_loc
        self.screen_size = screen_size
        self.vertex_shader = self.get_vertex_shader()
        self.fragment_shader = self.get_fragment_shader()
        self.ctx = ctx
        self.full_screen_render_quads = Shader.create_full_screen_quad(self.ctx)
        self.program = self.ctx.program(vertex_shader=self.vertex_shader, fragment_shader=self.fragment_shader)
        self.full_screen_render_object = self.ctx.vertex_array(self.program, [(self.full_screen_render_quads, '2f 2f', 'vert', 'texcoord')])
        self.flipped_fs_quads = Shader.get_flipped_fs_quads(self.ctx)

    def render_texture(self, tex: moderngl.Texture, fbo: moderngl.Framebuffer = None, flip_y=False,**kwargs):
        if fbo is None:
            fbo = self.ctx.screen
        fbo.use()
        renderer = self.full_screen_render_object
        if flip_y:
            renderer = self.ctx.vertex_array(self.program, [(self.flipped_fs_quads, '2f 2f', 'vert', 'texcoord')])
        tex.use(0)
        self.program["tex"] = 0
        sample2D_list_to_release = []
        for k, v in kwargs.items():
            if k.startswith(Shader.SAMPLE2D_PREFIX):
                sample2D_list_to_release.append(v)
                self.program[k[len(Shader.SAMPLE2D_PREFIX):]] = v
                continue
            self.program[k] = v
        renderer.render(mode=moderngl.TRIANGLE_STRIP)
        for i, v in enumerate(sample2D_list_to_release):
            v.release()
        if renderer is not self.full_screen_render_object:
            renderer.release()

    def render_frame_buffer(self, fbo: moderngl.Framebuffer = None, flip_y=False,**kwargs):
        color_texture = self.ctx.texture(self.screen_size, 4)  # RGBA texture

        # Create the framebuffer
        fboRenderer = self.ctx.framebuffer(
            color_attachments=[color_texture],
        )

        if fbo is None:
            fbo = self.ctx.screen
        fboRenderer.use()
        renderer = self.full_screen_render_object
        if flip_y:
            renderer = self.ctx.vertex_array(self.program, [(self.flipped_fs_quads, '2f 2f', 'vert', 'texcoord')])
        tex = fbo.color_attachments[0]
        tex.use(0)
        self.program["tex"] = 0
        sample2D_list_to_release = []
        for k, v in kwargs.items():
            if k.startswith(Shader.SAMPLE2D_PREFIX):
                sample2D_list_to_release.append(v)
                self.program[k[len(Shader.SAMPLE2D_PREFIX):]] = v
                continue
            self.program[k] = v
        renderer.render(mode=moderngl.TRIANGLE_STRIP)
        self.ctx.copy_framebuffer(fbo, fboRenderer)
        for i, v in enumerate(sample2D_list_to_release):
            v.release()
        if renderer is not self.full_screen_render_object:
            renderer.release()
        color_texture.release()
        fboRenderer.release()

    def render(self, surf: pygame.Surface, pos_rect: pygame.Rect, fbo: moderngl.Framebuffer = None, **kwargs):
        if fbo is None:
            fbo = self.ctx.screen
        fbo.use()
        o = pygame.Surface(self.screen_size, pygame.SRCALPHA).convert_alpha()
        o.fill((0, 0, 0, 0))
        o.blit(surf, pos_rect)
        frame_tex = Shader.surf_to_texture(o, self.ctx)
        frame_tex.use(0)
        self.program["tex"] = 0
        sample2D_list_to_release = []
        for k, v in kwargs.items():
            if k.startswith(Shader.SAMPLE2D_PREFIX):
                sample2D_list_to_release.append(v)
                self.program[k[len(Shader.SAMPLE2D_PREFIX):]] = v
                continue
            self.program[k] = v
        self.full_screen_render_object.render(mode=moderngl.TRIANGLE_STRIP)
        frame_tex.release()
        for i, v in enumerate(sample2D_list_to_release):
            v.release()

    @staticmethod
    def surf_to_texture(surf: pygame.Surface, ctx: moderngl.Context):
        tex = ctx.texture(surf.get_size(), 4)
        tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
        tex.swizzle = "BGRA"
        tex.write(surf.get_view("1"))
        return tex

    @staticmethod
    def create_quad(surf: pygame.Surface, top_left: tuple[float, float], screen_size: tuple[int, int], ctx: moderngl.Context):
        x, y = 2 * ((top_left[0] / screen_size[0]) - 0.5), -2 * ((top_left[1] / screen_size[1]) - 0.5)
        width_r, height_r = 2 * (surf.get_size()[0] / screen_size[0]), -2 * (surf.get_size()[1] / screen_size[1])
        vert = [
            # Pose (x,y), UV (UVx, UVy)
            x, y, 0.0, 0.0,  # Top Left
            x + width_r, y, 1.0, 0.0,  # Top Right
            x, y + height_r, 0.0, 1.0,  # Bottom Left
            x + width_r, y + height_r, 1.0, 1.0,  # Bottom Right
        ]
        quad_buffer = ctx.buffer(data=array('f', vert))

        return quad_buffer

    @staticmethod
    def create_full_screen_quad(ctx: moderngl.Context):
        quad_buffer = ctx.buffer(data=array('f', [
            # Pose (x,y), UV (UVx, UVy)
            -1.0, 1.0, 0.0, 0.0,  # Top Left
            1.0, 1.0, 1.0, 0.0,  # Top Right
            -1.0, -1.0, 0.0, 1.0,  # Bottom Left
            1.0, -1.0, 1.0, 1.0,  # Bottom Right
        ]))
        return quad_buffer

    @staticmethod
    def get_flipped_fs_quads(ctx: moderngl.Context):
        quad_buffer = ctx.buffer(data=array('f', [
            # Pose (x,y), UV (UVx, UVy)
            -1.0, -1.0, 0.0, 0.0,  # Top Left
            1.0, -1.0, 1.0, 0.0,  # Top Right
            -1.0, 1.0, 0.0, 1.0,  # Bottom Left
            1.0, 1.0, 1.0, 1.0,  # Bottom Right
        ]))
        return quad_buffer

    def get_vertex_shader(self) -> str:
        shader_vert_path = os.path.join(self.dir_loc, Shader.VERTEX_SHADER_PREFIX)
        if not os.path.exists(shader_vert_path):
            shader_vert_path = os.path.join(Shader.DEFAULT_SHADER_DIR, Shader.VERTEX_SHADER_PREFIX)
            if not os.path.exists(shader_vert_path):
                raise FileNotFoundError("Default Shader Vertex file was not found!")
        contents = ""
        with open(shader_vert_path, "r") as f:
            contents = f.read()
        return contents

    def get_fragment_shader(self) -> str:
        shader_vert_path = os.path.join(self.dir_loc, Shader.FRAGMENT_SHADER_PREFIX)
        if not os.path.exists(shader_vert_path):
            shader_vert_path = os.path.join(Shader.DEFAULT_SHADER_DIR, Shader.FRAGMENT_SHADER_PREFIX)
            if not os.path.exists(shader_vert_path):
                raise FileNotFoundError("Default Shader Fragment file was not found!")
        contents = ""
        with open(shader_vert_path, "r") as f:
            contents = f.read()
        return contents



