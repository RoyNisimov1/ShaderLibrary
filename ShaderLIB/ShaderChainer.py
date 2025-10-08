
from ShaderLibrary.ShaderLIB.Shader import Shader

class ShaderChainer:

    def __init__(self, shaders: list[Shader], ctx, screen_size):
        self.shaders = shaders
        self.ctx = ctx
        self.screen_size = screen_size
        self.color_texture = ctx.texture(self.screen_size, 4)  # RGBA texture

        # Create the framebuffer
        self.fbo = ctx.framebuffer(
            color_attachments=[self.color_texture],
        )

    def render(self, surf, pos_rect, render_fbo=None, args_for_shaders: list[dict]= None):
        self.fbo.clear()
        if args_for_shaders is None:
            args_for_shaders = []
            for i in range(len(self.shaders)):
                args_for_shaders.append({})
        if len(args_for_shaders) < len(self.shaders):
            for i in range(len(self.shaders) - len(args_for_shaders)):
                args_for_shaders.append({})

        for i in range(len(self.shaders) - 1):
            if i == 0:
                self.shaders[i].render(surf, pos_rect, self.fbo, **args_for_shaders[i])
                continue
            self.shaders[i].render_texture(self.color_texture, self.fbo, **args_for_shaders[i])
        self.shaders[len(self.shaders)-1].render_texture(self.color_texture, render_fbo, flip_y=True,  **args_for_shaders[len(self.shaders)-1])


    def render_framebuffer(self, render_fbo=None, args_for_shaders: list[dict]= None):
        self.fbo.clear()
        if args_for_shaders is None:
            args_for_shaders = []
            for i in range(len(self.shaders)):
                args_for_shaders.append({})
        if len(args_for_shaders) < len(self.shaders):
            for i in range(len(self.shaders) - len(args_for_shaders)):
                args_for_shaders.append({})

        for i in range(len(self.shaders) - 1):
            if i == 0:
                self.shaders[i].render_frame_buffer(render_fbo, **args_for_shaders[i])
                continue
            self.shaders[i].render_frame_buffer(render_fbo, **args_for_shaders[i])
        self.shaders[len(self.shaders) - 1].render_frame_buffer(render_fbo, flip_y=True,
                                                           **args_for_shaders[len(self.shaders) - 1])
