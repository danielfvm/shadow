from OpenGL import GL as gl
from PIL import Image

import mouse
from utils import load_file

from shader import Shader
from config import Config

import cv2
import logging

log = logging.getLogger(__name__)

class Element():
    def __init__(self):
        pass

    def render(self, elapsed, width, height, quality):
        pass

    def cleanup(self):
        pass

class ElementShader(Element):
    def __init__(self, file):
        self.shader = Shader({
            gl.GL_VERTEX_SHADER: '''\
                #version 330 core
                layout(location = 0) in vec2 pos;
                void main() {
                  gl_Position.xy = pos;
                  gl_Position.w = 1.0;
                }
                ''',
            gl.GL_FRAGMENT_SHADER: load_file(file)
        })

    def render(self, elapsed, width, height):
        mouseX, mouseY = mouse.get_position()

        self.shader.bind()
        gl.glUniform2f(self.shader.get_uniform("resolution"), int(width * Config.QUALITY), int(height * Config.QUALITY))
        gl.glUniform1f(self.shader.get_uniform("time"), elapsed)
        gl.glUniform2f(self.shader.get_uniform("mouse"), mouseX / width, 1 - mouseY / height)

        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)

    def cleanup(self):
        del self.shader

class ElementScript(Element):
    def __init__(self, file):
        self.script = __import__(file[:-3])
        if hasattr(self.script, "init"):
            self.script.init()

    def render(self, elapsed, width, height):
        if hasattr(self.script, "render"):
            self.script.render(elapsed, width, height)

    def cleanup(self):
        if hasattr(self.script, "cleanup"):
            self.script.cleanup()

class ElementVideo(Element):
    def __init__(self, file):
        self.texture_id = gl.glGenTextures(1)

        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture_id)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)

        self.video_capture = cv2.VideoCapture(file)

        if not self.video_capture.isOpened():
            log.error("Failed to open video file " + file)
            exit(0)

        self.frames = []
        self.frame_pos = 0


        self.frame_count = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        self.tex_width  = self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.tex_height = self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)

        success = True

        while success:
            success, frame = self.video_capture.read()

            if not success:
                break

            # convert image to OpenGL texture format
            image = Image.fromarray(frame)
            self.tex_width = image.size[0]
            self.tex_height = image.size[1]

            data = image.tobytes("raw", "BGR", 0, -1)

            self.frames.append(data)


        # load shader for texture
        self.shader = Shader({
            gl.GL_VERTEX_SHADER: '''\
                #version 330 core
                layout(location = 0) in vec2 pos;

                void main() {
                  gl_Position.xy = pos;
                  gl_Position.w = 1.0;
                }
                ''',
            gl.GL_FRAGMENT_SHADER: '''\
                #version 330 core
                uniform sampler2D tex;
                uniform vec2 resolution;
                uniform vec2 position;

                void main() {
                    gl_FragColor = texture(tex, gl_FragCoord.xy / resolution.xy - position / resolution.xy);
                }
                '''
        })


    def bind_frame(self):
        data = self.frames[self.frame_pos]

        self.frame_pos += 1
        if self.frame_pos >= len(self.frames):
            self.frame_pos = 0

        # create texture
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture_id)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, self.tex_width, self.tex_height, 0, gl.GL_RGB, gl.GL_UNSIGNED_BYTE, data)

    def render(self, _, width, height):
        self.bind_frame()

        # scale to fit screen
        s = max(width / self.tex_width, height / self.tex_height)

        w = self.tex_width * s
        h = self.tex_height * s

        # center image
        x = (width - w) / 2
        y = (height - h) / 2

        # bind image and render it
        self.shader.bind()
        gl.glUniform2f(self.shader.get_uniform("position"), x * Config.QUALITY, y * quality)
        gl.glUniform2f(self.shader.get_uniform("resolution"), w * Config.QUALITY, h * quality)
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)

    def cleanup(self):
        gl.glDeleteTextures(1, self.texture_id)
        del self.shader


class ElementImage(Element):
    def __init__(self, file):
        self.texture_id = gl.glGenTextures(1)

        gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture_id)
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_REPEAT)
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_REPEAT)
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR_MIPMAP_LINEAR)

        self.tex = Image.open(file)

        # For smaller images we want them to look pixely
        if self.tex.width > 256 and self.tex.height > 256:
            gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        else:
            gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)

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
            gl.GL_VERTEX_SHADER: '''\
                #version 330 core
                layout(location = 0) in vec2 pos;

                void main() {
                  gl_Position.xy = pos;
                  gl_Position.w = 1.0;
                }
                ''',
            gl.GL_FRAGMENT_SHADER: '''\
                #version 330 core
                uniform sampler2D tex;
                uniform vec2 resolution;
                uniform vec2 position;

                void main() {
                    gl_FragColor = texture(tex, gl_FragCoord.xy / resolution.xy - position / resolution.xy);
                }
                '''
        })

    def render(self, _, width, height):

        # scale to fit screen
        s = max(width / self.tex.width, height / self.tex.height)

        w = self.tex.width * s
        h = self.tex.height * s

        # center image
        x = (width - w) / 2
        y = (height - h) / 2

        # bind image and render it
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture_id)
        self.shader.bind()
        gl.glUniform2f(self.shader.get_uniform("position"), x * Config.QUALITY, y * Config.QUALITY)
        gl.glUniform2f(self.shader.get_uniform("resolution"), w * Config.QUALITY, h * Config.QUALITY)
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)


    def cleanup(self):
        gl.glDeleteTextures(1, self.texture_id)
        del self.shader
