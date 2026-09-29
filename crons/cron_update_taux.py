import requests
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st

def executer_mise_a_jour_taux_uniquement():
    logs = []
    logs.append(f"⏱️ Démarrage du Cron Taux Léger : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Récupération des clés centrales depuis votre utils.py
    from utils import URL_MATERIALS, db
    
    try:
        # Appel à l'API du jeu (on utilise l'API materials qui contient les métadonnées de configuration)
        reponse = requests.get(URL_MATERIALS, timeout=10)
        
        if reponse.status_code != 200:
            logs.append(f"❌ Erreur API Monde 8 (Code {reponse.status_code})")
            return logs
            
        data = reponse.json()
        
        # Extraction des deux taux du promoteur depuis les métadonnées du JSON
        taux_batiments = int(data.get("taux_promoteur_batiments", 0))
        taux_materiaux = int(data.get("taux_promoteur_materiaux", 0))
        
        date_liaison = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        payload_taux = {
            "date_extraction": date_liaison,
            "taux_promoteur_batiments": taux_batiments,
            "taux_promoteur_materiaux": taux_materiaux
        }
        
        # 1. Mise à jour de la table de configuration globale
        db.collection("configuration").document("configuration_actuelle").set(payload_taux)
        logs.append("✅ Table 'configuration' mise à jour avec les nouveaux taux.")
        
        # 2. Historisation dans une collection dédiée pour alimenter un futur graphique temporel
        id_doc_historique = f"taux_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        db.collection("historique_taux").document(id_doc_historique).set(payload_taux)
        logs.append(f"📈 Historique sauvegardé sous l'ID : {id_doc_historique}")
        
        logs.append(f"🎯 Fin du traitement avec succès ! [Bâtiments: {taux_batiments}% | Matériaux: {taux_materiaux}%]")
        
    except Exception as e:
        logs.append(f"💥 Erreur générale durant le Cron Taux : {str(e)}")
        
    return logs
