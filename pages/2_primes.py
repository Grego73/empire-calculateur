import streamlit as st
import requests

st.title("💰 Gestion & Contrôle des Primes")
st.markdown("Calcule la part des primes en fonction du tableau financier, et applique un filtrage et plafonnement strict basé sur le poste **PDG**.")

col1, col2 = st.columns(2)
with col1:
    pct_holding = st.slider("Pourcentage pour la Holding (%)", min_value=0, max_value=100, value=50, step=5)
with col2:
    pct_prime = 100 - pct_holding
    st.metric(label="Pourcentage pour la Prime (%)", value=f"{pct_prime}%")

st.subheader("📋 Saisie des données du jour")
donnees_exploitation = st.text_area("1. Collez ici le tableau financier classique :", height=250, key="data_tab_exploitation")
donnees_plafonds = st.text_area("2. Collez ici le tableau des directeurs :", height=250, key="data_tab_plafonds")

if st.button("🚀 Calculer, Filtrer et Envoyer sur Discord", use_container_width=True):
    if not donnees_exploitation.strip() or not donnees_plafonds.strip():
        st.error("❌ L'un des deux tableaux est vide.")
    else:
        try:
            url_webhook = st.secrets["webhooks"]["primes"]
            
            # Étape 1 : Plafonds
            plafonds_extraits = {}
            lignes_plafonds = donnees_plafonds.strip().split('\n')
            index_debut_plafonds = 1 if "poste" in donnees_plafonds.lower() else 0
            for ligne in lignes_plafonds[index_debut_plafonds:]:
                if not ligne.strip(): continue
                colonnes = ligne.split('\t')
                if len(colonnes) < 4: continue
                nom_filiale, poste, directeur, raw_prime_max = colonnes[0].strip(), colonnes[1].strip(), colonnes[2].strip(), colonnes[3].strip()
                if poste.upper() == "PDG" and directeur.upper() != "GREGO73" and "CONSTRUCTIONS" not in nom_filiale.upper() and "BTP" not in nom_filiale.upper():
                    plafonds_extraits[nom_filiale] = int(raw_prime_max) if raw_prime_max.isdigit() else 0

            # Étape 2 : Calculs du tableau financier pur pour l'importateur
            lignes_exploitation = donnees_exploitation.strip().split('\n')
            
            # L'en-tête officielle pour les primes doit être "Filiale\tPrimes"
            import_primes = ["Filiale\tPrimes"] 
            alertes_blocage = []
            
            index_debut_exploitation = 1 if ("filiale" in donnees_exploitation.lower() or "trésorerie" in donnees_exploitation.lower()) else 0
            for ligne in lignes_exploitation[index_debut_exploitation:]:
                if not ligne.strip(): continue
                colonnes = ligne.split('\t')
                if len(colonnes) < 3: continue
                nom_filiale, raw_valeur = colonnes[0].strip(), colonnes[2].strip()
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
            
            # --- STRUCTURE DU MESSAGE DISCORD ADAPTÉE ---
            texte_discord = f"📊 **RAPPORT DE CONTRÔLE DES PRIMES ({pct_holding}/{pct_prime})**\n"
            if alertes_blocage:
                texte_discord += "🚨 **MODIFICATIONS APPLIQUÉES (PLAFOND ATTEINT) :**\n" + "\n".join(alertes_blocage) + "\n\n"
                for alerte in alertes_blocage: st.warning(alerte)
            else:
                st.success("✅ Toutes les filiales valides respectent les plafonds !")

            texte_discord += "📥 **Téléchargez directement le fichier joint ci-dessous** pour l'importer sur Empire Immo (le bouton copier de Discord casse le format)."
            
            # Envoi vers Discord du fichier joint et du texte explicatif
            fichiers = {'file': ('primes_import_officiel.txt', crlf_primes_pur, 'text/plain')}
            reponse = requests.post(url_webhook, data={'content': texte_discord}, files=fichiers)
            
            if reponse.status_code == 200:
                st.success("🎉 Calculs réussis ! Le fichier d'importation officiel a été envoyé sur Discord.")
                st.download_button("📥 Télécharger le fichier d'import pur", data=crlf_primes_pur, file_name="primes_import_officiel.txt", mime="text/plain")
            else:
                st.error(f"🤖 Erreur Discord : {reponse.status_code}")
        except Exception as e:
            st.error(f"⚠️ Erreur système : {str(e)}")
