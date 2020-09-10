/*
 * Original shader from: https://www.shadertoy.com/view/Wt2BzK
 */

#ifdef GL_ES
precision mediump float;
#endif

// glslsandbox uniforms
uniform float time;
uniform vec2 resolution;

// shadertoy emulation
#define iTime time
#define iResolution resolution
const vec4 iMouse = vec4(0.);

// --------[ Original ShaderToy begins here ]---------- //
//Autor desconocido---unknown author

const vec3 COLOR_LINE = vec3(0x77, 0xB0, 0xE0) / 255.0;
const vec3 COLOR_MANELINE = vec3(0x1E, 0x98, 0xD3) / 255.0;
const vec3 COLOR_BODY = vec3(0x9E, 0xDB, 0xF9) / 255.0;
const vec3 COLOR_MANE1 = vec3(0xEE, 0x41, 0x44) / 255.0;
const vec3 COLOR_MANE2 = vec3(0xF3, 0x70, 0x33) / 255.0;
const vec3 COLOR_MANE3 = vec3(0xFD, 0xF6, 0xAF) / 255.0;
const vec3 COLOR_MANE4 = vec3(0x62, 0xBC, 0x4D) / 255.0;
const vec3 COLOR_MANE5 = vec3(0x67, 0x2F, 0x89) / 255.0;
const vec3 COLOR_EYEBROW = vec3(0x00, 0x00, 0x00) / 255.0;
const vec3 COLOR_IRIS1 = vec3(0xC6, 0x00, 0x6F) / 255.0;
const vec3 COLOR_IRIS2 = vec3(0x46, 0x00, 0x25) / 255.0;
const vec3 COLOR_BLACK = vec3(0x00, 0x00, 0x00) / 255.0;
const vec3 COLOR_WHITE = vec3(0xFF, 0xFF, 0xFF) / 255.0;

const float eps=0.0001;

bool line(vec2 p, vec2 a, vec2 b)
{
	return (p.x - a.x) * (a.y - b.y) > (p.y - a.y) * (a.x - b.x);
}

bool circle(vec2 p, vec2 a, float r)
{
	return (p.x - a.x) * (p.x - a.x) + (p.y - a.y) * (p.y - a .y) > r * r;
    
}

bool ellipse(vec2 p, vec2 a, vec2 r)
{
	//return (p.x - a.x) * (p.x - a.x) / r.x / r.x + (p.y - a.y) * (p.y - a .y) / r.y / r.y > 1.0;
    
    p = (p-a)/r ;
	return dot(p,p) > 1.0;
    //return smoothstep ( 1.0-eps, 1.0+eps, dot(p,p) )> 1.0;
	
    

}


vec2 m;

bool ear(inout vec3 c, vec2 p)
{	
	float off;
	if(mod((iTime/3.14), 5.)<4.5)
		off = 0.;
	else
		off = sin(iTime*15.);
	
	bool A = circle(p-off*8., vec2(638, 664), 362.);
	bool B = circle(p-off*8., vec2(1075, 641), 323.);
	bool C = circle(p-off*8., vec2(646, 708), 378.);
	if(!A && !B && !C)
	{
		bool D = circle(p-off*8., vec2(637, 662), 345.);
		bool E = circle(p-off*8., vec2(1109, 588), 363.);
		bool F = circle(p-off*8., vec2(651, 692), 269.);
		bool G = circle(p-off*8., vec2(395, 732), 516.);
		if(D || E || (!F && G))
			c = COLOR_LINE;
		else
			c = COLOR_BODY;
		return true;
	}
	return false;
}

