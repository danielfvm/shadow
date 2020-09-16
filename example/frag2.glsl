#define PI 3.141592653

// glslsandbox uniforms
uniform float time;
uniform vec2 resolution;
uniform vec2 mouse;

float rand(vec2 c){
	return fract(sin(dot(c.xy ,vec2(12.9898,78.233))) * 43758.5453);
}

float noise(vec2 p, float freq ){
	float unit = resolution.x/freq;
	vec2 ij = floor(p/unit);
	vec2 xy = mod(p,unit)/unit;
	//xy = 3.*xy*xy-2.*xy*xy*xy;
	xy = .5*(1.-cos(PI*xy));
	float a = rand((ij+vec2(0.,0.)));
	float b = rand((ij+vec2(1.,0.)));
	float c = rand((ij+vec2(0.,1.)));
	float d = rand((ij+vec2(1.,1.)));
	float x1 = mix(a, b, xy.x);
	float x2 = mix(c, d, xy.x);
	return mix(x1, x2, xy.y);
}

float pNoise(vec2 p, int res){
	float persistance = .5;
	float n = 0.;
	float normK = 0.;
	float f = 4.;
	float amp = 1.;
	int iCount = 0;
	for (int i = 0; i<50; i++){
		n+=amp*noise(p, f);
		f*=2.;
		normK+=amp;
		amp*=persistance;
		if (iCount == res) break;
		iCount++;
	}
	float nf = n/normK;
	return nf*nf*nf*nf;
}

void main(void)
{
    vec3 c = vec3(0.0);

    if (pNoise(gl_FragCoord.xy * 2.0 + time * 4.0, 10) > 0.1) {
        float d = min(distance(gl_FragCoord.xy, mouse * resolution) / 300.0, 0.99);

        if (sin(gl_FragCoord.y * 0.5 - time * 0.5) > d && sin(gl_FragCoord.x * 0.5 - time * 0.5) > d) {
            c = vec3(0.0, 1.0, 0.0);
        }
    }

    if (gl_FragCoord.x < 100.0 && gl_FragCoord.y < 100.0)
        gl_FragColor = vec4(1.0);
    else
        gl_FragColor = vec4(c, 1.0);
}
