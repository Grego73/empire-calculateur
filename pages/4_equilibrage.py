import streamlit as st
import pandas as pd
import re

st.title("⚖️ Équilibrage de la Valeur Réelle")
st.markdown("Calculez les injections nécessaires pour équilibrer la **Somme Globale (Trésorerie + Capitaux Propres)** de vos filiales.")

# Initialisation de la version du composant pour forcer la mise à jour visuelle
if "version_calcul" not in st.session_state:
    st.session_state["version_calcul"] = 0

# 1. FONCTION DE CONVERSION EN MONNAIE EMPIRE (SENS : NOMBRE -> TEXTE)
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

# 2. FONCTION DE TRADUCTION INVERSÉE (SENS : TEXTE ABREGE -> ENTIER PUR)
def convertir_saisie_en_nombre(saisie_texte):
    texte_propre = str(saisie_texte).strip().upper().replace(" ", "").replace("€", "")
    if not texte_propre:
        return 0
        
    dictionnaire_paliers = {
        "G": 10**3,  "T": 10**6,  "P": 10**9,  "E": 10**12,
        "Z": 10**15, "Y": 10**18, "R": 10**21, "Q": 10**24,
        "U": 10**27, "S": 10**30, "X": 10**33, "N": 10**36,
        "D": 10**39
    }
    
    match = re.match(r"^([0-9\.,]+)([A-Z]?)$", texte_propre)
    if match:
        nombre_partie = match.group(1).replace(",", ".")
        suffixe_partie = match.group(2)
        
        try:
            valeur_num = float(nombre_partie)
            if suffixe_partie in dictionnaire_paliers:
                return int(valeur_num * dictionnaire_paliers[suffixe_partie])
            return int(valeur_num)
        except:
            return 0
    return 0

# Fonction qui force le changement de version de la case de texte
def declencher_recalcul():
    st.session_state["version_calcul"] += 1

# Vérification si les données ont bien été synchronisées depuis l'accueil
if not st.session_state.get("donnees_chargees", False):
    st.warning("⚠️ Veuillez d'abord coller vos tableaux et cliquer sur le bouton de synchronisation sur la page d'accueil 🏠 avant d'utiliser cette page.")
else:
    tab_finance = st.session_state.get("tab_finance", "")
    tab_capital = st.session_state.get("tab_capital", "")

    try:
        # 1. Extraction des filiales et de leur trésorerie actuelle (Tableau Finance)
        lignes_fin = tab_finance.strip().split('\n')
        idx_debut_fin = 1 if lignes_fin and ("filiale" in lignes_fin.lower() or "trésorerie" in lignes_fin.lower()) else 0
        
        data_fin = {}
        for ligne in lignes_fin[idx_debut_fin:]:
            if not ligne.strip(): continue
            colonnes = [c.strip() for c in ligne.split('\t') if c.strip()]
            if len(colonnes) < 2: continue
            nom_filiale = colonnes
            treso = int(colonnes.replace(" ", "").replace("€", ""))
            data_fin[nom_filiale] = treso

        # 2. Extraction du Capital (Tableau Capital)
        lignes_cap = tab_capital.strip().split('\n')
        idx_debut_cap = 1 if lignes_cap and ("filiale" in lignes_cap.lower() or "apport" in lignes_cap.lower()) else 0
        
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
        
        st.markdown("**1. Cochez les filiales à inclure dans l'opération :**")
        all_filiales = df_base["Filiale"].tolist()
        
        # On attache la fonction pour détecter le clic et le décochage
        filiales_choisies = st.multiselect(
            "Filiales cibles :", 
            options=all_filiales, 
            default=all_filiales,
            on_change=declencher_recalcul
        )
        
        if not filiales_choisies:
            st.warning("⚠️ Veuillez sélectionner au moins une filiale.")
        else:
            df_filtre = df_base[df_base["Filiale"].isin(filiales_choisies)].copy()
            
            mode = st.radio(
                "**2. Choisissez la méthode de calcul :**",
                ["⚖️ Équilibrer vers une Valeur Cible unique (Trésorerie + Capitaux)", "💰 Diviser et injecter une enveloppe globale"]
            )
            
            import_rows = []
            
            # --- MODE 1 : ÉQUILIBRAGE VERS CIBLE DYNAMIQUE COMPLET ---
            if mode == "⚖️ Équilibrer vers une Valeur Cible unique (Trésorerie + Capitaux)":
                valeur_max_actuelle = int(df_filtre["Valeur Totale Actuelle RAW"].max())
                
                # Le paramètre key inclut le numéro de version de calcul, ce qui force Streamlit
                # à rafraîchir complètement la valeur par défaut du champ lors d'une modification
                saisie_cible = st.text_input(
                    "Définissez la Valeur Totale souhaitée (Exemples valides : 100Y, 1500E, ou un nombre brut) :",
                    value=str(valeur_max_actuelle),
                    key=f"input_cible_ver_{st.session_state['version_calcul']}"
                )
                montant_cible = convertir_saisie_en_nombre(saisie_cible)
                st.caption(f"ℹ️ Valeur cible interprétée : **{formater_monnaie_empire(montant_cible)}**")
                
                for _, row in df_filtre.iterrows():
                    ecart_brut = max(0, montant_cible - row["Valeur Totale Actuelle RAW"])
                    import_rows.append({
                        "Filiale": row["Filiale"],
                        "Trésorerie Actuelle": formater_monnaie_empire(row["Trésorerie Actuelle RAW"]),
                        "Capitaux Propres": formater_monnaie_empire(row["Capitaux Propres RAW"]),
                        "Valeur Totale Actuelle": formater_monnaie_empire(row["Valeur Totale Actuelle RAW"]),
                        "Montant à Injecter RAW": ecart_brut,
                        "Montant à Injecter (TAB)": formater_monnaie_empire(ecart_brut)
                    })
            
            # --- MODE 2 : INJECTION ENVELOPPE GLOBALE ---
            else:
                saisie_enveloppe = st.text_input(
                    "Montant total de l'enveloppe à distribuer (Exemples valides : 50Y, 2000P, ou un nombre brut) :",
                    value="10000000"
                )
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

            # --- RENDU ET AFFICHAGE ---
            df_resultat = pd.DataFrame(import_rows)
            st.success("✅ Calculs mis à jour en temps réel selon les filiales sélectionnées.")

            st.subheader("📊 Plan d'importation validé")
            df_affichage = df_resultat[["Filiale", "Trésorerie Actuelle", "Capitaux Propres", "Valeur Totale Actuelle", "Montant à Injecter (TAB)"]]
            st.dataframe(df_affichage, use_container_width=True)
            
            # Génération du texte d'importation pur (Filiale[TAB]Montant entier)
            lignes_import = []
            for _, row in df_resultat.iterrows():
                if row["Montant à Injecter RAW"] > 0:
                    lignes_import.append(f"{row['Filiale']}\t{row['Montant à Injecter RAW']}")
            
            contenu_crlf_pur = "\r\n".join(lignes_import) + "\r\n"
            
            st.subheader("📋 Bloc d'importation direct")
            st.markdown("Cliquez en haut à droite du bloc noir pour copier la liste, puis collez-la directement dans Empire Immo :")
            st.code(contenu_crlf_pur, language="text")
            
            st.download_button("📥 Télécharger le fichier d'import pur (.txt)", data=contenu_crlf_pur, file_name="equilibrage_valeur_empire.txt", mime="text/plain")

    except Exception as e:
        st.error(f"⚠️ Erreur lors du calcul de l'équilibrage : {str(e)}")
