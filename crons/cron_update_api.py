import os
import requests
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

API_KEY = "eiK8_110b18473efc48e9c63f76b5494ea18f"
BASE_URL = "https://empireimmo.com"

# 📥 INITIALISATION FIREBASE
DOSSIER_CRON = os.path.dirname(os.path.abspath(__file__))
RACINE_PROJET = os.path.dirname(DOSSIER_CRON)
CHEMIN_CLE = os.path.join(RACINE_PROJET, "data_cache", "firebase_credentials.json")

if not firebase_admin._apps:
    cred = credentials.Certificate(CHEMIN_CLE)
    firebase_admin.initialize_app(cred)

db = firestore.client()

def executer_mise_a_jour_cron():
    print("⏰ [CRON CLOUD] Démarrage de la récupération et envoi vers Firebase...")
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    timestamp_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    # --- 1. SYNC MATÉRIAUX ---
    try:
        req = requests.get(f"{BASE_URL}/materials.json?key={API_KEY}", timeout=15)
        if req.status_code == 200:
            data = req.json().get("materials", [])
            for m in data:
                # Stockage dans une sous-collection pour garder l'historique
                doc_id = f"{m.get('name').replace('/', '_')}_{timestamp_id}"
                db.collection("materiaux").document(doc_id).set({
                    "nom": m.get("name"),
                    "prix": int(m.get("price", 0)),
                    "unite": m.get("unit"),
                    "date_extraction": date_now
                })
            print("✅ Firebase : Collection 'materiaux' synchronisée.")
    except Exception as e:
        print(f"⚠️ Erreur matériaux : {e}")

    # --- 2. SYNC BÂTIMENTS ---
    try:
        req = requests.get(f"{BASE_URL}/buildings.json?key={API_KEY}", timeout=15)
        if req.status_code == 200:
            data = req.json().get("buildings_entreprise", [])
            for b in data:
                doc_id = f"{b.get('id')}_{timestamp_id}"
                db.collection("batiments").document(doc_id).set({
                    "id_jeu": b.get("id"),
                    "nom": b.get("name"),
                    "type": b.get("type"),
                    "valeur": int(b.get("value", 0)),
                    "loyer": int(b.get("rent", 0)),
                    "charge": int(b.get("charge", 0)),
                    "impot": int(b.get("tax", 0)),
                    "date_extraction": date_now
                })
            print("✅ Firebase : Collection 'batiments' synchronisée.")
    except Exception as e:
        print(f"⚠️ Erreur bâtiments : {e}")

    # --- 3. SYNC TRAVAUX ---
    try:
        req = requests.get(f"{BASE_URL}/works.json?key={API_KEY}", timeout=15)
        if req.status_code == 200:
            data = req.json().get("works_entreprise", [])
            for w in data:
                doc_id = f"{w.get('building_name').replace('/', '_')}_{w.get('type')}_{timestamp_id}"
                db.collection("travaux").document(doc_id).set({
                    "type_travaux": w.get("type"),
                    "building_name": w.get("building_name"),
                    "terrain_requis": w.get("terrain_required"),
                    "cout_estime": int(w.get("estimated_cost", 0)),
                    "duree_mois": int(w.get("duration", 0)),
                    "date_extraction": date_now
                })
            print("✅ Firebase : Collection 'travaux' synchronisée.")
    except Exception as e:
        print(f"⚠️ Erreur travaux : {e}")

    # --- 4. SYNC PLAYERS ---
    try:
        req = requests.get(f"{BASE_URL}/players.json?key={API_KEY}", timeout=15)
        if req.status_code == 200:
            data = req.json().get("players", [])
            for p in data:
                doc_id = f"{p.get('pseudo')}_{timestamp_id}"
                db.collection("players").document(doc_id).set({
                    "pseudo": p.get("pseudo"),
                    "points": int(p.get("points", 0)),
                    "classement": int(p.get("ranking", 0)),
                    "niveau": int(p.get("level", 0)),
                    "date_extraction": date_now
                })
            print("✅ Firebase : Collection 'players' synchronisée.")
    except Exception as e:
        print(f"⚠️ Erreur players : {e}")

    print("🎉 [FIREBASE] Base de données cloud à jour.")

if __name__ == "__main__":
    executer_mise_a_jour_cron()
