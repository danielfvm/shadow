#version 330 core

#ifdef GL_ES
precision highp float;
#endif

uniform vec2 resolution;
uniform float time;
uniform vec2 mouse;
uniform sampler2D prevBuffer;
uniform sampler2D currentBuffer;

void main() {
	vec2 p = gl_FragCoord.xy;

	int i = 0;
	int r = 2;
	vec3 colors[5*5];

	for (int x = -r; x <= r; ++ x) {
		for (int y = -r; y <= r; ++ y) {
			colors[i] = texture(currentBuffer, (p+vec2(x,y))/resolution).xyz;
			i += 1;
		}
	}

	for (int n = 5*5-1; n >= 0; --n) {
	  for (int i = 0; i < n; ++i) {
		vec3 tmp = min(colors[i], colors[i+1]); 
		colors[i+1] = colors[i+1] + colors[i] - tmp; 
		colors[i] = tmp;
	  }
	}

	gl_FragColor = vec4(vec3(colors[4]), 1.0);
}
