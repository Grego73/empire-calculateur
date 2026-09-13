import streamlit as st
import pandas as pd

st.title("⚖️ Équilibrage & Injection de Trésorerie")
st.markdown("Calculez les montants précis à importer pour équilibrer vos filiales ou injecter une enveloppe de cash.")

# Saisie du tableau d'origine
tab_finance = st.text_area("Collez votre tableau Finance du jour ici :", height=200, key="eq_tab_fin")

if tab_finance.strip():
    try:
        # Extraire les filiales et leur trésorerie actuelle
        lignes = tab_finance.strip().split('\n')
        idx_debut = 1 if "filiale" in lignes[0].lower() else 0
        
        filiales_data = []
        for ligne in lignes[idx_debut:]:
            if not ligne.strip(): continue
            colonnes = [c.strip() for c in ligne.split('\t') if c.strip()]
            if len(colonnes) < 2: continue
            
            nom_filiale = colonnes[0]
            # La trésorerie est dans la 2ème colonne
            treso = int(colonnes[1].replace(" ", "").replace("€", ""))
            filiales_data.append({"Filiale": nom_filiale, "Trésorerie Actuelle": treso})
        
        df_base = pd.DataFrame(filiales_data)
        
        st.subheader("⚙️ Configuration de l'opération")
        
        # 1. Sélection des filiales concernées
        st.markdown("**1. Cochez les filiales à inclure dans l'opération :**")
        all_filiales = df_base["Filiale"].tolist()
        filiales_choisies = st.multiselect("Filiales cibles :", options=all_filiales, default=all_filiales)
        
        if not filiales_choisies:
            st.warning("⚠️ Veuillez sélectionner au moins une filiale.")
        else:
            # Filtrer le dataframe avec uniquement les filiales cochées
            df_filtre = df_base[df_base["Filiale"].isin(filiales_choisies)].copy()
            
            # 2. Choix du mode
            mode = st.radio(
                "**2. Choisissez la méthode de calcul :**",
                ["⚖️ Équilibrer vers un montant cible unique", "💰 Diviser et injecter une enveloppe globale"]
            )
            
            import_rows = []
            
            # --- MODE 1 : ÉQUILIBRAGE VERS CIBLE ---
            if mode == "⚖️ Équilibrer vers un montant cible unique":
                treso_max_actuelle = int(df_filtre["Trésorerie Actuelle"].max())
                montant_cible = st.number_input(
                    "Définissez la Trésorerie Cible souhaitée pour chaque filiale :",
                    min_value=treso_max_actuelle,
                    value=treso_max_actuelle,
                    step=1000000,
                    help="Par défaut, configuré sur la filiale la plus riche pour mettre tout le monde à niveau sans retirer d'argent."
                )
                
                for _, row in df_filtre.iterrows():
                    ecart = montant_cible - row["Trésorerie Actuelle"]
                    import_rows.append({
                        "Filiale": row["Filiale"],
                        "Trésorerie Actuelle": row["Trésorerie Actuelle"],
                        "Montant à Injecter (TAB)": ecart
                    })
            
            # --- MODE 2 : INJECTION ENVELOPPE GLOBALE ---
            else:
                enveloppe_globale = st.number_input(
                    "Montant total de l'enveloppe à distribuer :",
                    min_value=0,
                    value=10000000,
                    step=1000000
                )
                
                type_repartition = st.selectbox(
                    "Type de répartition :",
                    ["Division à parts égales strictes", "Combler en priorité les plus pauvres (Égalisation progressive)"]
                )
                
                nb_filiales = len(df_filtre)
                
                if type_repartition == "Division à parts égales strictes":
                    part_egale = int(enveloppe_globale // nb_filiales)
                    for _, row in df_filtre.iterrows():
                        import_rows.append({
                            "Filiale": row["Filiale"],
                            "Trésorerie Actuelle": row["Trésorerie Actuelle"],
                            "Montant à Injecter (TAB)": part_egale
                        })
                else:
                    # Algorithme d'égalisation progressive par le bas
                    # Copie de travail pour simuler l'attribution du cash pièce par pièce
                    df_sim = df_filtre.copy()
                    df_sim["Injection"] = 0
                    
                    # On distribue l'enveloppe de manière à équilibrer au mieux
                    # Pour éviter des boucles lentes sur de très gros chiffres, on fait une approche par itération sur le tri
                    argent_restant = enveloppe_globale
                    
                    while argent_restant > 0:
                        df_sim = df_sim.sort_values(by=["Trésorerie Actuelle", "Injection"])
                        # Trouver combien de filiales partagent le niveau le plus bas
                        niveau_bas = df_sim.iloc[0]["Trésorerie Actuelle"] + df_sim.iloc[0]["Injection"]
                        filiales_au_sol = df_sim[(df_sim["Trésorerie Actuelle"] + df_sim["Injection"]) == niveau_bas]
                        count = len(filiales_au_sol)
                        
                        # Déterminer le prochain palier (la trésorerie de la filiale juste au-dessus)
                        filiales_au_dessus = df_sim[(df_sim["Trésorerie Actuelle"] + df_sim["Injection"]) > niveau_bas]
                        if not filiales_au_dessus.empty:
                            prochain_palier = filiales_au_dessus.iloc[0]["Trésorerie Actuelle"] + filiales_au_dessus.iloc[0]["Injection"]
                            difference_palier = prochain_palier - niveau_bas
                            besoin_total_palier = difference_palier * count
                        else:
                            besoin_total_palier = argent_restant + 1 # Pas de palier au-dessus
                        
                        if argent_restant >= besoin_total_palier:
                            # On fait monter tout le monde au palier supérieur d'un coup
                            for idx in filiales_au_sol.index:
                                df_sim.at[idx, "Injection"] += difference_palier
                            argent_restant -= besoin_total_palier
                        else:
                            # On distribue le reste équitablement entre les filiales au sol
                            part = int(argent_restant // count)
                            if part > 0:
                                for idx in filiales_au_sol.index:
                                    df_sim.at[idx, "Injection"] += part
                                argent_restant -= (part * count)
                            else:
                                # S'il reste des miettes impossibles à diviser, on donne 1 aux premières
                                for idx in filiales_au_sol.index[:int(argent_restant)]:
                                    df_sim.at[idx, "Injection"] += 1
                                argent_restant = 0
                                
                    for _, row in df_sim.iterrows():
                        import_rows.append({
                            "Filiale": row["Filiale"],
                            "Trésorerie Actuelle": row["Trésorerie Actuelle"],
                            "Montant à Injecter (TAB)": row["Injection"]
                        })

            # --- RENDU ET AFFICHAGE DU TEXTE PRÊT À COPIER ---
            df_resultat = pd.DataFrame(import_rows)
            
            st.subheader("📊 Plan d'importation calculé")
            st.dataframe(df_resultat.style.format({
                "Trésorerie Actuelle": "{:,.0f}",
                "Montant à Injecter (TAB)": "{:,.0f}"
            }), use_container_width=True)
            
            # Formatage de la chaîne finale strictement exigée par Empire Immo (Filiale[TAB]Montant)
            lignes_import = []
            for _, row in df_resultat.iterrows():
                # On ignore les lignes où l'injection est de 0
                if row["Montant à Injecter (TAB)"] > 0:
                    lignes_import.append(f"{row['Filiale']}\t{row['Montant à Injecter (TAB)']}")
            
            contenu_crlf_pur = "\r\n".join(lignes_import) + "\r\n"
            
            st.subheader("📋 Bloc d'importation direct")
            st.markdown("Cliquez en haut à droite du bloc noir pour copier la liste, puis collez-la directement dans l'outil d'importation d'Empire Immo :")
            st.code(contenu_crlf_pur, language="text")
            
            st.text_area("Alternative de copie rapide (CTRL+A puis CTRL+C) :", value=contenu_crlf_pur, height=150, key="copie_secours_eq")
            st.download_button("📥 Télécharger le fichier d'import pur (.txt)", data=contenu_crlf_pur, file_name="equilibrage_import_empire.txt", mime="text/plain")

    except Exception as e:
        st.error(f"⚠️ Erreur lors du traitement de l'équilibrage : {str(e)}")
