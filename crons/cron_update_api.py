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
            materials_list = req.json().get("materiaux", [])
            notifier(f"📦 {len(materials_list)} matériaux détectés dans le flux API.")
            for m in materials_list:
                nom_brut = m.get('nom', 'Inconnu')
                doc_id = f"{nom_brut.replace('/', '_')}_{timestamp_id}"
                db.collection("materiaux").document(doc_id).set({
                    "nom": nom_brut, 
                    "prix": int(float(m.get("prix", 0))), 
                    "unite": m.get("unite"), 
                    "date_extraction": date_now
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
            # Correction Clé : "batiments" pour le Monde 8
            buildings_list = req.json().get("batiments", [])
            notifier(f"🏢 {len(buildings_list)} bâtiments détectés dans le flux API.")
            for b in buildings_list:
                id_j = b.get('id', 0)
                doc_id = f"{id_j}_{timestamp_id}"
                db.collection("batiments").document(doc_id).set({
                    "id_jeu": id_j, 
                    "nom": b.get("nom", "Inconnu"), 
                    "type": b.get("type", "Standard"), 
                    "valeur": int(float(b.get("valeur", 0))),
                    "loyer": int(float(b.get("loyer", 0))), 
                    "charge": int(float(b.get("charge", 0))), 
                    "impot": int(float(b.get("impot", 0))), 
                    "date_extraction": date_now
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
            # Correction Clé : "travaux" pour le Monde 8
            works_list = req.json().get("travaux", [])
            notifier(f"🏗️ {len(works_list)} chantiers détectés dans le flux API.")
            for w in works_list:
                b_name = w.get('nom_batiment', 'Inconnu')
                t_type = w.get('type_travaux', 'Construction')
                doc_id = f"{b_name.replace('/', '_')}_{t_type}_{timestamp_id}"
                db.collection("travaux").document(doc_id).set({
                    "type_travaux": t_type, 
                    "building_name": b_name, 
                    "terrain_requis": w.get("terrain_requis", "Aucun"),
                    "cout_estime": int(float(w.get("cout_estime", 0))), 
                    "duree_mois": int(w.get("duree_mois", 0)), 
                    "date_extraction": date_now
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
            # Correction Clé : "joueurs" pour le Monde 8
            players_list = req.json().get("joueurs", [])
            notifier(f"🏆 {len(players_list)} joueurs détectés dans le flux API.")
            for p in players_list:
                pseudo_j = p.get('pseudo')
                doc_id = f"{pseudo_j}_{timestamp_id}"
                
                # 🔒 SÉCURISATION DU SCORE GIGANTESQUE (String de sécurité pour Firestore)
                points_bruts = str(p.get("points", 0))
                
                db.collection("players").document(doc_id).set({
                    "pseudo": pseudo_j, 
                    "points": points_bruts, 
                    "classement": int(p.get("classement", 0)),
                    "niveau": int(p.get("niveau", 0)), 
                    "date_extraction": date_now
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
