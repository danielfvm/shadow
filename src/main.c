// Shaders can be found at: http://glslsandbox.com

#include <GL/glew.h>
#include <GL/glx.h>
#include <GL/gl.h>

#include <Imlib2.h>

#include <X11/X.h>
#include <X11/Xlib.h>
#include <X11/Xatom.h>
#include <X11/extensions/Xrandr.h>

#include <unistd.h>
#include <string.h>
#include <stdlib.h>
#include <signal.h>
#include <stdio.h>
#include <time.h>
#include <math.h>

#include "shader.h"
#include "arghandler.h"

typedef struct {
	Shader shader;
	Window window;

	int width, height;

	/* uniforms */
	int locResolution;
	int locMouse;
	int locTime;

	/* create a new framebuffer */
	unsigned int fbo;
	unsigned int texture;

	/* used for converting framebuffer to Imlib_Image in root mode */
	unsigned int* buffer;
	Pixmap pmap;

	// TODO: 3d Models can be stored here
	
} Renderer; // other name?

static struct {
	float quality;  // shader quality
	float speed;    // shader animation speed
	float opacity;  // background transparency

	enum Mode {
		BACKGROUND,
		WINDOW,
		ROOT,
	} mode;

} options;

static int mode_conversion_amount = 3;
static EnumConvertInfo mode_conversion_table[] = {
	{ .name = "background", .enum_val = BACKGROUND },
	{ .name = "window", .enum_val = WINDOW },
	{ .name = "root", .enum_val = ROOT },
};

static volatile sig_atomic_t keep_running = 1;

static Renderer *renderers;
static Display *dpy;
static XVisualInfo *vi;
static Window root;
static GLXContext glc;

void init() {

	int screen;

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

	/* create new context for offscreen rendering */
	if (!(glc = glXCreateContext(dpy, vi, NULL, GL_TRUE))) {
		fprintf(stderr, "Failed to create context\n");
		exit(EXIT_FAILURE);
	}

	glXMakeCurrent(dpy, root, glc);

	/* init Glew */
	if (glewInit() != GLEW_OK || !GLEW_VERSION_2_1) {
		fprintf(stderr, "Failed to init GLEW\n");
		exit(EXIT_FAILURE);
	}

	/* init opengl */
	glMatrixMode(GL_PROJECTION);
	glLoadIdentity();
	glOrtho(0, 1, 1, 0, -1, 1);
	glMatrixMode(GL_MODELVIEW);
	glLoadIdentity();
	glEnable(GL_PROGRAM_POINT_SIZE);
	glEnable(GL_VERTEX_PROGRAM_POINT_SIZE);
}

void init_renderer(Renderer* r, int x, int y, int width, int height, char *shader_path) {
	XSetWindowAttributes swa;
	Colormap cmap;

	/* create a new window for mode window and background */
	if (options.mode == WINDOW || options.mode == BACKGROUND) {
		cmap = XCreateColormap(dpy, root, vi->visual, AllocNone);
		swa.colormap = cmap;
		swa.event_mask = ExposureMask;

		if (options.mode == BACKGROUND) {
			r->window = XCreateWindow(dpy, root, x, y, width, height, 0, vi->depth, InputOutput, vi->visual, CWColormap | CWEventMask, &swa);
			Atom window_type = XInternAtom(dpy, "_NET_WM_WINDOW_TYPE", False);
			long value = XInternAtom(dpy, "_NET_WM_WINDOW_TYPE_DESKTOP", False);
			XChangeProperty(dpy, r->window, window_type, XA_ATOM, 32, PropModeReplace, (unsigned char *) &value, 1);
		} else {
			r->window = XCreateWindow(dpy, root, 0, 0, 600, 600, 0, vi->depth, InputOutput, vi->visual, CWColormap | CWEventMask, &swa);
		}

		// make window transparent
		if (options.opacity < 1) {
			uint32_t cardinal_alpha = (uint32_t) (options.opacity * (uint32_t)-1);
			XChangeProperty(dpy, r->window, XInternAtom(dpy, "_NET_WM_WINDOW_OPACITY", 0), XA_CARDINAL, 32, PropModeReplace, (uint8_t*) &cardinal_alpha,1) ;
		}

		XMapWindow(dpy, r->window);
		XStoreName(dpy, r->window, "Show");
	} else {
		r->window = root;
	}

	/* initialize shader program from user path */
	if (!(r->shader = shader_compile(shader_path))) {
		fprintf(stderr, "Failed to compile Shader\n");
		exit(EXIT_FAILURE);
	}

	/* used for converting framebuffer to Imlib_Image */
	if (options.mode == ROOT) {
		int depth = DefaultDepth(dpy, DefaultScreen(dpy));
		r->pmap = XCreatePixmap(dpy, root, width, height, depth);
		r->buffer = (unsigned int*) malloc(width * height * 4);
	} else {
		r->buffer = NULL;
	}

	/* locate uniforms */
	shader_bind(r->shader);
	r->locResolution = shader_get_location(r->shader, "resolution");
	r->locMouse = shader_get_location(r->shader, "mouse");
	r->locTime = shader_get_location(r->shader, "time");
	shader_unbind();

	/* create a new framebuffer */
	glGenFramebuffers(1, &r->fbo);
	glBindFramebuffer(GL_FRAMEBUFFER, r->fbo);

	/* create a new texture */
	glGenTextures(1, &r->texture);
	glBindTexture(GL_TEXTURE_2D, r->texture);

	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, NULL);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);

	/* apply texture to framebuffer */
	glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, r->texture, 0);
	glBindFramebuffer(GL_FRAMEBUFFER, 0);

	/* width and height might change in window mode */
	r->height = height;
	r->width = width;
}


