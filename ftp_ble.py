import dbus
import dbus.mainloop.glib
import logging
import datetime
import base64
import struct
from gi.repository import GLib
from advertisement import Advertisement
from service import Application, Service, Characteristic, Descriptor
from agent import BlueAgent
from bleevents import device_event,get_disconnect_reason,set_adapter_pairable
from bleprofile import *
GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
NOTIFY_TIMEOUT = 500  # Temps en millisecondes (secondes)



LOG_LEVEL = logging.INFO
#LOG_FILE = "/var/log/syslog"
LOG_LEVEL = logging.DEBUG
LOG_FILE = "/dev/stdout"
LOG_FORMAT = "%(asctime)s %(levelname)s [%(module)s] %(message)s"

# ================== Setting up the bus ===================
# Initialisation of D-Bus to listen on hci0
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
system_bus = dbus.SystemBus()
# Subscribing to protities changes events
system_bus.add_signal_receiver(device_event,
                               dbus_interface="org.freedesktop.DBus.Properties",
                               signal_name="PropertiesChanged",
                               path_keyword="path")
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = dbus.SystemBus()
pin_code = "12345"
agent = BlueAgent(pin_code)
agent.registerAsDefault()
agent.startPairing()

# ====================== Application BLE ======================
app = Application()
app.add_service(JsonService(0))
app.register()

adv = JsonAdvertisement(0)
adv.register()

# Main loop
try:
    app.run()
except KeyboardInterrupt:
    app.quit()
