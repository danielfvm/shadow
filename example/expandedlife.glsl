#version 330 core

#define RADIUS 5

#ifdef GL_ES
precision highp float;
#endif

uniform vec2 resolution;
uniform float time;
uniform vec2 mouse;
uniform sampler2D prevBuffer;

float random (in vec2 point) {
	return fract(100.0 * sin(point.x + fract(100.0 * sin(point.y)))); // http://www.matteo-basei.it/noise
}

layout(location = 0) out vec4 diffuseColor;
void main() {
	vec2 p = gl_FragCoord.xy;
	int n = 0;

	float self = texture(prevBuffer, p/resolution).x;

	for (int x = -RADIUS; x <= RADIUS; ++ x) {
		for (int y = -RADIUS; y <= RADIUS; ++ y) {
			if (x == 0 && y == 0) 
				continue;

			n += texture(prevBuffer, (p+vec2(x,y))/resolution).x > 0.99 ? 1 : 0;
		}
	}

	bool alive = self > 0.99;
	if (!(n >= 34 && n <= 58) && alive)
		alive = false;
	if ((n >= 34 && n <= 45) && !alive)
		alive = true;

	vec4 color = vec4(distance(p, mouse * resolution) <= 4 || alive ? 1 : 0);

	if (time <= 0.1) {
		color = vec4(random(p) < 0.5 ? 1 : 0);
	}

	diffuseColor = color;
}
