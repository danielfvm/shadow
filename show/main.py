#!/usr/bin/python3
from screeninfo import get_monitors

from show.framelimiter import *
from show.config import *
from show.show import *

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
        sys.exit(0)

    all_args = argparse.ArgumentParser()
    all_args.add_argument("-q", "--quality", help="Changes quality level of the shader, default 1.", default=Config.QUALITY, type=float)
    all_args.add_argument("-s", "--speed", help="Changes animation speed, default 1.", default=Config.SPEED, type=float)
    all_args.add_argument("-o", "--opacity", help="Sets background window transparency, default 1.", default=Config.OPACITY, type=float)
    all_args.add_argument("-m", "--mode", help="Changes rendering mode. Modes: root, window, background.", default=Config.BACKGROUND_MODE, type=BackgroundMode)
    all_args.add_argument("-d", "--display", help="Selects a monitor", default=Config.DISPLAY, type=str)
    all_args.add_argument("-f", "--framelimit", help="Set the maximum framerate limit, default 60", default=Config.FRAMELIMIT, type=int)
    all_args.add_argument("-qm", "--qualitymode", help="Should it pixelize or smoothen the image at lower quality? default: smooth", default=Config.QUALITY_MODE, type=QualityMode)
    all_args.add_argument("-width", "--width", help="Set window width", default=900, type=int)
    all_args.add_argument("-height", "--height", help="Set window height", default=600, type=int)

    args, files = all_args.parse_known_args()
    args = vars(args)

    if len(files) <= 0:
        all_args.print_help()
        exit(0)

    Config.QUALITY = args["quality"]
    Config.SPEED = args["speed"]
    Config.OPACITY = args["opacity"]
    Config.BACKGROUND_MODE = args["mode"]
    Config.DISPLAY = args["display"]
    Config.FRAMELIMIT = args["framelimit"]
    Config.QUALITY_MODE = args["qualitymode"]

    monitor = parse_argument_monitor(Config.DISPLAY)
    frameLimiter = FrameLimiter(Config.FRAMELIMIT)

    show = None
    if Config.BACKGROUND_MODE == BackgroundMode.BACKGROUND:
        show = ShowBackground(monitor, files)
    elif Config.BACKGROUND_MODE == BackgroundMode.ROOT:
        show = ShowRoot(monitor, files)
    elif Config.BACKGROUND_MODE == BackgroundMode.WINDOW:
        show = ShowWindow(monitor, files, int(args["width"]), int(args["height"]))

    # this if should never be true
    if show == None:
        all_args.print_help()
        exit(0)

    try:
        while show.is_running():
            dt = frameLimiter.tick()
            show.render(dt * Config.SPEED)
            show.swap()
    except KeyboardInterrupt:
        log.debug("Exit signal received")

if __name__ == '__main__':
    main()
