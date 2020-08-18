// Shaders can be found at: http://glslsandbox.com

#include "Shader.h"

#define GLEW_STATIC

#include <GL/glew.h>
#include <GL/gl.h>
#include <gtk/gtk.h>
#include <gtkgl/gtkglarea.h>
#include <sys/time.h>

// shader settings
float quality = 1;
float speed = 1;

// path to fragment shader
char fragmentPath[100];

GtkWidget *window;
Shader *shader;

int init (GtkWidget *widget) {

	// setup opengl
	if (gtk_gl_area_make_current(GTK_GL_AREA(widget))) {
		glViewport(0, 0, widget->allocation.width / quality, widget->allocation.height / quality);
		glMatrixMode(GL_PROJECTION);
		glLoadIdentity();
		glOrtho(0, 1, 1, 0, -1, 1);
		glMatrixMode(GL_MODELVIEW);
		glLoadIdentity();
	}
	
	glEnable(GL_PROGRAM_POINT_SIZE);
	glEnable(GL_VERTEX_PROGRAM_POINT_SIZE);

	// Handles errors
	GLenum err = glewInit();
	if (err != GLEW_OK || !GLEW_VERSION_2_1) {
        fprintf(stderr, "Failed to init GLEW\n");
	    exit(EXIT_FAILURE);
    }
	
	// initialize shader program
	shader = new Shader("vertex.glsl", fragmentPath);

	return TRUE;
}

int draw (GtkWidget *widget, GdkEventExpose *event) {
	if (event->count > 0 || !gtk_gl_area_make_current(GTK_GL_AREA(widget))) {
		return TRUE;
    }

    // screen resolution
    int width = widget->allocation.width;
    int height = widget->allocation.height;
	
    // get the locations of the uniforms
    shader->bind();
    int locTime = shader->getLocation("time");
    int locResolution = shader->getLocation("resolution");
    int locMouse = shader->getLocation("mouse");
    shader->unbind();

    // create framebuffer
    unsigned int fbo;
    glGenFramebuffers(1, &fbo);
    glBindFramebuffer(GL_FRAMEBUFFER, fbo);

    // create texture
    unsigned int texture;
    glGenTextures(1, &texture);
    glBindTexture(GL_TEXTURE_2D, texture);

    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, NULL);

    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE); 

    // apply texture to framebuffer
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, texture, 0);  
    glBindFramebuffer(GL_FRAMEBUFFER, 0);  

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC_RAW, &start);

   while (TRUE) {
        clock_gettime(CLOCK_MONOTONIC_RAW, &end);
        uint64_t delta_us = (end.tv_sec - start.tv_sec) * 1000000 + (end.tv_nsec - start.tv_nsec) / 1000;

        width = widget->allocation.width;
        height = widget->allocation.height;

        // change viewport, and scale it down depending on quality level
        glViewport(0, 0, width / quality, height / quality);

        // bind Framebuffer
        glBindFramebuffer(GL_FRAMEBUFFER, fbo);

        // clear Framebuffer
        glClearColor(0.0f, 0.0f, 0.0f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT); 

        // bind shader background
        shader->bind();
        shader->setFloat(locTime, (float)delta_us * 0.0000005f * speed);
        shader->setFloat2(locResolution, width / quality, height / quality);
        shader->setFloat2(locMouse, 0, 0);
        
        // render shader on framebuffer
        glPushMatrix();
            glColor3f(1.0, 1.0, 1.0);
            glBegin(GL_QUADS);
                glVertex2f(0.0, 0.0);
                glVertex2f(1.0, 0.0);
                glVertex2f(1.0, 1.0);
                glVertex2f(0.0, 1.0);
            glEnd();
        glPopMatrix();
        shader->unbind();

        // change viewport to default
        glViewport(0, 0, width, height);

        // bind texture to render it on screen
        glEnable(GL_TEXTURE_2D);
        glBindFramebuffer(GL_FRAMEBUFFER, 0); // unbind FBO to set the default framebuffer
        glBindTexture(GL_TEXTURE_2D, texture); // color attachment texture

        // clear screen
        glClearColor(0.0, 0.0, 0.0, 1.0);
        glClear(GL_COLOR_BUFFER_BIT);

        // render texture on screen
        glPushMatrix();
            glScalef(quality, quality, 1.0);
            glTranslatef(-(1.0 - 1.0 / quality), -(1.0 - 1.0 / quality), 0);
            glColor3f(1.0, 1.0, 1.0);
            glBegin(GL_QUADS);
                glTexCoord2f(1, 0);
                glVertex2f(0, 1);
                glTexCoord2f(0, 0);
                glVertex2f(1, 1);
                glTexCoord2f(0, 1);
                glVertex2f(1, 0);
                glTexCoord2f(1, 1);
                glVertex2f(0, 0);
            glEnd();
        glPopMatrix();

        // swap it on gtk window
        gtk_gl_area_swap_buffers(GTK_GL_AREA(widget));
    }

	return TRUE;
}

