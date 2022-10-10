from OpenGL import GL as gl

import logging, ctypes, sys

log = logging.getLogger(__name__)

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

        else:
            gl.glBindBuffer(gl.GL_PIXEL_PACK_BUFFER, self.pbos[self.dx])

            ptr = gl.glMapBuffer(gl.GL_PIXEL_PACK_BUFFER, gl.GL_READ_ONLY)
            if ptr != None:
                self.pixels = (ctypes.c_char * self.nbytes).from_address(ptr)
                gl.glUnmapBuffer(gl.GL_PIXEL_PACK_BUFFER)
            else:
                log.error("Failed to map the buffer")

            # Trigger the next read.
            gl.glReadPixels(0, 0, self.width, self.height, self.fmt, gl.GL_UNSIGNED_BYTE, 0)

        self.dx += 1
        self.dx = self.dx % self.num_pbos

        self.num_downloads += 1

        if self.num_downloads == sys.maxsize:
            self.num_downloads = self.num_pbos

    gl.glBindBuffer(gl.GL_PIXEL_PACK_BUFFER, 0);

