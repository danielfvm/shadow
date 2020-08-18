# mousepos.py (linux only)
"""module mousepos
"""
# uses the package python-xlib
# from http://snipplr.com/view/19188/mouseposition-on-linux-via-xlib/
from Xlib import display
def mousepos():
    """mousepos() --> (x, y) get the mouse coordinates on the screen (linux, Xlib)."""
    data = display.Display().screen().root.query_pointer()._data
    return data["root_x"], data["root_y"]
if __name__ == "__main__":
	x, y = mousepos()
	print(x)
	print(y)
