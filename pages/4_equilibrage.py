import streamlit as st
import pandas as pd

st.title("⚖️ Équilibrage de la Valeur Réelle")
st.markdown("Calculez les injections nécessaires pour équilibrer la **Somme Globale (Trésorerie + Capitaux Propres)** de vos filiales.")

# FONCTION LOGIQUE DE CONVERSION EN MONNAIE EMPIRE
def formater_monnaie_empire(nombre):
    try:
        n = int(nombre)
    except:
        return str(nombre)
        
    abs_n = abs(n)
    paliers = [
        (10**39, "D"), (10**36, "N"), (10**33, "X"), (10**30, "S"),
        (10**27, "U"), (10**24, "Q"), (10**21, "R"), (10**18, "Y"),
        (10**15, "Z"), (10**12, "E"), (10**9, "P"), (10**6, "T"),
        (10**3, "G")
    ]
    
    for valeur, suffixe in paliers:
        if abs_n >= valeur:
            reste = abs_n / valeur
            signe = "-" if n < 0 else ""
            return f"{signe}{reste:,.2f} {suffixe}".replace(",", " ")
            
    return f"{n:,}".replace(",", " ")

# Vérification si les données ont bien été synchronisées depuis l'accueil
if not st.session_state.get("donnees_chargees", False):
    st.warning("⚠️ Veuillez d'abord coller vos tableaux et cliquer sur le bouton de synchronisation sur la page d'accueil 🏠 avant d'utiliser cette page.")
