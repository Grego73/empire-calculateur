import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, recuperer_derniere_donnee_table

# 📋 DÉCORATION ET NOMMAGE DE LA PAGE
st.title("✨ Opportunités du Jour — Biens en Promo")
st.markdown("Identification exclusive des infrastructures profitant d'une réduction active relevée en base de données.")

# 1. Chargement des tables Firebase Cloud Firestore
with st.spinner("Analyse des flux NoSQL Firestore..."):
    df_batiments = recuperer_derniere_donnee_table("batiments")
    df_materiaux = recuperer_derniere_donnee_table("materials") if "materials" in st.session_state else recuperer_derniere_donnee_table("materiaux")
    df_config = recuperer_derniere_donnee_table("configuration")

# Initialisation du taux de matériau de la configuration générale (pour les terrains)
taux_materiaux = 0
if df_config is not None and not df_config.empty:
    ligne_config = df_config.iloc[0]
    taux_materiaux = int(ligne_config.get("taux_promoteur_materials", ligne_config.get("taux_promoteur_materiaux", 0)))

# =========================================================
# 📊 SECTION VISUELLE : SUIVI DU TAUX MATÉRIAU GLOBAL
# =========================================================
st.subheader("🏛️ État du Taux Promoteur Global")
st.markdown(f"**Taux Promoteur Matériau (Terrains) : `{taux_materiaux}%`**")
st.bar_chart(pd.DataFrame({"Taux (%)": [taux_materiaux]}, index=["Matériau"]), y_label="Pourcentage", color="#00C49F", use_container_width=True)

st.markdown("---")

# =========================================================
# 🧮 EXTRACTION DIRECTE ET FILTRAGE DES PROMOTIONS FIRESTORE
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

        # 🚨 FILTRE MAJEUR : On retient uniquement les bâtiments ayant une promotion STRICTEMENT SUPÉRIEURE À ZERO
        df_promos_actives = df_batiments[df_batiments["promotion"] > 0].copy()

        if df_promos_actives.empty:
            st.info("⚪ Aucun bâtiment ne possède de promotion supérieure à 0% dans la base de données à cette heure.")
        else:
            # Table de correspondance pour le calcul optionnel du terrain remisé si nécessaire
            dict_materiaux = {}
            if df_materiaux is not None and not df_materiaux.empty:
                col_nom_mat = "nom" if "nom" in df_materiaux.columns else "name"
                col_prix_mat = "prix" if "prix" in df_materiaux.columns else "price"
                dict_materiaux = dict(zip(df_materiaux[col_nom_mat].str.upper(), df_materiaux[col_prix_mat]))

            liste_opportunites = []

            for _, r in df_promos_actives.iterrows():
                nom_bien = r.get("nom", "Infrastructure")
                cat_bien = str(r.get("categorie", "perso")).strip().lower()
                valeur_brute = int(r.get("valeur", 0))
                taux_promo_bien = int(r.get("promotion", 0))
                
                # Le champ 'construction' ou 'valeur' sert de pivot pour le calcul financier final
                base_calcul = int(r.get("construction", valeur_brute))
                
                # Application de la réduction individuelle du bâtiment enregistrée dans Firestore
                montant_remise = int(base_calcul * (taux_promo_bien / 100))
                prix_final_remise = max(0, base_calcul - montant_remise)

                liste_opportunites.append({
                    "Infrastructure": nom_bien,
                    "Type": r.get("type", "Non défini"),
                    "Niveau": f"Niv. {r.get('niveau', 1)}",
                    "Valeur Initiale": formater_monnaie_empire(base_calcul),
                    "Promotion": f"-{taux_promo_bien}%",
                    "Prix Après Remise Num": prix_final_remise,
                    "Prix Après Remise": formater_monnaie_empire(prix_final_remise),
                    "Économie Réalisée": formater_monnaie_empire(montant_remise),
                    "Catégorie": cat_bien
                })

            df_opportunites_final = pd.DataFrame(liste_opportunites)

            # =========================================================
            # 📦 SÉPARATION ÉTANCHE ET RESTITUTION PAR ONGLET
            # =========================================================
            # Tri systématique du moins cher au plus cher pour mettre en avant le podium
            df_ong_entreprise = df_opportunites_final[df_opportunites_final["Catégorie"] == "entreprise"].sort_values(by="Prix Après Remise Num")
            df_ong_perso = df_opportunites_final[df_opportunites_final["Catégorie"] == "perso"].sort_values(by="Prix Après Remise Num")

            tab_ent, tab_perso = st.tabs(["🏢 Bâtiments d'Entreprises en Promotion", "📦 Bâtiments Personnels en Promotion"])

            with tab_ent:
                if df_ong_entreprise.empty:
                    st.info("⚪ Aucun bâtiment d'entreprise avec une promotion active (>0%) n'a été détecté.")
                else:
                    st.success(f"🎯 `{len(df_ong_entreprise)}` bâtiments d'entreprises en promotion trouvés.")
                    colonnes_affichage = ["Infrastructure", "Type", "Niveau", "Valeur Initiale", "Promotion", "Prix Après Remise", "Économie Réalisée"]
                    st.dataframe(df_ong_entreprise[colonnes_affichage], use_container_width=True, hide_index=True)

            with tab_perso:
                if df_ong_perso.empty:
                    st.info("⚪ Aucun bâtiment personnel avec une promotion active (>0%) n'a été détecté.")
                else:
                    st.success(f"🎯 `{len(df_ong_perso)}` bâtiments personnels en promotion trouvés.")
                    colonnes_affichage = ["Infrastructure", "Type", "Niveau", "Valeur Initiale", "Promotion", "Prix Après Remise", "Économie Réalisée"]
                    st.dataframe(df_ong_perso[colonnes_affichage], use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"⚠️ Erreur lors du parsing des attributs NoSQL de promotions : {e}")
