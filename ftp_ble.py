import dbus
import dbus.mainloop.glib
import logging
from gi.repository import GLib
from advertisement import Advertisement
from service import Application, Service, Characteristic, Descriptor

GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
NOTIFY_TIMEOUT = 500  # Temps en millisecondes (secondes)
MAX_PACKET_SIZE = 185  # Taille max d'un paquet BLE
SERVICE_NAME = "org.bluez"
AGENT_IFACE = SERVICE_NAME + '.Agent1'
ADAPTER_IFACE = SERVICE_NAME + ".Adapter1"
DEVICE_IFACE = SERVICE_NAME + ".Device1"


LOG_LEVEL = logging.INFO
#LOG_FILE = "/var/log/syslog"
LOG_LEVEL = logging.DEBUG
LOG_FILE = "/dev/stdout"
LOG_FORMAT = "%(asctime)s %(levelname)s [%(module)s] %(message)s"

# Variables globales pour la gestion des paquets JSON
json_packets = []
json_index = 0

def getManagedObjects():
    bus = dbus.SystemBus()
    manager = dbus.Interface(bus.get_object("org.bluez", "/"), "org.freedesktop.DBus.ObjectManager")
    return manager.GetManagedObjects()


def findAdapter():
    objects = getManagedObjects();
    bus = dbus.SystemBus()
    for path, ifaces in objects.items():
        adapter = ifaces.get(ADAPTER_IFACE)
        if adapter is None:
            continue
        obj = bus.get_object(SERVICE_NAME, path)
        return dbus.Interface(obj, ADAPTER_IFACE)
    raise Exception("Bluetooth adapter not found")

class BlueAgent(dbus.service.Object):
    AGENT_PATH = "/blueagent5/agent"
    CAPABILITY = "KeyboardDisplay"
    pin_code = None

    def __init__(self, pin_code):
        dbus.service.Object.__init__(self, dbus.SystemBus(), BlueAgent.AGENT_PATH)
        self.pin_code = pin_code

        logging.basicConfig(filename=LOG_FILE, format=LOG_FORMAT, level=LOG_LEVEL)
        logging.info("Starting BlueAgent with PIN [{}]".format(self.pin_code))
        
    @dbus.service.method(AGENT_IFACE, in_signature="os", out_signature="")
    def DisplayPinCode(self, device, pincode):
        logging.debug("BlueAgent DisplayPinCode invoked")

    @dbus.service.method(AGENT_IFACE, in_signature="ouq", out_signature="")
    def DisplayPasskey(self, device, passkey, entered):
        logging.debug("BlueAgent DisplayPasskey invoked")

    @dbus.service.method(AGENT_IFACE, in_signature="o", out_signature="s")
    def RequestPinCode(self, device):
        logging.info("BlueAgent is pairing with device [{}]".format(device))
        self.trustDevice(device)
        return self.pin_code

    @dbus.service.method(AGENT_IFACE, in_signature="ou", out_signature="")
    def RequestConfirmation(self, device, passkey):
        """Always confirm"""
        logging.info("BlueAgent is pairing with device [{}]".format(device))
        self.trustDevice(device)
        return

    @dbus.service.method(AGENT_IFACE, in_signature="os", out_signature="")
    def AuthorizeService(self, device, uuid):
        """Always authorize"""
        logging.debug("BlueAgent AuthorizeService method invoked")
        return

    @dbus.service.method(AGENT_IFACE, in_signature="o", out_signature="u")
    def RequestPasskey(self, device):
        logging.debug("RequestPasskey returns 0")
        return dbus.UInt32(0)

    @dbus.service.method(AGENT_IFACE, in_signature="o", out_signature="")
    def RequestAuthorization(self, device):
        """Always authorize"""
        logging.info("BlueAgent is authorizing device [{}]".format(self.device))
        return

    @dbus.service.method(AGENT_IFACE, in_signature="", out_signature="")
    def Cancel(self):
        logging.info("BlueAgent pairing request canceled from device [{}]".format(self.device))

    def trustDevice(self, path):
        bus = dbus.SystemBus()
        device_properties = dbus.Interface(bus.get_object(SERVICE_NAME, path), "org.freedesktop.DBus.Properties")
        device_properties.Set(DEVICE_IFACE, "Trusted", True)

    def registerAsDefault(self):
        bus = dbus.SystemBus()
        manager = dbus.Interface(bus.get_object(SERVICE_NAME, "/org/bluez"), "org.bluez.AgentManager1")
        manager.RegisterAgent(BlueAgent.AGENT_PATH, BlueAgent.CAPABILITY)
        manager.RequestDefaultAgent(BlueAgent.AGENT_PATH)

    def startPairing(self):
        bus = dbus.SystemBus()
        adapter_path = findAdapter().object_path
        adapter = dbus.Interface(bus.get_object(SERVICE_NAME, adapter_path), "org.freedesktop.DBus.Properties")
#        adapter.Set(ADAPTER_IFACE, "Discoverable", True)
        
        logging.info("BlueAgent is waiting to pair with device")

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
        self.prev_value = 0

    def set_json_callback(self):
        if self.notifying:
            value = get_next_json_packet()
            if value != self.prev_value and value != 0xFF:
                self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])
                self.add_timeout(NOTIFY_TIMEOUT, self.set_json_callback)
                self.prev_value = value
        return self.notifying

    def StartNotify(self):
        if self.notifying:
            return

        print("Début du transfert du fichier JSON")
        load_json_file()  # Recharge le fichier avant de commencer
        value = get_next_json_packet()
        self.notifying = True
        
        
        #self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])
        #self.add_timeout(NOTIFY_TIMEOUT, self.set_json_callback)
        self.set_json_callback()

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
#set_adapter_pairable()
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = dbus.SystemBus()
pin_code = "12345"
agent = BlueAgent(pin_code)
agent.registerAsDefault()
agent.startPairing()
'''agent_manager = dbus.Interface(bus.get_object("org.bluez", "/org/bluez"),
                               "org.bluez.AgentManager1")

agent_manager.RegisterAgent("/test/agent", "DisplayYesNo")
agent_manager.RequestDefaultAgent("/test/agent")'''
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
