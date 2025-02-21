import sys
import time
import threading
from queue import Queue
from bleevents import get_connect_status
# Ajout du chemin pour db_utils
db_path = "/home/pi/StanForD-Parser/utils"
sys.path.append(db_path)
import db_utils  # Import après ajout du chemin

CHECK_INTERVAL = 30  # Vérification toutes les X secondes

class FileWatcher:
    def __init__(self, queue, json_characteristic):
        self.queue = queue
        self.json_characteristic = json_characteristic
        self.known_files = set()

    def check_for_new_files(self):
        """Vérifie si de nouveaux fichiers doivent être transférés."""
        files = set(db_utils.get_local_paths())  # Liste des fichiers à envoyer
        new_files = files - self.known_files  # Compare avec fichiers déjà connus

        if new_files:
            print(f"📂 Nouveaux fichiers détectés: {new_files}")
            for file in new_files:
                self.queue.put(file)  # Ajoute chaque fichier à la queue
            self.known_files = files  # Met à jour la liste des fichiers connus
            if get_connect_status():
                self.json_characteristic.StartNotify()  # ⚡ Active notify car il y a des fichiers
            else:
                print("no device connected, not setting notify up")

        elif self.queue.empty():
            self.json_characteristic.StopNotify()  # 🛑 Désactive notify si la queue est vide

    def start(self):
        """Démarre la surveillance en arrière-plan."""
        def run():
            while True:
                self.check_for_new_files()
                time.sleep(CHECK_INTERVAL)

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        print("🔍 Surveillance des fichiers démarrée.")

