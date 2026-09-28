import streamlit as st
import pandas as pd
import os
import sys
from utils import (
    formater_monnaie_empire, 
    recuperer_derniere_donnee_table, 
    recuperer_historique_joueur,
    recuperer_historique_materiaux 
)


# 🚀 INTERCEPTION DU CRON JOB SUR L'ACCUEIL
parametres = st.query_params

if "page" in parametres and parametres["page"] == "webhook_cron":
    if "token" in parametres and parametres["token"] == "MonCodeSecret2026":
        # On force la configuration minimale
        st.set_page_config(page_title="Cron Trigger", layout="centered")
        st.title("🔄 Déclencheur automatique d'API")
        
        # Déclenchement du script
        sys.path.append(os.path.abspath(os.path.dirname(__file__)))
        try:
            from crons.cron_update_api import executer_mise_a_jour_cron
            with st.spinner("Synchronisation Cloud Firestore en cours..."):
                logs = executer_mise_a_jour_cron()
            st.success("✅ Données synchronisées automatiquement avec succès !")
            st.code("\n".join(logs), language="text")
        except Exception as e:
            st.error(f"Erreur lors de la synchronisation : {e}")
        st.stop() # Arrête le chargement du reste de l'application pour le robot


# ⚙️ CONFIGURATION GLOBALE (Doit être la toute première commande)
st.set_page_config(page_title="Calculateur Empire", page_icon="💼", layout="centered")

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


def home_page():
    st.title("🏛️ Empire Calculateur — Tableau de Bord")
    st.write(f"Bienvenue, **Grego73** ! Votre calculateur automatique s'exécute en arrière-plan.")
    
    # --- 📈 BLOC GRAPHIQUE HISTORIQUE DES MATÉRIAUX ---
    st.subheader("📊 Évolution du Cours des Matériaux (Monde 8)")
    
    with st.spinner("Chargement du graphique des cours..."):
        # Appel de la fonction créée dans utils.py
        df_historique = recuperer_historique_materiaux()
    
    if df_historique is not None and not df_historique.empty:
        # 🔄 Pivot des données pour avoir une colonne par matériau (Béton, Acier, Bois...)
        # Cela permet à Streamlit de tracer automatiquement une ligne de couleur différente par ressource
        df_pivot = df_historique.pivot_table(
            index="Date", 
            columns="Matériau", 
            values="Prix ($)",
            sort=False # Conserve l'ordre chronologique du tri précédent
        )
        
        # Affichage du graphique linéaire interactif
        st.line_chart(df_pivot, width='stretch')
        
        # Petit indicateur visuel en bonus
        st.caption("💡 Astuce : Survolez les courbes avec votre souris pour voir les prix exacts à chaque heure d'extraction.")
    else:
        st.info("⚪ Aucun historique de prix disponible pour le moment. Le graphique apparaîtra dès que le robot aura effectué plusieurs synchronisations.")

    
    st.title("🏛️ Centre de Contrôle de l'Empire — Monde 8")
    
    st.subheader("📊 Tableau de Bord de votre Personnage")
    PSEUDO_JOUEUR = "Grego73"
    df_players_actuel = recuperer_derniere_donnee_table("players")
    df_historique = recuperer_historique_joueur(PSEUDO_JOUEUR)
    
    if df_players_actuel is not None and not df_players_actuel.empty:
        infos_joueur = df_players_actuel[df_players_actuel["pseudo"].str.upper() == PSEUDO_JOUEUR.upper()]
        if not infos_joueur.empty:
            row_j = infos_joueur.iloc[0]
            m1, m2, m3 = st.columns(3)
            with m1: st.metric(label="🏆 Classement Général", value=f"{row_j['classement']}e place")
            with m2: st.metric(label="⭐ Niveau Actuel", value=f"Niveau {row_j['niveau']}")
            with m3: st.metric(label="🎯 Score (Points)", value=formater_monnaie_empire(row_j['points']))
            st.caption(f"📅 *Dernière synchronisation automatique : {row_j['date_extraction']}*")
            
        if df_historique is not None and len(df_historique) > 1:
            with st.expander("📈 Visualiser la courbe de progression", expanded=False):
                df_historique["Date"] = pd.to_datetime(df_historique["date_extraction"]).dt.strftime("%d/%m %H:%M")
                st.line_chart(data=df_historique, x="Date", y="points", use_container_width=True)
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
            from utils import verifier_concordance_rapport
            erreurs, data = verifier_concordance_rapport(rapport_audit)
            if erreurs:
                st.error("🚨 CONCORDANCE INCORRECTE !")
                for err in erreurs: st.warning(err)
            else:
                st.success("✅ CONCORDANCE PARFAITE !")
                col1_aud, col2_aud = st.columns(2)
                with col1_aud: st.write(f"• Résultat NET : `{formater_monnaie_empire(data.get('net', 0))}`")
                with col2_aud: st.write(f"• Total Actif/Passif : `{formater_monnaie_empire(data.get('actif', 0))}`")

# DÉCLARATION DES PAGES NATIVES
page_home = st.Page(lambda: home_page(), title="📥 Accueil & Saisie Unique", icon="🏠")
page_frais = st.Page("pages/1_frais_gestion.py", title="Frais de Gestion", icon="📉")
page_primes = st.Page("pages/2_primes.py", title="Gestion des Primes", icon="💰")
page_perf = st.Page("pages/3_performance.py", title="Analyse de Performance", icon="📊")
page_equilibre = st.Page("pages/4_equilibrage.py", title="Équilibrage & Injection", icon="⚖️")
page_renta_const = st.Page("pages/5_analyse_locative.py", title="Analyse Locative & R.O.I", icon="📊")
page_renta_reno = st.Page("pages/6_chantiers_et_embellissement.py", title="Chantiers & Embellissement", icon="🏗️")
page_synthese = st.Page("pages/7_synthese_opportunites.py", title="🏆 Top Opportunités", icon="✨")
page_admin = st.Page("pages/8_admin.py", title="⚙️ Espace Administration", icon="🛠️")

pg = st.navigation({
    "Accueil": [page_home],
    "🏛️ Gestion Holding": [page_frais, page_primes, page_perf, page_equilibre],
    "🏗️ Calculs de Rentabilité": [page_renta_const, page_renta_reno, page_synthese],
    "🛠️ Administration": [page_admin]
})
pg.run()
