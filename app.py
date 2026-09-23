import streamlit as st

# Configuration globale de l'application
st.set_page_config(page_title="Calculateur Empire", page_icon="💼", layout="centered")

# 📥 INITIALISATION DES VARIABLES DE SESSION (Mémoire centrale de l'Empire)
# Blocs de Gestion Holding [1]
if "tab_finance" not in st.session_state: st.session_state["tab_finance"] = "" [1]
if "tab_capital" not in st.session_state: st.session_state["tab_capital"] = "" [1]
if "tab_primes" not in st.session_state: st.session_state["tab_primes"] = "" [1]
if "tab_frais" not in st.session_state: st.session_state["tab_frais"] = "" [1]

# Blocs de Fiches Projets / Rentabilité [1]
if "tab_projets_construction" not in st.session_state: st.session_state["tab_projets_construction"] = "" [1]
if "tab_projets_renovation" not in st.session_state: st.session_state["tab_projets_renovation"] = "" [1]

# Statuts de chargement indépendants pour éviter les blocages croisés
if "holding_chargee" not in st.session_state: st.session_state["holding_chargee"] = False
if "projets_charges" not in st.session_state: st.session_state["projets_charges"] = False


# 📋 DÉCLARATION DES PAGES DE L'APPLICATION [1]
page_home = st.Page(lambda: home_page(), title="📥 Accueil & Saisie Unique", icon="🏠") [1]

# Catégorie 1 : Gestion Holding [1]
page_frais = st.Page("pages/1_frais_gestion.py", title="Frais de Gestion", icon="📉") [1]
page_primes = st.Page("pages/2_primes.py", title="Gestion des Primes", icon="💰") [1]
page_perf = st.Page("pages/3_performance.py", title="Analyse de Performance", icon="📊") [1]
page_equilibre = st.Page("pages/4_equilibrage.py", title="Équilibrage & Injection", icon="⚖️") [1]

# Catégorie 2 : Calculs de Rentabilité [1]
page_renta_const = st.Page("pages/5_analyse_locative.py", title="Analyse Locative & R.O.I", icon="📊") [1]
page_renta_reno = st.Page("pages/6_chantiers_et_embellissement.py", title="Chantiers & Embellissement", icon="🏗️") [1]


# 🏠 DÉFINITION DE LA PAGE D'ACCUEIL CENTRALISÉE [1]
def home_page():
    st.title("🏠 Centre de Saisie Unique de l'Empire") [1]
    st.markdown("Collez vos données dans la section de votre choix. Chaque pôle possède son propre bouton de synchronisation indépendant.")
    
    # --- SECTION 1 : DONNÉES DE LA HOLDING --- [1]
    st.subheader("🏛️ 1. Données de Gestion Holding") [1]
    st.session_state["tab_finance"] = st.text_area("Tableau FINANCE :", value=st.session_state["tab_finance"], height=120) [1]
    st.session_state["tab_capital"] = st.text_area("Tableau CAPITAL :", value=st.session_state["tab_capital"], height=120) [1]
    st.session_state["tab_primes"] = st.text_area("Tableau DIRECTEURS / PLAFONDS PRIMES :", value=st.session_state["tab_primes"], height=120) [1]
    st.session_state["tab_frais"] = st.text_area("Tableau FRAIS DE GESTION (De la veille) :", value=st.session_state["tab_frais"], height=120) [1]
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Synchroniser uniquement la Holding", use_container_width=True):
            if not st.session_state["tab_finance"].strip():
                st.error("❌ Le tableau Finance est requis pour lancer la Holding.")
            else:
                st.session_state["holding_chargee"] = True
                st.success("🎉 Pôle Holding synchronisé et prêt !")
    with col2:
        if st.button("🗑️ Vider les données Holding", use_container_width=True): [1]
            st.session_state["tab_finance"] = "" [1]
            st.session_state["tab_capital"] = "" [1]
            st.session_state["tab_primes"] = "" [1]
            st.session_state["tab_frais"] = "" [1]
            st.session_state["holding_chargee"] = False
            st.rerun() [1]
    
    st.markdown("---")
    
    # --- SECTION 2 : DONNÉES DES PROJETS DE RENTABILITÉ --- [1]
    st.subheader("🏗️ 2. Fiches Projets & Rentabilité") [1]
    st.markdown("Collez ici vos rapports ou fiches de chantiers pour extraire les coûts et rendements.") [1]
    st.session_state["tab_projets_construction"] = st.text_area("5. Fiches CONSTRUCTION / NEUF / LOCATIF :", value=st.session_state["tab_projets_construction"], height=150) [1]
    st.session_state["tab_projets_renovation"] = st.text_area("6. Fiches RÉNOVATION / EMBELLISSEMENT :", value=st.session_state["tab_projets_renovation"], height=150) [1]
    
    col3, col4 = st.columns(2)
    with col3:
        if st.button("🚀 Synchroniser uniquement les Projets", use_container_width=True):
            if not st.session_state["tab_projets_construction"].strip():
                st.error("❌ La fiche de construction brute (bloc 5) est requise.")
            else:
                st.session_state["projets_charges"] = True
                st.success("🎉 Pôle Projets & Rentabilité synchronisé et prêt !")
    with col4:
        if st.button("🗑️ Vider les fiches Projets", use_container_width=True): [1]
            st.session_state["tab_projets_construction"] = "" [1]
            st.session_state["tab_projets_renovation"] = "" [1]
            st.session_state["projets_charges"] = False
            st.rerun() [1]
    
    st.markdown("---")
    
    # --- MODULE DE CONTRÔLE / AUDIT --- [1]
    st.subheader("🔍 Outil de Contrôle : Audit d'une filiale") [1]
    st.markdown("Collez le rapport complet d'une filiale (Résultat et Bilan) ci-dessous pour vérifier sa concordance comptable.") [1]
    rapport_audit = st.text_area("Collez le rapport de la filiale ici :", height=150, key="audit_input") [1]
    
    if st.button("👁️ Auditer les chiffres de la filiale", use_container_width=True): [1]
        if not rapport_audit.strip(): [1]
            st.error("❌ Veuillez coller un rapport à auditer.") [1]
        else:
            from utils import verifier_concordance_rapport, formater_monnaie_empire [1]
            erreurs, data = verifier_concordance_rapport(rapport_audit) [1]
            
            if erreurs: [1]
                st.error("🚨 CONCORDANCE INCORRECTE : Le rapport contient des anomalies comptables !") [1]
                for err in erreurs: [1]
                    st.warning(err) [1]
            else: [1]
                st.success("✅ CONCORDANCE PARFAITE : Les calculs de la filiale sont 100% valides et équilibrés !") [1]
                col1_aud, col2_aud = st.columns(2)
                with col1_aud: 
                    st.write(f"• Résultat NET : `{formater_monnaie_empire(data.get('net', 0))}`") [1]
                with col2_aud: 
                    st.write(f"• Total Actif/Passif : `{formater_monnaie_empire(data.get('actif', 0))}`") [1]


# 🗺️ CONFIGURATION DE LA NAVIGATION ET DU MENU PAR CATÉGORIES [1]
pg = st.navigation({
    "Accueil": [page_home],
    "🏛️ Gestion Holding": [page_frais, page_primes, page_perf, page_equilibre], [1]
    "🏗️ Calculs de Rentabilité": [page_renta_const, page_renta_reno] [1]
})

# Lancement de l'application [1]
pg.run() [1]