/*
 *  Draws pixmap on the root window
 *  original: https://github.com/derf/feh/blob/master/src/wallpaper.c
 */
void set_pixmap_to_root(Pixmap pmap_d1, int width, int height) {

	/* Used for setting pixmap to root window */
	XGCValues gcvalues;
	GC gc;
	Atom prop_root, prop_esetroot, type;
	int format;
	unsigned long length, after;
	unsigned char *data_root = NULL, *data_esetroot = NULL;

	/* local display to set closedownmode on */
	Display *dpy2;
	Window root2;

	int depth2;

	Pixmap pmap_d2;

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
}

void render(Renderer* r, float time) {

	unsigned int mask_return;
	int root_x, root_y;
	int win_x, win_y;

	Window window_returned;

	XWindowAttributes gwa;
	Imlib_Image img;

	/* set renderer's window as context */
	glXMakeCurrent(dpy, r->window, glc);

	/* get new size in case the window was resized */
	if (options.mode == WINDOW) {
		XGetWindowAttributes(dpy, r->window, &gwa);

		r->width = gwa.width;
		r->height = gwa.height;
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, r->width, r->height, 0, GL_RGBA, GL_UNSIGNED_BYTE, NULL);
	}

	/* change viewport, and scale it down depending on quality level */
	glViewport(0, 0, r->width * options.quality, r->height * options.quality);

	/* clear Framebuffer */
	glBindFramebuffer(GL_FRAMEBUFFER, r->fbo);
	glClearColor(0.0f, 0.0f, 0.0f, 1.0f);
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

	/* capture mouse position */
	XQueryPointer(dpy, root, &window_returned,
			&window_returned, &root_x, &root_y, &win_x, &win_y,
			&mask_return);

	/* bind shader background */
	shader_bind(r->shader);
	shader_set_float(r->locTime, time);
	shader_set_vec2(r->locResolution, r->width * options.quality, r->height * options.quality);
	shader_set_vec2(r->locMouse, (float)root_x / r->width, 1.0 - (float)root_y / r->height);

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
	glViewport(0, 0, r->width, r->height);

	/* bind texture to render it on screen */
	glEnable(GL_TEXTURE_2D);
	glBindFramebuffer(GL_FRAMEBUFFER, 0);  // unbind FBO to set the default framebuffer
	glBindTexture(GL_TEXTURE_2D, r->texture); // color attachment texture

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
		glReadPixels(0, 0, r->width, r->height, GL_BGRA, GL_UNSIGNED_BYTE, r->buffer); // a lot of cpu usage here :/

		img = imlib_create_image_using_data(r->width, r->height, r->buffer);
		imlib_context_set_image(img);
		imlib_context_set_drawable(r->pmap);
		imlib_image_flip_vertical();
		imlib_render_image_on_drawable_at_size(0, 0, r->width, r->height);
		imlib_free_image_and_decache();

		set_pixmap_to_root(r->pmap, r->width, r->height);
	} else {
		glXSwapBuffers(dpy, r->window);
	}
}

static void sig_handler(int sig) {
    keep_running = 0;
}

