import requests
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

def executer_mise_a_jour_taux_uniquement():
    logs = []
    logs.append(f"⏱️ Démarrage du Cron Taux Léger : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    from firebase_admin import firestore
    db = firestore.client()
    
    # Configuration stricte en minuscules pour l'arborescence API Monde 8
    API_KEY = "eik8_110b18473efc48e9c63f76b5494ea18f"
    BASE_URL = "https://monde8.empireimmo.com"
    
    url_materials = f"{BASE_URL}/api/materials.json?key={API_KEY}"
    url_buildings = f"{BASE_URL}/api/buildings.json?key={API_KEY}"
    
    taux_batiments = 0
    taux_materiaux = 0
    
    # 🛒 1. APPEL DE L'API MATERIALS (MATÉRIAUX)
    try:
        logs.append(f"[TRACE] Appel HTTP : {url_materials}")
        rep_mat = requests.get(url_materials, timeout=15)
        
        if rep_mat.status_code == 200:
            data_mat = rep_mat.json()
            # Extraction native du taux promoteur de la table des matériaux
            taux_materiaux = data_mat.get("taux_promoteur", 0)
            logs.append(f"[✅] Taux Matériaux extrait : {taux_materiaux}%")
        else:
            logs.append(f"❌ Échec API Materials — Code HTTP {rep_mat.status_code}")
    except Exception as e_mat:
        logs.append(f"❌ Erreur réseau lors de l'appel Materials : {e_mat}")

    # 🏢 2. APPEL DE L'API BUILDINGS (BÂTIMENTS)
    try:
        logs.append(f"[TRACE] Appel HTTP : {url_buildings}")
        rep_bld = requests.get(url_buildings, timeout=15)
        
        if rep_bld.status_code == 200:
            data_bld = rep_bld.json()
            # Extraction native du taux promoteur de la table des bâtiments
            taux_batiments = data_bld.get("taux_promoteur", 0)
            logs.append(f"[✅] Taux Bâtiments extrait : {taux_batiments}%")
        else:
            logs.append(f"❌ Échec API Buildings — Code HTTP {rep_bld.status_code}")
    except Exception as e_bld:
        logs.append(f"❌ Erreur réseau lors de l'appel Buildings : {e_bld}")

    # 3. ENREGISTREMENT COMPTABLE ET TRANSMISSION FIRESTORE
    try:
        # Conversion de sécurité des types
        taux_batiments = int(taux_batiments)
        taux_materiaux = int(taux_materiaux)
        
        date_liaison = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        payload_taux = {
            "date_extraction": date_liaison,
            "date_mise_a_jour": date_liaison,
            "taux_promoteur_batiments": taux_batiments,
            "taux_promoteur_materiaux": taux_materiaux
        }
        
        # Mettre à jour la ligne de configuration fixe lue par l'application
        db.collection("configuration").document("config_actuelle").set(payload_taux)
        logs.append("✅ Document maître 'configuration/config_actuelle' mis à jour.")
        
        # Injection de la ligne dans la collection historique d'évolution
        id_doc_historique = f"config_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        db.collection("configuration").document(id_doc_historique).set(payload_taux)
        logs.append(f"📈 Historique sauvegardé sous l'ID : '{id_doc_historique}'")
        
        logs.append(f"🎯 Fin de session réussie ! Valeurs finales -> Bâtiments : {taux_batiments}% | Matériaux : {taux_materiaux}%")
    except Exception as e_db:
        logs.append(f"💥 Erreur lors de l'écriture sur votre base Firestore NoSQL : {str(e_db)}")
        
    return logs
