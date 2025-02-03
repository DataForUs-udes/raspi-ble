import dbus
from advertisement import Advertisement
from service import Application, Service, Characteristic, Descriptor
import os

GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
NOTIFY_TIMEOUT = 55  # Temps en millisecondes (5 secondes)
MAX_PACKET_SIZE = 150     # Taille max d'un paquet BLE

# Variables globales pour la gestion des paquets JSON
json_packets = []
json_index = 0
prev_value = 0
def load_json_file():
    """Charge et divise le fichier JSON en paquets."""
    global json_packets, json_index
    json_index = 0

    try:
        with open("json_test.json", "r") as file:
            data = file.read()
        
        # Découpe en paquets de taille MAX_PACKET_SIZE
        json_packets = [data[i:i+MAX_PACKET_SIZE] for i in range(0, len(data), MAX_PACKET_SIZE)]
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
                self.prev_value = value
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

# Application Setup
app = Application()
app.add_service(JsonService(0))
app.register()

# Advertisement Setup
adv = JsonAdvertisement(0)
adv.register()

# Running the application
try:
    app.run()
except KeyboardInterrupt:
    app.quit()
