from gi.repository import GLib
from advertisement import Advertisement
from service import Application, Service, Characteristic, Descriptor
from jsonutils import load_json_file, get_next_json_packet
import logging

NOTIFY_TIMEOUT = 500  # Temps en millisecondes (secondes)
GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"

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
        self.add_characteristic(DelFileFrom(self))
        self.add_characteristic(ReceiveConfirmation(self))

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
            if value != self.prev_value and value != 'FIN':
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



class DelFileFrom(Characteristic):
    UUID = "19b10001-e8f2-537e-4f6c-d104768a1221"  # Remplace par ton propre UUID

    def __init__(self, service):
        Characteristic.__init__(
            self, self.UUID,
            ["write","write-without-response"],  # Cette caractéristique accepte l'écriture
            service
        )

    def WriteValue(self, value, options):
        print("Receiving data from phone")
        print("raw value : ", value)
        byte_list = bytes(value)
        byte_str = byte_list.decode('utf-8')  # Convertir en chaîne de caractères ASCII (si c'est du texte)

        try:
            # Vérifier si les données reçues sont bien des chiffres
            print(f"String reçu : {byte_str}")
            
            # Si c'est un timestamp en texte (par exemple "1739206948381")
            timestamp = int(byte_str)
            timestamp_seconds = timestamp / 1000
            dt_object = datetime.datetime.fromtimestamp(timestamp_seconds)
            print(f"📥 Timestamp reçu : {dt_object.strftime('%Y-%m-%d %H:%M:%S')}")

        except ValueError as e:
            print(f"⚠️ Erreur lors de la conversion du timestamp : {e}")



class ReceiveConfirmation(Characteristic):
    UUID = "19b10001-e8f2-537e-4f6c-d104768a1218"  # Remplace par ton propre UUID

    def __init__(self, service):
        Characteristic.__init__(
            self, self.UUID,
            ["write","write-without-response"],  # Cette caractéristique accepte l'écriture
            service
        )

    def WriteValue(self, value, options):
        print("Receiving file receive confirm from phone")
        print("raw value : ", value)
        byte_list = bytes(value)
        byte_str = byte_list.decode('utf-8')  # Convertir en chaîne de caractères ASCII (si c'est du texte)

        try:
            # Vérifier si les données reçues sont bien des chiffres
            print(f"String reçu : {byte_str}")
            
            # Si c'est un timestamp en texte (par exemple "1739206948381")
            

        except ValueError as e:
            print(f"⚠️ Erreur lors de la conversion du timestamp : {e}")


class JsonDescriptor(Descriptor):
    JSON_DESCRIPTOR_UUID = "2901"
    JSON_DESCRIPTOR_VALUE = "JSON File Transfer"

    def __init__(self, characteristic):
        Descriptor.__init__(self, self.JSON_DESCRIPTOR_UUID, ["read"], characteristic)

    def ReadValue(self, options):
        return [dbus.Byte(c.encode()) for c in self.JSON_DESCRIPTOR_VALUE]