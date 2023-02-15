from OpenGL import GL as gl

from show.config import Config, QualityMode

import xcffib
import cairocffi
import cairocffi.pixbuf
import xcffib.xproto

import struct
import io

import logging

log = logging.getLogger(__name__)

def set_wallpaper_pixmap(conn, screen, pixmap):
    # remove prev: kill()
    conn.core.ChangeProperty(
        xcffib.xproto.PropMode.Replace,
        screen.root,
        conn.core.InternAtom(False, 13, '_XROOTPMAP_ID').reply().atom,
        xcffib.xproto.Atom.PIXMAP,
        32, 1, [pixmap]
    )
    conn.core.ChangeProperty(
        xcffib.xproto.PropMode.Replace,
        screen.root,
        conn.core.InternAtom(False, 16, 'ESETROOT_PMAP_ID').reply().atom,
        xcffib.xproto.Atom.PIXMAP,
        32, 1, [pixmap]
    )

    conn.core.ChangeWindowAttributes(
        screen.root, xcffib.xproto.CW.BackPixmap, [pixmap]
    )
    conn.core.ClearArea(
        0, screen.root,
        0, 0,           # x and y position
        screen.width_in_pixels, screen.height_in_pixels
    )

    conn.flush()

    conn.core.SetCloseDownMode(xcffib.xproto.CloseDown.RetainPermanent)

def set_window_to_background(conn, window):
    value = conn.core.InternAtom(False, 27, '_NET_WM_WINDOW_TYPE_DESKTOP').reply().atom

    conn.core.ChangeProperty(
        xcffib.xproto.PropMode.Replace,
        window,
        conn.core.InternAtom(False, 19, '_NET_WM_WINDOW_TYPE').reply().atom,
        xcffib.xproto.Atom.ATOM,
        32, 1, [value]
    )

    conn.flush()

def get_root_visual(screen):
    for depth in screen.allowed_depths:
        for visual in depth.visuals:
            if visual.visual_id == screen.root_visual:
                return visual
    return None

def load_pixmap(conn, screen, path):
    with open(path, 'rb') as fd:
        image, _ = cairocffi.pixbuf.decode_to_image_surface(fd.read())

    pixmap = conn.generate_id()
    conn.core.CreatePixmap(
        screen.root_depth,
        pixmap,
        screen.root,
        screen.width_in_pixels,
        screen.height_in_pixels,
    )

    root_visual = get_root_visual(screen)

    surface = cairocffi.xcb.XCBSurface(
        conn, pixmap, root_visual,
        screen.width_in_pixels, screen.height_in_pixels,
    )

    with cairocffi.Context(surface) as context:
        context.set_source_surface(image)
        context.paint()

    return pixmap


# Original function from "xproto.py" was because of "xcffib.pack_list" too slow,
# this function call was removed from this function as it is not necessary.
def PutImage(conn, format, drawable, gc, width, height, dst_x, dst_y, left_pad, depth, data, is_checked=False):
    buf = io.BytesIO()
    p = struct.pack("=xB2xIIHHhhBB2x", format, drawable, gc, width, height, dst_x, dst_y, left_pad, depth)
    buf.write(p)
    buf.write(data)
    conn.core.send_request(72, buf, is_checked=is_checked)

def create_frametexture(width, height):
    texture = gl.glGenTextures(1)
    gl.glBindTexture(gl.GL_TEXTURE_2D, texture)

    width = int(width * Config.QUALITY)
    height = int(height * Config.QUALITY)

    gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, width, height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)

    gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
    gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
    gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
    gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)

    if Config.QUALITY_MODE == QualityMode.PIXEL:
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)

    return texture


def create_framebuffer(width, height):
    # create a new framebuffer
    fbo = gl.glGenFramebuffers(1)
    gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)

    # create a new texture
    texture = create_frametexture(width, height)

    # apply texture to framebuffer
    gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, texture, 0)
    gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    return texture, fbo
