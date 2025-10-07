#version 460 core

in vec2 uvs;
uniform sampler2D tex;
uniform vec3 color;
uniform float darkness_mult;

out vec4 fragColor;

void main() {

    vec4 textureColor = texture(tex, uvs);
    vec3 inputColor = color.rgb/255;

    float brightness = dot(textureColor.rgb, vec3(0.2126, 0.7152, 0.0722));

    float darkness = 1.0 - brightness;

    darkness = darkness * darkness_mult;

    float colorFactor = 1.0 - darkness; // This is mathematically equal to 'brightness'

    vec3 finalRGB = inputColor * colorFactor;

    fragColor = vec4(finalRGB, textureColor.a);
}