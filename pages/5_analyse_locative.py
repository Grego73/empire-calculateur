import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre, recuperer_derniere_donnee_table

st.title("📊 Analyse Locative & Rendements (Données Firebase Cloud)")

# 1. Récupération des données depuis le Cloud Firestore
df_batiments = recuperer_derniere_donnee_table("batiments")
df_config = recuperer_derniere_donnee_table("configuration")

if df_batiments is None or df_batiments.empty:
    st.error("🚨 Aucune donnée de bâtiment trouvée dans le Cloud Firebase. Exécutez le Cron d'abord depuis l'Espace Admin.")
else:
    # 2. Lecture sécurisée du Taux Promoteur global
    taux_promoteur = 0
    if df_config is not None and not df_config.empty:
        try:
            df_config_triee = df_config.sort_values(by="date_extraction", ascending=False)
            taux_promoteur = int(df_config_triee.iloc[0].get("taux_promoteur", 0))
        except Exception:
            taux_promoteur = 0
    
    st.caption(f"☁️ Source : Google Cloud Firestore | Dernière Synchro : `{df_batiments['date_extraction'].iloc[0]}`")
    if taux_promoteur > 0:
        st.caption(f"⚙️ Paramètre appliqué : Taux Promoteur Actuel = **{taux_promoteur}%**")

    # Zone de saisie utilisateur pour l'enveloppe d'achat
    saisie_capital = st.text_input("Budget disponible :", value="10G")
    capital_disponible = convertir_saisie_en_nombre(saisie_capital)

    try:
        # 3. Filtrage robuste : On exclut les terrains et parcs
        # On accepte 'entreprise', 'perso' ainsi que les anciennes lignes non taguées par sécurité
        df_biens = df_batiments[
            (~df_batiments["nom"].str.contains("TERRAIN|PARC", case=False, na=False)) &
            (df_batiments["valeur"] > 0)
        ].copy()

        if df_biens.empty:
            st.warning("⚠️ Aucun bâtiment locatif n'a été trouvé après filtrage des terrains.")
        else:
            # 4. Calculs des rentabilités annuelles de l'Empire
            df_biens["rev_net_annuel"] = (df_biens["loyer"] - df_biens["charge"] - df_biens["impot"]) * 12
            df_biens["Rendement Net (%)"] = (df_biens["rev_net_annuel"] / df_biens["valeur"] * 100).fillna(0)
            
            # Calcul des volumes d'achats maximaux possibles
            df_biens["Quantité Max Achetée"] = capital_disponible // df_biens["valeur"]
            df_biens["Gain Mensuel Cumulé"] = (df_biens["loyer"] - df_biens["charge"] - df_biens["impot"]) * df_biens["Quantité Max Achetée"]

            # 5. Répartition visuelle par onglets
            tab_ent, tab_perso, tab_tous = st.tabs(["🏢 Bâtiments d'Entreprises", "📦 Bâtiments Personnels", "🌐 Vue Globale"])

            with tab_ent:
                # Filtrage insensible à la casse pour 'entreprise'
                df_ent = df_biens[df_biens["categorie"].astype(str).str.lower() == "entreprise"].copy()
                if df_ent.empty:
                    st.info("⚪ Aucun bâtiment marqué 'entreprise' dans cette extraction. Lancez le nouveau Cron.")
                else:
                    df_ent_visuel = pd.DataFrame({
                        "Description": df_ent["nom"],
                        "Type": df_ent["type"],
                        "Prix d'Achat": df_ent["valeur"].apply(formater_monnaie_empire),
                        "Rendement Net": df_ent["Rendement Net (%)"].apply(lambda x: f"{x:.2f}%"),
                        "Quantité Max": df_ent["Quantité Max Achetée"],
                        "Gain Mensuel Cumulé": df_ent["Gain Mensuel Cumulé"].apply(formater_monnaie_empire),
                        "Renta_Num": df_ent["Rendement Net (%)"]
                    }).sort_values(by="Renta_Num", ascending=False)
                    st.dataframe(df_ent_visuel.drop(columns=["Renta_Num"]), use_container_width=True, hide_index=True)

            with tab_perso:
                # Filtrage insensible à la casse pour 'perso'
                df_perso = df_biens[df_biens["categorie"].astype(str).str.lower() == "perso"].copy()
                if df_perso.empty:
                    st.info("⚪ Aucun bâtiment marqué 'perso' dans cette extraction. Lancez le nouveau Cron.")
                else:
                    df_perso_visuel = pd.DataFrame({
                        "Description": df_perso["nom"],
                        "Type": df_perso["type"],
                        "Prix d'Achat": df_perso["valeur"].apply(formater_monnaie_empire),
                        "Rendement Net": df_perso["Rendement Net (%)"].apply(lambda x: f"{x:.2f}%"),
                        "Quantité Max": df_perso["Quantité Max Achetée"],
                        "Gain Mensuel Cumulé": df_perso["Gain Mensuel Cumulé"].apply(formater_monnaie_empire),
                        "Renta_Num": df_perso["Rendement Net (%)"]
                    }).sort_values(by="Renta_Num", ascending=False)
                    st.dataframe(df_perso_visuel.drop(columns=["Renta_Num"]), use_container_width=True, hide_index=True)

            with tab_tous:
                # Vue historique ou de secours regroupant l'intégralité du parc immobilier
                df_tous_visuel = pd.DataFrame({
                    "Description": df_biens["nom"],
                    "Catégorie": df_biens["categorie"].fillna("Non classé"),
                    "Prix d'Achat": df_biens["valeur"].apply(formater_monnaie_empire),
                    "Rendement Net": df_biens["Rendement Net (%)"].apply(lambda x: f"{x:.2f}%"),
                    "Quantité Max": df_biens["Quantité Max Achetée"],
                    "Gain Mensuel Cumulé": df_biens["Gain Mensuel Cumulé"].apply(formater_monnaie_empire),
                    "Renta_Num": df_biens["Rendement Net (%)"]
                }).sort_values(by="Renta_Num", ascending=False)
                st.dataframe(df_tous_visuel.drop(columns=["Renta_Num"]), use_container_width=True, hide_index=True)

    except Exception as e: 
        st.error(f"⚠️ Erreur lors de l'exécution des calculs locatifs : {e}")
