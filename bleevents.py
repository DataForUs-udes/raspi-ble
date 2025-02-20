


# ================== Gestion des événements de connexion/Déconnexion ===================



def device_event(interface, changed, invalidated, path):
    if interface != "org.bluez.Device1":
        return

    # Détection de connexion
    if "Connected" in changed:
        if changed["Connected"]:
            print(f"✅ Appareil connecté : {path}")
        else:
            print(f"❌ Appareil déconnecté : {path}")
            get_disconnect_reason(path)

    # Détection d'appariement
    if "Paired" in changed:
        if changed["Paired"]:
            print(f"🔐 Appariement réussi avec : {path}")
        else:
            print(f"🔓 Appariement annulé pour : {path}")

def get_disconnect_reason(device_path):
    try:
        bus = dbus.SystemBus()
        device = bus.get_object("org.bluez", device_path)
        iface = dbus.Interface(device, "org.freedesktop.DBus.Properties")
        # Tentative d'accès à une propriété après déconnexion pour forcer une erreur
        iface.Get("org.bluez.Device1", "RSSI")
    except dbus.DBusException as e:
        print(f"⚠️ Raison de la déconnexion : {e.get_dbus_message()}")

def set_adapter_pairable():
    bus = dbus.SystemBus()
    adapter_path = "/org/bluez/hci0"  # Remplace si nécessaire selon ton interface
    adapter = bus.get_object("org.bluez", adapter_path)
    adapter_props = dbus.Interface(adapter, "org.freedesktop.DBus.Properties")

    try:
        adapter_props.Set("org.bluez.Adapter1", "Powered", dbus.Boolean(1))
        adapter_props.Set("org.bluez.Adapter1", "Discoverable", dbus.Boolean(1))
        adapter_props.Set("org.bluez.Adapter1", "Pairable", dbus.Boolean(1))
        print("L'adaptateur est maintenant pairable et visible.")
    except dbus.DBusException as e:
        print(f"Erreur lors de la configuration de l'adaptateur : {e.get_dbus_message()}")