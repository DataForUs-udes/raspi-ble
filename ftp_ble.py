import dbus
import dbus.mainloop.glib
from gi.repository import GLib
from advertisement import Advertisement
from service import Application, Service, Characteristic, Descriptor

GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
NOTIFY_TIMEOUT = 55  # Temps en millisecondes (5 secondes)
MAX_PACKET_SIZE = 150  # Taille max d'un paquet BLE

# Variables globales pour la gestion des paquets JSON
json_packets = []
json_index = 0

class Agent(dbus.service.Object):
    AGENT_INTERFACE = 'org.bluez.Agent1'

    def __init__(self, bus, path):
        dbus.service.Object.__init__(self, bus, path)

    @dbus.service.method(AGENT_INTERFACE, in_signature="ou", out_signature="")
    def RequestConfirmation(self, device, passkey):
        print(f"Approbation automatique du code de confirmation : {passkey}")
        return


    @dbus.service.method(AGENT_INTERFACE, in_signature="os", out_signature="")
    def AuthorizeService(self, device, uuid):
        print(f"Autorisation automatique pour le service UUID : {uuid}")
        return


    @dbus.service.method(AGENT_INTERFACE, in_signature="", out_signature="")
    def Release(self):
        print("Agent libéré.")

def load_json_file():
    """Charge et divise le fichier JSON en paquets."""
    global json_packets, json_index
    json_index = 0

    try:
        with open("json_test.json", "r") as file:
            data = file.read()

        # Découpe en paquets de taille MAX_PACKET_SIZE
        json_packets = [data[i:i + MAX_PACKET_SIZE] for i in range(0, len(data), MAX_PACKET_SIZE)]
        json_packets.append("\xFF")  # Marqueur de fin de fichier
        print(f"Fichier JSON chargé ({len(json_packets)} paquets)")
    except Exception as e:
        print(f"Erreur lors du chargement du fichier JSON: {e}")
        json_packets = ["\xFF"]  # Si erreur, on envoie juste la fin

def get_next_json_packet():
    """Renvoie le prochain paquet JSON et met à jour l'index global."""
    global json_index
    if json_index < len(json_packets):
        value = json_packets[json_index]
        json_index += 1
    else:
        value = "\xFF"  # Sécurité : envoie toujours la fin si dépassement

    return [dbus.Byte(ord(c)) for c in value]

class JsonAdvertisement(Advertisement):
    def __init__(self, index):
        Advertisement.__init__(self, index, "peripheral")
        self.add_local_name("Abatteuse")
        self.include_tx_power = True

class JsonService(Service):
    JSON_SVC_UUID = "19b10000-e8f2-537e-4f6c-d104768a1214"

    def __init__(self, index):
        Service.__init__(self, index, self.JSON_SVC_UUID, True)
        self.add_characteristic(JsonCharacteristic(self))

class JsonCharacteristic(Characteristic):
    JSON_CHARACTERISTIC_UUID = "19b10001-e8f2-537e-4f6c-d104768a1217"

    def __init__(self, service):
        Characteristic.__init__(self, self.JSON_CHARACTERISTIC_UUID, ["notify", "read"], service)
        self.notifying = False
        self.add_descriptor(JsonDescriptor(self))

    def set_json_callback(self):
        if self.notifying:
            value = get_next_json_packet()
            self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])
        return self.notifying

    def StartNotify(self):
        if self.notifying:
            return

        print("Début du transfert du fichier JSON")
        load_json_file()  # Recharge le fichier avant de commencer
        self.notifying = True
        value = get_next_json_packet()
        self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])
        self.add_timeout(NOTIFY_TIMEOUT, self.set_json_callback)

    def StopNotify(self):
        print("Arrêt du transfert du fichier JSON")
        self.notifying = False

    def ReadValue(self, options):
        return get_next_json_packet()

class JsonDescriptor(Descriptor):
    JSON_DESCRIPTOR_UUID = "2901"
    JSON_DESCRIPTOR_VALUE = "JSON File Transfer"

    def __init__(self, characteristic):
        Descriptor.__init__(self, self.JSON_DESCRIPTOR_UUID, ["read"], characteristic)

    def ReadValue(self, options):
        return [dbus.Byte(c.encode()) for c in self.JSON_DESCRIPTOR_VALUE]

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


# Initialisation du bus D-Bus pour écouter les signaux
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
system_bus = dbus.SystemBus()

# Abonnement aux événements de changement de propriétés
system_bus.add_signal_receiver(device_event,
                               dbus_interface="org.freedesktop.DBus.Properties",
                               signal_name="PropertiesChanged",
                               path_keyword="path")
set_adapter_pairable()
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = dbus.SystemBus()

agent = Agent(bus, "/test/agent")
agent_manager = dbus.Interface(bus.get_object("org.bluez", "/org/bluez"),
                               "org.bluez.AgentManager1")

agent_manager.RegisterAgent("/test/agent", "DisplayYesNo")
agent_manager.RequestDefaultAgent("/test/agent")
# ====================== Application BLE ======================
app = Application()
app.add_service(JsonService(0))
app.register()

adv = JsonAdvertisement(0)
adv.register()

# Boucle principale
try:
    app.run()
except KeyboardInterrupt:
    app.quit()
