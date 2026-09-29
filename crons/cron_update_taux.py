import requests
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

def chercher_cle_recursive(dictionnaire, cle_cible):
    """Fouille tout le JSON de manière récursive pour trouver une clé, peu importe où elle est cachée."""
    if cle_cible in dictionnaire:
        return dictionnaire[cle_cible]
    for k, v in dictionnaire.items():
        if isinstance(v, dict):
            item = chercher_cle_recursive(v, cle_cible)
            if item is not None:
                return item
        elif isinstance(v, list):
            for element in v:
                if isinstance(element, dict):
                    item = chercher_cle_recursive(element, cle_cible)
                    if item is not None:
                        return item
    return None

def executer_mise_a_jour_taux_uniquement():
    logs = []
    logs.append(f"⏱️ Démarrage du Cron Taux Léger : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    from firebase_admin import firestore
    db = firestore.client()
    
    API_KEY = "eiK8_110b18473efc48e9c63f76b5494ea18f"
    BASE_URL = "https://empireimmo.com"
    
    url_materials = f"{BASE_URL}/api/materials.json?key={API_KEY}"
    url_buildings = f"{BASE_URL}/api/buildings.json?key={API_KEY}"
    
    taux_batiments = None
    taux_materiaux = None
    
    # 🛒 1. EXTRACTEUR EXCLUSIF POUR LES MATÉRIAUX
    try:
        rep_mat = requests.get(url_materials, timeout=15)
        if rep_mat.status_code == 200:
            data_mat = rep_mat.json()
            taux_materiaux = chercher_cle_recursive(data_mat, "taux_promoteur")
            if taux_materiaux is not None:
                logs.append(f"[✅] Taux Matériaux détecté par le scanner : {taux_materiaux}%")
            else:
                logs.append("⚠️ Scanner : Clé 'taux_promoteur' introuvable dans le flux Materials.")
        else:
            logs.append(f"❌ Erreur API Materials (Code HTTP {rep_mat.status_code})")
    except Exception as e_mat:
        logs.append(f"❌ Échec de la requête Materials : {e_mat}")

    # 🏢 2. EXTRACTEUR EXCLUSIF POUR LES BÂTIMENTS
    try:
        rep_bld = requests.get(url_buildings, timeout=15)
        if rep_bld.status_code == 200:
            data_bld = rep_bld.json()
            taux_batiments = chercher_cle_recursive(data_bld, "taux_promoteur")
            if taux_batiments is not None:
                logs.append(f"[✅] Taux Bâtiments détecté par le scanner : {taux_batiments}%")
            else:
                logs.append("⚠️ Scanner : Clé 'taux_promoteur' introuvable dans le flux Buildings.")
        else:
            logs.append(f"❌ Erreur API Buildings (Code HTTP {rep_bld.status_code})")
    except Exception as e_bld:
        logs.append(f"❌ Échec de la requête Buildings : {e_bld}")

    # Sécurité par défaut pour éviter d'écraser la base avec des zéros si l'API coupe
    if taux_materiaux is None: taux_materiaux = 0
    if taux_batiments is None: taux_batiments = 0

    # 3. ENREGISTREMENT DANS FIREBASE
    try:
        date_liaison = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        payload_taux = {
            "date_extraction": date_liaison,
            "date_mise_a_jour": date_liaison,
            "taux_promoteur_batiments": int(taux_batiments),
            "taux_promoteur_materiaux": int(taux_materiaux)
        }
        
        # Mise à jour du document maître fixe lu par Streamlit
        db.collection("configuration").document("config_actuelle").set(payload_taux)
        logs.append("✅ Document maître 'configuration/config_actuelle' mis à jour.")
        
        # Enregistrement historique
        id_doc_historique = f"config_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        db.collection("configuration").document(id_doc_historique).set(payload_taux)
        
        logs.append(f"🎯 Fin de session avec succès ! [Bâtiments : {taux_batiments}% | Matériaux : {taux_materiaux}%]")
        
    except Exception as e_db:
        logs.append(f"💥 Erreur d'écriture NoSQL : {str(e_db)}")
        
    return logs
