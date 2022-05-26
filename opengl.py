from utils import *
from threading import Thread
import contextlib, ctypes, logging, sys
from OpenGL import GL as gl
import glfw
import time
import io
import math

import mouse

import os
import struct
import xcffib
import xcffib.xproto

from PIL import Image
import numpy

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

@contextlib.contextmanager
def create_main_window(conn, mode, opacity, width, height):
    if not glfw.init():
        log.error('failed to initialize GLFW')
        sys.exit(1)
    try:
        log.debug('requiring modern OpenGL without any legacy features')
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.DOUBLEBUFFER, True)

        if mode == Mode.ROOT:
            glfw.window_hint(glfw.VISIBLE, glfw.FALSE)

        log.debug('opening window')
        window = glfw.create_window(width, height, "Show", None, None)
        if not window:
            log.error('failed to open GLFW window.')
            sys.exit(2)

        if mode == Mode.BACKGROUND:
            log.debug('changed window typehint to background')
            set_window_to_background(conn, glfw.get_x11_window(window))

        if mode != Mode.ROOT and opacity < 1:
            set_window_opacity(conn, glfw.get_x11_window(window), opacity)

        glfw.make_context_current(window)

        yield window

    finally:
        log.debug('terminating window context')
        glfw.terminate()

@contextlib.contextmanager
def create_vertex_array_object():
    log.debug('creating and binding the vertex array (VAO)')
    vertex_array_id = gl.glGenVertexArrays(1)
    try:
        gl.glBindVertexArray(vertex_array_id)
        yield
    finally:
        log.debug('cleaning up vertex array')
        gl.glDeleteVertexArrays(1, [vertex_array_id])

@contextlib.contextmanager
def create_vertex_buffer():
    with create_vertex_array_object():
        # 2 triangles
        vertex_data = [ 1, -1,   -1, -1,   -1,  1,
                       -1,  1,    1,  1,    1, -1 ]

        attr_id = 0  # No particular reason for 0,
                     # but must match the layout location in the shader.

        log.debug('creating and binding the vertex buffer (VBO)')
        vertex_buffer = gl.glGenBuffers(1)
        try:
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vertex_buffer)

            array_type = (gl.GLfloat * len(vertex_data))
            gl.glBufferData(gl.GL_ARRAY_BUFFER,
                            len(vertex_data) * ctypes.sizeof(ctypes.c_float),
                            array_type(*vertex_data),
                            gl.GL_STATIC_DRAW)

            log.debug('setting the vertex attributes')
            gl.glVertexAttribPointer(
               attr_id,            # attribute 0.
               2,                  # components per vertex attribute
               gl.GL_FLOAT,        # type
               False,              # to be normalized?
               0,                  # stride
               None                # array buffer offset
            )
            gl.glEnableVertexAttribArray(attr_id)  # use currently bound VAO
            yield
        finally:
            log.debug('cleaning up buffer')
            gl.glDisableVertexAttribArray(attr_id)
            gl.glDeleteBuffers(1, [vertex_buffer])

def load_shader_code(path):
    with open(path, 'r') as file:
        return file.read()

def load_shaders(shaders):
    log.debug('creating the shader program')
    program_id = gl.glCreateProgram()
    shader_ids = []

    try:
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

            gl.glAttachShader(program_id, shader_id)
            shader_ids.append(shader_id)

        log.debug('linking shader program')
        gl.glLinkProgram(program_id)

        # check if linking was successful
        result = gl.glGetProgramiv(program_id, gl.GL_LINK_STATUS)
        info_log_len = gl.glGetProgramiv(program_id, gl.GL_INFO_LOG_LENGTH)
        if info_log_len:
            logmsg = gl.glGetProgramInfoLog(program_id)
            log.error(logmsg)
            sys.exit(11)

        log.debug('installing shader program into rendering state')
        gl.glUseProgram(program_id)
    finally:
        log.debug('cleaning up shader program')
        for shader_id in shader_ids:
            gl.glDetachShader(program_id, shader_id)
            gl.glDeleteShader(shader_id)
        gl.glUseProgram(0)

        #gl.glDeleteProgram(program_id)
        return program_id

def create_framebuffer(width, height):
    # create a new framebuffer
    fbo = gl.glGenFramebuffers(1)
    gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)

    # create a new texture
    texture = gl.glGenTextures(1)
    gl.glBindTexture(gl.GL_TEXTURE_2D, texture)

    gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, width, height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)

    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)

    # apply texture to framebuffer
    gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, texture, 0)
    gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    return texture, fbo

# Origional function from "xproto.py", because of "xcffib.pack_list" 
# it was too slow and was removed in this function.
def PutImage(conn, format, drawable, gc, width, height, dst_x, dst_y, left_pad, depth, data, is_checked=False):
    buf = io.BytesIO()

    p = struct.pack("=xB2xIIHHhhBB2x", format, drawable, gc, width, height, dst_x, dst_y, left_pad, depth)
    buf.write(p)
    buf.write(data)
    l = time.time()
    conn.core.send_request(72, buf, is_checked=is_checked)
    #print((time.time() - l) * 1000)

