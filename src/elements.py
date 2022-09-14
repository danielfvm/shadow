from importlib.machinery import ModuleSpec
import importlib.util

from OpenGL import GL as gl
from PIL import Image

import mouse
from utils import load_file

from shader import Shader
from config import Config, QualityMode

import logging
import glfw

log = logging.getLogger(__name__)

class ComponentShader():
    def __init__(self, file):
        self.shader = Shader({
            gl.GL_VERTEX_SHADER: '''
                #version 330 core
                layout(location = 0) in vec2 pos;
                void main() {
                  gl_Position.xy = pos;
                  gl_Position.w = 1.0;
                }
                ''',
            gl.GL_FRAGMENT_SHADER: load_file(file)
        })

        self.elapsed = 0
        self.frame = 0

    def render(self, dt, window):
        self.elapsed += dt
        self.frame += 1

        mouseX, mouseY = mouse.get_position()
        winX, winY = glfw.get_window_pos(window)

        mouseX = (mouseX - winX) / Config.WIDTH
        mouseY = 1 - (mouseY - winY) / Config.HEIGHT

        width = int(Config.WIDTH * Config.QUALITY)
        height = int(Config.HEIGHT * Config.QUALITY)

        self.shader.bind()
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, window.texture) # prev frame
        gl.glUniform1i(self.shader.get_uniform("currentBuffer"), 1)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, window.prevTexture) # prev frame
        gl.glUniform1i(self.shader.get_uniform("prevBuffer"), 0)

        gl.glUniform2f(self.shader.get_uniform("resolution"), width, height)
        gl.glUniform2f(self.shader.get_uniform("mouse"), mouseX, mouseY)
        gl.glUniform1f(self.shader.get_uniform("time"), self.elapsed)

        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)

    def cleanup(self):
        del self.shader

    @staticmethod
    def is_file(name):
        return ".glsl" in name or ".frag" in name or ".fshader" in name or ".fsh" in name


class ComponentScript():
    def __init__(self, path):
        self.spec = importlib.util.spec_from_file_location("", path)
        assert type(self.spec) is ModuleSpec, "Error"
        self.script = importlib.util.module_from_spec(self.spec)
        assert self.spec.loader != None, "Error"
        self.spec.loader.exec_module(self.script)

        if hasattr(self.script, "init"):
            self.script.init()

    def render(self, dt, window):
        if hasattr(self.script, "render"):
            self.script.render(dt, window, Config)

    def cleanup(self):
        if hasattr(self.script, "cleanup"):
            self.script.cleanup()

    @staticmethod
    def is_file(name):
        return ".py" in name

class ComponentVideo():
    def __init__(self, file):
        print("Video is currently not supported")
        pass

    def render(self, _):
        pass

    def cleanup(self):
        pass


    @staticmethod
    def is_file(name):
        return False #".mp4" in name or ".mkv" in name # TODO: add remaining supported filetypes

