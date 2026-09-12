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
            
            # Vérification de la première ligne pour voir si c'est une en-tête
            if lignes:
                premiere_ligne_texte = lignes[0].lower()
                # Si la ligne contient des mots clés d'en-tête, on commence à la ligne suivante
                debut_index = 1 if ("filiale" in premiere_ligne_texte or "trésorerie" in premiere_ligne_texte) else 0
            else:
                debut_index = 0

            for ligne in lignes[debut_index:]:
                if not ligne.strip():
                    continue
                
                colonnes = ligne.split('\t')
                if len(colonnes) < 3:
                    continue  # Ignore les lignes incorrectes ou mal formées
                    
                nom_filiale = colonnes[0].strip()
                frais_de_gestion = colonnes[2].strip()  # Extraction stricte de la 3ème colonne
                
                lignes_finales.append(f"{nom_filiale}\t{frais_de_gestion}")

            # Création du contenu au format strict CRLF (\r\n) pour le fichier
            contenu_crlf = "\r\n".join(lignes_finales) + "\r\n"

            # Préparation du texte à afficher directement dans Discord (dans un bloc de code text)
            texte_discord = "✅ **Nouveau fichier d'importation des frais de gestion généré !**\n"
            texte_discord += "Vous pouvez copier le texte ci-dessous directement :\n"
            texte_discord += f"```text\n{contenu_crlf}```"

            # Envoi vers Discord (Fichier joint + Texte directement copiable dans le corps du message)
            fichiers = {'file': ('frais_gestion_import.txt', contenu_crlf, 'text/plain')}
            donnees_webhook = {'content': texte_discord}
            
            reponse = requests.post(url_webhook, data=donnees_webhook, files=fichiers)
            
            if reponse.status_code == 200:
                st.success("🎉 Succès ! Le fichier et le texte copiable ont été envoyés sur votre salon Discord.")
                st.download_button(label="📥 Télécharger le fichier généré localement", data=contenu_crlf, file_name="frais_gestion_import.txt", mime="text/plain")
            else:
                st.error(f"🤖 Erreur Discord (Code {reponse.status_code}). Vérifiez la validité de votre Webhook.")
                
        except Exception as e:
            st.error(f"⚠️ Une erreur est survenue lors du traitement : {str(e)}")
