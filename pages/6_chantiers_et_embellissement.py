import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre, recuperer_derniere_donnee_table

st.title("🏗️ Analyse des Chantiers & Arbitrage (Données SQL)")
st.markdown("Comparez les coûts réels d'auto-construction (devis + matières premières) face aux prix immédiats du marché.")

PLAFOND_MAX_BIENS = 500000000

# 📥 Extraction des trois tables nécessaires depuis SQLite
df_travaux = recuperer_derniere_donnee_table("travaux")
df_batiments = recuperer_derniere_donnee_table("batiments")
df_materiaux = recuperer_derniere_donnee_table("materiaux")

if df_travaux is None or df_batiments is None or df_materiaux is None:
    st.error("🚨 Les données en base sont incomplètes pour exécuter le comparateur de chantiers.")
else:
    st.caption(f"💾 Source : Base de données SQL | Alignement sur la date de synchro : `{df_travaux['date_extraction'].iloc[0]}`")

    st.subheader("💰 1. Capacité d'Investissement de la Holding")
    saisie_capital = st.text_input("Saisissez votre enveloppe budgétaire allouée aux chantiers (ex: 50G, 1T) :", value="50G", key="capital_input_sql_6")
    capital_disponible = convertir_saisie_en_nombre(saisie_capital)
    st.markdown("---")

    try:
        # Filtre de l'API travaux pour ne garder que l'auto-construction d'entreprise
        df_const = df_travaux[df_travaux["type_travaux"].str.upper() == "CONSTRUCTION"].copy()

        # Dictionnaire des prix des terrains (extrait de la table materiaux)
        df_terrains = df_materiaux[df_materiaux["nom"].str.contains("TERRAIN|PARC", case=False, na=False)]
        dict_prix_terrains = dict(zip(df_terrains["nom"].str.upper(), df_terrains["prix"]))

        # Calcul du coût réel indexé de la construction (Chantier + Terrain)
        df_const["prix_terrain"] = df_const["terrain_requis"].str.upper().map(dict_prix_terrains).fillna(0).astype(int)
        df_const["cout_total_construction"] = df_const["cout_estime"] + df_const["prix_terrain"]

        # Cartographie des prix du marché d'achat (depuis la table batiments)
        dict_prix_marche = dict(zip(df_batiments["nom"].str.upper(), df_batiments["valeur"]))
        df_const["prix_achat_marche"] = df_const["building_name"].str.upper().map(dict_prix_marche).fillna(0).astype(int)

        # --- ARBITRAGE DU CONSEIL DE LA HOLDING ---
        df_const["Arbitrage conseillé"] = "🏗️ Construire"
        df_const.loc[df_const["cout_total_construction"] >= df_const["prix_achat_marche"], "Arbitrage conseillé"] = "🛒 Acheter"
        df_const.loc[df_const["prix_achat_marche"] == 0, "Arbitrage conseillé"] = "🏗️ Exclusif Chantier"

        # Simulation volumétrique basée sur l'enveloppe
        df_const["Volume max réalisable"] = capital_disponible // df_const["cout_total_construction"]
        df_const["Volume max réalisable"] = df_const["Volume max réalisable"].clip(upper=PLAFOND_MAX_BIENS)

        # Calcul des plus-values latentes générées par l'opération
        df_const["marge_unitaire"] = df_const["prix_achat_marche"] - df_const["cout_total_construction"]
        df_const["Plus-Value Globale Financée RAW"] = df_const["marge_unitaire"] * df_const["Volume max réalisable"]
        df_const.loc[df_const["prix_achat_marche"] == 0, "Plus-Value Globale Financée RAW"] = 0

        # Organisation du tri final
        df_tri_chantiers = df_const.sort_values(by="Plus-Value Globale Financée RAW", ascending=False)

        # Construction du rendu d'affichage
        df_final_visuel = pd.DataFrame()
        df_final_visuel["Infrastructure"] = df_tri_chantiers["building_name"]
        df_final_visuel["Terrain requis"] = df_tri_chantiers["terrain_requis"]
        df_final_visuel["Achat Marché Direct"] = df_tri_chantiers["prix_achat_marche"].apply(lambda x: formater_monnaie_empire(x) if x > 0 else "N/A")
        df_final_visuel["Coût Auto-Construction"] = df_tri_chantiers["cout_total_construction"].apply(formater_monnaie_empire)
        df_final_visuel["Arbitrage"] = df_tri_chantiers["Arbitrage conseillé"]
        df_final_visuel["Volume réalisable"] = df_tri_chantiers["Volume max réalisable"].apply(lambda x: f"{x:,}".replace(",", " "))
        df_final_visuel["Plus-Value Totale Financée"] = df_tri_chantiers["Plus-Value Globale Financée RAW"].apply(lambda x: formater_monnaie_empire(x) if x > 0 else "N/A")

        st.subheader("📋 Vue d'ensemble comparative des chantiers profitables")
        st.dataframe(df_final_visuel, use_container_width=True, hide_index=True)

        if not df_tri_chantiers.empty and df_tri_chantiers.iloc[0]["Plus-Value Globale Financée RAW"] > 0:
            top_chantier = df_tri_chantiers.iloc[0]["building_name"]
            st.success(f"🚀 **Arbitrage validé :** L'opération d'auto-construction la plus rentable avec votre enveloppe actuelle est le lancement de chantiers de type **{top_chantier}**.")

    except Exception as e:
        st.error(f"⚠️ Erreur lors du croisement des tables SQL d'infrastructures : {str(e)}")