class ComponentAnimatedImage():
    def __init__(self, file):
        self.tex = Image.open(file)
        self.textures = []
        self.durations = []

        # TODO: currently loads gif to memory, will cause issues with bigger gifs
        for frame in range(0, self.tex.n_frames):
            self.tex.seek(frame)
            img = self.tex.convert("RGB")

            self.textures.append(gl.glGenTextures(1))
            self.durations.append(self.tex.info['duration'])

            gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.textures[frame])
            gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_REPEAT)
            gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_REPEAT)
            gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR_MIPMAP_LINEAR)

            # For smaller images we want them to look pixely
            if self.tex.width <= 256 or self.tex.height <= 256 or Config.QUALITY_MODE == QualityMode.PIXEL:
                gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
            else:
                gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)

            data = img.tobytes("raw", "RGB", 0, -1)
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, self.tex.width, self.tex.height, 0, gl.GL_RGB, gl.GL_UNSIGNED_BYTE, data)

            gl.glGenerateMipmap(gl.GL_TEXTURE_2D)

        # load shader for texture
        self.shader = Shader({
            gl.GL_VERTEX_SHADER: '''
                #version 330 core
                layout(location = 0) in vec2 pos;

                void main() {
                  gl_Position.xy = pos;
                  gl_Position.w = 1.0;
                }
                ''',
            gl.GL_FRAGMENT_SHADER: '''
                #version 330 core
                uniform sampler2D tex;
                uniform vec2 resolution;
                uniform vec2 position;

                void main() {
                    gl_FragColor = texture(tex, gl_FragCoord.xy / resolution.xy - position / resolution.xy);
                }
                '''
        })

        self.frame = 0
        self.elapsed = 0

    def render(self, dt, _):
        self.elapsed += dt

        # scale to fit screen
        s = max(Config.WIDTH / self.tex.width, Config.HEIGHT / self.tex.height)

        w = self.tex.width * s
        h = self.tex.height * s

        # center image
        x = (Config.WIDTH - w) / 2
        y = (Config.HEIGHT - h) / 2

        if self.frame >= self.tex.n_frames - 1:
            self.frame = 0
        elif self.elapsed > self.durations[self.frame] / 1000:
            self.elapsed -= self.durations[self.frame] / 1000
            self.frame += 1

        # bind image and render it
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.textures[self.frame])
        self.shader.bind()
        gl.glUniform2f(self.shader.get_uniform("position"), x * Config.QUALITY, y * Config.QUALITY)
        gl.glUniform2f(self.shader.get_uniform("resolution"), w * Config.QUALITY, h * Config.QUALITY)
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)


    def cleanup(self):
        for texID in self.textures:
            gl.glDeleteTextures(1, texID)

        del self.shader

    @staticmethod
    def is_file(name):
        return ".gif" in name


class ComponentImage():
    def __init__(self, file):
        self.texture_id = gl.glGenTextures(1)

        gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture_id)
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_REPEAT)
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_REPEAT)
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR_MIPMAP_LINEAR)

        self.tex = Image.open(file)

        # For smaller images we want them to look pixely
        if self.tex.width <= 256 or self.tex.height <= 256 or Config.QUALITY_MODE == QualityMode.PIXEL:
            gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        else:
            gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)

        # depending on image type we have an alpha channel
        mode = "".join(Image.Image.getbands(self.tex))
        if mode == "RGB":
            data = self.tex.tobytes("raw", "RGB", 0, -1)
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, self.tex.width, self.tex.height, 0, gl.GL_RGB, gl.GL_UNSIGNED_BYTE, data)
        else:
            data = self.tex.tobytes("raw", "RGBA", 0, -1)
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, self.tex.width, self.tex.height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, data)

        gl.glGenerateMipmap(gl.GL_TEXTURE_2D)

        # load shader for texture
        self.shader = Shader({
            gl.GL_VERTEX_SHADER: '''
                #version 330 core
                layout(location = 0) in vec2 pos;

                void main() {
                  gl_Position.xy = pos;
                  gl_Position.w = 1.0;
                }
                ''',
            gl.GL_FRAGMENT_SHADER: '''
                #version 330 core
                uniform sampler2D tex;
                uniform vec2 resolution;
                uniform vec2 position;

                void main() {
                    gl_FragColor = texture(tex, gl_FragCoord.xy / resolution.xy - position / resolution.xy);
                }
                '''
        })

    def render(self, _, __):

        # scale to fit screen
        s = max(Config.WIDTH / self.tex.width, Config.HEIGHT / self.tex.height)

        w = self.tex.width * s
        h = self.tex.height * s

        # center image
        x = (Config.WIDTH - w) / 2
        y = (Config.HEIGHT - h) / 2

        # bind image and render it
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture_id)
        self.shader.bind()
        gl.glUniform2f(self.shader.get_uniform("position"), x * Config.QUALITY, y * Config.QUALITY)
        gl.glUniform2f(self.shader.get_uniform("resolution"), w * Config.QUALITY, h * Config.QUALITY)
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)


    def cleanup(self):
        gl.glDeleteTextures(1, self.texture_id)
        del self.shader

    @staticmethod
    def is_file(name):
        return ".jpeg" in name or ".jpg" in name or ".png" in name or ".bmp" in name


def create_component_from_file(file):
    components = [ ComponentShader, ComponentScript, ComponentVideo, ComponentImage, ComponentAnimatedImage ]

    for c in components:
        if c.is_file(file):
            return c(file)

    log.error("Unsupported file format: " + file)

    return None
