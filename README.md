# Show
"Show" stands for `Shaders On Wallpaper` and it renders a realtime glsl shader on your Linux desktop.
It is compatible with many shaders from [glslsandbox.com](http://glslsandbox.com/).

There are currently 3 available render modes:

* Background (default):
The Show window is being set to the background using a `typehint`.
This might not be supported by your window manager (e.g. i3),
but works on most desktop environments (Gnome, Xfce, Awesome, KDE, ...)

* Root:
Show will render the shader on the X11 root window.
This mode has a lot of cpu usage and wont work in most desktop environments.
This is only advised if the `background` mode does not work for you.

* Window:
This mode might be useful for shader developers.
Show will create a normal window displaying the effect.

## Features
* Compatible with [glslsandbox.com](http://glslsandbox.com/)
* Three different render modes
* Change speed & quality level
* Opacity on wallpaper
* Mouse position support
* gif support
* mp4 support (work in progress)
* jpg/png support
* expandable with own python scripts (work in progress)

## Installation
```
$ git clone https://github.com/danielfvm/show.git
$ cd show
$ python -m pip install -r requirements.txt
$ python src/show.py
```

## Usage
```
Usage: show <path> [options]
Options:
  -q, --quality		Changes quality level of the shader, default 1.
  -s, --speed  		Changes animation speed, default 1.
  -m, --mode   		Changes rendering mode. Modes: root, window, background
  -o, --opacity		Sets background window transparency if in window/background mode

Example:
  show example.glsl -q 0.5 -m background
```

### Info:
* Opacity doesn't work on Wayland.
* Use `root` mode on i3wm
