#include "opengl.h"

#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"

uint8_t load_texture(const char* path, Texture* texture) {

    // stores the width, height, and how many bits are used per pixel
    int BitsPerPixel = 0;

    // flip it upside down because opengl reads it upside down
    stbi_set_flip_vertically_on_load(1);

    // loads the image and stores it in this buffer
    unsigned char* m_LocalBuffer = stbi_load(path, &texture->width, &texture->height, &BitsPerPixel, 4);

	if (m_LocalBuffer == NULL) {
		return 1;
	}


    // Create one OpenGL texture
    GLuint id;
    glGenTextures(1, &id);

    // "Bind" the newly created texture
    glBindTexture(GL_TEXTURE_2D, id);

    // Change picture settings
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST); 
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST); 
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE); 
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE); 

    // Set texture image from data
    glTexImage2D(
        GL_TEXTURE_2D,
        0,
        GL_RGBA8,
        texture->width,
        texture->height,
        0,
        GL_RGBA,
        GL_UNSIGNED_BYTE,
        m_LocalBuffer
    );

    glBindTexture(GL_TEXTURE_2D, 0);

	return 0;
}
