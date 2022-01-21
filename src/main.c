// Shaders can be found at: http://glslsandbox.com

#include <GL/glew.h>
#include <GL/glx.h>
#include <GL/gl.h>

#include <Imlib2.h>

#include <X11/X.h>
#include <X11/Xlib.h>
#include <X11/Xatom.h>

#include <unistd.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include <math.h>

#include "shader.h"

typedef struct {
	float quality;  // shader quality
	float speed;    // shader animation speed
	float opacity;  // background transparency

	enum Mode {
		BACKGROUND,
		WINDOW,
		ROOT,
	} mode;

} Option;

static Option options = {
	.quality = 1,
	.speed = 1,
	.opacity = 1,
	.mode = BACKGROUND,
};

static char help[] = {
	"Usage: %s <path> [options]\n"
	"Options:\n"
	"  -q, --quality\t\tChanges quality level of the shader, default 1.\n"
	"  -s, --speed  \t\tChanges animation speed, default 1.\n"
	"  -m, --mode   \t\tChanges rendering mode. Modes: root, window, background\n"
	"  -o, --opacity\t\tSets background window transparency if in window/background mode\n"
};

static Shader shader;


Display *dpy;
XVisualInfo *vi;

Window root;

/* Window used in background & window mode */
Window win;
XWindowAttributes gwa;


void init(char *filepath) {
	GLXContext glc;
	int screen;

	Colormap cmap;
	XSetWindowAttributes swa;

	/* open display, screen & root */
	if (!(dpy = XOpenDisplay(NULL))) {
		fprintf(stderr, "Error while opening display.\n");
		exit(EXIT_FAILURE);
	}

	screen = DefaultScreen(dpy);
	root = RootWindow(dpy, screen);

	/* setup imlib */
	imlib_context_set_display(dpy);
	imlib_context_set_visual(DefaultVisual(dpy, screen));
	imlib_context_set_colormap(DefaultColormap(dpy, screen));

	/* get visual matching attr */
	GLint attr[] = { GLX_RGBA, GLX_DEPTH_SIZE, 24, GLX_DOUBLEBUFFER, None };

	if (!(vi = glXChooseVisual(dpy, 0, attr))) {
		fprintf(stderr, "No appropriate visual found\n");
		exit(EXIT_FAILURE);
	}

	/* screen resolution */
	Screen *s = ScreenOfDisplay(dpy, 0);
	int width = s->width;
	int height = s->height;

	/* create a new window if mode: window, background */
	if (options.mode == WINDOW || options.mode == BACKGROUND) {
		cmap = XCreateColormap(dpy, root, vi->visual, AllocNone);
		swa.colormap = cmap;
		swa.event_mask = ExposureMask;

		if (options.mode == BACKGROUND) {
			win = XCreateWindow(dpy, root, 0, 0, width, height, 0, vi->depth, InputOutput, vi->visual, CWColormap | CWEventMask, &swa);
			Atom window_type = XInternAtom(dpy, "_NET_WM_WINDOW_TYPE", False);
			long value = XInternAtom(dpy, "_NET_WM_WINDOW_TYPE_DESKTOP", False);
			XChangeProperty(dpy, win, window_type, XA_ATOM, 32, PropModeReplace, (unsigned char *) &value, 1);
		} else {
			win = XCreateWindow(dpy, root, 0, 0, 600, 600, 0, vi->depth, InputOutput, vi->visual, CWColormap | CWEventMask, &swa);
		}

		// make window transparent
		if (options.opacity < 1) {
			uint32_t cardinal_alpha = (uint32_t) (options.opacity * (uint32_t)-1);
			XChangeProperty(dpy, win, XInternAtom(dpy, "_NET_WM_WINDOW_OPACITY", 0), XA_CARDINAL, 32, PropModeReplace, (uint8_t*) &cardinal_alpha,1) ;
		}

		XMapWindow(dpy, win);
		XStoreName(dpy, win, "Show");
	}

	/* create new context for offscreen rendering */
	if (!(glc = glXCreateContext(dpy, vi, NULL, GL_TRUE))) {
		fprintf(stderr, "Failed to create context\n");
		exit(EXIT_FAILURE);
	}

	if (options.mode == ROOT) {
		glXMakeCurrent(dpy, root, glc);
	} else {
		glXMakeCurrent(dpy, win, glc);
	}

	/* setup opengl */
	glMatrixMode(GL_PROJECTION);
	glLoadIdentity();
	glOrtho(0, 1, 1, 0, -1, 1);
	glMatrixMode(GL_MODELVIEW);
	glLoadIdentity();


	glEnable(GL_PROGRAM_POINT_SIZE);
	glEnable(GL_VERTEX_PROGRAM_POINT_SIZE);

	/* init Glew */
	GLenum err = glewInit();
	if (err != GLEW_OK || !GLEW_VERSION_2_1) {
		fprintf(stderr, "Failed to init GLEW\n");
		exit(EXIT_FAILURE);
	}

	/* initialize shader program from user path */
	if (!(shader = shader_compile(filepath))) {
		fprintf(stderr, "Failed to compile Shader\n");
		exit(EXIT_FAILURE);
	}
}

