import os
import json
import requests

API_KEY = "eiK8_110b18473efc48e9c63f76b5494ea18f"
BASE_URL = "https://empireimmo.com"
ENDPOINTS = ["buildings", "works", "materials", "players"]

# Dossier local pour stocker les fichiers JSON sur le serveur
DATA_DIR = "data_cache"
os.makedirs(DATA_DIR, exist_ok=True)

def executer_mise_a_jour_cron():
    print("⏰ [CRON] Lancement de la synchronisation avec l'API Empire Immo...")
    
    for endpoint in ENDPOINTS:
        url = f"{BASE_URL}/{endpoint}.json?key={API_KEY}"
        try:
            reponse = requests.get(url, timeout=15)
            if reponse.status_code == 200:
                chemin_fichier = os.path.join(DATA_DIR, f"{endpoint}.json")
                with open(chemin_fichier, "w", encoding="utf-8") as f:
                    json.dump(reponse.json(), f, ensure_ascii=False, indent=4)
                print(f"✅ Fichier synchronisé avec succès : {chemin_fichier}")
            else:
                print(f"❌ Erreur API sur {endpoint} : Code {reponse.status_code}")
        except Exception as e:
            print(f"⚠️ Erreur réseau lors de la récupération de {endpoint} : {e}")

if __name__ == "__main__":
    executer_mise_a_jour_cron()
