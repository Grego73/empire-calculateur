import requests
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

def executer_mise_a_jour_taux_uniquement():
    logs = []
    logs.append(f"⏱️ Démarrage du Cron Taux Léger : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Connexion sécurisée au client Firestore actif
    from firebase_admin import firestore
    db = firestore.client()
    
    # Configuration des adresses officielles du Monde 8
    API_KEY = "eiK8_110b18473efc48e9c63f76b5494ea18f"
    BASE_URL = "https://empireimmo.com"
    
    url_materials = f"{BASE_URL}/api/materials.json?key={API_KEY}"
    url_buildings = f"{BASE_URL}/api/buildings.json?key={API_KEY}"
    
    taux_batiments = 0
    taux_materiaux = 0
    
    # 🛒 1. EXTRACTION DU TAUX MATÉRIAUX
    try:
        rep_mat = requests.get(url_materials, timeout=15)
        if rep_mat.status_code == 200:
            data_mat = rep_mat.json()
            # Interception directe de la clé brute identifiée dans les logs
            taux_materiaux = int(data_mat.get("taux_promoteur", 0))
            logs.append(f"[✅] Taux Matériaux extrait avec succès : {taux_materiaux}%")
        else:
            logs.append(f"❌ Erreur API Materials (Code HTTP {rep_mat.status_code})")
    except Exception as e_mat:
        logs.append(f"❌ Échec de la requête Materials : {e_mat}")

    # 🏢 2. EXTRACTION DU TAUX BÂTIMENTS
    try:
        rep_bld = requests.get(url_buildings, timeout=15)
        if rep_bld.status_code == 200:
            data_bld = rep_bld.json()
            # Interception de la clé brute sur le deuxième fichier
            taux_batiments = int(data_bld.get("taux_promoteur", 0))
            logs.append(f"[✅] Taux Bâtiments extrait avec succès : {taux_batiments}%")
        else:
            logs.append(f"❌ Erreur API Buildings (Code HTTP {rep_bld.status_code})")
    except Exception as e_bld:
        logs.append(f"❌ Échec de la requête Buildings : {e_bld}")

    # 3. ENREGISTREMENT ET HISTORISATION DANS FIRESTORE
    try:
        date_liaison = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Structuration de l'objet de configuration
        payload_taux = {
            "date_extraction": date_liaison,
            "date_mise_a_jour": date_liaison,
            "taux_promoteur_batiments": taux_batiments,
            "taux_promoteur_materiaux": taux_materiaux
        }
        
        # Écriture du document maître fixe lu par Streamlit
        db.collection("configuration").document("config_actuelle").set(payload_taux)
        logs.append("✅ Document maître 'configuration/config_actuelle' mis à jour.")
        
        # Sauvegarde de la ligne dans l'historique temporel (toutes les 4h)
        id_doc_historique = f"config_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        db.collection("configuration").document(id_doc_historique).set(payload_taux)
        logs.append(f"📈 Historique complété sous l'ID : '{id_doc_historique}'")
        
        logs.append(f"🎯 Fin du processus avec succès ! Valeurs enregistrées -> Bâtiments : {taux_batiments}% | Matériaux : {taux_materiaux}%")
        
    except Exception as e_db:
        logs.append(f"💥 Erreur d'écriture NoSQL : {str(e_db)}")
        
    return logs
