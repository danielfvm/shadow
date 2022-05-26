#!/usr/bin/python3

from screeninfo import get_monitors
from utils import Mode

import opengl

import argparse
import xcffib
import sys
import os


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
            if monitor.name.lower() == select.lower():
                return monitor

        print("Please select one of the following monitors:")

        for monitor in monitors:
            print("\t{}{}: {}x{}+{}+{}".format('*' if monitor.is_primary else '', monitor.name, monitor.width, monitor.height, monitor.x, monitor.y))

        sys.exit(0)

    return get_default_monitor()

if __name__ == '__main__':
    all_args = argparse.ArgumentParser()
    all_args.add_argument("-q", "--quality", help="Changes quality level of the shader, default 1.", default=1, type=float)
    all_args.add_argument("-s", "--speed", help="Changes animation speed, default 1.", default=1, type=float)
    all_args.add_argument("-o", "--opacity", help="Sets background window transparency, default 1.", default=1, type=float)
    all_args.add_argument("-m", "--mode", help="Changes rendering mode. Modes: root, window, background.", default=Mode.BACKGROUND, type=Mode)
    all_args.add_argument("-d", "--display", help="Selects a monitor", default=None, type=str)
    all_args.add_argument("-f", "--framelimit", help="Set the maximum framerate limit, default 60", default=60, type=int)


    args, files = all_args.parse_known_args()
    args = vars(args)

    monitor = parse_argument_monitor(args["display"])
    conn = xcffib.Connection(display=os.environ.get("DISPLAY"))

    if args["mode"] == Mode.WINDOW:
        width = int(monitor.width / 2)
        height = int(monitor.height / 2)
    else:
        width = monitor.width
        height = monitor.height

    with opengl.create_main_window(conn, args["mode"], args["opacity"], width, height) as window:
       with opengl.create_vertex_buffer():
           opengl.main_loop(conn, args["mode"], args["quality"], args["speed"], args["framelimit"], window, files)