bool mane(inout vec3 c, vec2 p)
{	float off = (sin(iTime*10.)+.5)*10.;
	bool A = circle(p+off, vec2(434, 460), 514.);
	bool B = circle(p+off*.95, vec2(254, 110), 903.);
	bool C = circle(p+off*.90, vec2(384, 228), 668.);
	bool D = circle(p+off*.85, vec2(475, 505), 425.);
	bool E = circle(p+off*.80, vec2(513, 281), 536.);
	bool F = circle(p+off*.30, vec2(777, 435), 360.);
	bool G = circle(p+off*.20, vec2(915, 174), 554.);
	bool H = circle(p+off*.65, vec2(659, 444), 536.);
	bool I = circle(p+off*.60, vec2(-201, 601), 337.);
	bool J = line(p+off*.55, vec2(-253, 218), vec2(176, 590));
	bool K = circle(p+off*.20, vec2(-164, 1212), 882.);
	bool L = circle(p+off*.45, vec2(650, 764), 80.); // lol weird
	if(!A && !B && (C || (!D && E) || (!F && G) || (!H || (I && !J)) && !K) || !L)
	{
		bool M = circle(p+off, vec2(422, 434), 518.);
		bool N = circle(p+off*.9, vec2(372, 261), 647.);
		bool O = circle(p+off*.8, vec2(491, 499), 425.);
		bool P = circle(p+off*.7, vec2(395, 377), 402.);
		bool Q = circle(p+off*.6, vec2(790, 454), 352.);
		bool R = circle(p+off*.5, vec2(891, 216), 527.);
		bool S = circle(p+off*.4, vec2(680, 453), 536.);
		bool T = circle(p+off*.3, vec2(-217, 1332), 992.);
		bool U = circle(p+off*.2, vec2(-150, 586), 305.);
		bool V = line(p+off*.1, vec2(280, 404), vec2(119, 566));
		if((!M && N) || ((!O && P || !Q && !M) && R) || (!S && !M && !T) || (U && !T && V))
		{
			if(circle(p, vec2(491, 84)-off*.5, 764.))
				c = COLOR_MANE1;
			else
				if(circle(p, vec2(686, 204)-off*.2, 576.))
					c = COLOR_MANE2;
				else
					c = COLOR_MANE3;
		}
		else
			c = COLOR_MANELINE;
		return true;
	}
	return false;
}

bool mane2(inout vec3 c, vec2 p)
{
	bool A = circle(p, vec2(607, 464), 306.);
	bool B = circle(p, vec2(777, 485), 339.);
	bool C = circle(p, vec2(1181, -127), 463.);
	bool D = circle(p, vec2(-433, 198), 1442.);
	bool E = line(p, vec2(554, -80), vec2(1055, -80));
	if((A && !B || !C) && !D && E)
	{
		bool F = circle(p, vec2(613, 461), 319.);
		bool G = circle(p, vec2(769, 486), 323.);
		bool H = circle(p, vec2(1195, -123), 454.);
		bool I = circle(p, vec2(288, 485), 691.);
		bool J = circle(p, vec2(122, 278), 864.);
		if((F && !G || !H) && !I && !J)
			c = COLOR_MANE4;
		else
		{
			bool K = circle(p, vec2(388, 235), 607.);
			bool L = circle(p, vec2(416, 87), 570.);
			if(K && !L)
				c = COLOR_MANE5;
			else
				c = COLOR_MANELINE;
		}
		return true;
	}
	return false;
}

bool face(inout vec3 c, vec2 p)
{
	bool A = circle(p, vec2(588, 396), 357.);
	bool B = line(p, vec2(325, 74), vec2(887, 122));
	bool C = ellipse(p, vec2(489, 237), vec2(287, 166));
	bool D = circle(p, vec2(209, 437), 163.);
	if(!A && B || !C && D)
	{
		bool E = ellipse(p, vec2(536, 253), vec2(315, 170));
		bool F = circle(p, vec2(500, 921), 828.);
		bool G = circle(p, vec2(220, 367), 110.);
		bool H = line(p, vec2(201, 454), vec2(658, 108));
		bool I = line(p, vec2(237, 115), vec2(363, 238));
		bool J = ellipse(p, vec2(283, 204), vec2(68, 57));
		bool K = ellipse(p*(sin(iTime/1.75)/85.+1.), vec2(253, 192), vec2(102, 70));
		bool L = circle(p, vec2(285, 228), 19.);
		bool M = circle(p, vec2(281, 236), 19.);
		if((!E && !F && G || H) && (I || !J || K) && (L || !M))
			c = COLOR_BODY;
		else
			c = COLOR_LINE;
		return true;
	}
	return false;
}

