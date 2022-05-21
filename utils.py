import xcffib
import cairocffi
import cairocffi.pixbuf
import xcffib.xproto
import enum

def kill(conn, screen):
    XA_PIXMAP = 20
    atom = conn.core.InternAtom(True, 13, '_XROOTPMAP_ID').reply().atom
    atom = conn.core.InternAtom(True, 16, 'ESETROOT_PMAP_ID').reply().atom

    reply = conn.core.GetProperty(
        False, screen.root, atom, xcffib.xproto.GetPropertyType.Any, 0, 1
    ).reply()

    if reply.type == XA_PIXMAP:
        reply = conn.core.GetProperty(
            False, screen.root, atom, xcffib.xproto.GetPropertyType.Any, 0, 1
        ).reply()

        if reply.type == XA_PIXMAP:
            pixmap_addr = int.from_bytes(b''.join(reply.value), byteorder='little')
            conn.core.KillClient(pixmap_addr)

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

def set_window_opacity(conn, window, opacity):
    value = int(opacity * 0xffffffff)

    conn.core.ChangeProperty(
        xcffib.xproto.PropMode.Replace,
        window,
        conn.core.InternAtom(False, 22, '_NET_WM_WINDOW_OPACITY').reply().atom,
        xcffib.xproto.Atom.CARDINAL,
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

class Mode(enum.Enum):
    WINDOW = "window"
    BACKGROUND = "background"
    ROOT = "root"

