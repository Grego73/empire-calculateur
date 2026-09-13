import streamlit as st
import requests

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
            
            debut_index = 1 if lignes and ("filiale" in lignes[0].lower() or "trésorerie" in lignes[0].lower()) else 0

            for ligne in lignes[debut_index:]:
                if not ligne.strip(): continue
                # Séparation par tabulation et nettoyage des espaces vides
                colonnes = [col.strip() for col in ligne.split('\t') if col.strip()]
                if len(colonnes) < 2: continue # Sécurité si la ligne est incomplète
                
                # On prend le premier élément (nom) et le dernier ou le 3ème élément (frais)
                # Pour être sûr de ne pas prendre de colonne vide intermédiaire
                nom_filiale = colonnes[0]
                # Si le tableau d'origine avait 3 colonnes ou plus, les frais sont souvent en dernier
                frais_de_gestion = colonnes[-1] 
                
                # Écriture stricte : AUCUNE tabulation dans le nom de la filiale
                nom_filiale_nettoye = nom_filiale.replace('\t', ' ')
                lignes_finales.append(f"{nom_filiale_nettoye}\t{frais_de_gestion}")


            # Contenu d'importation pur au format CRLF (\r\n)
            contenu_crlf_pur = "\r\n".join(lignes_finales) + "\r\n"
            
            # --- STRUCTURE DU MESSAGE AVEC BLOC COPIABLE DISCORD ---
            texte_discord = "✅ **Nouveau fichier d'importation des FRAIS DE GESTION !**\n"
            texte_discord += "Cliquez sur l'icône de copie en haut à droite du bloc gris ci-dessous :\n"
            
            # Si le texte brut ne dépasse pas la limite de Discord (2000 caractères), on l'intègre au message
            if len(texte_discord) + len(contenu_crlf_pur) < 1900:
                texte_discord += f"```text\n{contenu_crlf_pur}```"
            else:
                texte_discord += "⚠️ *Le tableau est trop long pour être affiché en texte sur Discord. Utilisez le fichier joint.*"

            fichiers = {'file': ('frais_gestion_import_officiel.txt', contenu_crlf_pur, 'text/plain')}
            reponse = requests.post(url_webhook, data={'content': texte_discord}, files=fichiers)
            
            if reponse.status_code == 200:
                st.success("🎉 Envoyé sur Discord avec le bloc texte copiable !")
                st.download_button("📥 Télécharger le fichier d'import pur", data=contenu_crlf_pur, file_name="frais_gestion_import_officiel.txt", mime="text/plain")
            else:
                st.error(f"🤖 Erreur Discord : {reponse.status_code}")
                
        except Exception as e:
            st.error(f"⚠️ Erreur lors du traitement : {str(e)}")
