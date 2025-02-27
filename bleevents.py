import dbus
import subprocess

class BluetoothEventManager:
    def __init__(self):
        self.bus = dbus.SystemBus()
        self.adapter_path = "/org/bluez/hci0"
        self.connected = False

    def device_event(self, interface, changed, invalidated, path):
        if interface != "org.bluez.Device1":
            return

        # Connection detection
        if "Connected" in changed:
            if changed["Connected"]:
                print(f"✅ Device connected: {path}")
                self.connected = True
            else:
                print(f"❌ Device disconnected: {path}")
                self.get_disconnect_reason(path)
                self.connected = False

        # Pairing detection
        if "Paired" in changed:
            if changed["Paired"]:
                print(f"🔐 Pairing completed with: {path}")
            else:
                print(f"🔓 Pairing cancelled with: {path}")

    def is_connected(self):
        return self.connected
    def set_connected(self):
        print("setting connected true")
        self.is_connected = True

    def get_disconnect_reason(self, device_path):
        try:
            device = self.bus.get_object("org.bluez", device_path)
            iface = dbus.Interface(device, "org.freedesktop.DBus.Properties")
            iface.Get("org.bluez.Device1", "RSSI")
        except dbus.DBusException as e:
            print(f"⚠️ Disconnection reason: {e.get_dbus_message()}")

    def set_adapter_pairable(self):
        adapter = self.bus.get_object("org.bluez", self.adapter_path)
        adapter_props = dbus.Interface(adapter, "org.freedesktop.DBus.Properties")

        try:
            adapter_props.Set("org.bluez.Adapter1", "Powered", dbus.Boolean(1))
            adapter_props.Set("org.bluez.Adapter1", "Discoverable", dbus.Boolean(1))
            adapter_props.Set("org.bluez.Adapter1", "Pairable", dbus.Boolean(1))
            print("Adapter is now visible and connectable.")
        except dbus.DBusException as e:
            print(f"Error while configuring adapter: {e.get_dbus_message()}")
