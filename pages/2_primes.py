import streamlit as st
import requests

st.title("💰 Gestion & Contrôle des Primes")
st.markdown("Calcule la part des primes en fonction du tableau financier, et applique un plafonnement dynamique basé sur votre tableau de Primes Max.")

# --- PARAMÈTRES DE RÉPARTITION ---
st.subheader("🎛️ Choix de la répartition des gains")
col1, col2 = st.columns(2)
with col1:
    pct_holding = st.slider("Pourcentage pour la Holding (%)", min_value=0, max_value=100, value=50, step=5)
with col2:
    pct_prime = 100 - pct_holding
    st.metric(label="Pourcentage pour la Prime (%)", value=f"{pct_prime}%")

# --- ZONES DE SAISIE DES DEUX TABLEAUX ---
st.subheader("📋 Saisie des données du jour")

# 1. Zone pour le tableau contenant les plafonds
donnees_plafonds = st.text_area(
    "1. Collez ici le tableau des directeurs (contenant la colonne 'Prime Max') :", 
    height=200, 
    key="data_tab_plafonds",
    placeholder="Filiale\tPoste\tDirecteur\tPrime Max\tPrime..."
)

# 2. Zone pour le tableau financier classique
donnees_exploitation = st.text_area(
    "2. Collez ici le tableau financier classique (contenant le 'Résultat d'exploitation') :", 
    height=250, 
    key="data_tab_exploitation",
    placeholder="Filiale\tTrésorerie\tRésultat d'exploitation\tRésultat NET..."
)

if st.button("🚀 Calculer, Brider et Envoyer sur Discord", use_container_width=True):
    if not donnees_plafonds.strip():
        st.error("❌ Le tableau des Primes Max (Tableau 1) est vide.")
    elif not donnees_exploitation.strip():
        st.error("❌ Le tableau financier classique (Tableau 2) est vide.")
    else:
        try:
            url_webhook = st.secrets["webhooks"]["primes"]
            
            # --- 🛠️ ETAPE 1 : EXTRACTION DYNAMIQUE DES PLAFONDS ---
            plafonds_extraits = {}
            lignes_plafonds = donnees_plafonds.strip().split('\n')
            
            # Détection de l'en-tête du premier tableau
            index_debut_plafonds = 1 if lignes_plafonds and "poste" in lignes_plafonds[0].lower() else 0
            
            for ligne in lignes_plafonds[index_debut_plafonds:]:
                if not ligne.strip(): continue
                colonnes = ligne.split('\t')
                if len(colonnes) < 4: continue # S'assure qu'on a le nom de la filiale et la prime max
                
                nom_filiale = colonnes[0].strip()
                poste = colonnes[1].strip()
                raw_prime_max = colonnes[3].strip() # 4ème colonne : Prime Max
                
                # On ne prend le plafond que si la ligne correspond au poste "PDG"
                if poste.upper() == "PDG":
                    valeur_plafond = int(raw_prime_max) if raw_prime_max.isdigit() else 0
                    plafonds_extraits[nom_filiale] = valeur_plafond

            # --- 🛠️ ETAPE 2 : TRAITEMENT DU TABLEAU FINANCIER ET CALCULS ---
            lignes_exploitation = donnees_exploitation.strip().split('\n')
            import_primes = ["Filiale\tPrimes"]
            lignes_rapport_comparatif = []
            alertes_blocage = []
            
            index_debut_exploitation = 1 if lignes_exploitation and ("filiale" in lignes_exploitation[0].lower() or "trésorerie" in lignes_exploitation[0].lower()) else 0
            
            for ligne in lignes_exploitation[index_debut_exploitation:]:
                if not ligne.strip(): continue
                colonnes = ligne.split('\t')
                if len(colonnes) < 3: continue
                
                nom_filiale = colonnes[0].strip()
                raw_valeur = colonnes[2].strip() # 3ème colonne : Résultat d'exploitation
                
                valeur_exploitation = int(raw_valeur) if raw_valeur.isdigit() else 0
                valeur_prime_calculee = int(valeur_exploitation * (pct_prime / 100))
                
                # Récupération du plafond extrait dynamiquement (ou valeur infinie si absent du 1er tableau)
                plafond_max = plafonds_extraits.get(nom_filiale, 999999999999999999999999)
                
                prime_finale_envoyee = valeur_prime_calculee
                status_texte = "✅ OK"
                
                if valeur_prime_calculee > plafond_max:
                    prime_finale_envoyee = plafond_max
                    status_texte = "🚨 BRIDÉ (Plafond atteint)"
                    alertes_blocage.append(f"⚠️ **{nom_filiale}** : Prime calculée bridée de {valeur_prime_calculee} ➡️ **{plafond_max}** (Max)")

                import_primes.append(f"{nom_filiale}\t{prime_finale_envoyee}")
                
                lignes_rapport_comparatif.append(
                    f"🏢 **{nom_filiale}** :\n"
                    f"  • Prime calculée : {valeur_prime_calculee}\n"
                    f"  • Prime Max autorisée : {plafond_max}\n"
                    f"  • Statut : {status_texte}\n"
                )
            
            # Formatage final au format CRLF
            crlf_primes = "\r\n".join(import_primes) + "\r\n"
            
            # --- 🛠️ ETAPE 3 : ENVOI DU RAPPORT COMPLET SUR DISCORD ---
            texte_discord = f"📊 **RAPPORT DE CONTRÔLE DYNAMIQUE DES PRIMES ({pct_holding}/{pct_prime})**\n"
            texte_discord += f"Plafonds extraits en direct du tableau des directeurs fourni.\n\n"
            
            if alertes_blocage:
                texte_discord += "🚨 **MODIFICATIONS APPLIQUÉES (PLAFOND ATTEINT) :**\n"
                for alerte in alertes_blocage:
                    texte_discord += f"{alerte}\n"
                    st.warning(alerte)
                texte_discord += "\n"
            else:
                st.success("✅ Toutes les primes calculées respectent vos plafonds du jour !")
            
            texte_discord += "**📋 COMPARATIF DÉTAILLÉ PAR FILIALE :**\n"
            for ligne_comp in lignes_rapport_comparatif:
                texte_discord += ligne_comp
                
            texte_discord += "\n**💾 Fichier d'importation final (Primes bridées) :**\n"
            texte_discord += f"```text\n{crlf_primes}```"
            
            fichiers = {'file': ('primes_securisees_import.txt', crlf_primes, 'text/plain')}
            reponse = requests.post(url_webhook, data={'content': texte_discord}, files=fichiers)
            
            if reponse.status_code == 200:
                st.success("🎉 Calculs effectués et envoyés sur Discord !")
                st.download_button("📥 Télécharger le fichier final", data=crlf_primes, file_name="import_primes_securisees.txt", mime="text/plain")
            else:
                st.error(f"🤖 Erreur Discord : {reponse.status_code}")
                
        except ValueError:
            st.error("❌ Erreur : L'un des deux tableaux contient des données ou des chiffres mal formés.")
        except Exception as e:
            st.error(f"⚠️ Erreur système : {str(e)}")
