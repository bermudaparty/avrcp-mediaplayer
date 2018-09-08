#!/usr/bin/env python

# Dependencies:
# sudo apt-get install -y python-gobject

import time
import signal
import dbus
import dbus.service
import dbus.mainloop.glib
import gobject
import Tkinter
import sys

SERVICE_NAME = "org.bluez"
AGENT_IFACE = SERVICE_NAME + '.Agent1'
ADAPTER_IFACE = SERVICE_NAME + ".Adapter1"
DEVICE_IFACE = SERVICE_NAME + ".Device1"
PLAYER_IFACE = SERVICE_NAME + '.MediaPlayer1'
TRANSPORT_IFACE = SERVICE_NAME + '.MediaTransport1'

STR_BOX_TITLE = "Bluetooth Audio"
STR_WAITING = "Waiting for Media Player"


class BluePlayer():
    bus = None
    mainloop = None
    device = None
    deviceAlias = None
    player = None
    connected = None
    state = None
    status = None
    track = []
    

    infostring = "Test"
    window = None
    labeltext = None




    def __init__(self):
        """Specify a signal handler, and find any connected media players"""
        gobject.threads_init()
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)


        self.bus = dbus.SystemBus()

        self.bus.add_signal_receiver(self.playerHandler,
                bus_name="org.bluez",
                dbus_interface="org.freedesktop.DBus.Properties",
                signal_name="PropertiesChanged",
                path_keyword="path")

        self.findPlayer()
        self.updateDisplay()
        
        self.buildInfostring()
        self.window = Tkinter.Tk()
        self.labeltext = Tkinter.IntVar()
        self.labeltext.set(infostring)
        lbl = Tkinter.Label(self.window, textvariable=self.labeltext)
        playbtn = Tkinter.Button(self.window, text="Play", command=self.play)
        pausebtn = Tkinter.Button(self.window, text="Pause", command=self.pause)
        
        
        lbl.pack()
        playbtn.pack(side=Tkinter.LEFT)
        pausebtn.pack(side=Tkinter.LEFT)
        self.window.protocol("WM_DELETE_WINDOW", sys.exit)
                
    def refreshApp(self):
        self.window.update()
        return True

    def start(self):
        gobject.idle_add(self.refreshApp)
        """Start the BluePlayer by running the gobject Mainloop()"""
        self.mainloop = gobject.MainLoop()
        self.mainloop.run()

    def end(self):
        """Stop the gobject Mainloop()"""
        if (self.mainloop):
            self.mainloop.quit();

    def findPlayer(self):
        """Find any current media players and associated device"""
        manager = dbus.Interface(self.bus.get_object("org.bluez", "/"), "org.freedesktop.DBus.ObjectManager")
        objects = manager.GetManagedObjects()

        player_path = None
        for path, interfaces in objects.iteritems():
            if PLAYER_IFACE in interfaces:
                player_path = path
                break

        if player_path:
            self.connected = True
            self.getPlayer(player_path)
            player_properties = self.player.GetAll(PLAYER_IFACE, dbus_interface="org.freedesktop.DBus.Properties")
            if "Status" in player_properties:
                self.status = player_properties["Status"]
            if "Track" in player_properties:
                self.track = player_properties["Track"]

    def getPlayer(self, path):
        """Get a media player from a dbus path, and the associated device"""
        self.player = self.bus.get_object("org.bluez", path)
        device_path = self.player.Get("org.bluez.MediaPlayer1", "Device", dbus_interface="org.freedesktop.DBus.Properties")
        self.getDevice(device_path)

    def getDevice(self, path):
        """Get a device from a dbus path"""
        self.device = self.bus.get_object("org.bluez", path)
        self.deviceAlias = self.device.Get(DEVICE_IFACE, "Alias", dbus_interface="org.freedesktop.DBus.Properties")

    def playerHandler(self, interface, changed, invalidated, path):
        """Handle relevant property change signals"""
        iface = interface[interface.rfind(".") + 1:]
#        print("Interface: {}; changed: {}".format(iface, changed))

        if iface == "Device1":
            if "Connected" in changed:
                self.connected = changed["Connected"]
        elif iface == "MediaControl1":
            if "Connected" in changed:
                self.connected = changed["Connected"]
                if changed["Connected"]:
                    self.findPlayer()
        elif iface == "MediaPlayer1":
            if "Track" in changed:
                self.track = changed["Track"]
                self.updateDisplay()
            if "Status" in changed:
                self.status = (changed["Status"])
                
    def buildInfostring(self):
        global infostring
        if self.player:
            artist = "?"
            title = "?"
            if "Artist" in self.track:
                artist = self.track["Artist"]
            if "Title" in self.track:
                title = self.track["Title"]
            infostring = artist + " - " + title
        else:
            infostring = "Waiting for media player"
                
    def updateDisplay(self):
        self.buildInfostring()
        print(infostring)
        self.labeltext.set(infostring)

    def next(self):
        self.player.Next(dbus_interface=PLAYER_IFACE)

    def previous(self):
        self.player.Previous(dbus_interface=PLAYER_IFACE)

    def play(self):
        self.player.Play(dbus_interface=PLAYER_IFACE)

    def pause(self):
        self.player.Pause(dbus_interface=PLAYER_IFACE)

if __name__ == "__main__":
    player = None

    try:
        player = BluePlayer()
        player.start()
    except KeyboardInterrupt as ex:
        print("\nBluePlayer cancelled by user")
    except Exception as ex:
        print("Error: {}".format(ex))
    finally:
        if player: player.end()