import streamlit as st

# Configuration globale de l'application
st.set_page_config(page_title="Calculateur Empire", page_icon="💼", layout="centered")

# 📥 INITIALISATION DES VARIABLES DE SESSION (Mémoire centrale de l'Empire)
# Blocs de Gestion Holding
if "tab_finance" not in st.session_state: st.session_state["tab_finance"] = ""
if "tab_capital" not in st.session_state: st.session_state["tab_capital"] = ""
if "tab_primes" not in st.session_state: st.session_state["tab_primes"] = ""
if "tab_frais" not in st.session_state: st.session_state["tab_frais"] = ""

# Blocs de Fiches Projets / Rentabilité
if "tab_projets_construction" not in st.session_state: st.session_state["tab_projets_construction"] = ""
if "tab_projets_renovation" not in st.session_state: st.session_state["tab_projets_renovation"] = ""

# Statut global du chargement
if "donnees_chargees" not in st.session_state: st.session_state["donnees_chargees"] = False


# 📋 DÉCLARATION DES PAGES DE L'APPLICATION
page_home = st.Page(lambda: home_page(), title="📥 Accueil & Saisie Unique", icon="🏠")

# Catégorie 1 : Gestion Holding
page_frais = st.Page("pages/1_frais_gestion.py", title="Frais de Gestion", icon="📉")
page_primes = st.Page("pages/2_primes.py", title="Gestion des Primes", icon="💰")
page_perf = st.Page("pages/3_performance.py", title="Analyse de Performance", icon="📊")
page_equilibre = st.Page("pages/4_equilibrage.py", title="Équilibrage & Injection", icon="⚖️")

# Catégorie 2 : Calculs de Rentabilité
page_renta_const = st.Page("pages/5_analyse_locative.py", title="Analyse Locative & R.O.I", icon="📊")
page_renta_reno = st.Page("pages/6_chantiers_et_embellissement.py", title="Chantiers & Embellissement", icon="🏗️")


# 🏠 DÉFINITION DE LA PAGE D'ACCUEIL CENTRALISÉE
def home_page():
    st.title("🏠 Centre de Saisie Unique de l'Empire")
    st.markdown("Collez vos tableaux financiers et vos fiches de projets ici une seule fois. Ils seront automatiquement partagés dans tout l'Empire.")
    
    # --- SECTION 1 : DONNÉES DE LA HOLDING ---
    st.subheader("🏛️ 1. Données de Gestion Holding")
    st.session_state["tab_finance"] = st.text_area("Tableau FINANCE :", value=st.session_state["tab_finance"], height=120)
    st.session_state["tab_capital"] = st.text_area("Tableau CAPITAL :", value=st.session_state["tab_capital"], height=120)
    st.session_state["tab_primes"] = st.text_area("Tableau DIRECTEURS / PLAFONDS PRIMES :", value=st.session_state["tab_primes"], height=120)
    st.session_state["tab_frais"] = st.text_area("Tableau FRAIS DE GESTION (De la veille) :", value=st.session_state["tab_frais"], height=120)
    
    if st.button("🗑️ Vider toutes les données de gestion Holding", use_container_width=True):
        st.session_state["tab_finance"] = ""
        st.session_state["tab_capital"] = ""
        st.session_state["tab_primes"] = ""
        st.session_state["tab_frais"] = ""
        st.rerun()
    
    st.markdown("---")
    
    # --- SECTION 2 : DONNÉES DES PROJETS DE RENTABILITÉ ---
    st.subheader("🏗️ 2. Fiches Projets & Rentabilité")
    st.markdown("Collez ici vos rapports ou fiches de chantiers pour extraire les coûts et rendements.")
    st.session_state["tab_projets_construction"] = st.text_area("5. Fiches CONSTRUCTION / NEUF :", value=st.session_state["tab_projets_construction"], height=150)
    st.session_state["tab_projets_renovation"] = st.text_area("6. Fiches RÉNOVATION / LOCATION / EMBELLISSEMENT :", value=st.session_state["tab_projets_renovation"], height=150)
    
    if st.button("🗑️ Vider toutes les fiches Projets & Rentabilité", use_container_width=True):
        st.session_state["tab_projets_construction"] = ""
        st.session_state["tab_projets_renovation"] = ""
        st.rerun()
    
    st.markdown("---")
    
    # --- BOUTON DE SYNCHRONISATION GLOBAL ---
    if st.button("🚀 Répartir et synchroniser toutes les données de l'Empire", use_container_width=True):
        st.session_state["donnees_chargees"] = True
        st.success("🎉 Synchronisation réussie ! Les données de gestion et les fiches projets sont prêtes dans le menu de gauche.")
        
    st.markdown("---")
    
    # --- MODULE DE CONTRÔLE / AUDIT ---
    st.subheader("🔍 Outil de Contrôle : Audit d'une filiale")
    st.markdown("Collez le rapport complet d'une filiale (Résultat et Bilan) ci-dessous pour vérifier sa concordance comptable.")
    rapport_audit = st.text_area("Collez le rapport de la filiale ici :", height=150, key="audit_input")
    
    if st.button("👁️ Auditer les chiffres de la filiale", use_container_width=True):
        if not rapport_audit.strip():
            st.error("❌ Veuillez coller un rapport à auditer.")
        else:
            from utils import verifier_concordance_rapport, formater_monnaie_empire
            erreurs, data = verifier_concordance_rapport(rapport_audit)
            
            if erreurs:
                st.error("🚨 CONCORDANCE INCORRECTE : Le rapport contient des anomalies comptables !")
                for err in erreurs: 
                    st.warning(err)
            else:
                st.success("✅ CONCORDANCE PARFAITE : Les calculs de la filiale sont 100% valides et équilibrés !")
                col1, col2 = st.columns(2)
                with col1: 
                    st.write(f"• Résultat NET : `{formater_monnaie_empire(data.get('net', 0))}`")
                with col2: 
                    st.write(f"• Total Actif/Passif : `{formater_monnaie_empire(data.get('actif', 0))}`")


# 🗺️ CONFIGURATION DE LA NAVIGATION ET DU MENU PAR CATÉGORIES
pg = st.navigation({
    "Accueil": [page_home],
    "🏛️ Gestion Holding": [page_frais, page_primes, page_perf, page_equilibre],
    "🏗️ Calculs de Rentabilité": [page_renta_const, page_renta_reno]
})

# Lancement de l'application
pg.run()