int main(int argc, char **argv) {
	signal(SIGINT, sig_handler);

	int argument_count = 5;
	ArgOption arguments[] = {
		(ArgOption) {
			.abbreviation = "-q", .value = "1", .name = "--quality",
			.description = "Changes quality level of the shader, default: 1."
		}, (ArgOption) {
			.abbreviation = "-s", .value = "1", .name = "--speed",
			.description = "Changes animation speed, default 1."
		}, (ArgOption) {
			.abbreviation = "-o", .value = "1", .name = "--opacity",
			.description = "Sets background window transparency if in window/background mode"
		}, (ArgOption) {
			.abbreviation = "-m", .value = "background", .name = "--mode",
			.description = "Changes rendering mode. Modes: root, window, background"
		}, (ArgOption) {
			.abbreviation = "-d", .value = "full", .name = "--display", // full: render shader on all screens, TODO: other name for 'full', specify shader for monitor
			.description = ""
	}};

	// Check for arguments
	if (argc <= 1) {
		print_help(arguments, argument_count);
		return 0;
	}

	char *file_path = get_argument_values(argc, argv, arguments, argument_count);
	if (*file_path == '\0') {
		fprintf(stderr, "Error: File not specified!\n");
		print_help(arguments, argument_count);
		return EXIT_FAILURE;
	}

	// Check if file exists
	if (access(file_path, F_OK) == -1) {
		fprintf(stderr, "ERROR: File at '%s' does not exist\n", file_path);
		return EXIT_FAILURE;
	}
	
	options.quality = fmin(fmax(atof(arguments[0].value), 0.01), 1);
	options.speed = atof(arguments[1].value);
	options.opacity = atof(arguments[2].value);
	options.mode = in_to_enum(arguments[3].value, mode_conversion_table, mode_conversion_amount);
	
	if (options.mode == -1) {
		fprintf(stderr, "ERROR: Mode \"%s\" does not exist\n", arguments[3].value);
		print_help(arguments, argument_count);
		return EXIT_FAILURE;
	}

	init();

	/* Monitors */
	Screen *screen = ScreenOfDisplay(dpy, 0);
	int width = screen->width;
	int height = screen->height;
	int x = 0;
	int y = 0;

	if (strcmp(arguments[4].value, "full") != 0) {
		int monitor_count;
		XRRMonitorInfo *monitors = XRRGetMonitors(dpy, root, 1, &monitor_count);

		if (monitors == NULL) {
			fprintf(stderr, "ERROR: Failed to get monitors.");
			return EXIT_FAILURE;
		}

		_Bool monitor_found = 0;
		int m;

		for (m = 0; m < monitor_count; m++) {
			if (strcmp(XGetAtomName(dpy, monitors[m].name), arguments[4].value) == 0) {
				monitor_found = 1;
				x = monitors[m].x;
				y = monitors[m].y;
				width = monitors[m].width;
				height = monitors[m].height;
				break;
			}
		}
		
		if (!monitor_found) {
			fprintf(stderr, "ERROR: Monitor \"%s\" does not exist\nValid monitors:\n", arguments[4].value);
			for (m = 0; m < monitor_count; m++) {
				fprintf(stderr, " %d: %s%s%s %dx%d+%d+%d\n",
					m,
					monitors[m].automatic ? "+" : "",
					monitors[m].primary ? "*" : "",
					XGetAtomName(dpy, monitors[m].name),
					monitors[m].width,
					monitors[m].height,
					monitors[m].x,
					monitors[m].y);
			}
			return EXIT_FAILURE;
		}
	}

	// TODO: create multiple rendereres with specific shaders depending on argument: https://github.com/danielfvm/Show/issues/7
	int renderer_count = 1;
	renderers = (Renderer*) malloc(sizeof(Renderer) * renderer_count);
	init_renderer(renderers, x, y, width, height, file_path);

	/* setup timer */
	struct timespec start, end;
	clock_gettime(CLOCK_MONOTONIC_RAW, &start);

	int i;
	float time;

	/* Main loop */
	while (keep_running) {
		clock_gettime(CLOCK_MONOTONIC_RAW, &end);
		time = ((end.tv_sec - start.tv_sec) * 1000000 + (end.tv_nsec - start.tv_nsec) / 1000.0f) * 0.000001f;
		
		// TODO: add framerate limiter here

		for (i = 0; i < renderer_count; i++) {
			render(&renderers[i], time * options.speed);
		}
	}

	/* Free resources */
	for (i = 0; i < renderer_count; i++) {
		if (options.mode == ROOT) {
			free(renderers[i].buffer);
		} else {
			XDestroyWindow(dpy, renderers[i].window);
		}
	}

	free(renderers);

	return EXIT_SUCCESS;
}
