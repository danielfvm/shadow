from abc import abstractmethod
from functools import reduce
from threading import Thread
from OpenGL import GL as gl
from screeninfo import get_monitors

from .config import *
from .components import *
from .glutils import *
from .shader import *
from .PboDownloader import *

import logging
import sys
import os
import glfw
import ctypes

if sys.platform.startswith("linux"):
    import xcffib
    from .xutils import *
elif sys.platform.startswith("win"):
    from ctypes import wintypes
    user32 = ctypes.windll.user32

log = logging.getLogger(__name__)

class Shadow():
    def __init__(self, monitor, files, width, height, monitor_offset=(0, 0)):
        self.width = width
        self.height = height
        self.window = self.create_window()

        centerX = int((monitor.width - self.width) / 2)
        centerY = int((monitor.height - self.height) / 2)
        glfw.set_window_pos(self.window, monitor_offset[0] + monitor.x + centerX, monitor_offset[1] + monitor.y + centerY)

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
        gl.glDeleteFramebuffers(1, [self.fbo])
        gl.glDeleteTextures(2, [self.texture, self.prevTexture])

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
        glfw.window_hint(glfw.VISIBLE, glfw.FALSE)

        log.debug('creating window')
        window = glfw.create_window(self.width, self.height, "Shadow", None, None)

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
        gl.glReadBuffer(gl.GL_COLOR_ATTACHMENT0)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.prevTexture)
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

class ShadowWindow(Shadow):
    def __init__(self, monitor, files, width, height):
        super().__init__(monitor, files, width, height)
        glfw.show_window(self.window)

    def swap(self):
        glfw.swap_buffers(self.window)

        # If window size changes, update width, height and framebuffer
        nwidth, nheight = glfw.get_window_size(self.window)

        if nwidth != self.width or nheight != self.height:
            # width and height should not get to small
            self.width = max(nwidth, 10)
            self.height = max(nheight, 10)

            # Delete existing framebuffer and create a new one with new scale
            gl.glDeleteFramebuffers(1, [self.fbo])
            gl.glDeleteTextures(2, [self.texture, self.prevTexture])
            
            self.texture, self.fbo = create_framebuffer(self.width, self.height)
            self.prevTexture = create_frametexture(self.width, self.height)

class ShadowBackground(Shadow):
    def __init__(self, monitor, files):
        super().__init__(monitor, files, monitor.width, monitor.height)

        conn = xcffib.Connection(display=os.environ.get("DISPLAY"))
        set_window_to_background(conn, glfw.get_x11_window(self.window))
        glfw.set_window_opacity(self.window, Config.OPACITY)

        glfw.window_hint(glfw.DECORATED, False)
        glfw.window_hint(glfw.FOCUSED, False)
        glfw.show_window(self.window)

    def swap(self):
        glfw.swap_buffers(self.window)

class ShadowRoot(Shadow):
    def __init__(self, monitor, files):
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

class ShadowWin10(Shadow):
    def __init__(self, monitor, files):
        # We have to set these hints before the window is created and positioned
        glfw.window_hint(glfw.DECORATED, False)
        glfw.window_hint(glfw.FOCUSED, False)
        
        # On Windows, the screen-space coordinate system is relative to the primary monitor,
        # and weirdly different in other places. Calculating the (negative) topleft-most coordinate
        # of any monitor, then using *the double of* that as an offset for each window,
        # seems to solve the discrepancies.
        monitor_offset = reduce(lambda acc, m: (max(acc[0], -m.x), max(acc[1], -m.y)), get_monitors(), (0, 0))
        super().__init__(monitor, files, monitor.width, monitor.height, monitor_offset)

        progman_hwnd = user32.FindWindowW("Progman", None)
        res = ctypes.c_ulong()

        user32.SendMessageTimeoutW(progman_hwnd, 0x052C, ctypes.c_ulong(0), None, 0, 1000, ctypes.byref(res))

        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        # Search for workerw
        self.workerw = None
        def enum_windows_callback(hwnd, _):
            if user32.FindWindowExW(hwnd, None, "SHELLDLL_DefView", None) != 0:
                self.workerw = user32.FindWindowExW(None, hwnd, "WorkerW",  None)
            return True
        user32.EnumWindows(WNDENUMPROC(enum_windows_callback), 0)

        # Set created window as child of workerw
        hwnd = glfw.get_win32_window(self.window)
        user32.SetParent(hwnd, self.workerw)

        # Hide window icon
        GWL_EXSTYLE=-20
        WS_EX_TOOLWINDOW=0x80

        user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, WS_EX_TOOLWINDOW)
        glfw.show_window(self.window)

    def swap(self):
        glfw.swap_buffers(self.window)

        # If window size changes, update width, height and framebuffer
        nwidth, nheight = glfw.get_window_size(self.window)

        if nwidth != self.width or nheight != self.height:
            # width and height should not get to small
            self.width = max(nwidth, 10)
            self.height = max(nheight, 10)

            # Delete existing framebuffer and create a new one with new scale
            gl.glDeleteFramebuffers(1, [self.fbo])
            gl.glDeleteTextures(2, [self.texture, self.prevTexture])
            
            self.texture, self.fbo = create_framebuffer(self.width, self.height)
            self.prevTexture = create_frametexture(self.width, self.height)

    def __del__(self):
        log.debug("Remove parent")
        user32.SetParent(self.workerw, 0)
