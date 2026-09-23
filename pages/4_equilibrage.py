import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre

st.title("⚖️ Équilibrage basé sur les Capitaux Propres")
st.markdown("Calculez les injections nécessaires pour équilibrer uniquement les **Capitaux Propres** de vos filiales.")

if not st.session_state.get("donnees_chargees", False):
    st.warning("⚠️ Veuillez d'abord coller vos tableaux et cliquer sur le bouton de synchronisation sur la page d'accueil 🏠 avant d'utiliser cette page.")
else:
    tab_finance = st.session_state.get("tab_finance", "")
    tab_capital = st.session_state.get("tab_capital", "")

    try:
        # 1. Extraction des trésoreries (Tableau Finance)
        lignes_fin = tab_finance.strip().split('\n')
        idx_debut_fin = 1 if "filiale" in tab_finance.lower() or "trésorerie" in tab_finance.lower() else 0
        
        data_fin = {}
        for ligne in lignes_fin[idx_debut_fin:]:
            if not ligne.strip(): continue
            colonnes = [c.strip() for c in ligne.split('\t') if c.strip()]
            if len(colonnes) < 2: continue
            nom_filiale = colonnes[0]
            data_fin[nom_filiale] = convertir_saisie_en_nombre(colonnes[1])

        # 2. Extraction du Capital (Tableau Capital)
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

        # 3. Fusion des données
        filiales_jointes = []
        for nom, treso_actuelle in data_fin.items():
            if nom in data_cap:
                cap_propres = data_cap[nom]["propres"]
                
                filiales_jointes.append({
                    "Filiale": nom,
                    "Trésorerie Actuelle RAW": treso_actuelle,
                    "Capitaux Propres RAW": cap_propres,
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
            mode = st.radio("**2. Choisissez la méthode de calcul :**", ["⚖️ Équilibrer vers une Valeur Cible unique (Capitaux Propres)", "💰 Diviser et injecter une enveloppe globale"])
            
            import_rows = []
            
            # --- MODE 1 : ÉQUILIBRAGE STRICT SUR LES CAPITAUX PROPRES ---
            if mode == "⚖️ Équilibrer vers une Valeur Cible unique (Capitaux Propres)":
                # On cherche la valeur maximale uniquement dans les Capitaux Propres
                capitaux_max_cible = int(df_filtre["Capitaux Propres RAW"].max())
                
                enveloppe_minimale_requise = 0
                for _, row in df_filtre.iterrows():
                    enveloppe_minimale_requise += max(0, capitaux_max_cible - row["Capitaux Propres RAW"])
                
                st.info(f"💵 **Montant total minimal à injecter de la Holding pour équilibrer les Capitaux Propres** : {formater_monnaie_empire(enveloppe_minimale_requise)}")
                
                for _, row in df_filtre.iterrows():
                    # Calcul de l'écart basé uniquement sur les Capitaux Propres
                    ecart_individuel = max(0, capitaux_max_cible - row["Capitaux Propres RAW"])
                    import_rows.append({
                        "Filiale": row["Filiale"],
                        "Trésorerie Actuelle": formater_monnaie_empire(row["Trésorerie Actuelle RAW"]),
                        "Capitaux Propres Actuels": formater_monnaie_empire(row["Capitaux Propres RAW"]),
                        "Montant à Injecter RAW": ecart_individuel,
                        "Montant à Injecter (TAB)": formater_monnaie_empire(ecart_individuel)
                    })
                    
            # --- MODE 2 : INJECTION GLOBALE ÉQUITABLE ---
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
                        "Capitaux Propres Actuels": formater_monnaie_empire(row["Capitaux Propres RAW"]),
                        "Montant à Injecter RAW": part_egale,
                        "Montant à Injecter (TAB)": formater_monnaie_empire(part_egale)
                    })

            df_resultat = pd.DataFrame(import_rows)
            st.success("✅ Calculs mis à jour en fonction des Capitaux Propres.")

            st.subheader("📊 Plan d'importation validé")
            # Affichage du tableau nettoyé sans la colonne superflue de la valeur totale actuelle
            st.dataframe(df_resultat[["Filiale", "Trésorerie Actuelle", "Capitaux Propres Actuels", "Montant à Injecter (TAB)"]], use_container_width=True)
            
            # Génération du bloc d'importation au format Empire Immo (Filiale + Tabulation + Chiffre brut)
            lignes_import = []
            for _, row in df_resultat.iterrows():
                if row["Montant à Injecter RAW"] > 0:
                    lignes_import.append(f"{row['Filiale']}\t{row['Montant à Injecter RAW']}")
            
            contenu_crlf_pur = "\r\n".join(lignes_import) + "\r\n"
            st.subheader("📋 Bloc d'importation direct")
            st.code(contenu_crlf_pur, language="text")
            st.download_button("📥 Télécharger le fichier (.txt)", data=contenu_crlf_pur, file_name="equilibrage_capitaux_empire.txt", mime="text/plain")

    except Exception as e:
        st.error(f"⚠️ Erreur lors du calcul de l'équilibrage : {str(e)}")
