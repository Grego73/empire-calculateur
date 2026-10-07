import streamlit as st
import pandas as pd
import os
import sys
from datetime import datetime
from utils import (
    formater_monnaie_empire, 
    recuperer_derniere_donnee_table, 
    recuperer_historique_joueur,
    recuperer_historique_materiaux,
    verifier_concordance_rapport
)

# 🔒 1. CONFIGURATION GLOBALE INTERNATIONALE (Impérativement en ligne 1 en mode LARGE)
st.set_page_config(page_title="Calculateur Empire", page_icon="💼", layout="wide", initial_sidebar_state="expanded")

# Injection CSS pour bloquer la mise en page large permanente sans sauter
st.markdown(
    """
    <style>
        .block-container {
            max-width: 100% !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# 📥 INITIALISATION DES VARIABLES DE SESSION (Optimisée)
cles_session = [
    "tab_finance", "tab_capital", "tab_primes", "tab_frais", 
    "tab_projets_achat_loc", "tab_projets_construction", "tab_projets_embellissement"
]
for cle in cles_session:
    if cle not in st.session_state:
        st.session_state[cle] = ""

if "nom_bien_promo" not in st.session_state: st.session_state["nom_bien_promo"] = ""
if "taux_reduction_promo" not in st.session_state: st.session_state["taux_reduction_promo"] = 0
if "holding_chargee" not in st.session_state: st.session_state["holding_chargee"] = False
if "projets_charges" not in st.session_state: st.session_state["projets_charges"] = False


# =========================================================================
# 🏠 2. BLOC DE LA PAGE D'ACCUEIL PRINCIPALE
# =========================================================================
def home_page():
    st.title("🏛️ Centre de Contrôle de l'Empire — Monde 8")
    st.write(f"Bienvenue, **Grego73** ! Votre calculateur s'exécute avec les données du Cloud.")
    
    # --- 📈 BLOC GRAPHIQUE HISTORIQUE DES MATÉRIAUX ---
    st.subheader("📊 Évolution du Cours des Matériaux")
    
    with st.spinner("Chargement du graphique des cours..."):
        df_historique_mat = recuperer_historique_materiaux()
    
    if df_historique_mat is not None and not df_historique_mat.empty:
        df_pivot = df_historique_mat.pivot_table(
            index="Date", 
            columns="Matériau", 
            values="Prix", 
            sort=False 
        )
        st.line_chart(df_pivot, use_container_width=True)
        st.caption("💡 Astuce : Survolez les courbes avec votre souris pour voir les prix exacts à chaque heure d'extraction.")
    else:
        st.info("⚪ Aucun historique de prix disponible pour le moment. Le graphique apparaîtra dès que le robot aura effectué plusieurs synchronisations.")

    st.markdown("---")
    st.subheader("👑 Tableau de Bord de votre Personnage")
    PSEUDO_JOUEUR = "Grego73"
    df_players_actuel = recuperer_derniere_donnee_table("players")
    df_historique_joueur = recuperer_historique_joueur(PSEUDO_JOUEUR)
    
    if df_players_actuel is not None and not df_players_actuel.empty:
        infos_joueur = df_players_actuel[df_players_actuel["pseudo"].str.upper() == PSEUDO_JOUEUR.upper()]
        if not infos_joueur.empty:
            row_j = infos_joueur.iloc[0]
            m1, m2, m3 = st.columns(3)
            with m1: st.metric(label="🏆 Classement Général", value=f"{row_j['classement']}e place")
            with m2: st.metric(label="⭐ Niveau Actuel", value=f"Niveau {row_j['niveau']}")
            with m3: st.metric(label="🎯 Score (Points)", value=formater_monnaie_empire(row_j['points']))
            st.caption(f"📅 *Dernière synchronisation automatique : {row_j['date_extraction']}*")
            
        if df_historique_joueur is not None and len(df_historique_joueur) > 1:
            with st.expander("📈 Visualiser la courbe de progression", expanded=False):
                df_historique_joueur["Date"] = pd.to_datetime(df_historique_joueur["date_extraction"]).dt.strftime("%d/%m %H:%M")
                st.line_chart(data=df_historique_joueur, x="Date", y="points", use_container_width=True)
    else:
        st.info("📥 En attente de la première synchronisation Firebase depuis l'Espace Admin.")

    st.markdown("---")
    st.subheader("✍️ Saisie manuelle Holding & Rapports comptables")
    
    st.session_state["tab_finance"] = st.text_area("Tableau FINANCE :", value=st.session_state["tab_finance"], height=120)
    st.session_state["tab_capital"] = st.text_area("Tableau CAPITAL :", value=st.session_state["tab_capital"], height=120)
    st.session_state["tab_primes"] = st.text_area("Tableau DIRECTEURS / PLAFONDS PRIMES :", value=st.session_state["tab_primes"], height=120)
    st.session_state["tab_frais"] = st.text_area("Tableau FRAIS DE GESTION :", value=st.session_state["tab_frais"], height=120)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Synchroniser uniquement la Holding", use_container_width=True):
            if not st.session_state["tab_finance"].strip():
                st.error("❌ Le tableau Finance est requis.")
            else:
                st.session_state["holding_chargee"] = True
                st.success("🎉 Pôle Holding synchronisé !")
    with col2:
        if st.button("🗑️ Vider les données Holding", use_container_width=True):
            st.session_state["tab_finance"] = ""
            st.session_state["tab_capital"] = ""
            st.session_state["tab_primes"] = ""
            st.session_state["tab_frais"] = ""
            st.session_state["holding_chargee"] = False
            st.rerun()

    st.markdown("---")
    st.subheader("🔍 Outil de Contrôle : Audit d'une filiale")
    rapport_audit = st.text_area("Collez le rapport de la filiale ici :", height=150, key="audit_input")
    
    if st.button("👁️ Auditer les chiffres de la filiale", use_container_width=True):
        if not rapport_audit.strip():
            st.error("❌ Veuillez coller un rapport.")
        else:
            erreurs, data = verifier_concordance_rapport(rapport_audit)
            if erreurs:
                st.error("🚨 CONCORDANCE INCORRECTE !")
                for err in erreurs: st.warning(err)
            else:
                st.success("✅ CONCORDANCE PARFAITE !")
                col1_aud, col2_aud = st.columns(2)
                with col1_aud: st.write(f"• Résultat NET : `{formater_monnaie_empire(data.get('net', 0))}`")
                with col2_aud: st.write(f"• Total Actif/Passif : `{formater_monnaie_empire(data.get('actif', 0))}`")


# =========================================================================
# ⚙️ 3. FONCTION DE SÉCURITÉ DE VÉRIFICATION DES FICHIERS (ANTI-CRASH)
# =========================================================================
def securiser_page(chemin, title, icon):
    if os.path.exists(chemin):
        return st.Page(chemin, title=title, icon=icon)
    return None


# =========================================================================
# 🧭 4. CARTOGRAPHIE DYNAMIQUE DU MOTEUR DE NAVIGATION
# =========================================================================

# Déclaration sécurisée de l'accueil
page_home = st.Page(home_page, title="Accueil & Saisie Unique", icon="🏠", default=True)

# Pôle Holding & Comptabilité
list_holding = [
    securiser_page("pages/01_frais_gestion.py", "Frais de Gestion", "📊"),
    securiser_page("pages/02_primes.py", "Gestion des Primes", "💰"),
    securiser_page("pages/03_performance.py", "Analyse de Performance", "📈"),
    securiser_page("pages/04_equilibrage.py", "Équilibrage & Injection", "⚖️")
]
menu_holding = [p for p in list_holding if p is not None]

# Pôle Bancaire Fédéral (Découpage autonome)
list_banque = [
    securiser_page("pages/10_banque_cascade_livrets.py", "🔒 Cascade Livrets I", "⚔️"),
    securiser_page("pages/11_banque_cascade_comptes.py", "📈 Cascade Comptes Épargnes", "⚖️"),
    securiser_page("pages/12_banque_epargne.py", "💵 Épargne Progressive", "📊"),
    securiser_page("pages/13_banque_credits.py", "🏦 Emprunts & Crédits", "📉")
]
menu_banque = [p for p in list_banque if p is not None]

# Pôle Calculs de Rentabilité
list_renta = [
    securiser_page("pages/05_analyse_locative.py", "Analyse Locative & R.O.I", "📋"),
    securiser_page("pages/06_chantiers_et_embellissement.py", "Chantiers & Embellissement", "🏗️"),
    securiser_page("pages/07_synthese_opportunites.py", "🌟 Top Opportunités", "✨")
]
menu_renta = [p for p in list_renta if p is not None]

# Administration & Crons
list_admin = [
    securiser_page("pages/08_admin.py", "Espace Administration", "🛠️"),
    securiser_page("pages/09_cron_trigger_taux.py", "Déclencheur Crons", "⚙️")
]
menu_admin = [p for p in list_admin if p is not None]

# Assemblage final du dictionnaire de navigation
navigation_dict = {"Accueil": [page_home]}
if menu_holding: navigation_dict["🏛️ Gestion Holding"] = menu_holding
if menu_banque: navigation_dict["🏦 Pôle Bancaire Fédéral"] = menu_banque
if menu_renta: navigation_dict["Calculs de Rentabilité"] = menu_renta
if menu_admin: navigation_dict["Administration"] = menu_admin

# Exécution officielle sans possibilité de plantage
pg = st.navigation(navigation_dict)
pg.run()
