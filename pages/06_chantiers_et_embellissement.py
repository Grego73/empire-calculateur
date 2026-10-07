import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre, recuperer_derniere_donnee_table

st.title("🏗️ Arbitrage Financier : Achat Direct vs Construction")
st.markdown("Calculez le coût réel d'opportunité pour optimiser vos flux de trésorerie sur les chantiers.")

df_travaux = recuperer_derniere_donnee_table("travaux")
df_batiments = recuperer_derniere_donnee_table("batiments")
df_materiaux = recuperer_derniere_donnee_table("materiaux")

if df_travaux is None or df_batiments is None or df_materiaux is None:
    st.error("🚨 Données Firebase incomplètes pour effectuer l'arbitrage financier.")
else:
    # Initialisation des dictionnaires de prix
    dict_materiaux = dict(zip(df_materiaux["nom"].str.upper(), df_materiaux["prix"]))
    dict_bat_valeur = dict(zip(df_batiments["nom"].str.upper(), df_batiments["valeur"]))
    dict_bat_loyer_net = dict(zip(df_batiments["nom"].str.upper(), df_batiments["loyer"] - df_batiments["charge"] - df_batiments["impot"]))

    try:
        # Filtrage sur les constructions uniquement
        df_const = df_travaux[df_travaux["type_travaux"].str.upper() == "CONSTRUCTION"].copy()
        
        # Calcul des coûts de structure
        df_const["prix_terrain"] = df_const["terrain_requis"].str.upper().map(dict_materiaux).fillna(0).astype(int)
        df_const["cout_brut_construction"] = df_const["cout_estime"] + df_const["prix_terrain"]
        
        # Mapping avec le marché secondaire
        df_const["prix_achat_marche"] = df_const["building_name"].str.upper().map(dict_bat_valeur).fillna(0).astype(int)
        df_const["loyer_mensuel_perdu"] = df_const["building_name"].str.upper().map(dict_bat_loyer_net).fillna(0).astype(int)
        
        # 🔥 CALCUL DU COÛT D'OPPORTUNITÉ (Loyer perdu pendant la durée des travaux)
        df_const["manque_a_gagner_duree"] = df_const["loyer_mensuel_perdu"] * df_const["duree_mois"]
        df_const["Coût Réel Ajusté"] = df_const["cout_brut_construction"] + df_const["manque_a_gagner_duree"]

        # Formulation de la décision d'arbitrage
        df_const["Arbitrage Économique"] = "🏗️ Construire (Plus rentable)"
        df_const.loc[df_const["Coût Réel Ajusté"] >= df_const["prix_achat_marche"], "Arbitrage Économique"] = "🛒 Acheter Direct (Gain Temps)"

        # Différence financière absolue
        df_const["Économie Réalisée (€)"] = (df_const["prix_achat_marche"] - df_const["Coût Réel Ajusté"]).abs()

        # Construction du DataFrame visuel
        df_arbitrage_final = pd.DataFrame({
            "Infrastructure cible": df_const["building_name"],
            "Durée Travaux": df_const["duree_mois"].apply(lambda x: f"{x} mois"),
            "Achat Clé en main": df_const["prix_achat_marche"].apply(formater_monnaie_empire),
            "Coût Global (Terrain incl.)": df_const["cout_brut_construction"].apply(formater_monnaie_empire),
            "Loyers perdus (Chantier)": df_const["manque_a_gagner_duree"].apply(formater_monnaie_empire),
            "Décision": df_const["Arbitrage Économique"],
            "Écart Financier": df_const["Économie Réalisée (€)"].apply(formater_monnaie_empire)
        })

        st.subheader("📋 Matrice d'Arbitrage Décisionnelle")
        st.dataframe(df_arbitrage_final, use_container_width=True, hide_index=True)
        st.caption("💡 Note : 'Acheter Direct' devient conseillé si les loyers théoriques perdus pendant la construction dépassent l'économie brute du chantier.")

    except Exception as e:
        st.error(f"⚠️ Erreur lors du calcul de la matrice d'arbitrage : {e}")