class Element():
    def __init__(self) -> None:
        pass

    def render(self, elapsed, width, height, quality):
        pass

    def cleanup(self):
        pass

class ElementShader(Element):
    def __init__(self, file) -> None:
        self.shader_id = load_shaders({
            gl.GL_VERTEX_SHADER: '''\
                #version 330 core
                layout(location = 0) in vec2 pos;
                void main() {
                  gl_Position.xy = pos;
                  gl_Position.w = 1.0;
                }
                ''',
            gl.GL_FRAGMENT_SHADER: load_shader_code(file)
        })

    def render(self, elapsed, width, height, quality):
        mouseX, mouseY = mouse.get_position()

        gl.glUseProgram(self.shader_id)
        gl.glUniform2f(gl.glGetUniformLocation(self.shader_id, "resolution"), int(width * quality), int(height * quality))
        gl.glUniform1f(gl.glGetUniformLocation(self.shader_id, "time"), elapsed)
        gl.glUniform2f(gl.glGetUniformLocation(self.shader_id, "mouse"), mouseX / width, 1 - mouseY / height)

        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)

    def cleanup(self):
        gl.glDeleteProgram(self.shader_id)

class ElementScript(Element):
    def __init__(self, file) -> None:
        self.script = __import__(file[:-3])
        if hasattr(self.script, "init"):
            self.script.init()

    def render(self, elapsed, width, height, quality):
        if hasattr(self.script, "render"):
            self.script.render(elapsed, width, height, quality)

    def cleanup(self):
        if hasattr(self.script, "cleanup"):
            self.script.cleanup()


class ElementImage(Element):
    def __init__(self, file) -> None:
        self.id = gl.glGenTextures(1)

        gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.id)
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
        self.shader_id = load_shaders({
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

    def render(self, elapsed, width, height, quality):

        # scale to fit screen
        s = max(width / self.tex.width, height / self.tex.height)

        w = self.tex.width * s
        h = self.tex.height * s

        # center image
        x = (width - w) / 2
        y = (height - h) / 2

        # bind image and render it
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.id)
        gl.glUseProgram(self.shader_id)
        gl.glUniform2f(gl.glGetUniformLocation(self.shader_id, "position"), x * quality, y * quality)
        gl.glUniform2f(gl.glGetUniformLocation(self.shader_id, "resolution"), w * quality, h * quality)
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)


    def cleanup(self):
        gl.glDeleteTextures(1, self.id)
        gl.glDeleteProgram(self.shader_id)

class PboDownloader():
    def __init__(self, fmt, width, height, num) -> None:
        self.fmt = fmt
        self.num_pbos = num
        self.dx = 0
        self.num_downloads = 0
        self.width = width
        self.height = height

        if gl.GL_RED == self.fmt or gl.GL_GREEN == self.fmt or gl.GL_BLUE == self.fmt:
            self.nbytes = self.width * self.height
        elif gl.GL_RGB == self.fmt or gl.GL_BGR == self.fmt:
            self.nbytes = self.width * self.height * 3
        elif gl.GL_RGBA == self.fmt or gl.GL_BGRA == self.fmt:
            self.nbytes = self.width * self.height * 4
        else:
            self.nbytes = 0
            log.error("Unhandled pixel format, use GL_R, GL_RG, GL_RGB or GL_RGBA.")

        if self.nbytes == 0:
            log.error("Invalid width or height given: %{width} x %{height}")

        self.pbos = (ctypes.c_int * num)()

        self.pixels = (ctypes.c_char * self.nbytes)()

        gl.glGenBuffers(num, self.pbos)

        for i in range(num):
            log.debug("pbodownloader.pbos[%d] = %d, nbytes: %d", i, self.pbos[i], self.nbytes)

            gl.glBindBuffer(gl.GL_PIXEL_PACK_BUFFER, self.pbos[i])
            gl.glBufferData(gl.GL_PIXEL_PACK_BUFFER, self.nbytes, None, gl.GL_STREAM_READ)

        gl.glBindBuffer(gl.GL_PIXEL_PACK_BUFFER, 0)

    def download(self):
        if self.num_downloads < self.num_pbos:
            gl.glBindBuffer(gl.GL_PIXEL_PACK_BUFFER, self.pbos[self.dx])
            gl.glReadPixels(0, 0, self.width, self.height, self.fmt, gl.GL_UNSIGNED_BYTE, 0)   # When a GL_PIXEL_PACK_BUFFER is bound, the last 0 is used as offset into the buffer to read into.
            #log.debug("glReadPixels() with pbo: %{self.pbos[self.dx]}")
        else:
            #log.debug("glMapBuffer() with pbo: %{self.pbos[self.dx]}")

            gl.glBindBuffer(gl.GL_PIXEL_PACK_BUFFER, self.pbos[self.dx])

            ptr = gl.glMapBuffer(gl.GL_PIXEL_PACK_BUFFER, gl.GL_READ_ONLY)
            if ptr != None:
                #memcpy(self.pixels, ptr, self.nbytes)
                self.pixels = (ctypes.c_char * self.nbytes).from_address(ptr)
                gl.glUnmapBuffer(gl.GL_PIXEL_PACK_BUFFER)
            else:
                log.error("Failed to map the buffer")

            # Trigger the next read.
            #log.debug("glReadPixels() with pbo: %{self.pbos[self.dx]}")
            gl.glReadPixels(0, 0, self.width, self.height, self.fmt, gl.GL_UNSIGNED_BYTE, 0)

        self.dx += 1
        self.dx = self.dx % self.num_pbos

        self.num_downloads += 1

        if self.num_downloads == sys.maxsize:
            self.num_downloads = self.num_pbos

    gl.glBindBuffer(gl.GL_PIXEL_PACK_BUFFER, 0);


