import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre, recuperer_derniere_donnee_table

st.title("📊 Analyse Locative & Rendements (Données Firebase Cloud)")

df_batiments = recuperer_derniere_donnee_table("batiments")

if df_batiments is None or df_batiments.empty:
    st.error("🚨 Aucune donnée dans le Cloud Firebase. Exécutez le Cron d'abord.")
else:
    st.caption(f"☁️ Source : Google Cloud Firestore | Synchro : `{df_batiments['date_extraction'].iloc[0]}`")
    saisie_capital = st.text_input("Budget disponible :", value="10G")
    capital_disponible = convertir_saisie_en_nombre(saisie_capital)

    try:
        df_biens = df_batiments[~df_batiments["nom"].str.contains("TERRAIN|PARC", case=False, na=False)].copy()
        df_biens["rev_net_annuel"] = (df_biens["loyer"] - df_biens["charge"] - df_biens["impot"]) * 12
        df_biens["Rendement Net (%)"] = (df_biens["rev_net_annuel"] / df_biens["valeur"] * 100).fillna(0)
        df_biens["Quantité Max Achetée"] = capital_disponible // df_biens["valeur"]
        df_biens["Gain Mensuel Cumulé"] = (df_biens["loyer"] - df_biens["charge"] - df_biens["impot"]) * df_biens["Quantité Max Achetée"]

        df_visuel = pd.DataFrame({
            "Description": df_biens["nom"],
            "Prix d'Achat": df_biens["valeur"].apply(formater_monnaie_empire),
            "Rendement Net": df_biens["Rendement Net (%)"].apply(lambda x: f"{x:.2f}%"),
            "Quantité Max": df_biens["Quantité Max Achetée"],
            "Gain Mensuel Cumulé": df_biens["Gain Mensuel Cumulé"].apply(formater_monnaie_empire)
        }).sort_values(by="Rendement Net", ascending=False)

        st.dataframe(df_visuel, use_container_width=True, hide_index=True)
    except Exception as e: st.error(f"⚠️ Erreur de calcul : {e}")
