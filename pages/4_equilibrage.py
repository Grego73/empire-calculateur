import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre, calculer_repartitions_equilibrage

st.title("⚖️ Équilibrage des Capitaux Propres")
st.markdown("Visualisez le besoin théorique global et comparez vos 3 modèles de répartition de capital.")

if not st.session_state.get("holding_chargee", False):
    st.warning("⚠️ Synchronisez d'abord vos données sur l'accueil 🏠.")
else:
    try:
        # 1. Lecture et extraction rapide de la session
        data_fin = {l.split('\t')[0].strip(): convertir_saisie_en_nombre(l.split('\t')[1]) for l in st.session_state["tab_finance"].strip().split('\n')[1:] if len(l.split('\t')) >= 2}
        data_cap = {l.split('\t')[0].strip(): {"propres": convertir_saisie_en_nombre(l.split('\t')[2])} for l in st.session_state["tab_capital"].strip().split('\n')[1:] if len(l.split('\t')) >= 3}

        filiales = [{"Filiale": k, "Treso": data_fin[k], "Propres": data_cap[k]["propres"]} for k in data_fin if k in data_cap]
        df = pd.DataFrame(filiales)

        # 2. Interface utilisateur et sélection des cibles
        f_choisies = st.multiselect("Filiales à équilibrer :", options=df["Filiale"].tolist(), default=df["Filiale"].tolist())
        
        if f_choisies:
            df_f = df[df["Filiale"].isin(f_choisies)].copy()
            
            # Utilisation de float64 pour éviter le débordement d'entier (Value out of range)
            max_c = float(df_f["Propres"].max())
            
            import_rows = []
            lignes_import = []
            
            for _, r in df_f.iterrows():
                # Calcul de l'écart individuel en flottant sécurisé
                injecter = max(0.0, max_c - float(r["Propres"]))
                import_rows.append({
                    "Filiale": r["Filiale"], 
                    "Montant à Injecter": formater_monnaie_empire(injecter),
                    "Montant_RAW": injecter
                })
                if injecter > 0: 
                    lignes_import.append(f"{r['Filiale']}\t{int(injecter)}")

            df_selection = pd.DataFrame(import_rows)
            
            # Affichage de la table de base validée
            st.dataframe(df_selection[["Filiale", "Montant à Injecter"]], use_container_width=True, hide_index=True)
            
            # Saisie de l'enveloppe disponible dans votre Holding pour alimenter les répartitions 2 et 3
            st.markdown("---")
            st.subheader("💰 Configuration du budget Holding")
            saisie_holding = st.text_input("Montant disponible actuellement dans la Holding :", value="100 M")
            montant_holding = convertir_saisie_en_nombre(saisie_holding)
            st.caption(f"ℹ️ Budget interprété : **{formater_monnaie_empire(montant_holding)}**")

            # 3. Exécution des calculs des 3 répartitions d'origine
            total_requis, rep_strict, rep_egal, rep_prop = calculer_repartitions_equilibrage(df_selection, montant_holding)
            
            # Affichage du métrique général
            st.metric(
                label="🔴 Montant Total Théorique Requis pour l'Équilibrage Strict", 
                value=formater_monnaie_empire(total_requis)
            )
            
            # 4. Affichage des 3 Répartitions en colonnes (Ancien Modèle Restauré)
            st.markdown("### 📊 Comparatif des modèles d'injection")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("#### 🎯 1. Strict")
                if rep_strict is not None:
                    # Application visuelle du format monétaire Empire sur les lignes du tableau
                    rep_strict_visuel = rep_strict.copy()
                    rep_strict_visuel["Montant"] = rep_strict_visuel["Montant"].apply(formater_monnaie_empire)
                    st.dataframe(rep_strict_visuel, use_container_width=True, hide_index=True)
            
            with col2:
                st.markdown("#### ⚖️ 2. Égalitaire")
                if rep_egal is not None:
                    rep_egal_visuel = rep_egal.copy()
                    rep_egal_visuel["Montant"] = rep_egal_visuel["Montant"].apply(formater_monnaie_empire)
                    st.dataframe(rep_egal_visuel, use_container_width=True, hide_index=True)
            
            with col3:
                st.markdown("#### 📈 3. Proportionnelle")
                if rep_prop is not None:
                    rep_prop_visuel = rep_prop.copy()
                    rep_prop_visuel["Montant"] = rep_prop_visuel["Montant"].apply(formater_monnaie_empire)
                    st.dataframe(rep_prop_visuel, use_container_width=True, hide_index=True)

            # 5. Bloc d'importation direct (CRLF standard) basé sur l'injection stricte
            st.markdown("---")
            st.subheader("📋 Bloc d'importation direct (Strict)")
            crlf_txt = "\r\n".join(lignes_import) + "\r\n"
            st.code(crlf_txt, language="text")
            
    except Exception as e: 
        st.error(f"⚠️ Erreur lors de la génération des arbitrages : {e}")
