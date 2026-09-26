import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre, recuperer_derniere_donnee_table

st.title("📊 Analyse Locative & Rendements (Données SQL)")
st.markdown("Cette analyse se base sur les derniers prix réels de l'Empire récupérés en base de données.")

PLAFOND_MAX_BIENS = 500000000

# 📥 Lecture directe de la table SQL via notre utilitaire centralisé
df_batiments = recuperer_derniere_donnee_table("batiments")

if df_batiments is None or df_batiments.empty:
    st.error("🚨 Aucune donnée disponible en base de données. Veuillez attendre l'exécution du Cron.")
else:
    st.caption(f"💾 Source : Base de données SQL locale | Dernière synchronisation : `{df_batiments['date_extraction'].iloc[0]}`")

    # --- 💵 COMPOSANT DE BUDGET HOLDING ---
    st.subheader("💰 1. Capacité Financière de la Holding")
    saisie_capital = st.text_input("Saisissez votre budget disponible (ex: 500M, 10G, 5.5Z) :", value="10G", key="capital_input_sql_5")
    capital_disponible = convertir_saisie_en_nombre(saisie_capital)
    st.caption(f"ℹ️ Capital interprété par la Holding : **{formater_monnaie_empire(capital_disponible)}**")
    st.markdown("---")

    try:
        # Nettoyage et filtrage des lignes (on exclut les terrains et les parcs)
        df_biens = df_batiments[~df_batiments["nom"].str.contains("TERRAIN|PARC", case=False, na=False)].copy()

        # --- CALCULS VECTORIELS ULTRA-RAPIDES AVEC PANDAS (Zéro boucle for !) ---
        df_biens["rev_net_mensuel"] = df_biens["loyer"] - df_biens["charge"] - df_biens["impot"]
        df_biens["rev_net_annuel"] = df_biens["rev_net_mensuel"] * 12
        
        # Rendement net et ROI
        df_biens["Rendement Net (%)"] = (df_biens["rev_net_annuel"] / df_biens["valeur"] * 100).fillna(0)
        df_biens["R.O.I"] = df_biens["rev_net_annuel"].apply(lambda x: f"{int(df_biens['valeur'].iloc[0] / x)} ans" if x > 0 else "Aucun")

        # Quantité achetable selon votre trésorerie holding
        df_biens["Quantité Max Achetée"] = capital_disponible // df_biens["valeur"]
        df_biens["Quantité Max Achetée"] = df_biens["Quantité Max Achetée"].clip(upper=PLAFOND_MAX_BIENS)
        
        # Facteurs limitants et gains globaux
        df_biens["Facteur Limitant"] = df_biens["Quantité Max Achetée"].apply(lambda x: "⚠️ Bridé par la place (500M)" if x >= PLAFOND_MAX_BIENS else "💵 Limité par votre budget")
        df_biens["Gain Mensuel Cumulé RAW"] = df_biens["rev_net_mensuel"] * df_biens["Quantité Max Achetée"]

        # Tri par le plus gros générateur de cash-flow
        df_tri = df_biens.sort_values(by="Gain Mensuel Cumulé RAW", ascending=False)

        # Préparation d'une vue d'affichage propre pour l'utilisateur
        df_visuel = pd.DataFrame()
        df_visuel["Description"] = df_tri["nom"]
        df_visuel["Prix d'Achat"] = df_tri["valeur"].apply(formater_monnaie_empire)
        df_visuel["Rendement Net (%)"] = df_tri["Rendement Net (%)"].apply(lambda x: f"{x:.2f}%")
        df_visuel["R.O.I"] = df_tri["R.O.I"]
        df_visuel["Quantité Max Achetée"] = df_tri["Quantité Max Achetée"].apply(lambda x: f"{x:,}".replace(",", " "))
        df_visuel["Facteur Limitant"] = df_tri["Facteur Limitant"]
        df_visuel["Gain Mensuel Cumulé"] = df_tri["Gain Mensuel Cumulé RAW"].apply(formater_monnaie_empire)

        # --- RECHERCHE INTERACTIVE ---
        st.subheader("🔍 Filtrer et analyser les infrastructures")
        recherche = st.text_input("Filtrer par mot-clé (ex: Immeuble, Gratte-ciel) :", value="")
        if recherche:
            df_visuel = df_visuel[df_visuel["Description"].str.contains(recherche, case=False, na=False)]

        st.dataframe(df_visuel, use_container_width=True, hide_index=True)

        # Affichage dynamique du gagnant
        if not df_tri.empty and df_tri.iloc[0]["Gain Mensuel Cumulé RAW"] > 0:
            top_nom = df_tri.iloc[0]["nom"]
            top_gain = formater_monnaie_empire(df_tri.iloc[0]["Gain Mensuel Cumulé RAW"])
            st.success(f"👑 **Stratégie Holding Validée :** Le meilleur placement pour votre capital est l'achat massif de **{top_nom}**. Cela générera un flux de trésorerie net de **{top_gain} /mois** pour votre Empire !")

    except Exception as e:
        st.error(f"⚠️ Erreur lors de la compilation des données locatives : {str(e)}")
