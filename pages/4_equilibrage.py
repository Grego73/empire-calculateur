import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre

st.title("⚖️ Équilibrage de la Valeur Réelle")
st.markdown("Calculez les injections nécessaires pour équilibrer la **Somme Globale (Trésorerie + Capitaux Propres)** de vos filiales.")

if not st.session_state.get("donnees_chargees", False):
    st.warning("⚠️ Veuillez d'abord coller vos tableaux et cliquer sur le bouton de synchronisation sur la page d'accueil 🏠 avant d'utiliser cette page.")
else:
    tab_finance = st.session_state.get("tab_finance", "")
    tab_capital = st.session_state.get("tab_capital", "")

    try:
        # 1. Extraction des trésoreries
        lignes_fin = tab_finance.strip().split('\n')
        idx_debut_fin = 1 if "filiale" in tab_finance.lower() or "trésorerie" in tab_finance.lower() else 0
        
        data_fin = {}
        for ligne in lignes_fin[idx_debut_fin:]:
            if not ligne.strip(): continue
            colonnes = [c.strip() for c in ligne.split('\t') if c.strip()]
            if len(colonnes) < 2: continue
            nom_filiale = colonnes[0]
            data_fin[nom_filiale] = convertir_saisie_en_nombre(colonnes[1])

        # 2. Extraction du Capital
        lignes_cap = tab_capital.strip().split('\n')
        idx_debut_cap = 1 if "filiale" in tab_capital.lower() or "apport" in tab_capital.lower() else 0
        
        data_cap = {}
        for ligne in lignes_cap[idx_debut_cap:]:
            if not ligne.strip(): continue
            colonnes = [c.strip() for c in ligne.split('\t') if c.strip()]
            if len(colonnes) < 3: continue
            nom_filiale = colonnes[0]
            data_cap[nom_filiale] = {
                "apport": convertir_saisie_en_nombre(colonnes[1]),
                "propres": convertir_saisie_en_nombre(colonnes[2])
            }

        # 3. Fusion
        filiales_jointes = []
        for nom, treso_actuelle in data_fin.items():
            if nom in data_cap:
                cap_propres = data_cap[nom]["propres"]
                valeur_totale_actuelle = treso_actuelle + cap_propres
                
                filiales_jointes.append({
                    "Filiale": nom,
                    "Trésorerie Actuelle RAW": treso_actuelle,
                    "Capitaux Propres RAW": cap_propres,
                    "Valeur Totale Actuelle RAW": valeur_totale_actuelle,
                    "Apport Initial RAW": data_cap[nom]["apport"]
                })
        
        df_base = pd.DataFrame(filiales_jointes)

        st.subheader("⚙️ Configuration de l'opération")
        all_filiales = df_base["Filiale"].tolist()
        filiales_choisies = st.multiselect("Filiales cibles :", options=all_filiales, default=all_filiales)
        
        if not filiales_choisies:
            st.warning("⚠️ Veuillez sélectionner au moins une filiale.")
        else:
            df_filtre = df_base[df_base["Filiale"].isin(filiales_choisies)].copy()
            mode = st.radio("**2. Choisissez la méthode de calcul :**", ["⚖️ Équilibrer vers une Valeur Cible unique (Trésorerie + Capitaux)", "💰 Diviser et injecter une enveloppe globale"])
            
            import_rows = []
            
            if mode == "⚖️ Équilibrer vers une Valeur Cible unique (Trésorerie + Capitaux)":
                valeur_max_cible = int(df_filtre["Valeur Totale Actuelle RAW"].max())
                enveloppe_minimale_requise = 0
                for _, row in df_filtre.iterrows():
                    enveloppe_minimale_requise += max(0, valeur_max_cible - row["Valeur Totale Actuelle RAW"])
                
                st.info(f"💵 **Montant total minimal à injecter de la Holding** : {formater_monnaie_empire(enveloppe_minimale_requise)}")
                
                for _, row in df_filtre.iterrows():
                    ecart_individuel = max(0, valeur_max_cible - row["Valeur Totale Actuelle RAW"])
                    import_rows.append({
                        "Filiale": row["Filiale"],
                        "Trésorerie Actuelle": formater_monnaie_empire(row["Trésorerie Actuelle RAW"]),
                        "Capitaux Propres": formater_monnaie_empire(row["Capitaux Propres RAW"]),
                        "Valeur Totale Actuelle": formater_monnaie_empire(row["Valeur Totale Actuelle RAW"]),
                        "Montant à Injecter RAW": ecart_individuel,
                        "Montant à Injecter (TAB)": formater_monnaie_empire(ecart_individuel)
                    })
            else:
                saisie_enveloppe = st.text_input("Montant total de l'enveloppe à distribuer :", value="10000000")
                enveloppe_globale = convertir_saisie_en_nombre(saisie_enveloppe)
                st.caption(f"ℹ️ Enveloppe globale interprétée : **{formater_monnaie_empire(enveloppe_globale)}**")
                
                nb_filiales = len(df_filtre)
                part_egale = int(enveloppe_globale // nb_filiales)
                
                for _, row in df_filtre.iterrows():
                    import_rows.append({
                        "Filiale": row["Filiale"],
                        "Trésorerie Actuelle": formater_monnaie_empire(row["Trésorerie Actuelle RAW"]),
                        "Capitaux Propres": formater_monnaie_empire(row["Capitaux Propres RAW"]),
                        "Valeur Totale Actuelle": formater_monnaie_empire(row["Valeur Totale Actuelle RAW"]),
                        "Montant à Injecter RAW": part_egale,
                        "Montant à Injecter (TAB)": formater_monnaie_empire(part_egale)
                    })

            df_resultat = pd.DataFrame(import_rows)
            st.success("✅ Calculs mis à jour en temps réel.")

            st.subheader("📊 Plan d'importation validé")
            st.dataframe(df_resultat[["Filiale", "Trésorerie Actuelle", "Capitaux Propres", "Valeur Totale Actuelle", "Montant à Injecter (TAB)"]], use_container_width=True)
            
            lignes_import = []
            for _, row in df_resultat.iterrows():
                if row["Montant à Injecter RAW"] > 0:
                    lignes_import.append(f"{row['Filiale']}\t{row['Montant à Injecter RAW']}")
            
            contenu_crlf_pur = "\r\n".join(lignes_import) + "\r\n"
            st.subheader("📋 Bloc d'importation direct")
            st.code(contenu_crlf_pur, language="text")
            st.download_button("📥 Télécharger le fichier (.txt)", data=contenu_crlf_pur, file_name="equilibrage_valeur_empire.txt", mime="text/plain")

    except Exception as e:
        st.error(f"⚠️ Erreur lors du calcul de l'équilibrage : {str(e)}")
