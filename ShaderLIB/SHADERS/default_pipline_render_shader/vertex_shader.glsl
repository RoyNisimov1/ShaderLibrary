#version 460 core

in vec2 vert;
in vec2 texcoord;

out vec2 uvs;

void main(){
    uvs = texcoord;
    gl_Position = vec4(vert.x, vert.y, 0.0, 1.0);
}