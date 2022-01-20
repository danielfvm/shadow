# Show 
Show stands for `Shaders On Wallpaper` and it can render a realtime glsl shader on your Linux Desktop Background.
It is compatible with many shaders from [glslsandbox.com](http://glslsandbox.com/).
Duo to different Desktop Environments and Window Managers, there are currently 3 Modes you can choose from.

* background (default)
In this mode a new window is being created. It is being set to the background using a `typehint`. This might
not being supported by your Window Manager (like i3), but should work on most desktop environments (Gnome, Xfce, Awesome, ...)

* root
In this mode it will render the shader on the X11 Root Window. This mode has a lot of cpu usage and wont work 
in most Desktop Environments. You should only use this option if you are running a Window Manager that doesn't 
support the `background` mode.

* window
This mode might be usefull for those who want to develop a shader. It will create a normal window with a shader.

## Features
* Compatible with [glslsandbox.com](http://glslsandbox.com/)
* Three different render modes
* Change speed & quality
* Opacity on wallpaper
* Mouse support

## Installation
```
git clone https://github.com/danielfvm/show
cd show
make
make install
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

## Future Work
* Fix not working shaders from glslsandbox.com (missing `uniforms`)
* Multi Monitor support
