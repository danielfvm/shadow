#version 330 core

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

void main() {
	vec2 p = gl_FragCoord.xy;

	int n = 0;

	bool self = texture(prevBuffer, p/resolution).x > 0.5;

	for (int x = -1; x <= 1; ++ x) {
		for (int y = -1; y <= 1; ++ y) {
			if (x == 0 && y == 0) 
				continue;

			vec3 color = texture(prevBuffer, (p+vec2(x,y))/resolution).xyz;
			n += (color.x > 0.5) ? 1 : 0;
		}
	}

	bool alive = ((n == 2 || n == 3) && self) || (n == 3 && !self);

	vec3 color = (distance(p, mouse * resolution) <= 3) || alive ? vec3(1) : vec3(0);

	// init
	if (time <= 0.1) {
		color = random(p) > 0.5 ? vec3(1) : vec3(0);
	}

	gl_FragColor = vec4(color, 1.);
}
