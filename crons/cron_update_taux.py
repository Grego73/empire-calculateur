import requests
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

def executer_mise_a_jour_taux_uniquement():
    logs = []
    logs.append(f"⏱️ Démarrage du Cron Taux Léger : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Récupération des accès Firebase centraux
    from utils import URL_MATERIALS, db
    
    try:
        # 1. Appel sécurisé à l'API du jeu
        reponse = requests.get(URL_MATERIALS, timeout=10)
        
        if reponse.status_code != 200:
            logs.append(f"❌ Erreur API Monde 8 (Code {reponse.status_code})")
            return logs
            
        data = reponse.json()
        
        # 2. Extraction des taux depuis les métadonnées de l'API
        taux_batiments = int(data.get("taux_promoteur_batiments", 0))
        taux_materiaux = int(data.get("taux_promoteur_materiaux", 0))
        
        date_liaison = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Préparation du dictionnaire de données NoSQL
        payload_taux = {
            "date_extraction": date_liaison,
            "date_mise_a_jour": date_liaison,
            "taux_promoteur_batiments": taux_batiments,
            "taux_promoteur_materiaux": taux_materiaux
        }
        
        # 🔥 CORRECTION 1 : Écriture dans un document FIXE pour la page d'accueil de l'application
        # Ce document sera écrasé à chaque fois avec les taux les plus récents
        db.collection("configuration").document("config_actuelle").set(payload_taux)
        logs.append("✅ Collection 'configuration' [config_actuelle] mise à jour avec succès.")
        
        # 🔄 CORRECTION 2 : Écriture historique (ID unique) pour garder une trace des variations toutes les 4 heures
        id_doc_historique = f"config_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        db.collection("configuration").document(id_doc_historique).set(payload_taux)
        logs.append(f"📈 Historique sauvegardé sous l'ID : {id_doc_historique}")
        
        logs.append(f"🎯 Fin du traitement ! [Bâtiments: {taux_batiments}% | Matériaux: {taux_materiaux}%]")
        
    except Exception as e:
        logs.append(f"💥 Erreur générale durant le traitement du Cron : {str(e)}")
        
    return logs
