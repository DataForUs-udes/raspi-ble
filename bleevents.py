import dbus
import subprocess

# ================== paring/connection event manager ===================

FLG_CONNECTED = False


def device_event(interface, changed, invalidated, path):
    if interface != "org.bluez.Device1":
        return

    #  Connection  detection
    if "Connected" in changed:
        if changed["Connected"]:
            print(f"✅ Device connected : {path}")
            FLG_CONNECTED = True
        else:
            print(f"❌ Device disconnected : {path}")
            get_disconnect_reason(path)
            FLG_CONNECTED = False

    #  Pairing detection
    if "Paired" in changed:
        if changed["Paired"]:
            print(f"🔐 Pairing completed with : {path}")
        else:
            print(f"🔓 Pairing cancelled with : {path}")
def get_connect_status():
    return FLG_CONNECTED

def get_disconnect_reason(device_path):
    try:
        bus = dbus.SystemBus()
        device = bus.get_object("org.bluez", device_path)
        iface = dbus.Interface(device, "org.freedesktop.DBus.Properties")
        
        iface.Get("org.bluez.Device1", "RSSI")
    except dbus.DBusException as e:
        print(f"⚠️ Deconnection reason : {e.get_dbus_message()}")

def set_adapter_pairable():
    bus = dbus.SystemBus()
    adapter_path = "/org/bluez/hci0"  
    adapter = bus.get_object("org.bluez", adapter_path)
    adapter_props = dbus.Interface(adapter, "org.freedesktop.DBus.Properties")

    try:
        adapter_props.Set("org.bluez.Adapter1", "Powered", dbus.Boolean(1))
        adapter_props.Set("org.bluez.Adapter1", "Discoverable", dbus.Boolean(1))
        adapter_props.Set("org.bluez.Adapter1", "Pairable", dbus.Boolean(1))
        print("Adapter is now visible and connectable.")
    except dbus.DBusException as e:
        print(f"Error while configuring adaptor : {e.get_dbus_message()}")


