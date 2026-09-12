import streamlit as st
import requests

st.title("💰 Gestion & Contrôle des Primes")
st.markdown("Calcule la part des primes en fonction du tableau financier, applique les filtrages stricts et affiche l'analyse des lignes exclues.")

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
donnees_exploitation = st.text_area("1. Collez ici le tableau financier classique :", height=200, key="data_tab_exploitation")
donnees_plafonds = st.text_area("2. Collez ici le tableau des directeurs :", height=200, key="data_tab_plafonds")

if st.button("🚀 Calculer, Filtrer et Envoyer sur Discord", use_container_width=True):
    if not donnees_exploitation.strip() or not donnees_plafonds.strip():
        st.error("❌ L'un des deux tableaux est vide.")
    else:
        try:
            url_webhook = st.secrets["webhooks"]["primes"]
            
            # Variables de comptage pour les statistiques d'exclusion
            total_lignes_directeurs_recues = 0
            exclues_non_pdg = 0
            exclues_grego = 0
            exclues_btp_constructions = 0
            
            # --- 🛠️ ETAPE 1 : EXTRACTION ET COMPTAGE DU TABLEAU DES DIRECTEURS ---
            plafonds_extraits = {}
            lignes_plafonds = donnees_plafonds.strip().split('\n')
            index_debut_plafonds = 1 if "poste" in donnees_plafonds.lower() else 0
            
            for ligne in lignes_plafonds[index_debut_plafonds:]:
                if not ligne.strip(): continue
                total_lignes_directeurs_recues += 1
                colonnes = ligne.split('\t')
                if len(colonnes) < 4: continue
                
                nom_filiale = colonnes[0].strip()
                poste = colonnes[1].strip()
                directeur = colonnes[2].strip()
                raw_prime_max = colonnes[3].strip()
                
                # Contrôle du Poste
                if poste.upper() != "PDG":
                    exclues_non_pdg += 1
                    continue
                
                # Contrôle du Directeur Grego73
                if directeur.upper() == "GREGO73":
                    exclues_grego += 1
                    continue
                
                # Contrôle des filiales BTP / Constructions
                if "CONSTRUCTIONS" in nom_filiale.upper() or "BTP" in nom_filiale.upper():
                    exclues_btp_constructions += 1
                    continue
                    
                # Si la ligne passe tous les filtres, on mémorise le plafond du PDG
                plafonds_extraits[nom_filiale] = int(raw_prime_max) if raw_prime_max.isdigit() else 0

            # --- 🛠️ ETAPE 2 : CALCULS DU TABLEAU FINANCIER & CROISEMENT ---
            lignes_exploitation = donnees_exploitation.strip().split('\n')
            import_primes = ["Filiale\tFrais de gestion"]
            alertes_blocage = []
            
            total_lignes_financieres_recues = 0
            exclues_sans_pdg_valide = 0
            
            index_debut_exploitation = 1 if ("filiale" in donnees_exploitation.lower() or "trésorerie" in donnees_exploitation.lower()) else 0
            
            for ligne in lignes_exploitation[index_debut_exploitation:]:
                if not ligne.strip(): continue
                total_lignes_financieres_recues += 1
                colonnes = ligne.split('\t')
                if len(colonnes) < 3: continue
                
                nom_filiale = colonnes[0].strip()
                raw_valeur = colonnes[2].strip() # 3ème colonne
                
                # Croisement strict avec nos PDG admissibles filtrés à l'étape 1
                if nom_filiale not in plafonds_extraits:
                    exclues_sans_pdg_valide += 1
                    continue
                
                valeur_exploitation = int(raw_valeur) if raw_valeur.isdigit() else 0
                valeur_prime_calculee = int(valeur_exploitation * (pct_prime / 100))
                plafond_max = plafonds_extraits[nom_filiale]
                
                prime_finale = valeur_prime_calculee
                if valeur_prime_calculee > plafond_max:
                    prime_finale = plafond_max
                    alertes_blocage.append(f"⚠️ **{nom_filiale}** : Calculé **{valeur_prime_calculee}** ➡️ Bridé à **{plafond_max}** (Max)")

                import_primes.append(f"{nom_filiale}\t{prime_finale}")
            
            crlf_primes_pur = "\r\n".join(import_primes) + "\r\n"
            total_lignes_finales = len(import_primes) - 1 # Retrait de la ligne d'en-tête
            
            # --- 📊 ETAPE 3 : AFFICHAGE DU TABLEAU DE BORD DE SUIVI (STREAMLIT) ---
            st.subheader("📊 Rapport d'analyse et de filtrage")
            
            # Indicateurs principaux en colonnes
            c1, c2, c3 = st.columns(3)
            c1.metric("Lignes reçues (Financier)", total_lignes_financieres_recues)
            c2.metric("Lignes exclues au total", total_lignes_financieres_recues - total_lignes_finales, delta_color="inverse")
            c3.metric("Lignes finales d'import", total_lignes_finales)
            
            # Détails des motifs de filtrage
            st.markdown("**Détail des lignes supprimées dans le Tableau des Directeurs :**")
            st.info(f"• 👥 Postes ignorés (Car différents de 'PDG') : **{exclues_non_pdg}**")
            st.info(f"• 🚫 Directeur Grego73 exclu : **{exclues_grego}**")
            st.info(f"• 🏗️ Filiales BTP & Constructions exclues : **{exclues_btp_constructions}**")
            
            st.markdown("**Détail du croisement final :**")
            st.error(f"• 🔍 Filiales du tableau financier ignorées car elles n'ont pas de PDG admissible : **{exclues_sans_pdg_valide}**")

            # --- 🛠️ ETAPE 4 : STRUCTURE DU MESSAGE DISCORD ---
            texte_discord = f"📊 **RAPPORT DE CONTRÔLE DES PRIMES ({pct_holding}/{pct_prime})**\n"
            texte_discord += f"📈 *Statistiques : {total_lignes_financieres_recues} lignes reçues ➡️ {total_lignes_finales} lignes finales générées.*\n\n"
            
            if alertes_blocage:
                texte_discord += "🚨 **MODIFICATIONS APPLIQUÉES (PLAFOND ATTEINT) :**\n" + "\n".join(alertes_blocage) + "\n\n"
                for alerte in alertes_blocage: 
                    st.warning(alerte)
            else:
                st.success("✅ Toutes les filiales valides respectent les plafonds !")

            texte_discord += "📋 **Texte d'importation prêt à être copié :**\n"
            if len(texte_discord) + len(crlf_primes_pur) < 1900:
                texte_discord += f"```text\n{crlf_primes_pur}```"
            else:
                texte_discord += "⚠️ *Tableau trop long pour l'affichage plein texte Discord. Téléchargez le fichier joint.*"
            
            # Envoi vers Discord
            fichiers = {'file': ('primes_import_officiel.txt', crlf_primes_pur, 'text/plain')}
            reponse = requests.post(url_webhook, data={'content': texte_discord}, files=fichiers)
            
            if reponse.status_code == 200:
                st.success("🎉 Calculs réussis ! Les compteurs de contrôle et le fichier ont été envoyés sur Discord.")
                st.download_button("📥 Télécharger le fichier d'import pur", data=crlf_primes_pur, file_name="primes_import_officiel.txt", mime="text/plain")
            else:
                st.error(f"🤖 Erreur Discord : {reponse.status_code}")
        except Exception as e:
            st.error(f"⚠️ Erreur système : {str(e)}")
S