import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre

st.title("📊 Statistiques Générales des Filiales")

if not st.session_state.get("holding_chargee", False):
    st.warning("⚠️ Veuillez synchroniser vos tableaux sur l'accueil 🏠.")
else:
    try:
        # --- PARSING DU TABLEAU FINANCE ---
        data_fin = {}
        lignes_f = st.session_state["tab_finance"].strip().split('\n')
        # Détection intelligente : si le premier mot contient "filiale", c'est un en-tête, on commence à 1
        idx_f = 1 if lignes_f and "filiale" in lignes_f[0].lower() else 0
        
        for l in lignes_f[idx_f:]:
            if not l.strip(): continue
            cols = [c.strip() for c in l.split('\t')]
            if len(cols) < 5: continue
            data_fin[cols[0]] = {
                "treso": convertir_saisie_en_nombre(cols[1]), 
                "expo": convertir_saisie_en_nombre(cols[2]), 
                "net": convertir_saisie_en_nombre(cols[3]), 
                "prof": convertir_saisie_en_nombre(cols[4])
            }

        # --- PARSING DU TABLEAU CAPITAL ---
        data_cap = {}
        lignes_c = st.session_state["tab_capital"].strip().split('\n')
        idx_c = 1 if lignes_c and "filiale" in lignes_c[0].lower() else 0
        
        for l in lignes_c[idx_c:]:
            if not l.strip(): continue
            cols = [c.strip() for c in l.split('\t')]
            if len(cols) < 4: continue
            data_cap[cols[0]] = {
                "apport": convertir_saisie_en_nombre(cols[1]), 
                "propres": convertir_saisie_en_nombre(cols[2]), 
                "latence": convertir_saisie_en_nombre(cols[3])
            }

        # --- COMPILATION ET CALCULS DE PERFORMANCE ---
        rows = []
        for f, fin in data_fin.items():
            if f not in data_cap: continue
            cap = data_cap[f]
            rendement = (fin["expo"] / cap["apport"] * 100) if cap["apport"] > 0 else 0
            rows.append({
                "Filiale": f, 
                "Trésorerie": formater_monnaie_empire(fin["treso"]), 
                "Exploitation": formater_monnaie_empire(fin["expo"]), 
                "Net": formater_monnaie_empire(fin["net"]), 
                "Capitaux Propres": formater_monnaie_empire(cap["propres"]), 
                "Rendement (%)": rendement
            })

        df = pd.DataFrame(rows)
        if not df.empty:
            df["Rendement (%)"] = df["Rendement (%)"].apply(lambda x: f"{x:.2f}%")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("⚪ Aucune donnée concordante trouvée entre vos tableaux Finance et Capital.")
        
    except Exception as e: 
        st.error(f"⚠️ Erreur de compilation : {e}")
