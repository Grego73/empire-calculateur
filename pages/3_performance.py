import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre

st.title("📊 Statistiques Générales des Filiales")
st.markdown("Analyse croisée et indicateurs financiers complets pour l'ensemble des filiales de votre Empire.")

if not st.session_state.get("holding_chargee", False):
    st.warning("⚠️ Veuillez d'abord coller vos tableaux et cliquer sur le bouton de synchronisation sur la page d'accueil 🏠 avant d'utiliser cette page.")
else:
    tab_finance = st.session_state.get("tab_finance", "")
    tab_capital = st.session_state.get("tab_capital", "")
    tab_frais = st.session_state.get("tab_frais", "")

    try:
        # 1. Traitement du tableau Finance
        lignes_fin = tab_finance.strip().split('\n')
        idx_fin = 1 if "filiale" in lignes_fin[0].lower() else 0
        data_fin = {}
        for l in lignes_fin[idx_fin:]:
            if not l.strip(): continue
            cols = [c.strip() for c in l.split('\t') if c.strip()]
            if len(cols) < 5: continue
            nom = cols[0]
            data_fin[nom] = {
                "tresorerie": convertir_saisie_en_nombre(cols[1]),
                "exploitation": convertir_saisie_en_nombre(cols[2]),
                "net": convertir_saisie_en_nombre(cols[3]),
                "benefices": convertir_saisie_en_nombre(cols[4])
            }

        # 2. Traitement du tableau Capital
        lignes_cap = tab_capital.strip().split('\n')
        idx_cap = 1 if "filiale" in lignes_cap[0].lower() else 0
        data_cap = {}
        for l in lignes_cap[idx_cap:]:
            if not l.strip(): continue
            cols = [c.strip() for c in l.split('\t') if c.strip()]
            if len(cols) < 5: continue
            nom = cols[0]
            data_cap[nom] = {
                "apport": convertir_saisie_en_nombre(cols[1]),
                "propres": convertir_saisie_en_nombre(cols[2]),
                "latence": convertir_saisie_en_nombre(cols[3]),
                "plus_value": convertir_saisie_en_nombre(cols[4])
            }

        # 3. Traitement du tableau Frais
        data_frais = {}
        if tab_frais.strip():
            lignes_fr = tab_frais.strip().split('\n')
            idx_fr = 1 if "filiale" in lignes_fr[0].lower() else 0
            for l in lignes_fr[idx_fr:]:
                if not l.strip(): continue
                cols = [c.strip() for c in l.split('\t') if c.strip()]
                if len(cols) < 2: continue
                # S'assure de récupérer la valeur numérique de la 2e colonne (Frais de gestion)
                data_frais[cols[0]] = convertir_saisie_en_nombre(cols[1])

        # 4. Fusion et calculs statistiques
        analyse_rows = []
        total_treso = 0
        total_exploitation = 0
        total_net = 0
        total_apport = 0
        total_latence = 0

        for filiale, fin in data_fin.items():
            if filiale not in data_cap: continue
            cap = data_cap[filiale]
            frais = data_frais.get(filiale, 0)

            total_treso += fin["tresorerie"]
            total_exploitation += fin["exploitation"]
            total_net += fin["net"]
            total_apport += cap["apport"]
            total_latence += cap["latence"]

            rendement_apport = (fin["exploitation"] / cap["apport"] * 100) if cap["apport"] > 0 else 0
            poids_frais = (frais / fin["exploitation"] * 100) if fin["exploitation"] > 0 else 0

            analyse_rows.append({
                "Filiale": filiale,
                "Trésorerie": formater_monnaie_empire(fin["tresorerie"]),
                "Rès. Exploitation": formater_monnaie_empire(fin["exploitation"]),
                "Résultat NET": formater_monnaie_empire(fin["net"]),
                "Bénéfices/Pertes": formater_monnaie_empire(fin["benefices"]),
                "Capitaux Propres": formater_monnaie_empire(cap["propres"]),
                "Latence": formater_monnaie_empire(cap["latence"]),
                "Rendement (%)": rendement_apport,
                "Poids Frais (%)": round(poids_frais, 2) if frais > 0 else 0
            })

        df = pd.DataFrame(analyse_rows)

        st.success("🎉 Statistiques globales générées !")
        st.subheader("🏢 Vue d'ensemble de l'Empire")
        m1, m2, m3 = st.columns(3)
        with m1: st.metric("Trésorerie Totale", formater_monnaie_empire(total_treso))
        with m2: st.metric("Résultat Exploitation Total", formater_monnaie_empire(total_exploitation))
        with m3: st.metric("Résultat NET Total", formater_monnaie_empire(total_net))

        m4, m5 = st.columns(2)
        with m4: st.metric("Capital Total Apporté", formater_monnaie_empire(total_apport))
        with m5: st.metric("Latence Totale Dormante", formater_monnaie_empire(total_latence))

        st.subheader("📈 Liste Statistique Détaillée de Toutes les Filiales")
        df_tri = df.sort_values(by="Rendement (%)", ascending=False)
        df_affichage = df_tri.rename(columns={"Rendement (%)": "Rendement/Apport (%)"})
        
        st.dataframe(
            df_affichage.style.format({
                "Rendement/Apport (%)": "{:.2f}%",
                "Poids Frais (%)": "{:.2f}%"
            }),
            use_container_width=True
        )

        st.subheader("💡 Alertes de gestion")
        if not df_tri.empty:
            top_nom = df_tri.iloc[0]["Filiale"]
            top_val = df_tri.iloc[0]["Rendement (%)"]
            st.info(f"🚀 La filiale la plus performante est **{top_nom}** avec un taux de rendement de **{top_val:.2f}%**.")

        if tab_frais.strip():
            filiales_critiques = df[df["Poids Frais (%)"] >= 90]
            if not filiales_critiques.empty:
                for _, row in filiales_critiques.iterrows():
                    st.warning(f"🚨 **{row['Filiale']}** : Les frais absorbent **{row['Poids Frais (%)']}%** de l'exploitation. Action requise.")

    except Exception as e:
        st.error(f"⚠️ Erreur lors de la compilation des statistiques : {str(e)}")
