#ifndef SHADER_H
#define SHADER_H

#define GLEW_STATIC

#include <GL/glew.h>
#include <GL/gl.h>

#include <fstream>
#include <sstream>

class Shader {
public:
    unsigned int ID;

    Shader(const char* vertexPath, const char* fragmentPath) {
        std::string vertexCode;
        std::string fragmentCode;
        std::ifstream vShaderFile;
        std::ifstream fShaderFile;

        // ensure ifstream objects can throw exceptions:
        vShaderFile.exceptions(std::ifstream::failbit | std::ifstream::badbit);
        fShaderFile.exceptions(std::ifstream::failbit | std::ifstream::badbit);

        try {
            // open files
            vShaderFile.open(vertexPath);
            fShaderFile.open(fragmentPath);
            std::stringstream vShaderStream, fShaderStream;
            // read file's buffer contents into streams
            vShaderStream << vShaderFile.rdbuf();
            fShaderStream << fShaderFile.rdbuf();
            // close file handlers
            vShaderFile.close();
            fShaderFile.close();
            // convert stream into string
            vertexCode   = vShaderStream.str();
            fragmentCode = fShaderStream.str();
        } catch (...) {
            fprintf(stderr, "ERROR::SHADER::FILE_NOT_SUCCESFULLY_READ");
            exit(EXIT_FAILURE);
        }

        const char* vShaderCode = vertexCode.c_str();
        const char* fShaderCode = fragmentCode.c_str();

        // 2. compile shaders
        unsigned int vertex, fragment;

        // vertex shader
        vertex = glCreateShader(GL_VERTEX_SHADER);
        glShaderSource(vertex, 1, &vShaderCode, NULL);
        glCompileShader(vertex);
        checkCompileErrors(vertex, "VERTEX");

        // fragment Shader
        fragment = glCreateShader(GL_FRAGMENT_SHADER);
        glShaderSource(fragment, 1, &fShaderCode, NULL);
        glCompileShader(fragment);
        checkCompileErrors(fragment, "FRAGMENT");

        // shader Program
        ID = glCreateProgram();
        glAttachShader(ID, vertex);
        glAttachShader(ID, fragment);
        glLinkProgram(ID);
        checkCompileErrors(ID, "PROGRAM");

        // delete the shaders as they're linked into our program now and no longer necessary
        glDeleteShader(vertex);
        glDeleteShader(fragment);
    }

    void bind() { 
        glUseProgram(ID); 
    }

    void unbind() { 
        glUseProgram(0); 
    }

    void setBool(const int loc, bool value) const {         
        glUniform1i(loc, (int)value); 
    }

    void setInt(const int loc, int value) const { 
        glUniform1i(loc, value); 
    }

    void setFloat(const int loc, float value) const { 
        glUniform1f(loc, value); 
    }
    
    void setFloat2(const int loc, float value1, float value2) const { 
        glUniform2f(loc, value1, value2); 
    }

    int getLocation(const std::string &name) {
        return glGetUniformLocation(ID, name.c_str());
    }

private:
    void checkCompileErrors(unsigned int shader, std::string type) {
        int success;
        char infoLog[1024];
        if (type != "PROGRAM") {
            glGetShaderiv(shader, GL_COMPILE_STATUS, &success);
            if (!success) {
                glGetShaderInfoLog(shader, 1024, NULL, infoLog);
                fprintf(stderr, "ERROR::SHADER_COMPILATION_ERROR of type: %s\n%s\n", type.c_str(), infoLog);
            }
        } else {
            glGetProgramiv(shader, GL_LINK_STATUS, &success);
            if (!success) {
                glGetProgramInfoLog(shader, 1024, NULL, infoLog);
                fprintf(stderr, "ERROR::PROGRAM_LINKING_ERROR of type: %s\n%s\n", type.c_str(), infoLog);
            }
        }
    }
};
#endif
