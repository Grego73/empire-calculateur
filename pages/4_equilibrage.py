import streamlit as st
import pandas as pd

st.title("⚖️ Équilibrage de la Valeur Réelle")
st.markdown("Calculez les injections nécessaires pour équilibrer la **Somme Globale (Trésorerie + Capitaux Propres)** de vos filiales.")

# Vérification si les données ont bien été synchronisées depuis l'accueil
if not st.session_state.get("donnees_chargees", False):
    st.warning("⚠️ Veuillez d'abord coller vos tableaux et cliquer sur le bouton de synchronisation sur la page d'accueil 🏠 avant d'utiliser cette page.")
else:
    # Récupération automatique des données depuis la mémoire centrale
    tab_finance = st.session_state.get("tab_finance", "")
    tab_capital = st.session_state.get("tab_capital", "")

    try:
        # 1. Extraction des filiales et de leur trésorerie actuelle (Tableau Finance)
        lignes_fin = tab_finance.strip().split('\n')
        idx_debut_fin = 1 if "filiale" in lignes_fin.lower() else 0
        
        data_fin = {}
        for ligne in lignes_fin[idx_debut_fin:]:
            if not ligne.strip(): continue
            colonnes = [c.strip() for c in ligne.split('\t') if c.strip()]
            if len(colonnes) < 2: continue
            nom_filiale = colonnes
            treso = int(colonnes.replace(" ", "").replace("€", ""))
            data_fin[nom_filiale] = treso

        # 2. Extraction du Capital (Tableau Capital - Colonne 2: Apport, Colonne 3: Capitaux propres)
        lignes_cap = tab_capital.strip().split('\n')
        idx_debut_cap = 1 if "filiale" in lignes_cap.lower() else 0
        
        data_cap = {}
        for ligne in lignes_cap[idx_debut_cap:]:
            if not ligne.strip(): continue
            colonnes = [c.strip() for c in ligne.split('\t') if c.strip()]
            if len(colonnes) < 3: continue
            nom_filiale = colonnes
            apport = int(colonnes.replace(" ", "").replace("€", ""))
            capitaux_propres = int(colonnes.replace(" ", "").replace("€", ""))
            data_cap[nom_filiale] = {"apport": apport, "propres": capitaux_propres}

        # 3. Fusion et calcul de la Valeur Globale (Trésorerie + Capitaux Propres)
        filiales_jointes = []
        for nom, treso_actuelle in data_fin.items():
            if nom in data_cap:
                cap_propres = data_cap[nom]["propres"]
                # NOUVEAUTÉ : La valeur de référence est l'addition des deux colonnes
                valeur_totale_actuelle = treso_actuelle + cap_propres
                
                filiales_jointes.append({
                    "Filiale": nom,
                    "Trésorerie Actuelle": treso_actuelle,
                    "Capitaux Propres": cap_propres,
                    "Valeur Totale Actuelle": valeur_totale_actuelle,
                    "Apport Initial": data_cap[nom]["apport"]
                })
        
        df_base = pd.DataFrame(filiales_jointes)

        st.subheader("⚙️ Configuration de l'opération")
        
        # Sélection des filiales concernées
        st.markdown("**1. Cochez les filiales à inclure dans l'opération :**")
        all_filiales = df_base["Filiale"].tolist()
        filiales_choisies = st.multiselect("Filiales cibles :", options=all_filiales, default=all_filiales)
        
        if not filiales_choisies:
            st.warning("⚠️ Veuillez sélectionner au moins une filiale.")
        else:
            df_filtre = df_base[df_base["Filiale"].isin(filiales_choisies)].copy()
            
            # Choix du mode d'équilibrage basé sur la valeur totale
            mode = st.radio(
                "**2. Choisissez la méthode de calcul :**",
                ["⚖️ Équilibrer vers une Valeur Cible unique (Trésorerie + Capitaux)", "💰 Diviser et injecter une enveloppe globale"]
            )
            
            import_rows = []
            alertes_securite = []
            
            # --- MODE 1 : ÉQUILIBRAGE VERS CIBLE ---
            if mode == "⚖️ Équilibrer vers une Valeur Cible unique (Trésorerie + Capitaux)":
                valeur_max_actuelle = int(df_filtre["Valeur Totale Actuelle"].max())
                montant_cible = st.number_input(
                    "Définissez la Valeur Totale souhaitée pour chaque filiale :",
                    min_value=0,
                    value=valeur_max_actuelle,
                    step=1000000
                )
                
                for _, row in df_filtre.iterrows():
                    # L'écart se calcule par rapport à la Valeur Totale Actuelle
                    ecart_brut = max(0, montant_cible - row["Valeur Totale Actuelle"])
                    plafond_max = row["Capitaux Propres"]
                    apport_init = row["Apport Initial"]
                    
                    injection_finale = ecart_brut
                    
                    # SÉCURITÉ 1 : Plus de valeur immobilière
                    if plafond_max < apport_init:
                        injection_finale = 0
                        alertes_securite.append(f"❌ **{row['Filiale']}** : **BLOCAGE STRICT** - Plus de valeur immobilière. Injection annulée.")
                    
                    # SÉCURITÉ 2 : L'injection (qui se transforme en frais) ne peut pas dépasser les capitaux propres
                    elif ecart_brut > plafond_max:
                        injection_finale = plafond_max
                        alertes_securite.append(f"🚨 **{row['Filiale']}** : Écart de {ecart_brut:,} € ➡️ Bridé à **{plafond_max:,} €** pour protéger les Capitaux Propres")

                    import_rows.append({
                        "Filiale": row["Filiale"],
                        "Trésorerie Actuelle": row["Trésorerie Actuelle"],
                        "Capitaux Propres": plafond_max,
                        "Valeur Totale Actuelle": row["Valeur Totale Actuelle"],
                        "Montant à Injecter (TAB)": injection_finale
                    })
            
            # --- MODE 2 : INJECTION ENVELOPPE GLOBALE ---
            else:
                enveloppe_globale = st.number_input(
                    "Montant total de l'enveloppe à distribuer :",
                    min_value=0,
                    value=10000000,
                    step=1000000
                )
                
                nb_filiales = len(df_filtre)
                part_egale = int(enveloppe_globale // nb_filiales)
                
                for _, row in df_filtre.iterrows():
                    plafond_max = row["Capitaux Propres"]
                    apport_init = row["Apport Initial"]
                    
                    injection_finale = part_egale
                    
                    if plafond_max < apport_init:
                        injection_finale = 0
                        alertes_securite.append(f"❌ **{row['Filiale']}** : **BLOCAGE STRICT** - Plus de valeur immobilière. Injection annulée.")
                    elif part_egale > plafond_max:
                        injection_finale = plafond_max
                        alertes_securite.append(f"🚨 **{row['Filiale']}** : Part de {part_egale:,} € ➡️ Bridée à **{plafond_max:,} €** (Limite Capitaux Propres)")

                    import_rows.append({
                        "Filiale": row["Filiale"],
                        "Trésorerie Actuelle": row["Trésorerie Actuelle"],
                        "Capitaux Propres": plafond_max,
                        "Valeur Totale Actuelle": row["Valeur Totale Actuelle"],
                        "Montant à Injecter (TAB)": injection_finale
                    })

            # --- RENDU DE SÉCURITÉ ET AFFICHAGE ---
            df_resultat = pd.DataFrame(import_rows)
            
            if alertes_securite:
                st.error("⚠️ **CONTRÔLE DE FLUX :** Ajustements appliqués pour protéger la structure financière de vos filiales.")
                for alerte in alertes_securite:
                    st.warning(alerte)
            else:
                st.success("✅ Sécurité vérifiée : Toutes les filiales balancées respectent les équilibres comptables.")

            st.subheader("📊 Plan d'importation validé")
            st.dataframe(df_resultat.style.format({
                "Trésorerie Actuelle": "{:,.0f}",
                "Capitaux Propres": "{:,.0f}",
                "Valeur Totale Actuelle": "{:,.0f}",
                "Montant à Injecter (TAB)": "{:,.0f}"
            }), use_container_width=True)
            
            # Génération du texte d'importation (un seul \t exigé)
            lignes_import = []
            for _, row in df_resultat.iterrows():
                if row["Montant à Injecter (TAB)"] > 0:
                    lignes_import.append(f"{row['Filiale']}\t{row['Montant à Injecter (TAB)']}")
            
            contenu_crlf_pur = "\r\n".join(lignes_import) + "\r\n"
            
            st.subheader("📋 Bloc d'importation direct")
            st.markdown("Cliquez en haut à droite du bloc noir pour copier la liste, puis collez-la directement dans Empire Immo :")
            st.code(contenu_crlf_pur, language="text")
            
            st.text_area("Alternative de copie rapide (CTRL+A puis CTRL+C) :", value=contenu_crlf_pur, height=150, key="copie_secours_eq")
            st.download_button("📥 Télécharger le fichier d'import pur (.txt)", data=contenu_crlf_pur, file_name="equilibrage_valeur_empire.txt", mime="text/plain")

    except Exception as e:
        st.error(f"⚠️ Erreur lors du calcul de l'équilibrage : {str(e)}")
