import streamlit as st
import os
import sys

st.set_page_config(page_title="Déclencheur Taux 4H", layout="centered")

# Alignement pour charger le script
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from crons.cron_update_api import db # Vérification connexion Firebase
    from crons.cron_update_taux import executer_mise_a_jour_taux_uniquement
    CRON_TAUX_OK = True
except ImportError:
    CRON_TAUX_OK = False

st.title("🔄 Déclencheur Léger — Taux Promoteur (4h)")

# Récupération sécurisée du jeton d'URL
parametres = st.query_params

if "token" in parametres and parametres["token"] == "MonCodeSecret2026":
    if CRON_TAUX_OK:
        with st.spinner("Synchronisation des taux du promoteur en cours..."):
            journaux_taux = executer_mise_a_jour_taux_uniquement()
        st.success("✅ Taux du promoteur synchronisés avec succès !")
        st.code("\n".join(journaux_taux), language="text")
    else:
        st.error("Le script 'cron_update_taux.py' est introuvable sur le serveur.")
else:
    st.error("🔒 Accès interdit : Jeton de sécurité invalide ou manquant.")
