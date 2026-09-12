import streamlit as st
import requests

st.title("💰 Gestion & Contrôle des Primes")
st.markdown("Calcule la part des primes en fonction du tableau financier, et applique un filtrage et plafonnement strict basé sur le poste **PDG** (en excluant Grego73, BTP et Constructions).")

# --- PARAMÈTRES DE RÉPARTITION ---
st.subheader("🎛️ Choix de la répartition des gains")
col1, col2 = st.columns(2)
with col1:
    pct_holding = st.slider("Pourcentage pour la Holding (%)", min_value=0, max_value=100, value=50, step=5)
with col2:
    pct_prime = 100 - pct_holding
    st.metric(label="Pourcentage pour la Prime (%)", value=f"{pct_prime}%")

# --- ZONES DE SAISIE ---
st.subheader("📋 Saisie des données du jour")

donnees_exploitation = st.text_area(
    "1. Collez ici le tableau financier classique (contenant le 'Résultat d'exploitation') :", 
    height=250, 
    key="data_tab_exploitation",
    placeholder="Filiale\tTrésorerie\tRésultat d'exploitation..."
)

donnees_plafonds = st.text_area(
    "2. Collez ici le tableau des directeurs (contenant la colonne 'Poste', 'Directeur' et 'Prime Max') :", 
    height=250, 
    key="data_tab_plafonds",
    placeholder="Filiale\tPoste\tDirecteur\tPrime Max..."
)

if st.button("🚀 Calculer, Filtrer et Envoyer sur Discord", use_container_width=True):
    if not donnees_exploitation.strip():
        st.error("❌ Le tableau financier classique (Tableau 1) est vide.")
    elif not donnees_plafonds.strip():
        st.error("❌ Le tableau des directeurs (Tableau 2) est vide.")
    else:
        try:
            url_webhook = st.secrets["webhooks"]["primes"]
            
            # --- 🛠️ ETAPE 1 : EXTRACTION DU TABLEAU DES DIRECTEURS ---
            plafonds_extraits = {}
            lignes_plafonds = donnees_plafonds.strip().split('\n')
            index_debut_plafonds = 1 if "poste" in donnees_plafonds.lower() else 0
            
            for ligne in lignes_plafonds[index_debut_plafonds:]:
                if not ligne.strip(): continue
                colonnes = ligne.split('\t')
                if len(colonnes) < 4: continue
                
                nom_filiale = colonnes[0].strip()
                poste = colonnes[1].strip()
                directeur = colonnes[2].strip()
                raw_prime_max = colonnes[3].strip()
                
                if poste.upper() == "PDG":
                    if directeur.upper() == "GREGO73":
                        continue
                    if "CONSTRUCTIONS" in nom_filiale.upper() or "BTP" in nom_filiale.upper():
                        continue
                        
                    valeur_plafond = int(raw_prime_max) if raw_prime_max.isdigit() else 0
                    plafonds_extraits[nom_filiale] = valeur_plafond

            # --- 🛠️ ETAPE 2 : CALCULS ET CROISEMENT ---
            lignes_exploitation = donnees_exploitation.strip().split('\n')
            import_primes = ["Filiale\tPrimes"]
            lignes_rapport_comparatif = ["--- RAPPORT COMPARATIF DES PRIMES ---"]
            alertes_blocage = []
            
            index_debut_exploitation = 1 if ("filiale" in donnees_exploitation.lower() or "trésorerie" in donnees_exploitation.lower()) else 0
            
            for ligne in lignes_exploitation[index_debut_exploitation:]:
                if not ligne.strip(): continue
                colonnes = ligne.split('\t')
                if len(colonnes) < 3: continue
                
                nom_filiale = colonnes[0].strip()
                
                if nom_filiale not in plafonds_extraits:
                    continue
                    
                raw_valeur = colonnes[2].strip() # 3ème colonne
                valeur_exploitation = int(raw_valeur) if raw_valeur.isdigit() else 0
                valeur_prime_calculee = int(valeur_exploitation * (pct_prime / 100))
                
                plafond_max = plafonds_extraits[nom_filiale]
                prime_finale_envoyee = valeur_prime_calculee
                status_texte = "✅ OK"
                
                if valeur_prime_calculee > plafond_max:
                    prime_finale_envoyee = plafond_max
                    status_texte = "🚨 BRIDÉ"
                    # Modification du message d'alerte à l'écran pour bien afficher "Prime calculée"
                    alertes_blocage.append(
                        f"⚠️ **{nom_filiale}** : Prime calculée de **{valeur_prime_calculee}** ({pct_prime}%) "
                        f"bridée ➡️ **{plafond_max}** (Max autorisé)"
                    )

                import_primes.append(f"{nom_filiale}\t{prime_finale_envoyee}")
                
                lignes_rapport_comparatif.append(
                    f"🏢 {nom_filiale} :\n"
                    f"  - Prime calculee ({pct_prime}%) : {valeur_prime_calculee}\n"
                    f"  - Prime Max autorisee : {plafond_max}\n"
                    f"  - Statut : {status_texte}\n"
                )
            
            crlf_primes = "\r\n".join(import_primes) + "\r\n"
            
            lignes_rapport_comparatif.append("\n\n--- TABLEAU D'IMPORT FINAL ---")
            lignes_rapport_comparatif.append(crlf_primes)
            contenu_fichier_complet = "\r\n".join(lignes_rapport_comparatif) + "\r\n"
            
            # --- 🛠️ ETAPE 3 : ENVOI DISCORD ---
            texte_discord = f"📊 **RAPPORT DE CONTRÔLE DES PRIMES ({pct_holding}/{pct_prime})**\n"
            texte_discord += "Calculs basés sur le Résultat d'exploitation. Exclusions appliquées : Non-PDG, Grego73, BTP et Constructions.\n\n"
            
            if alertes_blocage:
                texte_discord += "🚨 **MODIFICATIONS APPLIQUÉES (PLAFOND ATTEINT) :**\n"
                for alerte in alertes_blocage:
                    texte_discord += f"{alerte}\n"
                    st.warning(alerte) # Affiche le nouveau message clair sur Streamlit
                texte_discord += "\n"
            else:
                st.success("✅ Toutes les filiales valides respectent les plafonds du jour !")
                texte_discord += "✅ Aucun dépassement détecté.\n"
                
            texte_discord += "\n📥 *Le détail complet ainsi que le texte d'importation se trouvent dans le fichier joint ci-dessous.*"
            
            fichiers = {'file': ('primes_et_rapport_import.txt', contenu_fichier_complet, 'text/plain')}
            reponse = requests.post(url_webhook, data={'content': texte_discord}, files=fichiers)
            
            if reponse.status_code == 200:
                st.success("🎉 Calculs réussis et transmis à Discord sans erreur !")
                st.download_button("📥 Télécharger le rapport & import", data=contenu_fichier_complet, file_name="primes_et_rapport_import.txt", mime="text/plain")
            else:
                st.error(f"🤖 Erreur Discord : {reponse.status_code}")
                
        except ValueError:
            st.error("❌ Erreur : Format de nombre incorrect dans l'un des deux tableaux.")
        except Exception as e:
            st.error(f"⚠️ Erreur système : {str(e)}")
