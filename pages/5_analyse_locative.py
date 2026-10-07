import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre, recuperer_derniere_donnee_table

st.set_page_config(page_title="Analyse Locative - Monde 8", layout="wide")

st.title("📊 Analyse Locative & Rendements Avancés")
st.markdown("Optimisez vos investissements immobiliers en analysant le ROI réel de vos infrastructures.")

# 1. Chargement des données
df_batiments = recuperer_derniere_donnee_table("batiments")

if df_batiments is None or df_batiments.empty:
    st.error("🚨 Aucune donnée de bâtiment trouvée dans le Cloud Firebase.")
else:
    # Nettoyage et alignement des types complexes
    for col in ["valeur", "loyer", "charge", "impot"]:
        if col in df_batiments.columns:
            df_batiments[col] = pd.to_numeric(df_batiments[col], errors='coerce').fillna(0).astype(int)
        else:
            df_batiments[col] = 0

    if "categorie" not in df_batiments.columns:
        df_batiments["categorie"] = "Non classé"

    # Filtrage des structures non-locatives
    df_biens = df_batiments[
        (~df_batiments["nom"].astype(str).str.contains("TERRAIN|PARC", case=False, na=False)) &
        (df_batiments["valeur"] > 0)
    ].copy()

    # --- CALCULS COMPTABLES AVANCÉS ---
    df_biens["rev_net_mensuel"] = df_biens["loyer"] - df_biens["charge"] - df_biens["impot"]
    df_biens["rev_net_annuel"] = df_biens["rev_net_mensuel"] * 12
    df_biens["Rendement Net (%)"] = (df_biens["rev_net_annuel"] / df_biens["valeur"] * 100).fillna(0)
    
    # Temps de retour sur investissement (Payback Period) en années
    df_biens["ROI_Annees"] = (df_biens["valeur"] / df_biens["rev_net_annuel"]).fillna(float('inf'))

    # --- SECTION DRIVERS / INPUTS ---
    with st.sidebar:
        st.header("⚙️ Paramètres du Budget")
        saisie_capital = st.text_input("Budget disponible (€) :", value="10 G")
        capital_disponible = convertir_saisie_en_nombre(saisie_capital)
        st.caption(f"Interprété : **{formater_monnaie_empire(capital_disponible)}**")
        
        st.header("🎯 Filtres de performance")
        rendement_min = st.slider("Rendement Net Minimum (%)", 0.0, 30.0, 5.0, 0.5)

    df_biens["Quantité Max Achetée"] = (float(capital_disponible) // df_biens["valeur"].astype(float)).fillna(0).astype(int)
    df_biens["Gain Mensuel Cumulé"] = df_biens["rev_net_mensuel"] * df_biens["Quantité Max Achetée"]

    # Filtrage dynamique
    df_filtre = df_biens[df_biens["Rendement Net (%)"] >= rendement_min].copy()

    # --- METRICS EN HAUT DE PAGE (KPIs) ---
    if not df_filtre.empty:
        top_bien = df_filtre.sort_values(by="Rendement Net (%)", ascending=False).iloc[0]
        m1, m2, m3 = st.columns(3)
        with m1: st.metric("🔥 Meilleur Rendement", f"{top_bien['Rendement Net (%)']:.2f}%", top_bien['nom'])
        with m2: st.metric("⏳ Amortissement le plus rapide", f"{top_bien['ROI_Annees']:.1f} ans")
        with m3: st.metric("📦 Infrastructures Disponibles", f"{len(df_filtre)} actifs")
    
    st.markdown("---")

    # --- TABLEAU DE BORD INTERACTIF ---
    def generer_tableau_visuel(dataframe):
        if dataframe.empty:
            st.info("⚪ Aucun actif ne correspond aux filtres actuels.")
            return
        
        df_visuel = pd.DataFrame({
            "Infrastructure": dataframe["nom"],
            "Type": dataframe["type"],
            "Prix d'Achat": dataframe["valeur"].apply(formater_monnaie_empire),
            "Rendement Net": dataframe["Rendement Net (%)"].apply(lambda x: f"{x:.2f}%"),
            "Temps de Retour": dataframe["ROI_Annees"].apply(lambda x: f"{x:.1f} ans" if x != float('inf') else "Infini"),
            "Achat Max possible": dataframe["Quantité Max Achetée"],
            "Cashflow Mensuel Possible": dataframe["Gain Mensuel Cumulé"].apply(formater_monnaie_empire),
            "_renta": dataframe["Rendement Net (%)"]
        }).sort_values(by="_renta", ascending=False)
        
        st.dataframe(df_visuel.drop(columns=["_renta"]), use_container_width=True, hide_index=True)

    # Structuration par catégories sans onglets lourds
    st.subheader("🌐 Vue d'Ensemble du Marché Immo")
    generer_tableau_visuel(df_filtre)

    col_e, col_p = st.columns(2)
    with col_e:
        st.subheader("🏢 Secteur Entreprises")
        generer_tableau_visuel(df_filtre[df_filtre["categorie"].str.lower() == "entreprise"])
    with col_p:
        st.subheader("📦 Secteur Personnel")
        generer_tableau_visuel(df_filtre[df_filtre["categorie"].str.lower() == "perso"])
