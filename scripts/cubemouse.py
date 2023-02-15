import mouse
import numpy as np

FACTOR = 0.1 # you can change this

def normalized(v):
    norm = np.linalg.norm(np.asarray_chkfinite(v), ord=None, axis=None, keepdims=False)
    return v / norm if norm > 0 else v

def perspective(fov, aspect, near, far):
    n, f = near, far
    t = np.tan((fov * np.pi / 180) / 2) * near
    b = - t
    r = t * aspect
    l = b * aspect
    assert abs(r - l) > 0
    assert abs(t - b) > 0
    assert abs(n - f) > 0
    return np.array((
        ((2*n)/(r-l),           0,           0,  0),
        (          0, (2*n)/(t-b),           0,  0),
        ((r+l)/(r-l), (t+b)/(t-b), (f+n)/(n-f), -1),
        (          0,           0, 2*f*n/(n-f),  0)))

def look_at(eye, target, up):
    zax = normalized(eye - target)
    xax = normalized(np.cross(up, zax))
    yax = np.cross(zax, xax)
    x = - xax.dot(eye)
    y = - yax.dot(eye)
    z = - zax.dot(eye)
    return np.array(((xax[0], yax[0], zax[0], 0),
                     (xax[1], yax[1], zax[1], 0),
                     (xax[2], yax[2], zax[2], 0),
                     (     x,      y,      z, 1)))

def create_mvp(eyeX, eyeY, eyeZ):
    fov, near, far = 90, 0.1, 1000
    eye = np.array((eyeX, eyeY, eyeZ))
    target, up = np.array((0,0,0)), np.array((0,1,0))
    projection = perspective(fov, 1, near, far)
    view = look_at(eye, target, up)
    model = np.identity(4)
    mvp = model @ view @ projection
    return mvp.astype(np.float32)

currentX = 0.5
currentY = 0.5

def render(_, show):
    global currentX, currentY

    mouseX, mouseY = mouse.get_position()

    mouseX = mouseX / show.width
    mouseY = 1 - mouseY / show.height

    currentX += (mouseX - currentX) * FACTOR
    currentY += (mouseY - currentY) * FACTOR

    show.mvp = create_mvp((0.5 - currentX) * 0.1, (0.5 - currentY) * 0.1, 1.9)
