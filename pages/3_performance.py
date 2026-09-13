import streamlit as st
import pandas as pd

st.title("📊 Statistiques Générales des Filiales")
st.markdown("Analyse croisée et indicateurs financiers complets pour l'ensemble des filiales de votre Empire.")

# Vérification si les données ont bien été synchronisées depuis l'accueil
if not st.session_state.get("donnees_chargees", False):
    st.warning("⚠️ Veuillez d'abord coller vos tableaux et cliquer sur le bouton de synchronisation sur la page d'accueil 🏠 avant d'utiliser cette page.")
else:
    # Récupération automatique des données textuelles depuis la mémoire centrale
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
                "tresorerie": int(cols[1].replace(" ", "").replace("€", "")),
                "exploitation": int(cols[2].replace(" ", "").replace("€", "")),
                "net": int(cols[3].replace(" ", "").replace("€", "")),
                "benefices": int(cols[4].replace(" ", "").replace("€", ""))
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
                "apport": int(cols[1].replace(" ", "").replace("€", "")),
                "propres": int(cols[2].replace(" ", "").replace("€", "")),
                "latence": int(cols[3].replace(" ", "").replace("€", "")),
                "plus_value": int(cols[4].replace(" ", "").replace("€", ""))
            }

        # 3. Traitement du tableau Frais (Optionnel)
        data_frais = {}
        if tab_frais.strip():
            lignes_fr = tab_frais.strip().split('\n')
            idx_fr = 1 if "filiale" in lignes_fr[0].lower() else 0
            for l in lignes_fr[idx_fr:]:
                if not l.strip(): continue
                cols = [c.strip() for c in l.split('\t') if c.strip()]
                if len(cols) < 2: continue
                data_frais[cols[0]] = int(cols[-1].replace(" ", "").replace("€", ""))

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

            # Cumuls pour les métriques globales
            total_treso += fin["tresorerie"]
            total_exploitation += fin["exploitation"]
            total_net += fin["net"]
            total_apport += cap["apport"]
            total_latence += cap["latence"]

            # Ratios individuels
            rendement_apport = (fin["exploitation"] / cap["apport"] * 100) if cap["apport"] > 0 else 0
            poids_frais = (frais / fin["exploitation"] * 100) if fin["exploitation"] > 0 else 0

            analyse_rows.append({
                "Filiale": filiale,
                "Trésorerie": fin["tresorerie"],
                "Rès. Exploitation": fin["exploitation"],
                "Résultat NET": fin["net"],
                "Bénéfices/Pertes": fin["benefices"],
                "Capitaux Propres": cap["propres"],
                "Latence": cap["latence"],
                "Rendement/Apport (%)": round(rendement_apport, 2),
                "Poids Frais (%)": round(poids_frais, 2) if frais > 0 else 0
            })

        df = pd.DataFrame(analyse_rows)

        # --- AFFICHAGE DU TABLEAU DE BORD GLOBAL ---
        st.success("🎉 Statistiques globales générées !")

        # Les KPIs du haut
        st.subheader("🏢 Vue d'ensemble de l'Empire")
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Trésorerie Totale", f"{total_treso:,}".replace(",", " "))
        with m2:
            st.metric("Résultat Exploitation Total", f"{total_exploitation:,}".replace(",", " "))
        with m3:
            st.metric("Résultat NET Total", f"{total_net:,}".replace(",", " "))

        m4, m5 = st.columns(2)
        with m4:
            st.metric("Capital Total Apporté", f"{total_apport:,}".replace(",", " "))
        with m5:
            st.metric("Latence Totale Dormante", f"{total_latence:,}".replace(",", " "))

        # Tableau complet et interactif
        st.subheader("📈 Liste Statistique Détaillée de Toutes les Filiales")
        st.markdown("Vous pouvez cliquer sur les en-têtes de colonnes pour trier les filiales (ex: par Trésorerie ou par Rendement).")
        
        # Formatage de l'affichage pour la lisibilité humaine des gros chiffres
        st.dataframe(
            df.style.format({
                "Trésorerie": "{:,.0f}",
                "Rès. Exploitation": "{:,.0f}",
                "Résultat NET": "{:,.0f}",
                "Bénéfices/Pertes": "{:,.0f}",
                "Capitaux Propres": "{:,.0f}",
                "Latence": "{:,.0f}",
                "Rendement/Apport (%)": "{:.2f}%",
                "Poids Frais (%)": "{:.2f}%"
            }),
            use_container_width=True
        )

        # Section Alertes et Conseils
        st.subheader("💡 Alertes de gestion")
        df_tri_rendement = df.sort_values(by="Rendement/Apport (%)", ascending=False)
        if not df_tri_rendement.empty:
            top_nom = df_tri_rendement.iloc[0]["Filiale"]
            top_val = df_tri_rendement.iloc[0]["Rendement/Apport (%)"]
            st.info(f"🚀 La filiale la plus performante est **{top_nom}** avec un taux de rendement de **{top_val}%**.")

        if tab_frais.strip():
            filiales_critiques = df[df["Poids Frais (%)"] >= 90]
            if not filiales_critiques.empty:
                for _, row in filiales_critiques.iterrows():
                    st.warning(f"🚨 **{row['Filiale']}** : Les frais absorbent **{row['Poids Frais (%)']}%** de l'exploitation. Action requise.")

    except Exception as e:
        st.error(f"⚠️ Erreur lors de la compilation des statistiques : {str(e)}")
