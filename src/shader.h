#ifndef showShaderH
#define showShaderH

/* Shader program id provided by opengl */
typedef unsigned long Shader;

/*
 *  Dont forget to free buffer
 */
char* readFile(char *filepath);

/*
 *  Check for errors which might have accured during compilation
 */
int shader_check_compile_errors(Shader shader, const char *type);

/*
 *  Compile shader from path, vertex shader is already included
 */
Shader shader_compile(char* vShaderCode, char* fShaderCode);

/*
 *  Bind shader to current gl context
 */
void shader_bind(Shader shader);

/*
 *  Unbind shader from current gl context
 */
void shader_unbind();

/*
 *  Sets the float uniform in the shader program
 */
void shader_set_float(const int loc, float value);

/*
 *  Sets the vec2 uniform in the shader program
 */
void shader_set_vec2(const int loc, float value1, float value2);

/*
 *  Returns the location address from uniform in shader by its name
 */
int shader_get_location(Shader shader, const char *name);
#endif
