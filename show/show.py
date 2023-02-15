from abc import abstractmethod
from threading import Thread
from OpenGL import GL as gl

from show.config import *
from show.components import *
from show.utils import *
from show.shader import *
from show.PboDownloader import *

import logging
import xcffib
import sys
import os
import glfw
import ctypes

log = logging.getLogger(__name__)

class Show():
    def __init__(self, monitor, files, width, height):
        self.width = width
        self.height = height
        self.window = self.create_window()

        centerX = int((monitor.width - self.width) / 2)
        centerY = int((monitor.height - self.height) / 2)
        glfw.set_window_pos(self.window, monitor.x + centerX, monitor.y + centerY)

        # Create vertex array
        log.debug('creating and binding the vertex array (VAO)')
        self.vertex_array_id = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(self.vertex_array_id)

        # Create vertex buffer
        vertex_data = [ 1, -1,   -1, -1,   -1,  1,
                       -1,  1,    1,  1,    1, -1 ]

        self.attr_id = 0  # No particular reason for 0,
                     # but must match the layout location in the shader.

        log.debug('creating and binding the vertex buffer (VBO)')
        self.vertex_buffer = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vertex_buffer)

        array_type = (gl.GLfloat * len(vertex_data))
        gl.glBufferData(gl.GL_ARRAY_BUFFER,
                        len(vertex_data) * ctypes.sizeof(ctypes.c_float),
                        array_type(*vertex_data),
                        gl.GL_STATIC_DRAW)

        log.debug('setting the vertex attributes')
        gl.glVertexAttribPointer(self.attr_id, 2, gl.GL_FLOAT, False, 0, None)
        gl.glEnableVertexAttribArray(self.attr_id)  # use currently bound VAO

        log.debug('creating framebuffers')
        self.texture, self.fbo = create_framebuffer(self.width, self.height)
        self.prevTexture = create_frametexture(self.width, self.height)

        log.debug('loading shaders and locations')
        self.shader_texture = Shader({
            gl.GL_VERTEX_SHADER: '''\
                #version 330 core
                layout(location = 0) in vec2 pos;
                out vec2 coords;
                uniform mat4 mvp;
                uniform bool swap;

                void main() {
                  vec4 position = mvp * vec4(pos, 1, 1);

                  if (swap) {
                    position *= vec4(1, -1, 1, 1);
                  }

                  gl_Position = position;
                  coords = pos * vec2(0.5) + vec2(0.5);
                }
                ''',
            gl.GL_FRAGMENT_SHADER: '''\
                #version 330 core
                uniform sampler2D tex;
                uniform vec2 resolution;

                out vec4 color;

                in vec2 coords;

                void main() {
                  color = texture(tex, coords);
                }
                ''',
        })
        self.location_resolution = self.shader_texture.get_uniform("resolution")
        self.location_swap = self.shader_texture.get_uniform("swap")
        self.location_mvp = self.shader_texture.get_uniform("mvp")

        # Can be used for cool 3d effects
        self.mvp = [[ 1., 0., 0.,  0., ],
                    [ 0., 1., 0.,  0., ],
                    [ 0., 0., -1,  -1.,],
                    [ 0., 0., 1.7, 1.9,]]

        # Initialize components at the end, in case if it references the above defined objects
        # that they are already initialized
        self.components = self.init_components(files)

    def __del__(self):
        log.debug('cleaning up components')
        for c in self.components:
            c.cleanup()

        log.debug('cleaning up vertex buffer')
        gl.glDisableVertexAttribArray(self.attr_id)
        gl.glDeleteBuffers(1, [self.vertex_buffer])

        log.debug('cleaning up vertex array')
        gl.glDeleteVertexArrays(1, [self.vertex_array_id])

        log.debug('deleting framebuffer and texture')
        gl.glDeleteFramebuffers(1, self.fbo)
        gl.glDeleteTextures(1, self.texture)

        log.debug('closing glfw')
        glfw.terminate()

    def init_components(self, files) -> list:
        log.debug('initializing components')

        components = []

        for file in files:
            c = create_component_from_file(file)
            if c is not None:
                components.append(c)

        return components

    def create_window(self) -> glfw._GLFWwindow:
        log.debug('requiring modern OpenGL without any legacy features')
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.DOUBLEBUFFER, True)
        glfw.window_hint(glfw.TRANSPARENT_FRAMEBUFFER, True)

        log.debug('creating window')
        window = glfw.create_window(self.width, self.height, "Show", None, None)
        if not window:
            log.error('failed to open GLFW window.')
            sys.exit(0)

        log.debug('making created window opengl context')
        glfw.make_context_current(window)

        return window

    def render(self, dt):
        # Render shader background animation to framebuffer with less quality if set
        gl.glViewport(0, 0, int(self.width * Config.QUALITY), int(self.height * Config.QUALITY))
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

        # Update all components
        for c in self.components:
            c.render(dt, self)

        # Copy rendered framebuffer to prevTexture which is being used for "prevBuffer" sampler
        gl.glReadBuffer(gl.GL_COLOR_ATTACHMENT0);
        gl.glActiveTexture(gl.GL_TEXTURE0);
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.prevTexture);
        gl.glCopyTexSubImage2D(gl.GL_TEXTURE_2D, 0, 0, 0, 0, 0, int(self.width * Config.QUALITY), int(self.height * Config.QUALITY));

        # Draw framebuffer with normal size to window
        gl.glViewport(0, 0, self.width, self.height)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)  # unbind FBO to set the default framebuffer
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture) # color attachment texture

        self.shader_texture.bind()
        gl.glUniform2f(self.location_resolution, self.width, self.height)
        gl.glUniform1i(self.location_swap, Config.BACKGROUND_MODE == BackgroundMode.ROOT) # root mode needs to be swapped vertically 
        gl.glUniformMatrix4fv(self.location_mvp, 1, False, self.mvp)

        # Draw rectangle with our texture
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)

        # Update
        glfw.poll_events()

    def is_running(self):
        return glfw.get_key(self.window, glfw.KEY_ESCAPE) != glfw.PRESS and not glfw.window_should_close(self.window)

    # Apply changes to canvas
    @abstractmethod
    def swap(self):
        log.error('No implementation!')