void draw() {
	/* Used for setting pixmap to root window */
	XGCValues gcvalues;
	GC gc;
	Atom prop_root, prop_esetroot, type;
	int format;
	unsigned long length, after;
	unsigned char *data_root = NULL, *data_esetroot = NULL;
	Pixmap pmap_d1, pmap_d2;

	/* local display to set closedownmode on */
	Display *dpy2;
	Window root2;
	int depth2;
	int depth;


	/* screen resolution */
	Screen *screen = ScreenOfDisplay(dpy, 0);
	int width = screen->width;
	int height = screen->height;

	depth = DefaultDepth(dpy, DefaultScreen(dpy));
	pmap_d1 = XCreatePixmap(dpy, root, width, height, depth);

	/* locate uniforms */
	shader_bind(shader);
	int locResolution = shader_get_location(shader, "resolution");
	int locMouse = shader_get_location(shader, "mouse");
	int locTime = shader_get_location(shader, "time");
	shader_unbind();

	/* create a new framebuffer */
	unsigned int fbo;
	glGenFramebuffers(1, &fbo);
	glBindFramebuffer(GL_FRAMEBUFFER, fbo);

	/* create a new texture */
	unsigned int texture;
	glGenTextures(1, &texture);
	glBindTexture(GL_TEXTURE_2D, texture);

	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, NULL);

	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);


	/* apply texture to framebuffer */
	glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, texture, 0);
	glBindFramebuffer(GL_FRAMEBUFFER, 0);

	/* setup timer */
	struct timespec start, end;
	clock_gettime(CLOCK_MONOTONIC_RAW, &start);

	/* used for converting framebuffer to Imlib_Image */
	unsigned int* buffer = (unsigned int*) malloc(width * height * 4);

	Window window_returned;
	int root_x, root_y;
	int win_x, win_y;
	unsigned int mask_return;

	// TODO: Exit condition
	while (1) {
		// TODO: add framerate limiter here

		if (options.mode == WINDOW) {
			XGetWindowAttributes(dpy, win, &gwa);
			width = gwa.width;
			height = gwa.height;
			glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, NULL);
		}

		clock_gettime(CLOCK_MONOTONIC_RAW, &end);
		uint64_t delta_us = (end.tv_sec - start.tv_sec) * 1000000 + (end.tv_nsec - start.tv_nsec) / 1000;

		/* change viewport, and scale it down depending on quality level */
		glViewport(0, 0, width * options.quality, height * options.quality);

		/* clear Framebuffer */
		glBindFramebuffer(GL_FRAMEBUFFER, fbo);
		glClearColor(0.0f, 0.0f, 0.0f, 1.0f);
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

		/* capture mouse position */
		XQueryPointer(dpy, root, &window_returned,
				&window_returned, &root_x, &root_y, &win_x, &win_y,
				&mask_return);

		/* bind shader background */
		shader_bind(shader);
		shader_set_float(locTime, (float)delta_us * 0.000001f * options.speed);
		shader_set_vec2(locResolution, width * options.quality, height * options.quality);
		shader_set_vec2(locMouse, (float)(root_x) / width, 1.0 - (float)(root_y) / height);

		/* render shader on framebuffer */
		glPushMatrix();
		glColor3f(1.0, 1.0, 1.0);
		glBegin(GL_QUADS);
		glVertex2f(0.0, 0.0);
		glVertex2f(1.0, 0.0);
		glVertex2f(1.0, 1.0);
		glVertex2f(0.0, 1.0);
		glEnd();
		glPopMatrix();
		shader_unbind();

		/* change viewport to default */
		glViewport(0, 0, width, height);

		/* bind texture to render it on screen */
		glEnable(GL_TEXTURE_2D);
		glBindFramebuffer(GL_FRAMEBUFFER, 0); // unbind FBO to set the default framebuffer
		glBindTexture(GL_TEXTURE_2D, texture); // color attachment texture

		/* clear screen */
		glClearColor(0.0, 0.0, 0.0, 1.0);
		glClear(GL_COLOR_BUFFER_BIT);

		/* render texture on screen */
		glPushMatrix();
		glScalef(1.0 / options.quality, 1.0 / options.quality, 1.0);
		glTranslatef(0.0, options.quality - 1.0, 0.0);
		glColor3f(1.0, 1.0, 1.0);
		glBegin(GL_QUADS);
		glTexCoord2f(0, 1);
		glVertex2f(0, 0);
		glTexCoord2f(1, 1);
		glVertex2f(1, 0);
		glTexCoord2f(1, 0);
		glVertex2f(1, 1);
		glTexCoord2f(0, 0);
		glVertex2f(0, 1);
		glEnd();
		glPopMatrix();

		// in root mode, get pixels from gl context and convert it to an Pixbuf and draw it on root window
		if (options.mode == ROOT) { 

			/* create Imlib_Image from current Frame */
			glReadPixels(0, 0, width, height, GL_BGRA, GL_UNSIGNED_BYTE, buffer); // a lot of cpu usage here :/

			Imlib_Image img = imlib_create_image_using_data(width, height, buffer);
			imlib_context_set_image(img);
			imlib_context_set_drawable(pmap_d1);
			imlib_image_flip_vertical();
			imlib_render_image_on_drawable_at_size(0, 0, width, height);
			imlib_free_image_and_decache();

			/*
			 *  create new display, copy pixmap to new display
			 *  original: https://github.com/derf/feh/blob/master/src/wallpaper.c
			 */
			if (!(dpy2 = XOpenDisplay(NULL))) {
				fprintf(stderr, "Can't reopen X display.");
				exit(EXIT_FAILURE);
			}

			root2 = RootWindow(dpy2, DefaultScreen(dpy2));
			depth2 = DefaultDepth(dpy2, DefaultScreen(dpy2));
			XSync(dpy, False);
			pmap_d2 = XCreatePixmap(dpy2, root2, width, height, depth2);
			gcvalues.fill_style = FillTiled;
			gcvalues.tile = pmap_d1;
			gc = XCreateGC(dpy2, pmap_d2, GCFillStyle | GCTile, &gcvalues);
			XFillRectangle(dpy2, pmap_d2, gc, 0, 0, width, height);
			XFreeGC(dpy2, gc);
			XSync(dpy2, False);
			XSync(dpy, False);

			prop_root = XInternAtom(dpy2, "_XROOTPMAP_ID", True);
			prop_esetroot = XInternAtom(dpy2, "ESETROOT_PMAP_ID", True);

			if (prop_root != None && prop_esetroot != None) {
				XGetWindowProperty(dpy2, root2, prop_root, 0L, 1L,
						False, AnyPropertyType, &type, &format, &length, &after, &data_root);
				if (type == XA_PIXMAP) {
					XGetWindowProperty(dpy2, root2,
							prop_esetroot, 0L, 1L,
							False, AnyPropertyType,
							&type, &format, &length, &after, &data_esetroot);
					if (data_root && data_esetroot) {
						if (type == XA_PIXMAP && *((Pixmap *) data_root) == *((Pixmap *) data_esetroot)) {
							XKillClient(dpy2, *((Pixmap *)
										data_root));
						}
					}
				}
			}

			if (data_root) {
				XFree(data_root);
			}

			if (data_esetroot) {
				XFree(data_esetroot);
			}

			/* This will locate the property, creating it if it doesn't exist */
			prop_root = XInternAtom(dpy2, "_XROOTPMAP_ID", False);
			prop_esetroot = XInternAtom(dpy2, "ESETROOT_PMAP_ID", False);

			if (prop_root == None || prop_esetroot == None) {
				fprintf(stderr, "creation of pixmap property failed.");
			}

			XChangeProperty(dpy2, root2, prop_root, XA_PIXMAP, 32, PropModeReplace, (unsigned char *) &pmap_d2, 1);
			XChangeProperty(dpy2, root2, prop_esetroot, XA_PIXMAP, 32, PropModeReplace, (unsigned char *) &pmap_d2, 1);

			XSetWindowBackgroundPixmap(dpy2, root2, pmap_d2);
			XClearWindow(dpy2, root2);
			XFlush(dpy2);
			XSetCloseDownMode(dpy2, RetainPermanent);
			XCloseDisplay(dpy2);
		} else { // on mode window, swap buffer to x11 window
			glXSwapBuffers(dpy, win);
		}
	}

	free(buffer);
}

