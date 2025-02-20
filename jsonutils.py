import dbus

# Variables globales pour la gestion des paquets JSON
MAX_PACKET_SIZE = 185  # Taille max d'un paquet BLE
json_packets = []
json_index = 0


def load_json_file():
    """Charge et divise le fichier JSON en paquets."""
    global json_packets, json_index
    json_index = 0

    try:
        with open("json_test.json", "r") as file:
            data = file.read()

        # Découpe en paquets de taille MAX_PACKET_SIZE
        json_packets = [data[i:i + MAX_PACKET_SIZE] for i in range(0, len(data), MAX_PACKET_SIZE)]
        json_packets.append("END")  # Marqueur de fin de fichier
        print(f"Fichier JSON chargé ({len(json_packets)} paquets)")
    except Exception as e:
        print(f"Erreur lors du chargement du fichier JSON: {e}")
        json_packets = ["ERR"]  # Si erreur, on envoie juste la fin

def get_next_json_packet():
    """Renvoie le prochain paquet JSON et met à jour l'index global."""
    global json_index
    if json_index < len(json_packets):
        value = json_packets[json_index]
        json_index += 1
    else:
        value = "END"  # Sécurité : envoie toujours la fin si dépassement

    return [dbus.Byte(ord(c)) for c in value]