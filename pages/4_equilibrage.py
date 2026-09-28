import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre, calculer_repartitions_equilibrage

st.title("⚖️ Équilibrage des Capitaux Propres")
st.markdown("Calculez les injections nécessaires pour équilibrer vos filiales selon la méthode de votre choix.")

if not st.session_state.get("holding_chargee", False):
    st.warning("⚠️ Veuillez d'abord coller vos tableaux et cliquer sur le bouton de synchronisation sur la page d'accueil 🏠 avant d'utiliser cette page.")
else:
    try:
        # 1. Lecture et extraction rapide depuis st.session_state
        data_fin = {l.split('\t')[0].strip(): convertir_saisie_en_nombre(l.split('\t')[1]) for l in st.session_state["tab_finance"].strip().split('\n')[1:] if len(l.split('\t')) >= 2}
        data_cap = {l.split('\t')[0].strip(): {"propres": convertir_saisie_en_nombre(l.split('\t')[2])} for l in st.session_state["tab_capital"].strip().split('\n')[1:] if len(l.split('\t')) >= 3}

        filiales = [{"Filiale": k, "Treso": data_fin[k], "Propres": data_cap[k]["propres"]} for k in data_fin if k in data_cap]
        df = pd.DataFrame(filiales)

        # 2. Sélection des filiales cibles
        f_choisies = st.multiselect("Filiales à équilibrer :", options=df["Filiale"].tolist(), default=df["Filiale"].tolist())
        
        if f_choisies:
            df_f = df[df["Filiale"].isin(f_choisies)].copy()
            max_c = float(df_f["Propres"].max())
            
            import_rows = []
            for _, r in df_f.iterrows():
                injecter = max(0.0, max_c - float(r["Propres"]))
                import_rows.append({
                    "Filiale": r["Filiale"], 
                    "Montant à Injecter": formater_monnaie_empire(injecter),
                    "Montant_RAW": injecter
                })

            df_selection = pd.DataFrame(import_rows)
            
            # Saisie de l'enveloppe Holding
            st.subheader("💰 Configuration du budget Holding")
            saisie_holding = st.text_input("Montant disponible dans la Holding (pour répartition 2 and 3) :", value="100 M")
            montant_holding = convertir_saisie_en_nombre(saisie_holding)
            st.caption(f"ℹ️ Budget Holding interprété : **{formater_monnaie_empire(montant_holding)}**")

            # 3. Exécution des calculs des 3 répartitions d'origine
            total_requis, rep_strict, rep_egal, rep_prop = calculer_repartitions_equilibrage(df_selection, montant_holding)
            
            st.markdown("---")
            st.subheader("🛠️ Choix de la méthode d'injection")
            
            # 🔘 LES 3 BOUTONS HORIZONTAUX COMME DANS VOTRE ANCIEN MODÈLE
            choix_methode = st.radio(
                "**Sélectionnez le modèle à appliquer pour générer le bloc d'import :**",
                ["🎯 1. Injection Stricte (Besoin réel)", "⚖️ 2. Répartition Égalitaire", "📈 3. Répartition Proportionnelle"],
                horizontal=True
            )

            df_active = None
            message_info = ""

            if choix_methode == "🎯 1. Injection Stricte (Besoin réel)":
                df_active = rep_strict
                message_info = f"Le besoin théorique total pour niveler les filiales est de **{formater_monnaie_empire(total_requis)}**."
            elif choix_methode == "⚖️ 2. Répartition Égalitaire":
                df_active = rep_egal
                message_info = f"Le budget de la Holding est divisé strictement équitablement entre toutes les filiales cibles."
            else:
                df_active = rep_prop
                message_info = f"Le budget de la Holding est distribué proportionnellement selon l'importance du déficit de chaque filiale."

            # 4. Affichage dynamique du tableau de la méthode sélectionnée
            if df_active is not None:
                st.info(message_info)
                
                df_visuel = df_active.copy()
                df_visuel["Montant à Injecter"] = df_visuel["Montant"].apply(formater_monnaie_empire)
                st.dataframe(df_visuel[["Filiale", "Montant à Injecter"]], use_container_width=True, hide_index=True)
                
                # 📋 Génération du BLOC D'IMPORTATION direct (CRLF) spécifique au bouton cliqué
                lignes_import = []
                for _, row in df_active.iterrows():
                    valeur_brute = int(float(row["Montant"]))
                    if valeur_brute > 0:
                        lignes_import.append(f"{row['Filiale']}\t{valeur_brute}")
                
                st.subheader("📋 Bloc d'importation direct pour le jeu")
                crlf_txt = "\r\n".join(lignes_import) + "\r\n"
                st.code(crlf_txt, language="text")
                st.download_button("📥 Télécharger le fichier (.txt)", data=crlf_txt, file_name="equilibrage_capitaux_empire.txt", mime="text/plain")

    except Exception as e: 
        st.error(f"⚠️ Erreur lors de la génération des arbitrages : {e}")