bool eye1(inout vec3 c, vec2 p, vec2 off)
{	
		
	// skewed ellipse please ignore
#define SQR(q) ((q) * (q))
	bool A = SQR((p.x - 590.0) / 150.0 - (p.y - 378.0) / 900.0) + SQR((p.y - 378.0) / 180.0) < 1.0;
	if(A)
	{
		bool B = SQR((p.x - 593.0) / 149.0 - (p.y - 382.0) / 900.0) + SQR((p.y - 361.0) / 180.0) < 1.0;
		if(B)
		{
			vec2 d = vec2(0.0, 0.0) - vec2(580, 360);
			if(length(d) > 60.0)
			   d = d / length(d) * 60.0;
			bool C = ellipse(p-off*50., vec2(580, 360) + d, vec2(112, 162));
			if(C)
				c = COLOR_WHITE;
			else
			{
				bool D = ellipse(p-off*55., vec2(551, 305) + d, vec2(19, 26));
				bool E = ellipse(p-off*55., vec2(601, 410) + d, vec2(35, 57));
				if(D && E)
				{
					bool F = ellipse(p-off*50., vec2(580, 360) + d * 1.3, vec2(71, 126));
					if(F)
						c = mix(COLOR_IRIS1, COLOR_IRIS2, SQR((p.y - 360.0 - d.y) / 252.0 + 0.5));
					else
						c = COLOR_BLACK;
				}
				else
					c = COLOR_WHITE;
			}
		}
		else
			c = COLOR_EYEBROW;
		return true;
	}
	// rotating ellipses hacks, nothing to see here
	bool G = ellipse(p, vec2(757, 430), vec2(40, 5));
	bool H = ellipse(vec2(p.x + p.y * 0.3, p.x * -0.3 + p.y), vec2(890, 260), vec2(40, 6));
	bool I = ellipse(vec2(p.x + p.y * 0.5, p.x * -0.5 + p.y), vec2(990, 175), vec2(40, 7));
	if(!G || !H || !I)
	{
		c = COLOR_BLACK;
		return true;
	}
	return false;
}

bool eye2(inout vec3 c, vec2 p, vec2 off)
{
	bool A = line(p, vec2(207, 460), vec2(323, 265));
	bool B = circle(p, vec2(213, 434), 158.);
	bool C = circle(p, vec2(739, 417), 500.);
	bool D = ellipse(p, vec2(289, 444), vec2(50, 144));
	if(!A && !B && !C || !D)
	{
		bool E = ellipse(p, vec2(285, 390), vec2(47, 184));
		if(!E)
		{
			vec2 d = vec2(0.0, 0.0) - vec2(290, 360);
			if(length(d) > 60.0)
			   d = d / length(d) * 60.0;
			d *= vec2(0.33, 1.0);
			bool F = ellipse(p-off*50., vec2(290, 360) + d, vec2(50, 162));
			if(F)
				c = COLOR_WHITE;
			else
			{
				bool D = ellipse(p-off*55., vec2(304, 446) + d, vec2(17, 41));
				bool E = ellipse(p-off*55., vec2(278, 354) + d, vec2(11, 24));
				if(D && E)
				{
					bool F = ellipse(p-off*50., vec2(290, 360) + d * 1.3, vec2(42, 126));
					if(F)
						c = mix(COLOR_IRIS1, COLOR_IRIS2, SQR((p.y - 360.0 - d.y) / 252.0 + 0.5));
					else
						c = COLOR_BLACK;
				}
				else
					c = COLOR_WHITE;
			}
		}
		else
			c = COLOR_EYEBROW;
		return true;
	}
	return false;
}

bool neck(inout vec3 c, vec2 p)
{
	bool A = circle(p, vec2(1247, -28), 638.);
	bool B = circle(p, vec2(353, 258), 638.);
	bool C = line(p, vec2(554, -80), vec2(1055, -80));
	if(!A && !B && C)
	{
		bool D = circle(p, vec2(1235, -21), 606.);
		if(D)
			c = COLOR_LINE;
		else
			c = COLOR_BODY;
		return true;
	}
	return false;
}

vec2 transform(vec2 x)
{
	return (x - iResolution.xy / 2.0) / iResolution.y * 1000.0 + 500.0;
}

float sinslope(float t)
{
	return sin(t) - sin(t - 0.01);	
}

void  mainImage( out vec4 fragColor, in vec2 fragCoord )
{
	float off = sin(iTime/1.75);
	if(off < 0.)
		off=0.;
	else if(off > .8)
		off=.8;
	
	m = transform(iMouse.xy * iResolution.xy);
	vec2 p = transform(fragCoord.xy);
	p.x += sin(iTime) * 200.0;
	p.y += abs(sin(iTime*7.0))*10.0 * (abs(sinslope(iTime)) * 200.0);
	vec3 c = vec3(1, 1, 1);
	ear(c, p) || mane(c, p) || mane2(c, p) || eye1(c, p, vec2(off*1.6,off*.5)) || eye2(c, p, vec2(off*.4,off*.5))  || face(c, p) || neck(c, p);
	fragColor = vec4(c, 1);
}


// --------[ Original ShaderToy ends here ]---------- //

void main(void)
{
    mainImage(gl_FragColor, gl_FragCoord.xy);
}
