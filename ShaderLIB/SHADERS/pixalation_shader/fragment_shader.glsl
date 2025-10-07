#version 460 core

uniform sampler2D tex;
uniform int pixelSize;

in vec2 uvs; 

out vec4 fragColor;


void main() {

    vec2 scaleduvs = uvs * float(pixelSize);
    vec2 pixelateduvs_index = floor(scaleduvs) + 0.5;
    vec2 finaluvs = pixelateduvs_index / float(pixelSize);
    vec4 textureColor = texture(tex, finaluvs);
    fragColor = textureColor;
}