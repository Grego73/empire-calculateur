import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre

st.title("⚖️ Équilibrage des Capitaux Propres")

if not st.session_state.get("holding_chargee", False):
    st.warning("⚠️ Synchronisez d'abord vos données sur l'accueil 🏠.")
else:
    try:
        # Lecture
        data_fin = {l.split('\t')[0].strip(): convertir_saisie_en_nombre(l.split('\t')[1]) for l in st.session_state["tab_finance"].strip().split('\n')[1:] if len(l.split('\t')) >= 2}
        data_cap = {l.split('\t')[0].strip(): {"propres": convertir_saisie_en_nombre(l.split('\t')[2])} for l in st.session_state["tab_capital"].strip().split('\n')[1:] if len(l.split('\t')) >= 3}

        filiales = [{"Filiale": k, "Treso": data_fin[k], "Propres": data_cap[k]["propres"]} for k in data_fin if k in data_cap]
        df = pd.DataFrame(filiales)

        f_choisies = st.multiselect("Filiales à équilibrer :", options=df["Filiale"].tolist(), default=df["Filiale"].tolist())
        
        if f_choisies:
            df_f = df[df["Filiale"].isin(f_choisies)].copy()
            max_c = int(df_f["Propres"].max())
            
            import_rows = []
            lignes_import = []
            
            for _, r in df_f.iterrows():
                injecter = max(0, max_c - r["Propres"])
                import_rows.append({"Filiale": r["Filiale"], "Montant à Injecter": formater_monnaie_empire(injecter)})
                if injecter > 0: lignes_import.append(f"{r['Filiale']}\t{injecter}")

            st.dataframe(pd.DataFrame(import_rows), use_container_width=True, hide_index=True)
            crlf_txt = "\r\n".join(lignes_import) + "\r\n"
            st.code(crlf_txt, language="text")
    except Exception as e: st.error(f"⚠️ Erreur calculs : {e}")
