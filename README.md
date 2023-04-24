# Show
"Show" stands for `Shaders On Wallpaper` and it renders a realtime glsl shader on your Linux or Windows desktop. It is compatible with most shaders from [glslsandbox.com](http://glslsandbox.com/). Additionally you can put multiple shaders, images, videos and interactive scripts on top of each other to create an amazing looking desktop.

To support different desktop environments and operating systems there are different render modes one can select from:

* background (Linux only):
The Show window is being set to the background using a `typehint`. This might not be supported by your window manager (e.g. i3), but works on most desktop environments (Gnome, Xfce, Awesome, KDE, ...)

* root (Linux only):
Show will render the shader on the X11 root window. This mode has a lot of cpu usage and wont work in most desktop environments. This is only advised if the `background` mode does not work for you. Use this mode for window managers like i3wm.

* window:
This mode might be useful for shader developers. Show will create a normal window displaying the effect.

* win10 (Windows only):
This mode spawns a window behind the desktop icons. This is the default mode for Windows. This mode has only been tested on Windows 10 and might therefore not work on newer or older versions. 

## Features
* Compatible with [glslsandbox.com](http://glslsandbox.com/)
* 4 different render modes, supporting Linux & Windows
* Change speed & quality level
* Mixing shaders, images and scripts together (see Examples)
* Opacity on wallpaper
* Mouse position support
* gif support
* mp4 support
* jpg/png support
* expandable with own python scripts (still work in progress)

## Installation
```
$ git clone https://github.com/danielfvm/show.git
$ cd show
$ poetry install
$ poetry run show
```
After the installation, you can use the program by writing `show` in the terminal. For more information look at the `Usage` and `Examples` section.

## Usage
```
usage: show [-h] [-q QUALITY] [-s SPEED] [-o OPACITY] [-m MODE] [-d DISPLAY] [-f FRAMELIMIT] [-qm QUALITYMODE] [-width WIDTH] [-height HEIGHT]

options:
  -h, --help            show this help message and exit
  -q QUALITY, --quality QUALITY
                        Changes quality level of the shader, default 1.
  -s SPEED, --speed SPEED
                        Changes animation speed, default 1.
  -o OPACITY, --opacity OPACITY
                        Sets background window transparency, default 1.
  -m MODE, --mode MODE  Changes rendering mode. modes: root, window, background, win10.
  -d DISPLAY, --display DISPLAY
                        Selects a monitor
  -f FRAMELIMIT, --framelimit FRAMELIMIT
                        Set the maximum framerate limit, default 60
  -qm QUALITYMODE, --qualitymode QUALITYMODE
                        Set it to pixelize or smoothen the image at lower quality. default: smooth; modes: pixel, smooth
  -width WIDTH, --width WIDTH
                        Set window width
  -height HEIGHT, --height HEIGHT
                        Set window height
```

## Examples
#### Shader with framerate limit at 30 and display it as a normal window
```
show example/frag0.glsl -f 30 -m window
```

#### Shader with reduced quality (10%) and pixelize
```
show example/frag0.glsl -q 0.1 -qm pixel
```

#### Combining images and shaders
```
show path/to/my/image.png example/expandedlife.glsl
```

## Infos
* Opacity doesn't work on Wayland and Windows 10.
* Use `root` mode on i3wm
* Use the `--quality` option to save resources / gain more performance

## Todos
* Rework `README.md` file to show examples with gifs
* GUI for configuring show without terminal (and having presets)
* Packages/Releases - Installation file for Windows
* Testing show on win11
* An extension based on Hanabi for better Gnome support
* Fix mouse translations (sth related to projection matrix)
