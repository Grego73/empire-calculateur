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
    
    try:
        # On teste uniquement sur les matériaux pour comprendre la structure
        req = requests.get(f"{BASE_URL}/api/materials.json?key={API_KEY}", timeout=15)
        logs_session.append(f"[TEST STRUCTURE] Code HTTP : {req.status_code}")
        
        # On affiche les 500 premiers caractères du fichier JSON réel renvoyé par le jeu
        contenu_brut = str(req.text)[:500]
        logs_session.append(f"[CONTENU REÇU] : {contenu_brut}")
        
    except Exception as e:
        logs_session.append(f"[ERREUR TEST] : {e}")
        
    return logs_session



if __name__ == "__main__":
    executer_mise_a_jour_cron()
