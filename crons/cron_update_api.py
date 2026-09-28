import streamlit as st
import os
import sys
import requests
import csv
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

    # --- 1. MATÉRIAUX (JSON) ---
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

    # --- 2. BÂTIMENTS (ASPIRES DEPUIS LES 3 FILES CSV DU JEU) ---
    fichiers_csv = [
        "buildings_batiments_terrain.csv",
        "buildings_batiments_entreprise.csv",
        "buildings_batiments_perso.csv"
    ]
    
    total_batiments_sauves = 0
    batch = db.batch()
    c_batch = 0
    
    for nom_csv in fichiers_csv:
        try:
            url_csv = f"{BASE_URL}/api/{nom_csv}?key={API_KEY}"
            req = requests.get(url_csv, timeout=15)
            
            if req.status_code == 200:
                lignes = req.text.strip().split('\n')
                # Séparateur par défaut du jeu (tabulation ou virgule)
                lecteur = csv.DictReader(lignes, delimiter='\t')
                if len(lecteur.fieldnames or []) <= 1:
                    lecteur = csv.DictReader(lignes, delimiter=',')
                
                compteur_fichier = 0
                for ligne in lecteur:
                    id_j = ligne.get('id', ligne.get('id_jeu', str(total_batiments_sauves + 1)))
                    nom_b = ligne.get('nom', ligne.get('name', 'Bâtiment Inconnu'))
                    
                    doc_id = f"{id_j}_{timestamp_id}"
                    doc_ref = db.collection("batiments").document(doc_id)
                    
                    batch.set(doc_ref, {
                        "id_jeu": id_j,
                        "nom": nom_b,
                        "type": ligne.get("type", nom_csv.split('_')[-1].replace('.csv', '')),
                        "valeur": int(float(ligne.get("valeur", ligne.get("value", 0)))),
                        "loyer": int(float(ligne.get("loyer", ligne.get("rent", 0)))),
                        "charge": int(float(ligne.get("charge", ligne.get("charges", 0)))),
                        "impot": int(float(ligne.get("impot", ligne.get("tax", 0)))),
                        "date_extraction": date_now
                    })
                    
                    compteur_fichier += 1
                    total_batiments_sauves += 1
                    c_batch += 1
                    
                    if c_batch >= 500:
                        batch.commit()
                        batch = db.batch()
                        c_batch = 0
                
                notifier(f"🏢 {compteur_fichier} infrastructures chargées depuis {nom_csv}.")
        except Exception as e:
            notifier(f"💥 Incident sur {nom_csv} : {e}")
            
    if c_batch > 0:
        batch.commit()
    notifier(f"✅ Collection 'batiments' synchronisée ({total_batiments_sauves} lignes au total).")

    # --- 3. TRAVAUX (JSON FLUX SECOURS OU VIDE) ---
    try:
        req = requests.get(f"{BASE_URL}/api/works.json?key={API_KEY}", timeout=15)
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
    except Exception as e: 
        notifier(f"💥 Crash Travaux : {e}")

    notifier("🏁 [CRON CLOUD] Fin du processus de synchronisation.")
    return logs_session


if __name__ == "__main__":
    executer_mise_a_jour_cron()
