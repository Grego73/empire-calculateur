import streamlit as st

# Configuration globale
st.set_page_config(page_title="Calculateur Empire", page_icon="💼", layout="centered")

# INITIALISATION DES VARIABLES DE SESSION (La mémoire de l'application)
if "tab_finance" not in st.session_state: st.session_state["tab_finance"] = ""
if "tab_capital" not in st.session_state: st.session_state["tab_capital"] = ""
if "tab_primes" not in st.session_state: st.session_state["tab_primes"] = ""
if "tab_frais" not in st.session_state: st.session_state["tab_frais"] = ""
if "donnees_chargees" not in st.session_state: st.session_state["donnees_chargees"] = False

# MENU DE SÉLECTION DES PAGES
page_home = st.Page(lambda: home_page(), title="📥 Accueil & Saisie Unique", icon="🏠")
page_frais = st.Page("pages/1_frais_gestion.py", title="Frais de Gestion", icon="📉")
page_primes = st.Page("pages/2_primes.py", title="Gestion des Primes", icon="💰")
page_perf = st.Page("pages/3_performance.py", title="Analyse de Performance", icon="📊")
page_equilibre = st.Page("pages/4_equilibrage.py", title="Équilibrage & Injection", icon="⚖️")

# DÉFINITION DE LA PAGE D'ACCUEIL CENTRALISÉE
def home_page():
    st.title("🏠 Centre de Saisie Unique de l'Empire")
    st.markdown("Collez vos **4 tableaux financiers** ici une seule fois. Ils seront automatiquement envoyés vers les pages de calcul correspondantes.")
    
    # Zones de texte connectées à la mémoire session_state
    st.session_state["tab_finance"] = st.text_area("1. Tableau FINANCE :", value=st.session_state["tab_finance"], height=150)
    st.session_state["tab_capital"] = st.text_area("2. Tableau CAPITAL :", value=st.session_state["tab_capital"], height=150)
    st.session_state["tab_primes"] = st.text_area("3. Tableau DIRECTEURS / PLAFONDS PRIMES :", value=st.session_state["tab_primes"], height=150)
    st.session_state["tab_frais"] = st.text_area("4. Tableau FRAIS DE GESTION (De la veille) :", value=st.session_state["tab_frais"], height=150)
    
    if st.button("🚀 Répartir et synchroniser les données dans tout l'Empire", use_container_width=True):
        if not st.session_state["tab_finance"].strip():
            st.error("❌ Le tableau Finance est obligatoire pour démarrer.")
        else:
            st.session_state["donnees_chargees"] = True
            st.success("🎉 Synchronisation réussie ! Vous pouvez maintenant naviguer dans le menu de gauche. Les calculs sont déjà prêts.")

# Lancement de la navigation avec la page d'accueil en premier
pg = st.navigation([page_home, page_frais, page_primes, page_perf, page_equilibre])
pg.run()
