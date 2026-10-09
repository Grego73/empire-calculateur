import os
import sys
import requests
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

def executer_mise_a_jour_taux_uniquement():
    logs = []
    logs.append(f"⏱️ Démarrage du Cron Taux Léger : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Récupération de l'instance Firestore active
    db = firestore.client()
    
    # 🔑 CONFIGURATION STRICTE ET CENTRALISÉE DU MONDE 8
    API_KEY = "eiK8_110b18473efc48e9c63f76b5494ea18f"
    BASE_URL = "https://empireimmo.com"  # ✅ URL unifiée pour éviter les erreurs de routage
    
    url_materials = f"{BASE_URL}/api/materials.json?key={API_KEY}"
    url_buildings = f"{BASE_URL}/api/buildings.json?key={API_KEY}"
    
    # 🌐 En-tête obligatoire pour s'identifier proprement auprès de l'API d'Empire Immo
    headers_navigation = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Application-Empire-Calculateur",
        "Accept": "application/json"
    }
    
    taux_batiments = 0
    taux_materiaux = 0
    
    # 🛒 1. APPEL DE L'API MATERIALS (MATÉRIAUX)
    try:
        logs.append("[TRACE] Requête HTTP Materials lancée...")
        rep_mat = requests.get(url_materials, headers=headers_navigation, timeout=15)
        
        if rep_mat.status_code == 200:
            data_mat = rep_mat.json()
            taux_materiaux = int(data_mat.get("taux_promoteur", 0))
            logs.append(f"[✅] Authentification Materials validée. Taux extrait : {taux_materiaux}%")
        elif rep_mat.status_code == 429:
            logs.append("⚠️ [API EMPIRE] Trop de requêtes sur l'API Materials.")
        else:
            logs.append(f"❌ Rejet API Materials — Code HTTP {rep_mat.status_code}")
    except Exception as e_mat:
        logs.append(f"❌ Erreur de transmission Materials : {e_mat}")

    # 🏢 2. APPEL DE L'API BUILDINGS (BÂTIMENTS)
    try:
        logs.append("[TRACE] Requête HTTP Buildings lancée...")
        rep_bld = requests.get(url_buildings, headers=headers_navigation, timeout=15)
        
        if rep_bld.status_code == 200:
            data_bld = rep_bld.json()
            taux_batiments = int(data_bld.get("taux_promoteur", 0))
            logs.append(f"[✅] Authentification Buildings validée. Taux extrait : {taux_batiments}%")
        elif rep_bld.status_code == 429:
            logs.append("⚠️ [API EMPIRE] Trop de requêtes sur l'API Buildings.")
        else:
            logs.append(f"❌ Rejet API Buildings — Code HTTP {rep_bld.status_code}")
    except Exception as e_bld:
        logs.append(f"❌ Erreur de transmission Buildings : {e_bld}")

    # 🗄️ 3. ENREGISTREMENT ET HISTORISATION FIRESTORE
    try:
        date_liaison = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        timestamp_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        payload_taux = {
            "date_extraction": date_liaison,
            "date_mise_a_jour": date_liaison,
            "taux_promoteur_batiments": taux_batiments,
            "taux_promoteur_materiaux": taux_materiaux
        }
        
        # Écriture / Écrasement du document maître lu en continu par l'application Streamlit
        db.collection("configuration").document("config_actuelle").set(payload_taux, merge=True)
        logs.append("✅ Document maître 'configuration/config_actuelle' mis à jour.")
        
        # Création de l'entrée d'historique pour alimenter vos graphiques temporels de la page 7
        id_doc_historique = f"config_{timestamp_id}"
        db.collection("configuration").document(id_doc_historique).set(payload_taux, merge=True)
        logs.append(f"📈 Historique sauvegardé sous l'ID : '{id_doc_historique}'")
        
        logs.append(f"🎯 Fin de session réussie ! Valeurs : Bâtiments {taux_batiments}% | Matériaux {taux_materiaux}%")
    except Exception as e_db:
        logs.append(f"💥 Erreur d'écriture NoSQL Firestore : {str(e_db)}")
        
    return logs
