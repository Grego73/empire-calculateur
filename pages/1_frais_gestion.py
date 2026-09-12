import streamlit as st
import requests

st.title("📉 Extraction des Frais de Gestion")
st.markdown("Isole la **3ème colonne** de votre tableau financier et génère un fichier d'importation parfaitement épuré.")

donnees_brutes = st.text_area("Collez votre tableau financier complet ici :", height=300, key="data_frais")

if st.button("🚀 Envoyer les Frais sur Discord", use_container_width=True):
    if not donnees_brutes.strip():
        st.error("❌ Le tableau est vide.")
    else:
        try:
            # Récupération du Webhook depuis les Secrets Streamlit
            url_webhook = st.secrets["webhooks"]["frais_gestion"]
            
            lignes = donnees_brutes.strip().split('\n')
            
            # STRUCTURE DU FICHIER : Uniquement l'en-tête officielle attendue
            lignes_finales = ["Filiale\tFrais de gestion"]
            
            # Détection automatique de la ligne d'en-tête d'origine pour l'ignorer
            debut_index = 1 if lignes and ("filiale" in lignes[0].lower() or "trésorerie" in lignes[0].lower()) else 0

            for ligne in lignes[debut_index:]:
                if not ligne.strip(): 
                    continue
                colonnes = ligne.split('\t')
                if len(colonnes) < 3: 
                    continue # Ignore les lignes incomplètes
                
                nom_filiale = colonnes[0].strip()
                frais_de_gestion = colonnes[2].strip()  # Extraction stricte de la 3ème colonne
                
                lignes_finales.append(f"{nom_filiale}\t{frais_de_gestion}")

            # Création du contenu de fichier pur avec le saut de ligne réglementaire CRLF (\r\n)
            contenu_crlf_pur = "\r\n".join(lignes_finales) + "\r\n"
            
            # Message d'accompagnement court sur Discord pour ne pas perturber l'importation
            texte_discord = "✅ **Nouveau fichier pur d'importation des FRAIS DE GESTION généré !**\n"
            texte_discord += "Le fichier joint ci-dessous est nettoyé et prêt à être importé directement."

            # Envoi du fichier textuel strict
            fichiers = {'file': ('frais_gestion_import_officiel.txt', contenu_crlf_pur, 'text/plain')}
            reponse = requests.post(url_webhook, data={'content': texte_discord}, files=fichiers)
            
            if reponse.status_code == 200:
                st.success("🎉 Fichier d'importation des frais envoyé avec succès sur Discord !")
                st.download_button("📥 Télécharger le fichier d'import pur", data=contenu_crlf_pur, file_name="frais_gestion_import_officiel.txt", mime="text/plain")
            else:
                st.error(f"🤖 Erreur Discord : {reponse.status_code}. Vérifiez vos Secrets Streamlit.")
                
        except Exception as e:
            st.error(f"⚠️ Erreur lors du traitement : {str(e)}")