int main(int argc, char **argv) {

	// Check for arguments
	if (argc <= 1) {
        printf(help, argv[0]);
		return 0;
	}

	// Handle arguments
	for (int i = 2; i < argc - 1; ++ i) {
		if (argv[i][1] == 'q' || strcmp(argv[i], "--quality") == 0) {
			options.quality = fmin(fmax(atof(argv[i+1]), 0.01), 1);
		} else if (argv[i][1] == 's' || strcmp(argv[i], "--speed") == 0) {
			options.speed = atof(argv[i+1]);
		} else if (argv[i][1] == 'o' || strcmp(argv[i], "--opacity") == 0) {
			options.opacity = atof(argv[i+1]);
		} else if (argv[i][1] == 'm' || strcmp(argv[i], "--mode") == 0) {
			if (strcmp(argv[i+1], "root") == 0) {
				options.mode = ROOT;
			} else if (strcmp(argv[i+1], "window") == 0) {
				options.mode = WINDOW;
			} else if (strcmp(argv[i+1], "background") == 0) {
				options.mode = BACKGROUND;
			} else {
				printf("Mode '%s' does not exist\n\n", argv[i+1]);
				printf(help, argv[0]);
				return EXIT_FAILURE;
			}
		}
	}

	// Check if file exists
	if (access(argv[1], F_OK) == -1) {
		fprintf(stderr, "ERROR: File at '%s' does not exist\n", argv[1]);
		return EXIT_FAILURE;
	}

	init(argv[1]);
	draw();

	return EXIT_SUCCESS;
}
