#include "shader.h"

#include <GL/glew.h>
#include <GL/glx.h>
#include <GL/gl.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

char* readFile(char *filepath) {
	FILE *file;
	char *buffer;
	long lSize;

	/* open file read only */
	if (!(file = fopen(filepath, "r"))) {
		fprintf(stderr, "Failed to open file\n");
		return NULL;
	}

	fseek(file, 0L, SEEK_END);
	lSize = ftell(file);
	rewind(file);

	/* allocate memory for entire content */
	buffer = (char*) calloc( 1, lSize+1 );
	if (!buffer) {
		fclose(file);
		fprintf(stderr, "Memory alloc fails\n");
		return NULL;
	}

	/* copy the file into the buffer */
	if (fread( buffer , lSize, 1 , file) != 1) {
		fclose(file);
		free(buffer);
		fprintf(stderr, "Entire read fails\n");
		return NULL;
	}

	fclose(file);

	return buffer;
}

int shader_check_compile_errors(Shader shader, const char *type) {
	char infoLog[1024];
	int success;

	if (strcmp(type, "PROGRAM") != 0) {
		glGetShaderiv(shader, GL_COMPILE_STATUS, &success);
		if (!success) {
			glGetShaderInfoLog(shader, 1024, NULL, infoLog);
			fprintf(stderr, "ERROR::SHADER_COMPILATION_ERROR of type: %s\n%s\n", type, infoLog);
			return 0;
		}
	} else {
		glGetProgramiv(shader, GL_LINK_STATUS, &success);
		if (!success) {
			glGetProgramInfoLog(shader, 1024, NULL, infoLog);
			fprintf(stderr, "ERROR::PROGRAM_LINKING_ERROR of type: %s\n%s\n", type, infoLog);
			return 0;
		}
	}
	return 1;
}

Shader shader_compile(char* vShaderCode, char* fShaderCode) {
	unsigned int vertex, fragment;
	Shader shader = 0;

	/* vertex shader */
	vertex = glCreateShader(GL_VERTEX_SHADER);
	glShaderSource(vertex, 1, (const GLchar *const *)&vShaderCode, NULL);
	glCompileShader(vertex);

	if (!shader_check_compile_errors(vertex, "VERTEX")) {
		return 0;
	}

	/* fragment Shader */
	fragment = glCreateShader(GL_FRAGMENT_SHADER);
	glShaderSource(fragment, 1, (const GLchar *const *)&fShaderCode, NULL);
	glCompileShader(fragment);

	if (!shader_check_compile_errors(fragment, "FRAGMENT")) {
		glDeleteShader(vertex);
		return 0;
	}

	/* shader Program */
	shader = glCreateProgram();
	glAttachShader(shader, vertex);
	glAttachShader(shader, fragment);
	glLinkProgram(shader);

	if (!shader_check_compile_errors(shader, "PROGRAM")) {
		glDeleteShader(vertex);
		glDeleteShader(fragment);
		return 0;
	}

	/* delete the shaders as they're linked into our program now and no longer necessary */
	glDeleteShader(vertex);
	glDeleteShader(fragment);

	return shader;
}

void shader_bind(Shader shader) {
	glUseProgram(shader);
}

void shader_unbind() {
	glUseProgram(0);
}

void shader_set_float(const int loc, float value) {
	glUniform1f(loc, value);
}

void shader_set_vec2(const int loc, float value1, float value2) {
	glUniform2f(loc, value1, value2);
}

int shader_get_location(Shader shader, const char *name) {
	return glGetUniformLocation(shader, name);
}
