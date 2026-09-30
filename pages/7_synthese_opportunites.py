import streamlit as st
import pandas as pd
from utils import (
    formater_monnaie_empire, 
    recuperer_derniere_donnee_table,
    recuperer_derniers_taux_configuration  # Utilisation directe du lecteur optimisé
)

# 📋 CONFIGURATION DU TITRE DE LA PAGE
st.title("✨ Opportunités du Jour — Biens en Promo")
st.markdown("Consultez immédiatement l'ensemble des infrastructures en promotion et l'état des taux du promoteur.")

# 1. Chargement des tables Firebase Cloud Firestore
with st.spinner("Analyse des flux NoSQL Firestore..."):
    df_batiments = recuperer_derniere_donnee_table("batiments")
    # Récupération sécurisée des taux du promoteur depuis la base NoSQL
    config_taux = recuperer_derniers_taux_configuration()

taux_batiments = config_taux.get("batiments", 0)
taux_materiaux = config_taux.get("materiaux", 0)

# =========================================================
# 🧮 EXTRACTION DIRECTE ET CALCULS COMPTABLES INVERSÉS
# =========================================================

if df_batiments is None or df_batiments.empty:
    st.error("🚨 Base de données des bâtiments indisponible ou vide.")
else:
    try:
        # Harmonisation forcée du type de la colonne promotion
        if "promotion" in df_batiments.columns:
            df_batiments["promotion"] = pd.to_numeric(df_batiments["promotion"], errors='coerce').fillna(0).astype(int)
        else:
            df_batiments["promotion"] = 0

        # FILTRE : On retient uniquement les bâtiments ayant une promotion active (> 0)
        df_promos_actives = df_batiments[df_batiments["promotion"] > 0].copy()

        if df_promos_actives.empty:
            st.info("⚪ Aucun bâtiment ne possède de promotion supérieure à 0% dans la base de données actuellement.")
        else:
            liste_opportunites = []

            for _, r in df_promos_actives.iterrows():
                nom_bien = r.get("nom", "Infrastructure")
                cat_bien = str(r.get("categorie", "perso")).strip().lower()
                taux_promo_bien = int(r.get("promotion", 0))
                
                # Le champ 'valeur' représente le prix après remise (déjà remisé dans le jeu)
                prix_apres_remise = int(r.get("valeur", 0))
                
                # CALCUL COMPTABLE INVERSE : Reconstitution du prix initial brut d'origine
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

            # Séparation étanche des jeux de données et tri du moins cher au plus cher
            df_ong_entreprise = df_opportunites_final[df_opportunites_final["Catégorie"] == "entreprise"].sort_values(by="Prix Après Remise Num")
            df_ong_perso = df_opportunites_final[df_opportunites_final["Catégorie"] == "perso"].sort_values(by="Prix Après Remise Num")

            # =========================================================
            # 📋 SECTION DES TABLEAUX EN HAUT DE LA PAGE (AFFICHAGE DIRECT)
            # =========================================================
            colonnes_affichage = ["Infrastructure", "Type", "Niveau", "Prix Initial", "Promo", "Prix En Jeu", "Économie"]

            # 🏢 TABLEAU 1 : ENTREPRISES
            st.subheader("🏢 Bâtiments d'Entreprises en Promotion")
            if df_ong_entreprise.empty:
                st.info("⚪ Aucun bâtiment d'entreprise avec une promotion active (>0%) n'a été détecté.")
            else:
                st.dataframe(df_ong_entreprise[colonnes_affichage], use_container_width=True, hide_index=True)

            st.markdown("---")

            # 📦 TABLEAU 2 : PERSONNELS
            st.subheader("📦 Bâtiments Personnels en Promotion")
            if df_ong_perso.empty:
                st.info("⚪ Aucun bâtiment personnel avec une promotion active (>0%) n'a été détecté.")
            else:
                st.dataframe(df_ong_perso[colonnes_affichage], use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"⚠️ Erreur lors du traitement comptable : {e}")

# =========================================================
# 📊 SECTION DES GRAPHISTES EN BAS DE LA PAGE
# =========================================================
st.markdown("---")
st.subheader("🏛️ État des Taux du Promoteur")

st.markdown(f"**Taux Promoteur Bâtiment : `{taux_batiments}%`**")
df_jauge_bat = pd.DataFrame({"Taux (%)": [taux_batiments]}, index=["Bâtiment"])
st.bar_chart(df_jauge_bat, y_label="Pourcentage", color="#FF4B4B", use_container_width=True)

st.markdown(f"**Taux Promoteur Matériau (Terrains) : `{taux_materiaux}%`**")
df_jauge_mat = pd.DataFrame({"Taux (%)": [taux_materiaux]}, index=["Matériau"])
st.bar_chart(df_jauge_mat, y_label="Pourcentage", color="#00C49F", use_container_width=True)
