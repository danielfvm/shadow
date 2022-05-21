#ifndef OPENGL_H
#define OPENGL_H

#include <GL/glew.h>

typedef struct {
	int width;
	int height;
	GLuint id;
} Texture;

uint8_t load_texture(const char* path, Texture* texture);

#endif // OPENGL_H
