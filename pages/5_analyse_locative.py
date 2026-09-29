import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre, recuperer_derniere_donnee_table

st.title("📊 Analyse Locative & Rendements (Données Firebase Cloud)")

df_batiments = recuperer_derniere_donnee_table("batiments")

if df_batiments is None or df_batiments.empty:
    try:
        from utils import db
        docs_secours = db.collection("batiments").limit(250).stream()
        liste_secours = [doc.to_dict() for doc in docs_secours]
        if liste_secours:
            df_batiments = pd.DataFrame(liste_secours)
    except Exception:
        df_batiments = None

if df_batiments is None or df_batiments.empty:
    st.error("🚨 Aucune donnée de bâtiment trouvée dans le Cloud Firebase. Exécutez le Cron d'abord depuis l'Espace Admin.")
else:
    st.caption(f"☁️ Source : Google Cloud Firestore | Éléments détectés : `{len(df_batiments)} bâtiments`")

    saisie_capital = st.text_input("Budget disponible :", value="10G")
    capital_disponible = convertir_saisie_en_nombre(saisie_capital)

    try:
        for col in ["valeur", "loyer", "charge", "impot"]:
            if col in df_batiments.columns:
                df_batiments[col] = pd.to_numeric(df_batiments[col], errors='coerce').fillna(0).astype(int)
            else:
                df_batiments[col] = 0

        if "categorie" not in df_batiments.columns:
            df_batiments["categorie"] = "Non classé"

        df_biens = df_batiments[
            (~df_batiments["nom"].astype(str).str.contains("TERRAIN|PARC", case=False, na=False)) &
            (df_batiments["valeur"] > 0)
        ].copy()

        if df_biens.empty:
            st.warning("⚠️ Aucun bâtiment locatif n'a été trouvé après filtrage des terrains.")
        else:
            df_biens["rev_net_annuel"] = (df_biens["loyer"] - df_biens["charge"] - df_biens["impot"]) * 12
            df_biens["Rendement Net (%)"] = (df_biens["rev_net_annuel"] / df_biens["valeur"] * 100).fillna(0)
            df_biens["Quantité Max Achetée"] = capital_disponible // df_biens["valeur"]
            df_biens["Gain Mensuel Cumulé"] = (df_biens["loyer"] - df_biens["charge"] - df_biens["impot"]) * df_biens["Quantité Max Achetée"]

            tab_tous, tab_ent, tab_perso = st.tabs(["🌐 Vue Globale (Monde 8)", "🏢 Bâtiments d'Entreprises", "📦 Bâtiments Personnels"])

            with tab_tous:
                df_tous_visuel = pd.DataFrame({
                    "Description": df_biens["nom"],
                    "Type": df_biens["type"],
                    "Prix d'Achat": df_biens["valeur"].apply(formater_monnaie_empire),
                    "Rendement Net": df_biens["Rendement Net (%)"].apply(lambda x: f"{x:.2f}%"),
                    "Quantité Max": df_biens["Quantité Max Achetée"],
                    "Gain Mensuel Cumulé": df_biens["Gain Mensuel Cumulé"].apply(formater_monnaie_empire),
                    "Renta_Num": df_biens["Rendement Net (%)"]
                }).sort_values(by="Renta_Num", ascending=False)
                st.dataframe(df_tous_visuel.drop(columns=["Renta_Num"]), use_container_width=True, hide_index=True)

            with tab_ent:
                df_ent = df_biens[df_biens["categorie"].astype(str).str.lower() == "entreprise"].copy()
                if df_ent.empty:
                    st.info("⚪ Aucun bâtiment marqué 'entreprise'.")
                else:
                    df_ent_visuel = pd.DataFrame({
                        "Description": df_ent["nom"],
                        "Prix d'Achat": df_ent["valeur"].apply(formater_monnaie_empire),
                        "Rendement Net": df_ent["Rendement Net (%)"].apply(lambda x: f"{x:.2f}%"),
                        "Quantité Max": df_ent["Quantité Max Achetée"],
                        "Gain Mensuel Cumulé": df_ent["Gain Mensuel Cumulé"].apply(formater_monnaie_empire),
                        "Renta_Num": df_ent["Rendement Net (%)"]
                    }).sort_values(by="Renta_Num", ascending=False)
                    st.dataframe(df_ent_visuel.drop(columns=["Renta_Num"]), use_container_width=True, hide_index=True)

            with tab_perso:
                df_perso = df_biens[df_biens["categorie"].astype(str).str.lower() == "perso"].copy()
                if df_perso.empty:
                    st.info("⚪ Aucun bâtiment marqué 'perso'.")
                else:
                    df_perso_visuel = pd.DataFrame({
                        "Description": df_perso["nom"],
                        "Prix d'Achat": df_perso["valeur"].apply(formater_monnaie_empire),
                        "Rendement Net": df_perso["Rendement Net (%)"].apply(lambda x: f"{x:.2f}%"),
                        "Quantité Max": df_perso["Quantité Max Achetée"],
                        "Gain Mensuel Cumulé": df_perso["Gain Mensuel Cumulé"].apply(formater_monnaie_empire),
                        "Renta_Num": df_perso["Rendement Net (%)"]
                    }).sort_values(by="Renta_Num", ascending=False)
                    st.dataframe(df_perso_visuel.drop(columns=["Renta_Num"]), use_container_width=True, hide_index=True)

    except Exception as e: 
        st.error(f"⚠️ Erreur lors de l'exécution des calculs locatifs : {e}")