else:
    tab_finance = st.session_state.get("tab_finance", "")
    tab_capital = st.session_state.get("tab_capital", "")

    try:
        # 1. Extraction des filiales et de leur trésorerie actuelle (Tableau Finance)
        lignes_fin = tab_finance.strip().split('\n')
        
        # CORRECTION DU .LOWER() ICI (On vérifie la première ligne si elle existe)
        idx_debut_fin = 0
        if lignes_fin and len(lignes_fin) > 0:
            if "filiale" in lignes_fin[0].lower() or "trésorerie" in lignes_fin[0].lower():
                idx_debut_fin = 1
        
        data_fin = {}
        for ligne in lignes_fin[idx_debut_fin:]:
            if not ligne.strip(): continue
            colonnes = [c.strip() for c in ligne.split('\t') if c.strip()]
            if len(colonnes) < 2: continue
            nom_filiale = colonnes[0]
            treso = int(colonnes[1].replace(" ", "").replace("€", ""))
            data_fin[nom_filiale] = treso

        # 2. Extraction du Capital (Tableau Capital)
        lignes_cap = tab_capital.strip().split('\n')
        
        # CORRECTION DU .LOWER() ICI AUSSI
        idx_debut_cap = 0
        if lignes_cap and len(lignes_cap) > 0:
            if "filiale" in lignes_cap[0].lower() or "apport" in lignes_cap[0].lower():
                idx_debut_cap = 1
        
        data_cap = {}
        for ligne in lignes_cap[idx_debut_cap:]:
            if not ligne.strip(): continue
            colonnes = [c.strip() for c in ligne.split('\t') if c.strip()]
            if len(colonnes) < 3: continue
            nom_filiale = colonnes[0]
            apport = int(colonnes[1].replace(" ", "").replace("€", ""))
            capitaux_propres = int(colonnes[2].replace(" ", "").replace("€", ""))
            data_cap[nom_filiale] = {"apport": apport, "propres": capitaux_propres}

        # 3. Fusion et calcul de la Valeur Globale (Trésorerie + Capitaux Propres)
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
        
        st.markdown("**1. Cochez les filiales à les inclure dans l'opération :**")
        all_filiales = df_base["Filiale"].tolist()
        filiales_choisies = st.multiselect("Filiales cibles :", options=all_filiales, default=all_filiales)
        
        if not filiales_choisies:
            st.warning("⚠️ Veuillez sélectionner au moins une filiale.")
        else:
            df_filtre = df_base[df_base["Filiale"].isin(filiales_choisies)].copy()
            
            mode = st.radio(
                "**2. Choisissez la méthode de calcul :**",
                ["⚖️ Équilibrer vers une Valeur Cible unique (Trésorerie + Capitaux)", "💰 Diviser et injecter une enveloppe globale"]
            )
            
            import_rows = []
            alertes_securite = []
            
            # --- MODE 1 : ÉQUILIBRAGE VERS CIBLE ---
            if mode == "⚖️ Équilibrer vers une Valeur Cible unique (Trésorerie + Capitaux)":
                valeur_max_actuelle = int(df_filtre["Valeur Totale Actuelle RAW"].max())
                montant_cible = st.number_input(
                    "Définissez la Valeur Totale souhaitée pour chaque filiale :",
                    min_value=0,
                    value=valeur_max_actuelle,
                    step=1000000
                )
                
                for _, row in df_filtre.iterrows():
                    ecart_brut = max(0, montant_cible - row["Valeur Totale Actuelle RAW"])
                    plafond_max = row["Capitaux Propres RAW"]
                    apport_init = row["Apport Initial RAW"]
                    
                    injection_finale = ecart_brut
                    
                    if plafond_max < apport_init:
                        injection_finale = 0
                        alertes_securite.append(f"❌ **{row['Filiale']}** : **BLOCAGE STRICT** - Plus de valeur immobilière. Injection annulée.")
                    elif ecart_brut > plafond_max:
                        injection_finale = plafond_max
                        alertes_securite.append(f"🚨 **{row['Filiale']}** : Écart bridé à **{formater_monnaie_empire(plafond_max)}** pour protéger les Capitaux Propres")

                    import_rows.append({
                        "Filiale": row["Filiale"],
                        "Trésorerie Actuelle": formater_monnaie_empire(row["Trésorerie Actuelle RAW"]),
                        "Capitaux Propres": formater_monnaie_empire(plafond_max),
                        "Valeur Totale Actuelle": formater_monnaie_empire(row["Valeur Totale Actuelle RAW"]),
                        "Montant à Injecter RAW": injection_finale,
                        "Montant à Injecter (TAB)": formater_monnaie_empire(injection_finale)
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
                    plafond_max = row["Capitaux Propres RAW"]
                    apport_init = row["Apport Initial RAW"]
                    
                    injection_finale = part_egale
                    
                    if plafond_max < apport_init:
                        injection_finale = 0
                        alertes_securite.append(f"❌ **{row['Filiale']}** : **BLOCAGE STRICT** - Plus de valeur immobilière. Injection annulée.")
                    elif part_egale > plafond_max:
                        injection_finale = plafond_max
                        alertes_securite.append(f"🚨 **{row['Filiale']}** : Part bridée à **{formater_monnaie_empire(plafond_max)}** (Limite Capitaux Propres)")

                    import_rows.append({
                        "Filiale": row["Filiale"],
                        "Trésorerie Actuelle": formater_monnaie_empire(row["Trésorerie Actuelle RAW"]),
                        "Capitaux Propres": formater_monnaie_empire(plafond_max),
                        "Valeur Totale Actuelle": formater_monnaie_empire(row["Valeur Totale Actuelle RAW"]),
                        "Montant à Injecter RAW": injection_finale,
                        "Montant à Injecter (TAB)": formater_monnaie_empire(injection_finale)
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
            # Affichage propre sans coupure grâce au formatage texte string pré-géré
            df_affichage = df_resultat[["Filiale", "Trésorerie Actuelle", "Capitaux Propres", "Valeur Totale Actuelle", "Montant à Injecter (TAB)"]]
            st.dataframe(df_affichage, use_container_width=True)
            
            # Génération du texte d'importation au format brut (sans lettres) exigé par Empire Immo (Filiale[TAB]Montant)
            lignes_import = []
            for _, row in df_resultat.iterrows():
                if row["Montant à Injecter RAW"] > 0:
                    lignes_import.append(f"{row['Filiale']}\t{row['Montant à Injecter RAW']}")
            
            contenu_crlf_pur = "\r\n".join(lignes_import) + "\r\n"
            
            st.subheader("📋 Bloc d'importation direct")
            st.markdown("Cliquez en haut à droite du bloc noir pour copier la liste, puis collez-la directement dans Empire Immo :")
            st.code(contenu_crlf_pur, language="text")
            
            st.text_area("Alternative de copie rapide (CTRL+A puis CTRL+C) :", value=contenu_crlf_pur, height=150, key="copie_secours_eq")
            st.download_button("📥 Télécharger le fichier d'import pur (.txt)", data=contenu_crlf_pur, file_name="equilibrage_valeur_empire.txt", mime="text/plain")

    except Exception as e:
        st.error(f"⚠️ Erreur lors du calcul de l'équilibrage : {str(e)}")
