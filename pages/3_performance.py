import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre

st.title("📊 Statistiques Générales des Filiales")

if not st.session_state.get("holding_chargee", False):
    st.warning("⚠️ Veuillez synchroniser vos tableaux sur l'accueil 🏠.")
else:
    try:
        # Extraction Finance
        data_fin = {}
        for l in st.session_state["tab_finance"].strip().split('\n')[1:]:
            cols = [c.strip() for c in l.split('\t') if c.strip()]
            if len(cols) < 5: continue
            data_fin[cols[0]] = {"treso": convertir_saisie_en_nombre(cols[1]), "expo": convertir_saisie_en_nombre(cols[2]), "net": convertir_saisie_en_nombre(cols[3]), "prof": convertir_saisie_en_nombre(cols[4])}

        # Extraction Capital
        data_cap = {}
        for l in st.session_state["tab_capital"].strip().split('\n')[1:]:
            cols = [c.strip() for c in l.split('\t') if c.strip()]
            if len(cols) < 5: continue
            data_cap[cols[0]] = {"apport": convertir_saisie_en_nombre(cols[1]), "propres": convertir_saisie_en_nombre(cols[2]), "latence": convertir_saisie_en_nombre(cols[3])}

        # Fusion & Calculs
        rows = []
        for f, fin in data_fin.items():
            if f not in data_cap: continue
            cap = data_cap[f]
            rendement = (fin["expo"] / cap["apport"] * 100) if cap["apport"] > 0 else 0
            rows.append({"Filiale": f, "Trésorerie": formater_monnaie_empire(fin["treso"]), "Exploitation": formater_monnaie_empire(fin["expo"]), "Net": formater_monnaie_empire(fin["net"]), "Capitaux Propres": formater_monnaie_empire(cap["propres"]), "Rendement (%)": rendement})

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
    except Exception as e: st.error(f"⚠️ Erreur de compilation : {e}")
