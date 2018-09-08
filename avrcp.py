#!/usr/bin/env python

# Dependencies:
# sudo apt-get install -y python-gobject

import dbus
import dbus.service
import dbus.mainloop.glib
import gobject
import Tkinter

SERVICE_NAME = "org.bluez"
AGENT_IFACE = SERVICE_NAME + '.Agent1'
ADAPTER_IFACE = SERVICE_NAME + ".Adapter1"
DEVICE_IFACE = SERVICE_NAME + ".Device1"
PLAYER_IFACE = SERVICE_NAME + '.MediaPlayer1'
TRANSPORT_IFACE = SERVICE_NAME + '.MediaTransport1'

STR_BOX_TITLE = "Bluetooth Audio"
STR_WAITING   = "Waiting for Media Player"
STR_ART_UNKNOWN = "[Artist Unknown]"
STR_TIT_UNKNOWN = "[Title Unknown]"


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

    window = None
    titlestring = STR_TIT_UNKNOWN
    artiststring = STR_ART_UNKNOWN

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
        self.buildTrackstrings()

        self.window = Tkinter.Tk()
        self.window.title(STR_BOX_TITLE)

        self.titlevar = Tkinter.StringVar()
        self.titlevar.set(self.titlestring)
        self.artistvar = Tkinter.StringVar()
        self.artistvar.set(self.artiststring)

        emptyrow = Tkinter.Label(self.window, text="", width=20).grid(row=0, columnspan=3)
        title = Tkinter.Label(self.window, textvariable=self.titlevar, width=20, font=("Verdana", 30, "bold")).grid(row=1, columnspan=3)
        artist = Tkinter.Label(self.window, textvariable=self.artistvar, width=20, font=("Verdana", 18)).grid(row=2, columnspan=3)
        emptyrow2 = Tkinter.Label(self.window, text="", width=20).grid(row=3, columnspan=3)
        prevbtn  = Tkinter.Button(self.window, text="|<<", command=self.previous).grid(row=4, column=0, sticky="e")
        playpausebtn = Tkinter.Button(self.window, text="Play - Pause", command=self.playpause).grid(row=4, column=1, sticky="we")
        nextbtn  = Tkinter.Button(self.window, text=">>|", command=self.next).grid(row=4, column=2, sticky="w")

        self.window.protocol("WM_DELETE_WINDOW", self.end)
        self.updateDisplay()
        gobject.idle_add(self.refreshWindow)
        self.window.update()
        self.window.minsize(self.window.winfo_width(), self.window.winfo_height())
        self.window.maxsize(self.window.winfo_width(), self.window.winfo_height())

    def refreshWindow(self):
        self.window.update()
        return True


    def start(self):
        """Start the BluePlayer by running the gobject Mainloop()"""
        #self.window.mainloop()

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
        device_path = self.player.Get("org.bluez.MediaPlayer1", "Device",
                                      dbus_interface="org.freedesktop.DBus.Properties")
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

    def buildTrackstrings(self):
        if self.player:
            artist = STR_ART_UNKNOWN
            title = STR_TIT_UNKNOWN
            if "Artist" in self.track:
                artist = self.track["Artist"]
            if "Title" in self.track:
                title = self.track["Title"]
            self.artiststring = artist
            self.titlestring = title
        else:
            self.artiststring = STR_WAITING
            self.titlestring = "---"

    def updateDisplay(self):
        self.buildTrackstrings()
        self.artistvar.set(self.artiststring)
        self.titlevar.set(self.titlestring)

    def next(self):
        self.player.Next(dbus_interface=PLAYER_IFACE)

    def previous(self):
        self.player.Previous(dbus_interface=PLAYER_IFACE)

    def play(self):
        self.player.Play(dbus_interface=PLAYER_IFACE)

    def pause(self):
        self.player.Pause(dbus_interface=PLAYER_IFACE)

    def playpause(self):
        if self.status == "playing":
            self.pause()
        else:
            self.play()


if __name__ == "__main__":
    player = None

    try:
        player = BluePlayer()
        player.start()
    finally:
        if player: player.end()