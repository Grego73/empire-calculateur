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
            
            batch = db.batch()
            for m in materials_list:
                nom_brut = m.get('nom', 'Inconnu')
                doc_id = f"{nom_brut.replace('/', '_')}_{timestamp_id}"
                doc_ref = db.collection("materiaux").document(doc_id)
                batch.set(doc_ref, {
                    "nom": nom_brut, 
                    "prix": int(float(m.get("prix", 0))), 
                    "unite": m.get("unite"), 
                    "date_extraction": date_now
                })
            batch.commit()
            notifier("✅ Collection 'materiaux' synchronisée avec succès.")
        else:
            notifier(f"❌ Erreur API Matériaux : {req.text[:200]}")
    except Exception as e: 
        notifier(f"💥 Crash Matériaux : {e}")

    # --- 2. BÂTIMENTS (FUSION ET NETTOYAGE NUMÉRIQUE) ---
    try:
        req = requests.get(f"{BASE_URL}/api/buildings.json?key={API_KEY}", timeout=15)
        notifier(f"📡 API Bâtiments — Code : {req.status_code}")
        if req.status_code == 200:
            data_json = req.json()
            
            liste_perso = data_json.get("batiments_perso", [])
            liste_entreprise = data_json.get("batiments_entreprise", [])
            liste_terrain = data_json.get("batiments_terrain", [])
            
            buildings_list = liste_perso + liste_entreprise + liste_terrain
            
            notifier(f"🏢 Détection JSON : {len(liste_perso)} perso, {len(liste_entreprise)} entreprise, {len(liste_terrain)} terrain.")
            notifier(f"🚀 Traitement global de {len(buildings_list)} infrastructures...")
            
            # Limite maximale des entiers signés 64-bits pour Firestore
            MAX_INT64 = 9223372036854775807
            
            def securiser_entier(valeur):
                """Convertit proprement en int et sature à la limite max 64-bits si besoin"""
                try:
                    num = int(float(valeur))
                    return min(num, MAX_INT64)
                except (ValueError, TypeError):
                    return 0

            batch = db.batch()
            c_batch = 0
            
            for b in buildings_list:
                id_j = b.get('id', 0)
                doc_id = f"{id_j}_{timestamp_id}"
                doc_ref = db.collection("batiments").document(doc_id)
                
                batch.set(doc_ref, {
                    "id_jeu": id_j, 
                    "nom": b.get("nom", "Inconnu"), 
                    "type": b.get("type", "Standard"), 
                    "valeur": securiser_entier(b.get("valeur", 0)),
                    "loyer": securiser_entier(b.get("loyer", 0)), 
                    "charge": securiser_entier(b.get("charge", 0)), 
                    "impot": securiser_entier(b.get("impot", 0)), 
                    "date_extraction": date_now
                })
                
                c_batch += 1
                if c_batch >= 500:
                    batch.commit()
                    batch = db.batch()
                    c_batch = 0
                    
            if c_batch > 0:
                batch.commit()
                
            notifier(f"✅ Collection 'batiments' entièrement synchronisée ({len(buildings_list)} lignes enregistrées).")
        else:
            notifier(f"❌ Erreur API Bâtiments : {req.text[:200]}")
    except Exception as e: 
        notifier(f"💥 Crash Bâtiments : {e}")

    # --- 3. TRAVAUX ---
    try:
        req = requests.get(f"{BASE_URL}/api/works.json?key={API_KEY}", timeout=15)
        notifier(f"📡 API Travaux — Code : {req.status_code}")
        if req.status_code == 200:
            works_list = req.json().get("travaux", [])
            notifier(f"🏗️ {len(works_list)} chantiers détectés dans le flux API.")
            if works_list:
                batch = db.batch()
                for w in works_list:
                    b_name = w.get('nom_batiment', 'Inconnu')
                    t_type = w.get('type_travaux', 'Construction')
                    doc_id = f"{b_name.replace('/', '_')}_{t_type}_{timestamp_id}"
                    doc_ref = db.collection("travaux").document(doc_id)
                    batch.set(doc_ref, {
                        "type_travaux": t_type, 
                        "building_name": b_name, 
                        "terrain_requis": w.get("terrain_requis", "Aucun"),
                        "cout_estime": int(float(w.get("cout_estime", 0))), 
                        "duree_mois": int(w.get("duree_mois", 0)), 
                        "date_extraction": date_now
                    })
                batch.commit()
            notifier("✅ Collection 'travaux' synchronisée avec succès.")
        else:
            notifier(f"❌ Erreur API Travaux : {req.text[:200]}")
    except Exception as e: 
        notifier(f"💥 Crash Travaux : {e}")

    notifier("🏁 [CRON CLOUD] Fin du processus de synchronisation.")
    return logs_session



if __name__ == "__main__":
    executer_mise_a_jour_cron()
