import streamlit as st
import requests

# Configuration de la page web
st.set_page_config(page_title="Convertisseur de Frais & Discord", page_icon="💼", layout="centered")

st.title("💼 Convertisseur de Frais & Export Discord")
st.markdown("Transformez vos tableaux financiers au format réglementaire et envoyez-les directement sur Discord.")

# 1. Premier cadre : URL du Webhook
url_webhook = st.text_input("1. Collez l'URL de votre Webhook Discord :", type="password", help="Votre URL reste sécurisée et n'est pas stockée.")

# 2. Deuxième cadre : Zone de texte pour le tableau
donnees_brutes = st.text_area("2. Collez votre tableau complet ici (avec les tabulations d'origine) :", height=300)

# Bouton d'action
if st.button("🚀 Transformer et Envoyer sur Discord", use_container_width=True):
    if not url_webhook or "://discord.com" not in url_webhook:
        st.error("❌ Veuillez saisir une URL de Webhook Discord valide.")
    elif not donnees_brutes.strip():
        st.error("❌ Le cadre des données est vide.")
    else:
        try:
            # Traitement des lignes
            lignes = donnees_brutes.strip().split('\n')
            lignes_finales = ["Filiale\tFrais de gestion"]
            
            # Détection et retrait automatique d'une éventuelle en-tête d'origine
            premiere_ligne = lignes[0].lower()
            debut_index = 1 if "filiale" in premiere_ligne or "trésorerie" in premiere_ligne else 0

            for ligne in lignes[debut_index:]:
                if not ligne.strip():
                    continue
                
                colonnes = ligne.split('\t')
                if len(colonnes) < 3:
                    continue  # Ignore les lignes incorrectes
                    
                nom_filiale = colonnes[0].strip()
                frais_de_gestion = colonnes[2].strip()  # Extraction de la 3ème colonne
                
                lignes_finales.append(f"{nom_filiale}\t{frais_de_gestion}")

            # Création du contenu au format strict CRLF (\r\n)
            contenu_crlf = "\r\n".join(lignes_finales) + "\r\n"

            # Envoi vers Discord
            fichiers = {'file': ('frais_gestion_import.txt', contenu_crlf, 'text/plain')}
            donnees_webhook = {'content': "✅ **Nouveau fichier d'importation des frais de gestion généré depuis l'application Web !**"}
            
            reponse = requests.post(url_webhook, data=donnees_webhook, files=fichiers)
            
            if reponse.status_code in [200, 204]:
                st.success("🎉 Succès ! Le fichier a été correctement envoyé sur votre salon Discord.")
                # Optionnel : Permet aussi de télécharger le fichier directement depuis le site web
                st.download_button(label="📥 Télécharger le fichier généré localement", data=contenu_crlf, file_name="frais_gestion_import.txt", mime="text/plain")
            else:
                st.error(f"🤖 Erreur Discord (Code {reponse.status_code}). Vérifiez la validité de votre Webhook.")
                
        except Exception as e:
            st.error(f"⚠️ Une erreur est survenue lors du traitement : {str(e)}")
