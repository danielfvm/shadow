# SGround
A real shader background for your Linux (Tiling) Window Manager.
Supports Mouse interaction with Shader.

## Supported WM
Should work on most (Tiling) Window Managers with normal x11 root background.
Currently tested on:
* i3wm (working)
* awesome (working)
* Gnome (not working)

## Installation
```
git clone https://github.com/danielfvm/SGround
cd SGround
make
make install
```

## Usage
```
sground <path>
sground <path> [quality]
sground <path> [quality] [speed]
```

quality default: 1.0
(higher: lower quality)

speed default: 1.0
(higher: faster speed)

You can write your own fragment shader, or get one
from: http://glslsandbox.com/

## Future Work
* Multi Monitor support
* Support for Gnome
