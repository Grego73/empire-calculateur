import streamlit as st
import requests
from utils import formater_monnaie_empire, convertir_saisie_en_nombre

st.title("💰 Gestion & Contrôle des Primes")
st.markdown("Calcule la part des primes et applique le filtrage et plafonnement strict basé sur le poste **PDG**.")

if not st.session_state.get("holding_chargee", False):
    st.warning("⚠️ Veuillez d'abord coller vos tableaux et cliquer sur le bouton de synchronisation sur la page d'accueil 🏠 avant d'utiliser cette page.")
else:
    donnees_exploitation = st.session_state.get("tab_finance", "")
    donnees_plafonds = st.session_state.get("tab_primes", "")

    col1, col2 = st.columns(2)
    with col1:
        pct_holding = st.slider("Pourcentage pour la Holding (%)", min_value=0, max_value=100, value=50, step=5)
    with col2:
        pct_prime = 100 - pct_holding
        st.metric(label="Pourcentage pour la Prime (%)", value=f"{pct_prime}%")

    # --- OPTION DE MISE À ZÉRO GLOBALE POUR TOUTES LES FILIALES ---
    st.markdown("---")
    forcer_zero = st.checkbox("🛑 Forcer TOUTES les filiales à zéro pour cet import (Mise à zéro générale)", value=False)
    st.markdown("---")

    tab1, tab2 = st.tabs(["🔍 Tableau Finance connecté", "🔍 Tableau Plafonds connecté"])
    with tab1: st.text(donnees_exploitation)
    with tab2: st.text(donnees_plafonds)

    if st.button("🚀 Calculer, Filtrer et Envoyer sur Discord", use_container_width=True):
        try:
            url_webhook = st.secrets["webhooks"]["primes"]
            
            # Étape 1 : Extraction et filtrage sécurisé des plafonds (Utile uniquement si forcer_zero est Faux)
            plafonds_extraits = {}
            if not forcer_zero:
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
                    
                    if poste.upper() == "PDG" and directeur.upper() != "GREGO73" and "CONSTRUCTIONS" not in nom_filiale.upper() and "BTP" not in nom_filiale.upper():
                        plafonds_extraits[nom_filiale] = convertir_saisie_en_nombre(raw_prime_max)

            # Étape 2 : Traitement des filiales du tableau financier
            lignes_exploitation = donnees_exploitation.strip().split('\n')
            import_primes = ["Filiale\tPrimes"] 
            alertes_blocage = []
            
            index_debut_exploitation = 1 if ("filiale" in donnees_exploitation.lower() or "trésorerie" in donnees_exploitation.lower()) else 0
            for ligne in lignes_exploitation[index_debut_exploitation:]:
                if not ligne.strip(): continue
                colonnes = ligne.split('\t')
                if len(colonnes) < 3: continue
                
                nom_filiale = colonnes[0].strip()
                raw_valeur = colonnes[2].strip()
                
                # LOGIQUE DE MISE À ZÉRO GÉNÉRALE : Prend TOUTES les filiales du tableau
                if forcer_zero:
                    import_primes.append(f"{nom_filiale}\t0")
                else:
                    # Logique classique filtrée par les critères PDG
                    if nom_filiale not in plafonds_extraits: continue
                    
                    valeur_exploitation = convertir_saisie_en_nombre(raw_valeur)
                    valeur_prime_calculee = int(valeur_exploitation * (pct_prime / 100))
                    plafond_max = plafonds_extraits[nom_filiale]
                    
                    prime_finale = valeur_prime_calculee
                    if valeur_prime_calculee > plafond_max:
                        prime_finale = plafond_max
                        alertes_blocage.append(f"⚠️ **{nom_filiale}** : Calculé **{formater_monnaie_empire(valeur_prime_calculee)}** ➡️ Bridé à **{formater_monnaie_empire(plafond_max)}**")

                    import_primes.append(f"{nom_filiale}\t{prime_finale}")
            
            crlf_primes_pur = "\r\n".join(import_primes) + "\r\n"
            
            # Message Discord adaptatif
            if forcer_zero:
                texte_discord = "🛑 **RAPPORT GÉNÉRAL : TOUTES LES FILIALES DE L'EMPIRE ONT ÉTÉ FORCÉES À 0 !**\n"
                st.info("ℹ️ Remise à niveau globale : L'intégralité des filiales a été injectée à 0 dans le fichier d'import.")
            else:
                texte_discord = f"📊 **RAPPORT DE CONTRÔLE DES PRIMES ({pct_holding}/{pct_prime})**\n"
                if alertes_blocage:
                    texte_discord += "🚨 **MODIFICATIONS APPLIQUÉES (PLAFOND ATTEINT) :**\n" + "\n".join(alertes_blocage) + "\n\n"
                    for alerte in alertes_blocage: st.warning(alerte)
                else:
                    st.success("✅ Toutes les filiales valides respectent les plafonds !")

            texte_discord += "📋 **Texte d'importation prêt à être copié :**\n"
            if len(texte_discord) + len(crlf_primes_pur) < 1900:
                texte_discord += f"```text\n{crlf_primes_pur}```"
            else:
                texte_discord += "⚠️ *Tableau trop long. Utilisez le fichier joint.*"
            
            fichiers = {'file': ('primes_import_officiel.txt', crlf_primes_pur, 'text/plain')}
            reponse = requests.post(url_webhook, data={'content': texte_discord}, files=fichiers)
            
            if reponse.status_code == 200 or reponse.status_code == 204:
                st.success("🎉 Calculs réussis et rapport envoyé sur Discord !")
                st.code(crlf_primes_pur, language="text")
                st.download_button(label="📥 Télécharger le fichier .txt", data=crlf_primes_pur, file_name="primes_import_officiel.txt", mime="text/plain")
            else:
                st.error(f"🤖 Erreur Discord : {reponse.status_code}")
                
        except Exception as e:
            st.error(f"⚠️ Erreur système : {str(e)}")
