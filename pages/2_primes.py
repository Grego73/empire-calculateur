import streamlit as st
import requests

st.title("💰 Gestion & Contrôle des Primes")
st.markdown("Calcule la part des primes et applique le filtrage et plafonnement strict basé sur le poste **PDG**.")

# Vérification si les données ont bien été synchronisées depuis l'accueil
if not st.session_state.get("donnees_chargees", False):
    st.warning("⚠️ Veuillez d'abord coller vos tableaux et cliquer sur le bouton de synchronisation sur la page d'accueil 🏠 avant d'utiliser cette page.")
else:
    # Récupération automatique des données depuis la mémoire centrale
    donnees_exploitation = st.session_state.get("tab_finance", "")
    donnees_plafonds = st.session_state.get("tab_primes", "")

    # Réglage des pourcentages (Slider dynamique)
    col1, col2 = st.columns(2)
    with col1:
        pct_holding = st.slider("Pourcentage pour la Holding (%)", min_value=0, max_value=100, value=50, step=5)
    with col2:
        pct_prime = 100 - pct_holding
        st.metric(label="Pourcentage pour la Prime (%)", value=f"{pct_prime}%")

    # Rappel visuel des données récupérées sous forme d'onglets discrets
    tab1, tab2 = st.tabs(["🔍 Tableau Finance connecté", "🔍 Tableau Plafonds connecté"])
    with tab1:
        st.text(donnees_exploitation)
    with tab2:
        st.text(donnees_plafonds)

    if st.button("🚀 Calculer, Filtrer et Envoyer sur Discord", use_container_width=True):
        try:
            url_webhook = st.secrets["webhooks"]["primes"]
            
            # Étape 1 : Extraction et filtrage des plafonds
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
                
                # Règle stricte : Poste PDG uniquement, pas Grego73, pas de Constructions, pas de BTP
                if poste.upper() == "PDG" and directeur.upper() != "GREGO73" and "CONSTRUCTIONS" not in nom_filiale.upper() and "BTP" not in nom_filiale.upper():
                    plafonds_extraits[nom_filiale] = int(raw_prime_max) if raw_prime_max.isdigit() else 0

            # Étape 2 : Calculs du tableau financier pur pour l'importateur
            lignes_exploitation = donnees_exploitation.strip().split('\n')
            
            # L'en-tête officielle obligatoire pour les primes
            import_primes = ["Filiale\tPrimes"] 
            alertes_blocage = []
            
            index_debut_exploitation = 1 if ("filiale" in donnees_exploitation.lower() or "trésorerie" in donnees_exploitation.lower()) else 0
            for ligne in lignes_exploitation[index_debut_exploitation:]:
                if not ligne.strip(): continue
                colonnes = ligne.split('\t')
                if len(colonnes) < 3: continue
                
                nom_filiale = colonnes[0].strip()
                raw_valeur = colonnes[2].strip() # Résultat d'exploitation (3ème colonne)
                
                if nom_filiale not in plafonds_extraits: continue
                
                valeur_exploitation = int(raw_valeur) if raw_valeur.isdigit() else 0
                valeur_prime_calculee = int(valeur_exploitation * (pct_prime / 100))
                plafond_max = plafonds_extraits[nom_filiale]
                
                prime_finale = valeur_prime_calculee
                if valeur_prime_calculee > plafond_max:
                    prime_finale = plafond_max
                    alertes_blocage.append(f"⚠️ **{nom_filiale}** : Calculé **{valeur_prime_calculee}** ➡️ Bridé à **{plafond_max}** (Max)")

                import_primes.append(f"{nom_filiale}\t{prime_finale}")
            
            crlf_primes_pur = "\r\n".join(import_primes) + "\r\n"
            
            # --- STRUCTURE DU MESSAGE DISCORD ---
            texte_discord = f"📊 **RAPPORT DE CONTRÔLE DES PRIMES ({pct_holding}/{pct_prime})**\n"
            if alertes_blocage:
                texte_discord += "🚨 **MODIFICATIONS APPLIQUÉES (PLAFOND ATTEINT) :**\n" + "\n".join(alertes_blocage) + "\n\n"
                for alerte in alertes_blocage: st.warning(alerte)
            else:
                st.success("✅ Toutes les filiales valides respectent les plafonds !")

            texte_discord += "📋 **Texte d'importation prêt à être copié (Copiez bien TOUT le bloc gris d'un coup) :**\n"
            if len(texte_discord) + len(crlf_primes_pur) < 1900:
                texte_discord += f"```text\n{crlf_primes_pur}```"
            else:
                texte_discord += "⚠️ *Tableau trop long pour l'affichage plein texte Discord. Utilisez impérativement le fichier joint.*"
            
            # Envoi vers Discord du fichier joint et du texte du rapport
            fichiers = {'file': ('primes_import_officiel.txt', crlf_primes_pur, 'text/plain')}
            reponse = requests.post(url_webhook, data={'content': texte_discord}, files=fichiers)
            
            if reponse.status_code == 200 or reponse.status_code == 204:
                st.success("🎉 Calculs réussis et rapport envoyé sur Discord !")
                
                # --- AFFICHAGE SUR LE SITE AVEC LES OPTIONS DE COPIE ---
                st.subheader("📋 Résultat prêt à être copié :")
                st.markdown("Utilisez l'icône en haut à droite du bloc noir ci-dessous pour copier les primes :")
                st.code(crlf_primes_pur, language="text")
                
                # Zone alternative pour le CTRL+A / CTRL+C tactile/rapide
                st.text_area("Alternative de copie rapide (Faites CTRL+A puis CTRL+C dedans) :", value=crlf_primes_pur, height=150, key="copie_secours_primes")
                
                # Téléchargement sécurisé du fichier physique
                st.download_button(
                    label="📥 Télécharger le fichier d'import pur", 
                    data=crlf_primes_pur, 
                    file_name="primes_import_officiel.txt", 
                    mime="text/plain"
                )
            else:
                st.error(f"🤖 Erreur Discord : {reponse.status_code}")
                
        except Exception as e:
            st.error(f"⚠️ Erreur système : {str(e)}")
