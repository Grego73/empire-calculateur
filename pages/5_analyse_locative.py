import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre, recuperer_derniere_donnee_table

st.title("📊 Analyse Locative & Rendements (Données Firebase Cloud)")

# 1. Récupération des tables dans Firestore
df_batiments = recuperer_derniere_donnee_table("batiments")
df_config = recuperer_derniere_donnee_table("configuration")

if df_batiments is None or df_batiments.empty:
    st.error("🚨 Aucune donnée de bâtiment trouvée dans le Cloud Firebase. Exécutez le Cron d'abord depuis l'Espace Admin.")
else:
    # 2. Extraction du taux promoteur de secours ou depuis la configuration
    taux_promoteur = 0
    if df_config is not None and not df_config.empty:
        # On extrait le taux du document le plus récent
        taux_promoteur = df_config.sort_values(by="date_extraction", ascending=False).iloc[0].get("taux_promoteur", 0)
    
    st.caption(f"☁️ Source : Google Cloud Firestore | Dernière Synchro : `{df_batiments['date_extraction'].iloc[0]}`")
    if taux_promoteur > 0:
        st.caption(f"⚙️ Paramètre appliqué : Taux Promoteur Actuel = **{taux_promoteur}%**")

    # Configuration du budget de l'utilisateur
    saisie_capital = st.text_input("Budget disponible :", value="10G")
    capital_disponible = convertir_saisie_en_nombre(saisie_capital)

    try:
        # 3. Filtrage dynamique : On exclut les terrains et les parcs via la nouvelle colonne 'categorie' ou le nom
        # On ne garde que les catégories 'entreprise' et 'perso' qui génèrent des loyers
        df_biens = df_batiments[
            (df_batiments["categorie"].isin(["entreprise", "perso"])) & 
            (~df_batiments["nom"].str.contains("TERRAIN|PARC", case=False, na=False))
        ].copy()

        if df_biens.empty:
            st.warning("⚠️ Aucun bâtiment locatif (entreprise ou perso) trouvé dans les données actuelles.")
        else:
            # 4. Calculs financiers du Monde 8 (Revenus nets sur 12 mois)
            df_biens["rev_net_annuel"] = (df_biens["loyer"] - df_biens["charge"] - df_biens["impot"]) * 12
            df_biens["Rendement Net (%)"] = (df_biens["rev_net_annuel"] / df_biens["valeur"] * 100).fillna(0)
            
            # Gestion des divisions par zéro si la valeur d'un bien est corrompue
            df_biens["Quantité Max Achetée"] = df_biens.apply(
                lambda r: capital_disponible // r["valeur"] if r["valeur"] > 0 else 0, axis=1
            )
            df_biens["Gain Mensuel Cumulé"] = (df_biens["loyer"] - df_biens["charge"] - df_biens["impot"]) * df_biens["Quantité Max Achetée"]

            # 5. Séparateur par onglets pour isoler la Holding de vos biens personnels
            tab_ent, tab_perso = st.tabs(["🏢 Bâtiments d'Entreprises", "📦 Bâtiments Personnels"])

            with tab_ent:
                df_visual_ent = df_biens[df_biens["categorie"] == "entreprise"].copy()
                if df_visual_ent.empty:
                    st.info("Aucune infrastructure d'entreprise disponible.")
                else:
                    df_ent_clean = pd.DataFrame({
                        "Description": df_visual_ent["nom"],
                        "Type": df_visual_ent["type"],
                        "Prix d'Achat": df_visual_ent["valeur"].apply(formater_monnaie_empire),
                        "Rendement Net": df_visual_ent["Rendement Net (%)"].apply(lambda x: f"{x:.2f}%"),
                        "Quantité Max": df_visual_ent["Quantité Max"],
                        "Gain Mensuel Cumulé": df_visual_ent["Gain Mensuel Cumulé"].apply(formater_monnaie_empire),
                        "Tri_Renta": df_visual_ent["Rendement Net (%)"] # Caché pour le tri
                    }).sort_values(by="Tri_Renta", ascending=False)
                    
                    st.dataframe(df_ent_clean.drop(columns=["Tri_Renta"]), use_container_width=True, hide_index=True)

            with tab_perso:
                df_visual_perso = df_biens[df_biens["categorie"] == "perso"].copy()
                if df_visual_perso.empty:
                    st.info("Aucun bâtiment personnel disponible.")
                else:
                    df_perso_clean = pd.DataFrame({
                        "Description": df_visual_perso["nom"],
                        "Type": df_visual_perso["type"],
                        "Prix d'Achat": df_visual_perso["valeur"].apply(formater_monnaie_empire),
                        "Rendement Net": df_visual_perso["Rendement Net (%)"].apply(lambda x: f"{x:.2f}%"),
                        "Quantité Max": df_visual_perso["Quantité Max"],
                        "Gain Mensuel Cumulé": df_visual_perso["Gain Mensuel Cumulé"].apply(formater_monnaie_empire),
                        "Tri_Renta": df_visual_perso["Rendement Net (%)"]
                    }).sort_values(by="Tri_Renta", ascending=False)
                    
                    st.dataframe(df_perso_clean.drop(columns=["Tri_Renta"]), use_container_width=True, hide_index=True)

    except Exception as e: 
        st.error(f"⚠️ Erreur de calcul algorithmique : {e}")
