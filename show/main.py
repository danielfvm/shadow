#!/usr/bin/python3
from screeninfo import get_monitors

from .framelimiter import *
from .config import *
from .show import *

import logging
import argparse
import sys
import glfw

log = logging.getLogger(__name__)

def get_default_monitor():
    monitors = get_monitors()
    for monitor in monitors:
        if monitor.is_primary:
            return monitor
    return monitors[0]

def parse_argument_monitor(select):
    if select != None:
        monitors = get_monitors()

        for monitor in monitors:
            if monitor.name != None and monitor.name.lower() == select.lower():
                return monitor

        print("Please select one of the following monitors:")

        for monitor in monitors:
            print("\t{}{}: {}x{}+{}+{}".format('*' if monitor.is_primary else '', monitor.name, monitor.width, monitor.height, monitor.x, monitor.y))

        sys.exit(0)

    return get_default_monitor()

def main():
    logging.basicConfig(level=logging.DEBUG)

    if not glfw.init():
        log.error('failed to initialize GLFW')
        return

    all_args = argparse.ArgumentParser()
    all_args.add_argument("-q", "--quality", help="Changes quality level of the shader, default 1.", default=Config.QUALITY, type=float)
    all_args.add_argument("-s", "--speed", help="Changes animation speed, default 1.", default=Config.SPEED, type=float)
    all_args.add_argument("-o", "--opacity", help="Sets background window transparency, default 1.", default=Config.OPACITY, type=float)
    all_args.add_argument("-m", "--mode", help="Changes rendering mode. modes: root, window, background, win10.", default=Config.BACKGROUND_MODE, type=BackgroundMode)
    all_args.add_argument("-d", "--display", help="Selects a monitor", default=Config.DISPLAY, type=str)
    all_args.add_argument("-f", "--framelimit", help="Set the maximum framerate limit, default 60", default=Config.FRAMELIMIT, type=int)
    all_args.add_argument("-qm", "--qualitymode", help="Set it to pixelize or smoothen the image at lower quality. default: smooth; modes: pixel, smooth", default=Config.QUALITY_MODE, type=QualityMode)
    all_args.add_argument("-width", "--width", help="Set window width", default=900, type=int)
    all_args.add_argument("-height", "--height", help="Set window height", default=600, type=int)

    args, files = all_args.parse_known_args()
    args = vars(args)

    if len(files) <= 0:
        all_args.print_help()
        return

    Config.QUALITY = args["quality"]
    Config.SPEED = args["speed"]
    Config.OPACITY = args["opacity"]
    Config.BACKGROUND_MODE = args["mode"]
    Config.DISPLAY = args["display"]
    Config.FRAMELIMIT = args["framelimit"]
    Config.QUALITY_MODE = args["qualitymode"]

    monitor = parse_argument_monitor(Config.DISPLAY)
    frameLimiter = FrameLimiter(Config.FRAMELIMIT)

    if not sys.platform.startswith("linux") and (Config.BACKGROUND_MODE == BackgroundMode.BACKGROUND or Config.BACKGROUND_MODE == BackgroundMode.ROOT):
        print("This mode is not supported by your current operating system.")
        print("If you are on Windows, please select the 'window' or 'win10' mode instead.")
        return

    if not sys.platform.startswith("win") and Config.BACKGROUND_MODE == BackgroundMode.WIN10:
        print("This mode is only supported by windows.")
        return

    show = None
    if Config.BACKGROUND_MODE == BackgroundMode.BACKGROUND:
        show = ShowBackground(monitor, files)
    elif Config.BACKGROUND_MODE == BackgroundMode.WIN10:
        show = ShowWin10(monitor, files)
    elif Config.BACKGROUND_MODE == BackgroundMode.ROOT:
        show = ShowRoot(monitor, files)
    elif Config.BACKGROUND_MODE == BackgroundMode.WINDOW:
        show = ShowWindow(monitor, files, int(args["width"]), int(args["height"]))

    # this if should never be true
    if show == None:
        all_args.print_help()
        return

    try:
        while show.is_running():
            dt = frameLimiter.tick()
            show.render(dt * Config.SPEED)
            show.swap()
    except KeyboardInterrupt:
        log.debug("Exit signal received")

if __name__ == '__main__':
    main()
