#ifdef GL_ES
precision highp float;
#endif

uniform float time;
uniform vec2 mouse;
uniform vec2 resolution;

float add(vec2 to_add) {
	return to_add.x+to_add.y;
}
float dif(vec2 to_add) {
	return to_add.x-to_add.y;
}
float ellipse(float radius, vec2 center, vec2 delta, vec2 position) {
	vec2 positive = position-(center+delta);
	vec2 negative = position-(center-delta);
	return length(positive) + length(negative) - radius;
}
float lines(float distance, vec2 direction, vec2 position) {
	float valued_position = dif(normalize(direction).yx*position);
	return valued_position*valued_position-distance*distance*distance*distance;
}
float btw(float x, float bot, float top) {
	return min(20.0*max(x-bot, 0.0), 0.0)*min(20.0*max(top-x, 0.0), 1.0);
}
float limit(float x) {
	return x/sqrt(x*x+1.0);
}
vec2 limit(vec2 v) {
	return v/sqrt(v.x*v.x+v.y*v.y+9.0);
}

void main( void ) {
	
	float scaling_factor = resolution.x / resolution.y;

	vec2 position = ( gl_FragCoord.xy / resolution.xy );
	
	float screen_x = (position.x*2.0-1.0) * scaling_factor;
	float screen_y = (position.y*2.0-1.0);
	vec2 Screen = vec2(screen_x, screen_y);
	float mouse_x = (mouse.x*2.0-1.0) * scaling_factor;
	float mouse_y = (mouse.y*2.0-1.0);
	vec2 Mouse = vec2(mouse_x, mouse_y);
	vec2 O = vec2(0.0, 0.0);
	mat2 Right = mat2(0.0, -1.0, 1.0, 0.0);

	float color = 0.0;
	color += 01.06 / abs(ellipse(0.5, O, Right*limit(Mouse)*0.25, Screen)) * btw(add(Mouse*Screen), -2.0, 0.0);
	color +=  0.1 / abs(ellipse(0.5, Mouse, Right*limit(Mouse)*0.25, Screen));
	color += 01.01 / abs(lines(0.5, Mouse, Screen)) * btw(add(Mouse*Screen), (-0.01*add(Mouse*Mouse)), (add(Mouse*Mouse)));

	gl_FragColor = vec4( vec3( color*1.0, color*0.2, color*0.7 ), color / 2.0 );

}
