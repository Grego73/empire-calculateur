import streamlit as st
import os
import sys
import requests
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# Alignement du chemin d'importation
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils import API_KEY, BASE_URL

if not firebase_admin._apps:
    if "firebase_credentials" in st.secrets:
        info_cles = dict(st.secrets["firebase_credentials"])
        info_cles["private_key"] = info_cles["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(info_cles)
        firebase_admin.initialize_app(cred)
    else:
        DOSSIER_CRON = os.path.dirname(os.path.abspath(__file__))
        RACINE_PROJET = os.path.dirname(DOSSIER_CRON)
        CHEMIN_CLE = os.path.join(RACINE_PROJET, "data_cache", "firebase_credentials.json")
        cred = credentials.Certificate(CHEMIN_CLE)
        firebase_admin.initialize_app(cred)

db = firestore.client()

def executer_mise_a_jour_cron():
    logs_session = []
    
    def notifier(texte):
        print(texte)
        logs_session.append(f"[{datetime.now().strftime('%H:%M:%S')}] {texte}")

    notifier("⏰ [CRON CLOUD] Démarrage de la récupération...")
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    timestamp_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    # --- 1. MATÉRIAUX ---
    try:
        req = requests.get(f"{BASE_URL}/api/materials.json?key={API_KEY}", timeout=15)
        notifier(f"📡 API Matériaux — Code : {req.status_code}")
        if req.status_code == 200:
            materials_list = req.json().get("materials", [])
            notifier(f"📦 {len(materials_list)} matériaux détectés dans le flux API.")
            for m in materials_list:
                doc_id = f"{m.get('name').replace('/', '_')}_{timestamp_id}"
                db.collection("materiaux").document(doc_id).set({
                    "nom": m.get("name"), "prix": int(m.get("price", 0)), "unite": m.get("unit"), "date_extraction": date_now
                })
            notifier("✅ Collection 'materiaux' synchronisée avec succès.")
        else:
            notifier(f"❌ Erreur API Matériaux : {req.text[:200]}")
    except Exception as e: 
        notifier(f"💥 Crash Matériaux : {e}")

    # --- 2. BÂTIMENTS ---
    try:
        req = requests.get(f"{BASE_URL}/api/buildings.json?key={API_KEY}", timeout=15)
        notifier(f"📡 API Bâtiments — Code : {req.status_code}")
        if req.status_code == 200:
            buildings_list = req.json().get("buildings_entreprise", [])
            notifier(f"🏢 {len(buildings_list)} bâtiments détectés dans le flux API.")
            for b in buildings_list:
                doc_id = f"{b.get('id')}_{timestamp_id}"
                db.collection("batiments").document(doc_id).set({
                    "id_jeu": b.get("id"), "nom": b.get("name"), "type": b.get("type"), "valeur": int(b.get("value", 0)),
                    "loyer": int(b.get("rent", 0)), "charge": int(b.get("charge", 0)), "impot": int(b.get("tax", 0)), "date_extraction": date_now
                })
            notifier("✅ Collection 'batiments' synchronisée avec succès.")
        else:
            notifier(f"❌ Erreur API Bâtiments : {req.text[:200]}")
    except Exception as e: 
        notifier(f"💥 Crash Bâtiments : {e}")

    # --- 3. TRAVAUX ---
    try:
        req = requests.get(f"{BASE_URL}/api/works.json?key={API_KEY}", timeout=15)
        notifier(f"📡 API Travaux — Code : {req.status_code}")
        if req.status_code == 200:
            works_list = req.json().get("works_entreprise", [])
            notifier(f"🏗️ {len(works_list)} chantiers détectés dans le flux API.")
            for w in works_list:
                doc_id = f"{w.get('building_name').replace('/', '_')}_{w.get('type')}_{timestamp_id}"
                db.collection("travaux").document(doc_id).set({
                    "type_travaux": w.get("type"), "building_name": w.get("building_name"), "terrain_requis": w.get("terrain_required"),
                    "cout_estime": int(w.get("estimated_cost", 0)), "duree_mois": int(w.get("duration", 0)), "date_extraction": date_now
                })
            notifier("✅ Collection 'travaux' synchronisée avec succès.")
        else:
            notifier(f"❌ Erreur API Travaux : {req.text[:200]}")
    except Exception as e: 
        notifier(f"💥 Crash Travaux : {e}")

    # --- 4. PLAYERS ---
    try:
        req = requests.get(f"{BASE_URL}/api/players.json?key={API_KEY}", timeout=15)
        notifier(f"📡 API Players — Code : {req.status_code}")
        if req.status_code == 200:
            players_list = req.json().get("players", [])
            notifier(f"🏆 {len(players_list)} joueurs détectés dans le flux API.")
            for p in players_list:
                doc_id = f"{p.get('pseudo')}_{timestamp_id}"
                db.collection("players").document(doc_id).set({
                    "pseudo": p.get("pseudo"), "points": int(p.get("points", 0)), "classement": int(p.get("ranking", 0)),
                    "niveau": int(p.get("level", 0)), "date_extraction": date_now
                })
            notifier("✅ Collection 'players' synchronisée avec succès.")
        else:
            notifier(f"❌ Erreur API Players : {req.text[:200]}")
    except Exception as e: 
        notifier(f"💥 Crash Players : {e}")

    notifier("🏁 [CRON CLOUD] Fin du processus de synchronisation.")
    return logs_session


if __name__ == "__main__":
    executer_mise_a_jour_cron()
