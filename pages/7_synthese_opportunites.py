import streamlit as st
import pandas as pd
from datetime import datetime
from utils import (
    formater_monnaie_empire, 
    recuperer_derniere_donnee_table,
    recuperer_derniers_taux_configuration,
    db  # Import direct pour requêter l'historique des taux
)

# 📋 CONFIGURATION DU TITRE DE LA PAGE
st.title("✨ Opportunités du Jour — Biens en Promo")
st.markdown("Consultez immédiatement l'ensemble des infrastructures en promotion et l'évolution historique des taux du promoteur.")

# 1. Chargement des tables Firebase Cloud Firestore
with st.spinner("Analyse des flux NoSQL Firestore..."):
    df_batiments = recuperer_derniere_donnee_table("batiments")
    config_taux = recuperer_derniers_taux_configuration()

taux_batiments_actuel = config_taux.get("batiments", 0)
taux_materiaux_actuel = config_taux.get("materiaux", 0)

# =========================================================
# 🧮 EXTRACTION DIRECTE ET CALCULS COMPTABLES INVERSÉS
# =========================================================
if df_batiments is None or df_batiments.empty:
    st.error("🚨 Base de données des bâtiments indisponible ou vide.")
else:
    try:
        if "promotion" in df_batiments.columns:
            df_batiments["promotion"] = pd.to_numeric(df_batiments["promotion"], errors='coerce').fillna(0).astype(int)
        else:
            df_batiments["promotion"] = 0

        df_promos_actives = df_batiments[df_batiments["promotion"] > 0].copy()

        if df_promos_actives.empty:
            st.info("⚪ Aucun bâtiment ne possède de promotion supérieure à 0% dans la base de données actuellement.")
        else:
            liste_opportunites = []
            for _, r in df_promos_actives.iterrows():
                nom_bien = r.get("nom", "Infrastructure")
                cat_bien = str(r.get("categorie", "perso")).strip().lower()
                taux_promo_bien = int(r.get("promotion", 0))
                prix_apres_remise = int(r.get("valeur", 0))
                
                if 0 < taux_promo_bien < 100:
                    valeur_initiale_brute = int(prix_apres_remise / (1 - (taux_promo_bien / 100)))
                    montant_economise = max(0, valeur_initiale_brute - prix_apres_remise)
                else:
                    valeur_initiale_brute = prix_apres_remise
                    montant_economise = 0

                liste_opportunites.append({
                    "Infrastructure": nom_bien,
                    "Type": r.get("type", "Non défini"),
                    "Niveau": f"Niv. {r.get('niveau', 1)}",
                    "Prix Initial": formater_monnaie_empire(valeur_initiale_brute),
                    "Promo": f"-{taux_promo_bien}%",
                    "Prix Après Remise Num": prix_apres_remise,
                    "Prix En Jeu": formater_monnaie_empire(prix_apres_remise),
                    "Économie": formater_monnaie_empire(montant_economise),
                    "Catégorie": cat_bien
                })

            df_opportunites_final = pd.DataFrame(liste_opportunites)
            df_ong_entreprise = df_opportunites_final[df_opportunites_final["Catégorie"] == "entreprise"].sort_values(by="Prix Après Remise Num")
            df_ong_perso = df_opportunites_final[df_opportunites_final["Catégorie"] == "perso"].sort_values(by="Prix Après Remise Num")

            colonnes_affichage = ["Infrastructure", "Type", "Niveau", "Prix Initial", "Promo", "Prix En Jeu", "Économie"]

            st.subheader("🏢 Bâtiments d'Entreprises en Promotion")
            if df_ong_entreprise.empty:
                st.info("⚪ Aucun bâtiment d'entreprise avec une promotion active (>0%) n'a été détecté.")
            else:
                st.dataframe(df_ong_entreprise[colonnes_affichage], use_container_width=True, hide_index=True)

            st.markdown("---")

            st.subheader("📦 Bâtiments Personnels en Promotion")
            if df_ong_perso.empty:
                st.info("⚪ Aucun bâtiment personnel avec une promotion active (>0%) n'a été détecté.")
            else:
                st.dataframe(df_ong_perso[colonnes_affichage], use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"⚠️ Erreur lors du traitement comptable : {e}")