class ShowWindow(Show):
    def __init__(self, monitor, files, width, height):
        super().__init__(monitor, files, width, height)

    def swap(self):
        glfw.swap_buffers(self.window)

        # If window size changes, update width, height and framebuffer
        nwidth, nheight = glfw.get_window_size(self.window)

        if nwidth != self.width or nheight != self.height:
            # width and height should not get to small
            self.width = max(nwidth, 10)
            self.height = max(nheight, 10)

            # Delete existing framebuffer and create a new one with new scale
            gl.glDeleteFramebuffers(1, self.fbo)
            gl.glDeleteTextures(1, self.texture)
            self.texture, self.fbo = create_framebuffer(self.width, self.height)

            gl.glDeleteTextures(1, self.prevTexture)
            self.prevTexture = create_frametexture(self.width, self.height)

class ShowBackground(Show):
    def __init__(self, monitor, files):
        super().__init__(monitor, files, monitor.width, monitor.height)

        conn = xcffib.Connection(display=os.environ.get("DISPLAY"))
        set_window_to_background(conn, glfw.get_x11_window(self.window))
        glfw.set_window_opacity(self.window, Config.OPACITY)

        glfw.window_hint(glfw.DECORATED, False)
        glfw.window_hint(glfw.FOCUSED, False)

    def swap(self):
        glfw.swap_buffers(self.window)

class ShowRoot(Show):
    def __init__(self, monitor, files):
        glfw.window_hint(glfw.VISIBLE, glfw.FALSE)

        super().__init__(monitor, files, monitor.width, monitor.height)

        self.conn = xcffib.Connection(display=os.environ.get("DISPLAY"))
        self.screen = self.conn.get_setup().roots[0]
        self.pbo = PboDownloader(gl.GL_BGRA, self.width, self.height, 1)

        # Pixmap used to set root background image
        self.pixmap = self.conn.generate_id()
        self.conn.core.CreatePixmap(
            self.screen.root_depth,
            self.pixmap,
            self.screen.root,
            self.width,
            self.height,
        )

        # GC used for converting OpenGL's framebuffer to a pixmap
        self.gc = self.conn.generate_id()
        self.conn.core.CreateGC(
            self.gc,
            self.pixmap,
            0,
            None,
        )

    def swap(self):
        def pbo_to_screen():
            PutImage(self.conn, xcffib.xproto.ImageFormat.ZPixmap, self.pixmap, self.gc, self.width, self.height, 0, 0, 0, self.screen.root_depth, self.pbo.pixels)
            set_wallpaper_pixmap(self.conn, self.screen, self.pixmap)

        self.pbo.download()
        Thread(target=pbo_to_screen, args=()).start()

    def __del__(self):
        self.conn.core.FreePixmap(self.pixmap)
        self.conn.core.FreeGC(self.gc)
        super().__del__()
