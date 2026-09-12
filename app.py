import streamlit as st

# Configuration globale de l'application
st.set_page_config(page_title="Calculateur Empire", page_icon="💼", layout="centered")

# Définition des pages de navigation
page_frais = st.Page("pages/1_frais_gestion.py", title="Frais de Gestion", icon="📉")
page_primes = st.Page("pages/2_primes.py", title="Gestion des Primes", icon="💰")

# Lancement de la navigation (crée automatiquement un menu à gauche)
pg = st.navigation([page_frais, page_primes])
pg.run()
