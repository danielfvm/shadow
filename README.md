# Show
"Show" stands for `Shaders On Wallpaper` and it renders a realtime glsl shader on your Linux desktop.
It is compatible with most shaders from [glslsandbox.com](http://glslsandbox.com/). Additionally you can put multiple shaders, images, videos and interactive scripts on top of each other to create an amazing looking desktop.

![image](https://user-images.githubusercontent.com/23420640/174047138-8fcfc170-c4ed-4fa3-ab06-8030dd264b46.png)


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
usage: show.py [-h] [-q QUALITY] [-s SPEED] [-o OPACITY] [-m MODE] [-d DISPLAY] [-f FRAMELIMIT] [-qm QUALITYMODE]

options:
  -h, --help            show this help message and exit
  -q QUALITY, --quality QUALITY
                        Changes quality level of the shader, default 1.
  -s SPEED, --speed SPEED
                        Changes animation speed, default 1.
  -o OPACITY, --opacity OPACITY
                        Sets background window transparency, default 1.
  -m MODE, --mode MODE  Changes rendering mode. Modes: root, window, background.
  -d DISPLAY, --display DISPLAY
                        Selects a monitor
  -f FRAMELIMIT, --framelimit FRAMELIMIT
                        Set the maximum framerate limit, default 60
  -qm QUALITYMODE, --qualitymode QUALITYMODE
                        Should it pixelize or smoothen the image at lower quality? default: smooth
```

## Examples

### Info:
* Opacity doesn't work on Wayland.
* Use `root` mode on i3wm
