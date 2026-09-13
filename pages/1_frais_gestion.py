import streamlit as st
import requests

# Titre et description de la page
st.title("📉 Extraction des Frais de Gestion")
st.markdown("Isole la **3ème colonne** de votre tableau financier et génère le format d'importation.")

donnees_brutes = st.text_area("Collez votre tableau financier complet ici :", height=300, key="data_frais")

if st.button("🚀 Envoyer les Frais sur Discord", use_container_width=True):
    if not donnees_brutes.strip():
        st.error("❌ Le tableau est vide.")
    else:
        try:
            url_webhook = st.secrets["webhooks"]["frais_gestion"]
            lignes = donnees_brutes.strip().split('\n')
            lignes_finales = ["Filiale\tFrais de gestion"]
            
            # Détection corrigée de l'en-tête sur la première ligne
            debut_index = 0
            if lignes and len(lignes) > 0:
                premiere_ligne = lignes[0].lower()
                if "filiale" in premiere_ligne or "trésorerie" in premiere_ligne:
                    debut_index = 1

            for ligne in lignes[debut_index:]:
                if not ligne.strip(): continue
                colonnes = ligne.split('\t')
                if len(colonnes) < 3: continue
                
                nom_filiale = colonnes[0].strip()
                frais_de_gestion = colonnes[2].strip()
                lignes_finales.append(f"{nom_filiale}\t{frais_de_gestion}")

            # Contenu d'importation pur au format CRLF (\r\n)
            contenu_crlf_pur = "\r\n".join(lignes_finales) + "\r\n"
            
            # --- ENVOI DISCORD ---
            texte_discord = "✅ **Nouveau fichier d'importation des FRAIS DE GESTION !**\n"
            if len(texte_discord) + len(contenu_crlf_pur) < 1900:
                texte_discord += f"```text\n{contenu_crlf_pur}```"
            else:
                texte_discord += "⚠️ *Le tableau est trop long pour être affiché en texte sur Discord. Utilisez le fichier joint.*"

            fichiers = {'file': ('frais_gestion_import_officiel.txt', contenu_crlf_pur, 'text/plain')}
            reponse = requests.post(url_webhook, data={'content': texte_discord}, files=fichiers)
            
            if reponse.status_code == 200:
                st.success("🎉 Traitement réussi et envoyé sur Discord !")
                
                # --- NOUVEAUTÉ : BLOC DE CODE SUR LE SITE AVEC BOUTON COPIER ---
                st.subheader("📋 Résultat prêt à être copié :")
                st.markdown("Utilisez l'icône en haut à droite du bloc noir ci-dessous pour copier le texte :")
                st.code(contenu_crlf_pur, language="text")
                
                # Bouton de téléchargement de secours
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
