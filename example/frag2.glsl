/*
 * Original shader from: https://www.shadertoy.com/view/Wscyz2
 */
#version 330 core

#ifdef GL_ES
precision highp float;
#endif

// glslsandbox uniforms
uniform float time;
uniform vec2 resolution;

// shadertoy emulation
#define iTime time
#define iResolution resolution

// --------[ Original ShaderToy begins here ]---------- //
// SST Squelcher

#define AA 1	// make this 2 if you are feeling cold...
#define HEIGHT 12.

vec3 _col;





    
#define PI 3.14159
#define	TAU 6.28318


vec3 spunk(vec2 uv)
{
	vec3 col = vec3(.55,0.35,1.225);		// Drop Colour
	uv.x += sin(0.2+uv.y*0.8)*0.5;
    uv.x = uv.x*50.0;						// H-Count
    float dx = fract(uv.x);
    uv.x = floor(uv.x);
    float t =  iTime*0.4;
    uv.y *= 0.15;							// stretch
    float o=sin(uv.x*215.4);				// offset
    float s=cos(uv.x*33.1)*.3 +.7;			// speed
    float trail = mix(95.0,35.0,s);			// trail length
    float yv = fract(uv.y + t*s + o) * trail;
    yv = 1.0/yv;
    yv = smoothstep(0.0,1.0,yv*yv);
    yv = sin(yv*PI)*(s*5.0);
    float d2 = sin(dx*PI);
    yv *= d2*d2;
    col = col*yv;
	return col;
}
void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
     // camera movement	
    float an = sin(iTime*0.8);
    
    //float dist = 36.0+sin(iTime)*7.0;
    float dist = 28.0;
    
	vec3 ro = vec3( dist*cos(an), sin(iTime*0.75)*14.0, dist*sin(an) );
	//vec3 ro = vec3( 16.0*cos(an), 0.0, 16.0*sin(an) );
    vec3 ta = vec3( 0.0, 0.0, 0.0 );
    // camera matrix
    vec3 ww = normalize( ta - ro );
    vec3 uu = normalize( cross(ww,vec3(0.0,1.0,0.0) ) );
    vec3 vv = normalize( cross(uu,ww));

    vec3 tot = vec3(0.0);
	    vec2 ppp = (-iResolution.xy + 2.*(fragCoord))/iResolution.y;

	vec3 bbk = spunk(ppp.xy);
	

    
    #if AA>1
    for( int m=0; m<AA; m++ )
    for( int n=0; n<AA; n++ )
    {
        // pixel coordinates
        vec2 o = vec2(float(m),float(n)) / float(AA) - 0.5;
        vec2 p = (-iResolution.xy + 2.0*(fragCoord+o))/iResolution.y;
        #else    
        vec2 p = (-iResolution.xy + 2.0*fragCoord)/iResolution.y;
        #endif

	    // create view ray
        vec3 rd = normalize( p.x*uu + p.y*vv + 1.5*ww );

        // raymarch
        const float tmax = 65.0;
        float t = 0.0;
        for( int i=0; i<160; i++ )
        {
            vec3 pos = ro + t*rd;

        }
    
        // shading/lighting	
        float v = 1.0-abs(p.y);
        vec3 col = bbk*v*2.0;	//vec3(v*0.1);

        if( t<tmax )
        {
            vec3 pos = ro + t*rd;

            
            vec3 dir = normalize(vec3(1.0,0.7,0.0));
        }
        // gamma        
        col = sqrt( col );
	    tot += col;
    #if AA>1
    }
    tot /= float(AA*AA);
    #endif

	fragColor = vec4( tot, 1.0 );
}
// --------[ Original ShaderToy ends here ]---------- //

layout(location = 0) out vec4 diffuseColor;
void main(void)
{
    mainImage(diffuseColor, gl_FragCoord.xy);
}
