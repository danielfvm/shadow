#ifdef GL_ES
precision mediump float;
#endif

uniform float time;
uniform vec2 mouse;
uniform vec2 resolution;

float check(vec2 p, float size, float t) {
	return mod(floor(p.x * size ) + floor(p.y * size ), 2.0);
}

void main( void ) {

	vec2 p = ((gl_FragCoord.xy / resolution) - 0.5) * 2.0;
	p.x *= resolution.x/resolution.y;	

	//inertia bby
	float t = sin(mouse.x + mouse.y - distance(p, vec2(0.0)))* 2.0;
	p *= mat2(cos(t), -sin(t),
		  sin(t), cos(t)
	);
  
  	float r = length(p) * 0.8;
	r = 2.0 * r - 1.0;
	float alpha = 1.0 / (4.0 * abs(r));

	float colour = check(p, 5.0, t) * (1.0/length(p))*0.1;
  	colour *= alpha;
	gl_FragColor = vec4(colour * cos(t) , colour * -sin(t) , colour * sin(t) , 1.0  );
}
