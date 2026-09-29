import requests
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

def executer_mise_a_jour_taux_uniquement():
    logs = []
    logs.append(f"⏱️ Démarrage du Cron Taux Léger : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Récupération sécurisée du client Firestore actif
    from firebase_admin import firestore
    db = firestore.client()
    
    # 🌐 CONFIGURATION CORRECTE DU SOUS-DOMAINE MONDE 8
    API_KEY = "eiK8_110b18473efc48e9c63f76b5494ea18f"
    BASE_URL = "https://monde8.empireimmo.com"  # ◄--- FIXÉ : Ajout du sous-domaine 'monde8.'
    
    url_cible = f"{BASE_URL}/api/materials.json?key={API_KEY}"
    logs.append(f"[TRACE] Requête HTTP lancée sur : {url_cible}")
    
    try:
        reponse = requests.get(url_cible, timeout=15)
        
        # Gestion alternative si l'API du jeu bascule au singulier
        if reponse.status_code == 404:
            logs.append("⚠️ Endpoint 'materials.json' non trouvé (404). Essai sur 'material.json'...")
            url_cible = f"{BASE_URL}/api/material.json?key={API_KEY}"
            reponse = requests.get(url_cible, timeout=15)
            
        if reponse.status_code != 200:
            logs.append(f"❌ Échec de la connexion à l'API Monde 8 (Code HTTP {reponse.status_code})")
            return logs
            
        data = reponse.json()
        logs.append("[✅] Réponse JSON reçue du serveur.")
        
        # Extraction des deux taux du promoteur
        taux_batiments = int(data.get("taux_promoteur_batiments", data.get("taux_promoteur_batiment", 0)))
        taux_materiaux = int(data.get("taux_promoteur_materials", data.get("taux_promoteur_materiaux", 0)))
        
        date_liaison = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Structuration de l'objet NoSQL
        payload_taux = {
            "date_extraction": date_liaison,
            "date_mise_a_jour": date_liaison,
            "taux_promoteur_batiments": taux_batiments,
            "taux_promoteur_materiaux": taux_materiaux
        }
        
        # 🏛️ ÉCRITURE 1 : Enregistrement dans le document FIXE lu par Streamlit
        db.collection("configuration").document("config_actuelle").set(payload_taux)
        logs.append("✅ Document fixe 'configuration/config_actuelle' créé ou mis à jour dans Firestore.")
        
        # 📈 ÉCRITURE 2 : Sauvegarde dans l'historique NoSQL
        id_doc_historique = f"config_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        db.collection("configuration").document(id_doc_historique).set(payload_taux)
        logs.append(f"📈 Copie d'historique sauvegardée sous l'ID : '{id_doc_historique}'")
        
        logs.append(f"🎯 Traitement finalisé avec succès ! [Bâtiments : {taux_batiments}% | Matériaux : {taux_materiaux}%]")
        
    except Exception as e:
        logs.append(f"💥 Incident critique durant le traitement du Cron Taux : {str(e)}")
        
    return logs
