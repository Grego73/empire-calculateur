import streamlit as st
import pandas as pd
import datetime
from utils import (
    formater_monnaie_empire, 
    convertir_saisie_en_nombre, 
    recuperer_derniere_donnee_table, 
    recuperer_historique_joueur
)

def home_page():
    st.title("🏛️ Centre de Contrôle de l'Empire — Monde 8")
    
    # =========================================================
    # 📈 MODULE ANALYTIQUE : SUIVI DES JOUEURS & CLASSEMENT
    # =========================================================
    st.subheader("📊 Tableau de Bord de votre Personnage")
    
    PSEUDO_JOUEUR = "Grego73" # Configuré d'après les logs de votre compte
    df_players_actuel = recuperer_derniere_donnee_table("players")
    df_historique = recuperer_historique_joueur(PSEUDO_JOUEUR)
    
    if df_players_actuel is not None and not df_players_actuel.empty:
        # Extraction des données actuelles du joueur
        infos_joueur = df_players_actuel[df_players_actuel["pseudo"].str.upper() == PSEUDO_JOUEUR.upper()]
        
        if not infos_joueur.empty:
            row_j = infos_joueur.iloc[0]
            
            # Affichage des indicateurs clés (Metrics)
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric(label="🏆 Classement Général", value=f"{row_j['classement']}e place")
            with m2:
                st.metric(label="⭐ Niveau Actuel", value=f"Niveau {row_j['niveau']}")
            with m3:
                # Formatage du score avec l'échelle de l'Empire
                score_formate = formater_monnaie_empire(row_j['points'])
                st.metric(label="🎯 Score (Points)", value=score_formate)
                
            st.caption(f"📅 *Dernière synchronisation automatique de l'API : {row_j['date_extraction']}*")
        else:
            st.info(f"👋 Bienvenue ! Le joueur **{PSEUDO_JOUEUR}** n'apparaît pas encore dans la dernière extraction. Attendez le prochain passage du Cron.")
            
        # --- GRAPHIQUE D'ÉVOLUTION DE L'EMPIRE ---
        if df_historique is not None and len(df_historique) > 1:
            with st.expander("📈 Visualiser la courbe de progression de vos points", expanded=False):
                # Nettoyage de la date pour l'affichage du graphique
                df_historique["Date"] = pd.to_datetime(df_historique["date_extraction"]).dt.strftime("%d/%m %H:%M")
                
                # Rendu du graphique natif Streamlit (Points en fonction du temps)
                st.line_chart(data=df_historique, x="Date", y="points", use_container_width=True)
    else:
        st.warning("📥 Aucune donnée analytique en base de données. Assurez-vous que votre script `cron_update_api.py` a été exécuté au moins une fois.")

    st.markdown("---")

    # =========================================================
    # 🏛️ EXTRANT : VOTRE CODE EXISTANT DE SAISIE MANUELLE
    # =========================================================
    st.subheader("✍️ Saisie manuelle Holding & Rapports comptables")
    st.markdown("Collez vos données spécifiques dans les sections ci-dessous pour alimenter vos pages de gestion.")
    
    # --- SECTION 1 : DONNÉES DE LA HOLDING ---
    st.markdown("##### 🏢 Données de Gestion Holding")
    st.session_state["tab_finance"] = st.text_area("Tableau FINANCE :", value=st.session_state["tab_finance"], height=120)
    st.session_state["tab_capital"] = st.text_area("Tableau CAPITAL :", value=st.session_state["tab_capital"], height=120)
    st.session_state["tab_primes"] = st.text_area("Tableau DIRECTEURS / PLAFONDS PRIMES :", value=st.session_state["tab_primes"], height=120)
    st.session_state["tab_frais"] = st.text_area("Tableau FRAIS DE GESTION (De la veille) :", value=st.session_state["tab_frais"], height=120)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Synchroniser uniquement la Holding", use_container_width=True):
            if not st.session_state["tab_finance"].strip():
                st.error("❌ Le tableau Finance est requis pour lancer la Holding.")
            else:
                st.session_state["holding_chargee"] = True
                st.success("🎉 Pôle Holding synchronisé et prêt !")
    with col2:
        if st.button("🗑️ Vider les données Holding", use_container_width=True):
            st.session_state["tab_finance"] = ""
            st.session_state["tab_capital"] = ""
            st.session_state["tab_primes"] = ""
            st.session_state["tab_frais"] = ""
            st.session_state["holding_chargee"] = False
            st.rerun()
    
    st.markdown("---")
    
    # --- SECTION 2 : PROMOTIONS DU JOUR MANUELLES (Si nécessaire) ---
    st.markdown("##### 🏷️ Option Promotion temporaire du Marché")
    p_col1, p_col2 = st.columns(2)
    with p_col1:
        st.session_state["nom_bien_promo"] = st.text_input("Rechercher le mot-clé du bien en promo (ex: Mégapôle, Bureaux) :", value=st.session_state["nom_bien_promo"])
    with p_col2:
        st.session_state["taux_reduction_promo"] = st.number_input("Pourcentage de réduction appliqué dans le jeu (%) :", min_value=0, max_value=99, value=st.session_state["taux_reduction_promo"], step=5)

    st.markdown(" ")
    st.session_state["tab_projets_construction"] = st.text_area("6. Fiches CONSTRUCTION :", value=st.session_state["tab_projets_construction"], height=120)
    st.session_state["tab_projets_embellissement"] = st.text_area("7. Fiches EMBELLISSEMENT :", value=st.session_state["tab_projets_embellissement"], height=120)
    
    col3, col4 = st.columns(2)
    with col3:
        if st.button("🚀 Synchroniser uniquement les Projets", use_container_width=True):
            if not st.session_state["tab_projets_achat_loc"].strip() and not st.session_state["tab_projets_construction"].strip():
                st.error("❌ Veuillez remplir au moins une fiche de projet pour synchroniser.")
            else:
                st.session_state["projets_charges"] = True
                st.success("🎉 Pôle Projets & Rentabilité synchronisé et prêt !")
    with col4:
        if st.button("🗑️ Vider les fiches Projets", use_container_width=True):
            st.session_state["tab_projets_achat_loc"] = ""
            st.session_state["tab_projets_construction"] = ""
            st.session_state["tab_projets_embellissement"] = ""
            st.session_state["nom_bien_promo"] = ""
            st.session_state["taux_reduction_promo"] = 0
            st.session_state["projets_charges"] = False
            st.rerun()
    
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
                col1_aud, col2_aud = st.columns(2)
                with col1_aud:
                    st.write(f"• Résultat NET : `{formater_monnaie_empire(data.get('net', 0))}`")
                with col2_aud:
                    st.write(f"• Total Actif/Passif : `{formater_monnaie_empire(data.get('actif', 0))}`")


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
page_synthese = st.Page("pages/7_synthese_opportunites.py", title="🏆 Top Opportunités", icon="✨")

# 🗺️ CONFIGURATION DE LA NAVIGATION ET DU MENU PAR CATÉGORIES
pg = st.navigation({
    "Accueil": [page_home],
    "🏛️ Gestion Holding": [page_frais, page_primes, page_perf, page_equilibre],
    "🏗️ Calculs de Rentabilité": [page_renta_const, page_renta_reno, page_synthese]
})

# Lancement de l'application
pg.run()
