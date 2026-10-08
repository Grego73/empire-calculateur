import requests
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

def executer_mise_a_jour_taux_uniquement():
    import zoneinfo
    # Configuration du fuseau horaire de l'Empire (Heure de Paris)
    tz_paris = zoneinfo.ZoneInfo("Europe/Paris")
    
    logs = []
    logs.append(f"⏱️ Démarrage du Cron Taux Léger : {datetime.now(tz_paris).strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Récupération du client Firestore
    db = firestore.client()
    
    # 🔑 CLÉ OFFICIELLE RESTAURÉE (Respect strict de la casse)
    API_KEY = "eiK8_110b18473efc48e9c63f76b5494ea18f"
    BASE_URL = "https://empireimmo.com"
    
    url_materials = f"{BASE_URL}/api/materials.json?key={API_KEY}"
    url_buildings = f"{BASE_URL}/api/buildings.json?key={API_KEY}"
    
    # En-tête obligatoire pour s'identifier proprement auprès de l'API du jeu
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
            taux_materiaux = data_mat.get("taux_promoteur", 0)
            logs.append(f"[✅] Authentification Materials validée. Taux extrait : {taux_materiaux}%")
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
            taux_batiments = data_bld.get("taux_promoteur", 0)
            logs.append(f"[✅] Authentification Buildings validée. Taux extrait : {taux_batiments}%")
        else:
            logs.append(f"❌ Rejet API Buildings — Code HTTP {rep_bld.status_code}")
    except Exception as e_bld:
        logs.append(f"❌ Erreur de transmission Buildings : {e_bld}")

    # 3. ENREGISTREMENT ET HISTORISATION FIRESTORE AVEC HORLOGE EMPIRE
    try:
        taux_batiments = int(taux_batiments)
        taux_materiaux = int(taux_materiaux)
        
        # Capture des dates synchronisées sur l'heure française
        date_liaison = datetime.now(tz_paris).strftime("%Y-%m-%d %H:%M:%S")
        timestamp_id = datetime.now(tz_paris).strftime("%Y%m%d_%H%M%S")
        
        payload_taux = {
            "date_extraction": date_liaison,
            "date_mise_a_jour": date_liaison,
            "taux_promoteur_batiments": taux_batiments,
            "taux_promoteur_materiaux": taux_materiaux
        }
        
        # Écriture du document fixe lu en direct par l'application Streamlit
        db.collection("configuration").document("config_actuelle").set(payload_taux)
        logs.append("✅ Document maître 'configuration/config_actuelle' mis à jour.")
        
        # Enregistrement dans la collection historique d'évolution (Courbes graphiques)
        id_doc_historique = f"config_{timestamp_id}"
        db.collection("configuration").document(id_doc_historique).set(payload_taux)
        logs.append(f"📈 Historique sauvegardé sous l'ID : '{id_doc_historique}'")
        
        logs.append(f"🎯 Fin de session réussie ! Valeurs enregistrées en base -> Bâtiments : {taux_batiments}% | Matériaux : {taux_materiaux}%")
    except Exception as e_db:
        logs.append(f"💥 Erreur d'écriture NoSQL Firestore : {str(e_db)}")
        
    return logs