int main (int argc, char **argv) {

    if (argc <= 1) {
        printf("sground - A Shader background for your desktop\n\n");
        printf("Usage:\n");
        printf("  sground <path>\n");
        printf("  sground <path> [quality]\n");
        printf("  sground <path> [quality] [speed]\n");
    } else {
        strcpy(fragmentPath, argv[1]);

        std::ifstream f(fragmentPath);
        if (!f.good()) {
            fprintf(stderr, "Failed to open file.\n");
            return EXIT_FAILURE;
        }

        if (argc >= 3) {
            quality = std::stof(argv[2]);
        }

        if (argc == 4) {
            speed = std::stof(argv[3]);
        }

        // all widgets
        GtkWidget *glarea;

        int attrlist[] = {
            GDK_GL_RGBA,
            GDK_GL_RED_SIZE,1,
            GDK_GL_GREEN_SIZE,1,
            GDK_GL_BLUE_SIZE,1,
            GDK_GL_DOUBLEBUFFER,
            GDK_GL_NONE 
        };

        // initialize gtk
        gtk_init(&argc, &argv);
        
        // exits if error occurred
        if (gdk_gl_query() == FALSE) {
            fprintf(stderr, "Error occurred in gtk query.\n");
            return EXIT_FAILURE;
        }
        
        // creates th gtk window
        window = gtk_window_new(GTK_WINDOW_TOPLEVEL);
        gtk_window_set_title(GTK_WINDOW(window), "sground");
    	gtk_window_set_type_hint (GTK_WINDOW (window), GDK_WINDOW_TYPE_HINT_DESKTOP);
        gtk_container_set_border_width(GTK_CONTAINER(window), 10);
        gtk_container_set_border_width(GTK_CONTAINER(window), 0);
        g_signal_connect(window, "delete_event", G_CALLBACK(gtk_main_quit), NULL);
        
        // set window scale & position
        GdkScreen* screen = gdk_screen_get_default();
        gtk_window_set_default_size(GTK_WINDOW (window), gdk_screen_get_width(screen), gdk_screen_get_height(screen));

        // creates glarea widget
        glarea = GTK_WIDGET(gtk_gl_area_new (attrlist));
        gtk_widget_set_events(GTK_WIDGET(glarea), GDK_EXPOSURE_MASK | GDK_BUTTON_PRESS_MASK);
        g_signal_connect(glarea, "expose_event", G_CALLBACK(draw), NULL);
        g_signal_connect(glarea, "realize", G_CALLBACK(init), NULL);
        
        // adds glarea to window
        gtk_container_add(GTK_CONTAINER(window), GTK_WIDGET(glarea));

        // shows widget: glarea & window
        gtk_widget_show(GTK_WIDGET(glarea));
        gtk_widget_show(GTK_WIDGET(window));
        
        // calls gtk's main function
        gtk_main();
    }
	
	return EXIT_SUCCESS;
}
