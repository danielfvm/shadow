/**
 * Copyright (C) 2022 Jeff Shee (jeffshee8969@gmail.com)
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

/**
 * Special thanks to the black magic of DING extension.
 * Especially the ManageWindow class that gives superpower to Wayland windows.
 * That is one of the most crucial parts for this extension to work.
 * Also, the replaceMethod function is very convenient and helpful.
 * Without them, I don't know how to get started.
 */

const { Meta, Gio, GLib } = imports.gi;

const Main = imports.ui.main;

const ExtensionUtils = imports.misc.extensionUtils;
const Config = imports.misc.config;

const Me = ExtensionUtils.getCurrentExtension();
const EmulateX11 = Me.imports.emulateX11WindowType;
const GnomeShellOverride = Me.imports.gnomeShellOverride;

// This object will contain all the global variables
let data = {};

class Extension {
    enable() {
        if (!data.GnomeShellOverride) {
            data.GnomeShellOverride =
                new GnomeShellOverride.GnomeShellOverride();
        }

        if (!data.x11Manager) {
            data.x11Manager = new EmulateX11.EmulateX11WindowType();
        }

        // If the desktop is still starting up, wait until it is ready
        if (Main.layoutManager._startingUp) {
            data.startupPreparedId = Main.layoutManager.connect(
                "startup-complete",
                () => {
                    innerEnable(true);
                }
            );
        } else {
            innerEnable(false);
        }
    }

    disable() {
        data.isEnabled = false;
        data.GnomeShellOverride.disable();
        data.x11Manager.disable();
    }
}

function init() {
    data.isEnabled = false;
    data.launchRendererId = 0;
    data.currentProcess = null;
    data.reloadTime = 100;
    data.GnomeShellVersion = parseInt(Config.PACKAGE_VERSION.split(".")[0]);

    data.GnomeShellOverride = null;
    data.x11Manager = null;

    /**
     * Ensures that there aren't "rogue" processes.
     * This is a safeguard measure for the case of Gnome Shell being relaunched
     *  (for example, under X11, with Alt+F2 and R), to kill any old renderer instance.
     * That's why it must be here, in init(), and not in enable() or disable()
     * (disable already guarantees thag the current instance is killed).
     */
    return new Extension();
}

/**
 * The true code that configures everything and launches the renderer
 */
function innerEnable(removeId) {
    if (removeId) {
        Main.layoutManager.disconnect(data.startupPreparedId);
        data.startupPreparedId = null;
    }

    data.GnomeShellOverride.enable();
    data.x11Manager.enable();

    data.isEnabled = true;
    if (data.launchRendererId) {
        GLib.source_remove(data.launchRendererId);
    }
}
