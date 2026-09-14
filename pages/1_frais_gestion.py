import streamlit as st
import requests
from utils import formater_monnaie_empire, convertir_saisie_en_nombre

# Titre et description de la page
st.title("📉 Extraction des Frais de Gestion")
st.markdown("Cette page utilise automatiquement le tableau **Finance** collé sur l'accueil pour isoler la 3ème colonne.")

# Vérification si les données ont bien été synchronisées depuis l'accueil
if not st.session_state.get("donnees_chargees", False):
    st.warning("⚠️ Veuillez d'abord coller vos tableaux et cliquer sur le bouton de synchronisation sur la page d'accueil 🏠 avant d'utiliser cette page.")
else:
    # Récupération automatique du tableau Finance depuis la mémoire centrale
    donnees_brutes = st.session_state.get("tab_finance", "")

    # Rappel visuel des données prêtes à être traitées
    with st.expander("🔍 Voir le tableau Finance récupéré depuis l'accueil"):
        st.text(donnees_brutes)

    if st.button("🚀 Extraire et Envoyer les Frais sur Discord", use_container_width=True):
        try:
            url_webhook = st.secrets["webhooks"]["frais_gestion"]
            lignes = donnees_brutes.strip().split('\n')
            lignes_finales = ["Filiale\tFrais de gestion"]
            
            # Détection et exclusion automatique de l'en-tête du tableau Finance
            debut_index = 0
            if lignes and len(lignes) > 0:
                premiere_ligne = lignes[0].lower()
                if "filiale" in premiere_ligne or "trésorerie" in premiere_ligne:
                    debut_index = 1

            # Extraction de la 1ère colonne (Filiale) et 3ème colonne (Résultat d'exploitation)
            for ligne in lignes[debut_index:]:
                if not ligne.strip(): continue
                colonnes = ligne.split('\t')
                if len(colonnes) < 3: continue
                
                nom_filiale = colonnes[0].strip()
                raw_frais = colonnes[2].strip()
                
                # Traduction via l'outil central si la valeur contient une lettre
                frais_numerique = convertir_saisie_en_nombre(raw_frais)
                
                # SÉCURITÉ EN CAS DE VALEUR NÉGATIVE : Force à 0
                if frais_numerique < 0:
                    frais_numerique = 0
                
                lignes_finales.append(f"{nom_filiale}\t{frais_numerique}")

            # Contenu d'importation au format CRLF (\r\n) pour Empire Immo
            contenu_crlf_pur = "\r\n".join(lignes_finales) + "\r\n"
            
            # --- STRUCTURE DU MESSAGE DISCORD ---
            texte_discord = "✅ **Nouveau fichier d'importation des FRAIS DE GESTION !**\n"
            texte_discord += "Cliquez sur l'icône de copie en haut à droite du bloc gris ci-dessous :\n"
            
            if len(texte_discord) + len(contenu_crlf_pur) < 1900:
                texte_discord += f"```text\n{contenu_crlf_pur}```"
            else:
                texte_discord += "⚠️ *Le tableau est trop long pour être affiché en texte sur Discord. Utilisez le fichier joint.*"

            # Envoi des données et du fichier vers le webhook Discord
            fichiers = {'file': ('frais_gestion_import_officiel.txt', contenu_crlf_pur, 'text/plain')}
            reponse = requests.post(url_webhook, data={'content': texte_discord}, files=fichiers)
            
            if reponse.status_code in:
                st.success("🎉 Traitement réussi et envoyé sur Discord !")
                
                # --- AFFICHAGE DU BLOC NOIR AVEC BOUTON COPIER DIRECT SUR LE SITE ---
                st.subheader("📋 Résultat prêt à être copié :")
                st.markdown("Utilisez l'icône en haut à droite du bloc noir ci-dessous pour copier le texte :")
                st.code(contenu_crlf_pur, language="text")
                
                # Bouton de téléchargement direct du fichier .txt pur
                st.download_button(
                    label="📥 Télécharger le fichier d'import pur", 
                    data=contenu_crlf_pur, 
                    file_name="frais_gestion_import_officiel.txt", 
                    mime="text/plain"
                )
            else:
                st.error(f"🤖 Erreur Discord : {reponse.status_code}")
                
        except Exception as e:
            st.error(f"⚠️ Erreur lors du traitement : {str(e)}")
