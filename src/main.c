// Shaders can be found at: http://glslsandbox.com

#include <GL/glew.h>
#include <GL/glx.h>
#include <GL/gl.h>

#include <Imlib2.h>

#include <X11/Xlib.h>
#include <X11/Xatom.h>

#include <unistd.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <time.h>

#include "shader.h"
#include "toon.h"

/* shader settings */
float quality = 1;
float speed = 1;

Shader shader;

Display *dpy;
XVisualInfo *vi;

Window root;

void init(char *filepath) {
    Window parent;
    GLXContext glc;
    int screen;

    /* open display, screen & root */
    if (!(dpy = XOpenDisplay(NULL))) {
        fprintf(stderr, "Error while opening display.\n");
        exit(EXIT_FAILURE);
    }

    screen = DefaultScreen(dpy);
    root = ToonGetRootWindow(dpy, screen, &parent);

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
        fputs("Failed to init GLEW", stderr);
        exit(EXIT_FAILURE);
    }
	
	/* initialize shader program from user path */
	if (!(shader = shader_compile(filepath))) {
        fprintf(stderr, "Failed to compile Shader\n");
	    exit(EXIT_FAILURE);
    }
}

/* 3 color values to 1 hex color value */
unsigned int createRGB(int r, int g, int b) {   
    return ((r & 0xff) << 16) + ((g & 0xff) << 8) + (b & 0xff);
}

void draw() {
    XGCValues gcvalues;
	GC gc;
    Atom prop_root, prop_esetroot, type;
    int format, i;
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

    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, NULL);

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
    unsigned char* buffer = (unsigned char*) malloc(width * height * 3);
    unsigned int* buffer_hex = (unsigned int*) malloc(width * height * 4);

    Window window_returned;
    int root_x, root_y;
    int win_x, win_y;
    unsigned int mask_return;


    while (1) {
        clock_gettime(CLOCK_MONOTONIC_RAW, &end);
        uint64_t delta_us = (end.tv_sec - start.tv_sec) * 1000000 + (end.tv_nsec - start.tv_nsec) / 1000;

        /* change viewport, and scale it down depending on quality level */
        glViewport(0, 0, width / quality, height / quality);

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
        shader_set_float(locTime, (float)delta_us * 0.000001f * speed);
        shader_set_vec2(locResolution, width / quality, height / quality);
        shader_set_vec2(locMouse, (float)root_x / width, (float)root_y / height);
        
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
            glScalef(quality, quality, 1.0);
            glColor3f(1.0, 1.0, 1.0);
            glBegin(GL_QUADS);
                glTexCoord2f(0, 1);
                glVertex2f(0, 1);
                glTexCoord2f(1, 1);
                glVertex2f(1, 1);
                glTexCoord2f(1, 0);
                glVertex2f(1, 0);
                glTexCoord2f(0, 0);
                glVertex2f(0, 0);
            glEnd();
        glPopMatrix();

        /* create Imlib_Image from current Frame */
        glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE, buffer); // a lot of cpu usage :/

        for (i = 0; i < width * height; ++ i) {
            buffer_hex[i] = createRGB(buffer[i * 3], buffer[i * 3 + 1], buffer[i * 3 + 2]);
        }

        Imlib_Image img = imlib_create_image_using_data(width, height, buffer_hex);

        imlib_context_set_image(img);
        imlib_context_set_drawable(pmap_d1);
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
    }

    free(buffer);
    free(buffer_hex);
}

int main(int argc, char **argv) {
    if (argc <= 1) {
        printf("sground - A Shader background for your desktop\n\n");
        printf("Usage:\n");
        printf("  sground <path>\n");
        printf("  sground <path> [quality]\n");
        printf("  sground <path> [quality] [speed]\n");
        printf("\n");
        printf("  [quality] ... higher number => lower quality (minimum 1)\n");
        printf("  [speed] ... higher number => higher speed (can be negativ)\n");
    } else {
        if (access(argv[1], F_OK) == -1) {
            fprintf(stderr, "File does not exist\n");
            return EXIT_FAILURE;
        }

        if (argc >= 3) {
            quality = atof(argv[2]);
            if (quality < 1) {
                quality = 1;
            }
        }

        if (argc == 4) {
            speed = atof(argv[3]);
        }


        init(argv[1]);
        draw();
    }
	
	return EXIT_SUCCESS;
}
