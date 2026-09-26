import streamlit as st
import pandas as pd
import requests
from utils import formater_monnaie_empire, convertir_saisie_en_nombre, recuperer_derniere_donnee_table

st.title("💰 Gestion & Contrôle des Primes (Via SQL)")
st.markdown("Calculez la part des primes et appliquez le filtrage et le plafonnement strict basé sur le poste **PDG** depuis la base de données.")

# Vérification des prérequis de la holding (tableaux manuels de l'accueil)
if not st.session_state.get("holding_chargee", False):
    st.warning("⚠️ Veuillez d'abord coller vos tableaux et cliquer sur le bouton de synchronisation sur la page d'accueil 🏠 avant d'utiliser cette page.")
else:
    # 📥 Extraction des données financières brutes de la session (Tableau Finance et Tableau Primes de l'accueil)
    donnees_exploitation = st.session_state.get("tab_finance", "")
    donnees_plafonds = st.session_state.get("tab_primes", "")

    # Config de répartition de la Holding
    col1, col2 = st.columns(2)
    with col1:
        pct_holding = st.slider("Pourcentage pour la Holding (%)", min_value=0, max_value=100, value=50, step=5)
    with col2:
        pct_prime = 100 - pct_holding
        st.metric(label="Pourcentage pour la Prime (%)", value=f"{pct_prime}%")

    st.markdown("---")
    forcer_zero = st.checkbox("🛑 Forcer TOUTES les filiales à zéro pour cet import (Mise à zéro générale)", value=False)
    st.markdown("---")

    tab1, tab2 = st.tabs(["🔍 Aperçu Données Exploitation", "🔍 Aperçu Données Plafonds"])
    with tab1: st.text(donnees_exploitation)
    with tab2: st.text(donnees_plafonds)

    if st.button("🚀 Calculer, Filtrer et Envoyer sur Discord", use_container_width=True):
        try:
            # Récupération de l'URL du Webhook depuis les secrets d'environnement
            url_webhook = st.secrets["webhooks"]["primes"]
            
            # --- ÉTAPE 1 : EXTRACTION ET FILTRAGE DES PLAFONDS ---
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
                    
                    # Application des règles constitutionnelles strictes de l'Empire
                    if (poste.upper() == "PDG" and 
                        directeur.upper() != "GREGO73" and 
                        "CONSTRUCTIONS" not in nom_filiale.upper() and 
                        "BTP" not in nom_filiale.upper()):
                        
                        plafonds_extraits[nom_filiale] = convertir_saisie_en_nombre(raw_prime_max)

            # --- ÉTAPE 2 : CALCUL DES PRIMES FILIALE PAR FILIALE ---
            lignes_exploitation = donnees_exploitation.strip().split('\n')
            import_primes = ["Filiale\tPrimes"] 
            alertes_blocage = []
            lignes_affichage_tableau = []
            
            index_debut_exploitation = 1 if ("filiale" in donnees_exploitation.lower() or "trésorerie" in donnees_exploitation.lower()) else 0
            
            for ligne in lignes_exploitation[index_debut_exploitation:]:
                if not ligne.strip(): continue
                colonnes = ligne.split('\t')
                if len(colonnes) < 3: continue
                
                nom_filiale = colonnes[0].strip()
                raw_valeur = colonnes[2].strip() # Résultat d'exploitation (3e colonne)
                
                if forcer_zero:
                    import_primes.append(f"{nom_filiale}\t0")
                    lignes_affichage_tableau.append({
                        "Filiale": nom_filiale, 
                        "Exploitation": "N/A", 
                        "Prime Calculée": "0", 
                        "Statut": "Mise à zéro forcée"
                    })
                else:
                    # Si la filiale ne respecte pas les critères PDG / Grego73 / BTP, elle est ignorée
                    if nom_filiale not in plafonds_extraits: 
                        continue
                    
                    valeur_exploitation = convertir_saisie_en_nombre(raw_valeur)
                    valeur_prime_calculee = int(valeur_exploitation * (pct_prime / 100))
                    plafond_max = plafonds_extraits[nom_filiale]
                    
                    prime_finale = valeur_prime_calculee
                    statut_filiale = "✅ Conforme"
                    
                    # Application du plafonnement
                    if valeur_prime_calculee > plafond_max:
                        prime_finale = plafond_max
                        statut_filiale = "🚨 Plafonné"
                        alertes_blocage.append(f"⚠️ **{nom_filiale}** : Calculé **{formater_monnaie_empire(valeur_prime_calculee)}** ➡️ Bridé à **{formater_monnaie_empire(plafond_max)}**")

                    import_primes.append(f"{nom_filiale}\t{prime_finale}")
                    lignes_affichage_tableau.append({
                        "Filiale": nom_filiale,
                        "Exploitation": formater_monnaie_empire(valeur_exploitation),
                        "Prime Calculée": formater_monnaie_empire(prime_finale),
                        "Statut": statut_filiale
                    })
            
            # Structuration finale du fichier texte au format CRLF (\r\n) pour le jeu
            crlf_primes_pur = "\r\n".join(import_primes) + "\r\n"
            
            # --- ÉTAPE 3 : RENDER ET ENVOI DE LA NOTIFICATION DISCORD ---
            if forcer_zero:
                texte_discord = "🛑 **RAPPORT GÉNÉRAL : TOUTES LES FILIALES DE L'EMPIRE ONT ÉTÉ FORCÉES À 0 !**\n"
                st.info("ℹ️ Remise à niveau globale : L'intégralité des filiales a été injectée à 0 dans le fichier d'import.")
            else:
                texte_discord = f"📊 **RAPPORT DE CONTRÔLE DES PRIMES ({pct_holding}% Holding / {pct_prime}% Primes)**\n"
                if alertes_blocage:
                    texte_discord += "🚨 **PLAFONDS ATTEINTS (MODIFICATIONS APPLIQUÉES) :**\n" + "\n".join(alertes_blocage) + "\n\n"
                    for alerte in alertes_blocage: 
                        st.warning(alerte)
                else:
                    st.success("✅ Toutes les filiales actives respectent scrupuleusement leurs plafonds réglementaires !")

            texte_discord += "📋 **Bloc d'importation direct généré :**\n"
            if len(texte_discord) + len(crlf_primes_pur) < 1900:
                texte_discord += f"```text\n{crlf_primes_pur}```"
            else:
                texte_discord += "⚠️ *Le tableau étant volumineux, veuillez exploiter le fichier texte joint au message.*"
            
            # Envoi HTTP POST multi-part (Texte + Fichier)
            fichiers = {'file': ('primes_import_officiel.txt', crlf_primes_pur, 'text/plain')}
            reponse = requests.post(url_webhook, data={'content': texte_discord}, files=fichiers)
            
            if reponse.status_code in [200,204]:
                st.success("🎉 Calculs comptabilisés et rapport envoyé avec succès sur le canal Discord !")
                
                # Rendu du tableau récapitulatif
                st.subheader("📋 Tableau récapitulatif des primes")
                st.dataframe(pd.DataFrame(lignes_affichage_tableau), use_container_width=True, hide_index=True)
                
                # Bloc Copier-Coller direct et Bouton de Téléchargement
                st.subheader("✂️ Code d'importation rapide")
                st.code(crlf_primes_pur, language="text")
                st.download_button(label="📥 Télécharger le fichier .txt", data=crlf_primes_pur, file_name="primes_import_officiel.txt", mime="text/plain")
            else:
                st.error(f"🤖 Une erreur est survenue lors de la communication avec Discord (Code erreur : {reponse.status_code})")
                
        except Exception as e:
            st.error(f"⚠️ Erreur interne du système d'allocation : {str(e)}")
