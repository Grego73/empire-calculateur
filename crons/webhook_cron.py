import streamlit as st
import os
import sys

# Forcer l'affichage d'une page blanche minimaliste
st.set_page_page_config(page_title="Cron Trigger", layout="centered")

# Alignement des dossiers pour charger le script de mise à jour
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from crons.cron_update_api import executer_mise_a_jour_cron
    CRON_OK = True
except ImportError:
    CRON_OK = False

st.title("🔄 Déclencheur automatique d'API")

# 🔒 VÉRIFICATION DE SÉCURITÉ : Vérifie la présence d'un jeton secret dans l'URL
# Exemple d'URL attendue : https://streamlit.app
parametres = st.query_params

if "token" in parametres and parametres["token"] == "MonCodeSecret2026":
    if CRON_OK:
        with st.spinner("Synchronisation Cloud Firestore en cours..."):
            logs = executer_mise_a_jour_cron()
        st.success("✅ Données synchronisées automatiquement avec succès !")
        st.code("\n".join(logs), language="text")
    else:
        st.error("Le script de synchronisation est introuvable sur le serveur.")
else:
    st.error("🔒 Accès interdit : Jeton de sécurité invalide ou manquant.")
    st.info("Cette page est réservée au robot de synchronisation automatique.")
