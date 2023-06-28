from OpenGL import GL as gl

import logging
import sys

log = logging.getLogger(__name__)

class Shader():
    def __init__(self, shaders):
        log.debug('creating the shader program')
        self.program_id = gl.glCreateProgram()
        self.shader_ids = []

        for shader_type, shader_src in shaders.items():
            shader_id = gl.glCreateShader(shader_type)
            gl.glShaderSource(shader_id, shader_src)

            log.debug(f'compiling the {shader_type} shader')
            gl.glCompileShader(shader_id)

            # check if compilation was successful
            result = gl.glGetShaderiv(shader_id, gl.GL_COMPILE_STATUS)
            info_log_len = gl.glGetShaderiv(shader_id, gl.GL_INFO_LOG_LENGTH)
            if info_log_len:
                logmsg = gl.glGetShaderInfoLog(shader_id)
                log.error(logmsg)
                sys.exit(10)

            gl.glAttachShader(self.program_id, shader_id)
            self.shader_ids.append(shader_id)

        log.debug('linking shader program')
        gl.glLinkProgram(self.program_id)

        # check if linking was successful
        success = gl.glGetProgramiv(self.program_id, gl.GL_LINK_STATUS)
        info_log_len = gl.glGetProgramiv(self.program_id, gl.GL_INFO_LOG_LENGTH)
        if not success:
            logmsg = gl.glGetProgramInfoLog(self.program_id)
            log.error(logmsg)
            sys.exit(0)

        log.debug('installing shader program into rendering state')
        gl.glUseProgram(self.program_id)

    def bind(self):
        gl.glUseProgram(self.program_id)

    def get_uniform(self, name):
        return gl.glGetUniformLocation(self.program_id, name)

    def __del__(self):
        log.debug('cleaning up shader program')
        for shader_id in self.shader_ids:
            gl.glDetachShader(self.program_id, shader_id)
            gl.glDeleteShader(shader_id)
        gl.glDeleteProgram(self.program_id)
        gl.glUseProgram(0)