def main_loop(conn, mode, quality, speed, framelimit, window, files):
    old = time.time()
    width = 1920
    height = 1080

    screen = conn.get_setup().roots[0]

    texture, fbo = create_framebuffer(int(width * quality), int(height * quality))

    elements = []

    for file in files:
        if file.endswith(".glsl"):
            elements.append(ElementShader(file))
        elif file.endswith(".py"):
            elements.append(ElementScript(file))
        elif file.endswith(".png") or file.endswith(".jpg") or file.endswith(".jpeg"):
            elements.append(ElementImage(file))

    shader_texture_id = load_shaders({
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
            uniform bool swap;
            void main() {
              if (swap) {
                gl_FragColor = texture(tex, vec2(0, 1) + gl_FragCoord.xy / resolution.xy * vec2(1, -1));
              } else {
                gl_FragColor = texture(tex, gl_FragCoord.xy / resolution.xy);
              }
            }
            ''',
    })

    # Pixmap used to set root background image
    pixmap = conn.generate_id()
    conn.core.CreatePixmap(
        screen.root_depth,
        pixmap,
        screen.root,
        width,
        height,
    )

    # GC used for converting OpenGL's framebuffer to a pixmap
    gc = conn.generate_id()
    conn.core.CreateGC(
        gc,
        pixmap,
        0,
        None,
    )

    frames = 0
    passed = 0
    elapsed = 0

    pbo = PboDownloader(gl.GL_BGRA, width, height, 1)

    try:
        while glfw.get_key(window, glfw.KEY_ESCAPE) != glfw.PRESS and not glfw.window_should_close(window):

            # Calculate framerate limit
            now = time.time()
            dt = now - old
            time.sleep(max(1 / framelimit - dt, 0))

            # calculate deltatime
            now = time.time()
            dt = now - old
            old = now

            elapsed += dt * speed
            passed += dt
            frames += 1

            if passed >= 1:
                print(frames)
                passed = 0
                frames = 0

            # If window size changes, update width, height and framebuffer
            nwidth, nheight = glfw.get_window_size(window)

            if nwidth != width or nheight != height:
                width = nwidth
                height = nheight
                gl.glDeleteFramebuffers(1, fbo)
                gl.glDeleteTextures(1, texture)
                texture, fbo = create_framebuffer(int(width * quality), int(height * quality))


            # Render shader background animation to framebuffer with less quality if set
            gl.glViewport(0, 0, int(width * quality), int(height * quality))
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

            gl.glEnable(gl.GL_BLEND)
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

            for element in elements:
                element.render(elapsed, width, height, quality)

            # Draw framebuffer with normal size to window
            gl.glViewport(0, 0, width, height)
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)  # unbind FBO to set the default framebuffer
            gl.glBindTexture(gl.GL_TEXTURE_2D, texture) # color attachment texture

            gl.glUseProgram(shader_texture_id)
            gl.glUniform2f(gl.glGetUniformLocation(shader_texture_id, "resolution"), width, height)
            gl.glUniform1i(gl.glGetUniformLocation(shader_texture_id, "swap"), mode == Mode.ROOT) # root mode needs to be swapped vertically 

            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
            gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)

            # Convert framebuffer to pixmap and set it to root window
            if mode == Mode.ROOT:
                def pbo_to_screen():
                    PutImage(conn, xcffib.xproto.ImageFormat.ZPixmap, pixmap, gc, width, height, 0, 0, 0, screen.root_depth, pbo.pixels)
                    set_wallpaper_pixmap(conn, screen, pixmap)

                pbo.download()
                Thread(target=pbo_to_screen,args=()).start()

            else:
                glfw.swap_buffers(window) # Apply changes to window

            glfw.poll_events()
    except KeyboardInterrupt:
        log.debug("user send exit signal")

    # Free buffers
    gl.glDeleteFramebuffers(1, fbo)
    gl.glDeleteTextures(1, texture)
    gl.glDeleteProgram(shader_texture_id)

    for element in elements:
        element.cleanup()

    conn.core.FreePixmap(pixmap)
    conn.core.FreeGC(gc)
