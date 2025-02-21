import dbus
import dbus.mainloop.glib
from advertisement import Advertisement
from service import Application
from agent import BlueAgent
from bleevents import device_event,get_disconnect_reason,set_adapter_pairable
from bleprofile import JsonAdvertisement, JsonService,JsonCharacteristic
import queue
from filedetection import FileWatcher

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
# ====================== File Transfert ======================
q = queue.Queue()
json_service = JsonService(0,q)
json_char = json_service.get_data_char()
fw = FileWatcher(q,json_char)
fw.start()

# ====================== BLE Application ======================
app = Application()
app.add_service(json_service)
app.register()

adv = JsonAdvertisement(0)
adv.register()

# Main loop
try:
    app.run()
except KeyboardInterrupt:
    app.quit()