# =========================================================
# 📈 EXTRACTEUR NO SQL & SUIVI DES COURBES (DESSUS / DESSOUS)
# =========================================================
st.markdown("---")
st.subheader("🏛️ Suivi Temporel de l'Évolution des Taux")

@st.cache_data(ttl=600)  # Mise en cache 10 minutes pour économiser vos quotas Firestore
def extraire_historique_taux_cloud():
    try:
        # Récupération de l'ensemble des configurations historisées
        docs = db.collection("configuration").stream()
        points_historiques = []
        
        for doc in docs:
            d = doc.to_dict()
            # Ignorer le document maître statique pour ne pas fausser l'historique temporel
            if doc.id == "config_actuelle": 
                continue
                
            extraction_brute = d.get("date_extraction")
            t_bat = d.get("taux_promoteur_batiments")
            t_mat = d.get("taux_promoteur_materiaux")
            
            if extraction_brute and t_bat is not None and t_mat is not None:
                try:
                    dt = datetime.strptime(extraction_brute, "%Y-%m-%d %H:%M:%S")
                    label_date = dt.strftime("%d/%m %H:%M")
                except:
                    label_date = extraction_brute
                    
                points_historiques.append({
                    "Date": label_date,
                    "Date_RAW": extraction_brute,
                    "Taux Bâtiments (%)": int(t_bat),
                    "Taux Matériaux (%)": int(t_mat)
                })
        
        if not points_historiques:
            return None
            
        # Tri chronologique selon la date brute
        df_hist = pd.DataFrame(points_historiques).sort_values(by="Date_RAW")
        return df_hist
    except Exception as e:
        print(f"Erreur historique global taux : {e}")
        return None

with st.spinner("Compilation des courbes historiques..."):
    df_suivi_taux = extraire_historique_taux_cloud()

# Affichage adaptatif des graphiques
if df_suivi_taux is not None and len(df_suivi_taux) > 1:
    
    # 📉 1. COURBE DU HAUT : Taux Bâtiments
    st.markdown(f"📉 **Évolution — Taux Promoteur Bâtiment (Actuel : `{taux_batiments_actuel}%`)**")
    st.line_chart(data=df_suivi_taux, x="Date", y="Taux Bâtiments (%)", color="#FF4B4B", use_container_width=True)
    
    st.markdown("---")
    
    # 📈 2. COURBE DU BAS : Taux Matériaux
    st.markdown(f"📈 **Évolution — Taux Promoteur Matériau / Terrains (Actuel : `{taux_materiaux_actuel}%`)**")
    st.line_chart(data=df_suivi_taux, x="Date", y="Taux Matériaux (%)", color="#00C49F", use_container_width=True)
    
else:
    # Mode secours si l'historique NoSQL ne contient pas assez d'éléments
    st.info("⚪ Historique en cours de constitution. Affichage des taux instantanés actuels.")
    
    st.markdown(f"**Taux Promoteur Bâtiment : `{taux_batiments_actuel}%`**")
    df_jauge_bat = pd.DataFrame({"Taux (%)": [taux_batiments_actuel]}, index=["Bâtiment"])
    st.bar_chart(df_jauge_bat, y_label="Pourcentage", color="#FF4B4B", use_container_width=True)
    
    st.markdown("---")
    
    st.markdown(f"**Taux Promoteur Matériau (Terrains) : `{taux_materiaux_actuel}%`**")
    df_jauge_mat = pd.DataFrame({"Taux (%)": [taux_materiaux_actuel]}, index=["Matériau"])
    st.bar_chart(df_jauge_mat, y_label="Pourcentage", color="#00C49F", use_container_width=True)
