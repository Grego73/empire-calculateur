import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre, recuperer_derniere_donnee_table

st.title("🏗️ Analyse des Chantiers & Arbitrage Cloud")

df_travaux = recuperer_derniere_donnee_table("travaux")
df_batiments = recuperer_derniere_donnee_table("batiments")
df_materiaux = recuperer_derniere_donnee_table("materiaux")

if df_travaux is None or df_batiments is None or df_materiaux is None:
    st.error("🚨 Données Firebase incomplètes.")
else:
    saisie_capital = st.text_input("Enveloppe Chantier :", value="50G")
    capital_disponible = convertir_saisie_en_nombre(saisie_capital)

    try:
        df_const = df_travaux[df_travaux["type_travaux"].str.upper() == "CONSTRUCTION"].copy()
        dict_m = dict(zip(df_materiaux["nom"].str.upper(), df_materiaux["prix"]))
        
        df_const["prix_terrain"] = df_const["terrain_requis"].str.upper().map(dict_m).fillna(0).astype(int)
        df_const["cout_total_construction"] = df_const["cout_estime"] + df_const["prix_terrain"]
        
        dict_b = dict(zip(df_batiments["nom"].str.upper(), df_batiments["valeur"]))
        df_const["prix_achat_marche"] = df_const["building_name"].str.upper().map(dict_b).fillna(0).astype(int)

        df_const["Arbitrage"] = "🏗️ Construire"
        df_const.loc[df_const["cout_total_construction"] >= df_const["prix_achat_marche"], "Arbitrage"] = "🛒 Acheter"

        df_final = pd.DataFrame({
            "Infrastructure": df_const["building_name"],
            "Marché Direct": df_const["prix_achat_marche"].apply(formater_monnaie_empire),
            "Coût Construction": df_const["cout_total_construction"].apply(formater_monnaie_empire),
            "Arbitrage Conseillé": df_const["Arbitrage"]
        })
        st.dataframe(df_final, use_container_width=True, hide_index=True)
    except Exception as e: st.error(f"⚠️ Erreur arbitrage : {e}")
