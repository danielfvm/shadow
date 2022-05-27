from threading import Thread
from OpenGL import GL as gl

import xcffib
import xcffib.xproto

from elements import *
from utils import *
from shader import Shader

from PboDownloader import PboDownloader

import contextlib
import logging
import ctypes
import time
import glfw
import sys

log = logging.getLogger(__name__)

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
        elif file.endswith(".mp4") or file.endswith(".mkv"):
            elements.append(ElementVideo(file))

    shader_texture = Shader({
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

            shader_texture.bind()
            gl.glUniform2f(shader_texture.get_uniform("resolution"), width, height)
            gl.glUniform1i(shader_texture.get_uniform("swap"), mode == Mode.ROOT) # root mode needs to be swapped vertically 

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

    del shader_texture

    for element in elements:
        element.cleanup()

    conn.core.FreePixmap(pixmap)
    conn.core.FreeGC(gc)
