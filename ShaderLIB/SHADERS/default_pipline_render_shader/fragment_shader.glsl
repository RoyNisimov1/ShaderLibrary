#version 460 core
in vec2 uvs;
uniform sampler2D tex;

out vec4 fragColor;

void main() {
    fragColor = texture(tex, uvs);
}