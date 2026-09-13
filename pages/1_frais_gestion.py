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
            lignes_finales = []
            
            debut_index = 1 if lignes and ("filiale" in lignes.lower() or "trésorerie" in lignes.lower()) else 0

            for ligne in lignes[debut_index:]:
                if not ligne.strip(): continue
                
                colonnes = ligne.split('\t')
                if len(colonnes) < 3: continue
                
                nom_filiale = colonnes[0].strip()
                frais_de_gestion = colonnes[2].strip()
                
                lignes_finales.append(f"{nom_filiale}\t{frais_de_gestion}")

            # Contenu au format strict CRLF (\r\n) pour le fichier joint
            contenu_crlf_pur = "\r\n".join(lignes_finales) + "\r\n"
            
            # Message Discord optimisé pour le téléchargement direct du fichier
            texte_discord = "✅ **Nouveau fichier d'importation des FRAIS DE GESTION !**\n"
            texte_discord += "📥 **Téléchargez directement le fichier joint ci-dessous** pour l'importer sur Empire Immo (le bouton copier de Discord casse le format)."

            fichiers = {'file': ('frais_gestion_import_officiel.txt', contenu_crlf_pur, 'text/plain')}
            reponse = requests.post(url_webhook, data={'content': texte_discord}, files=fichiers)
            
            if reponse.status_code == 200:
                st.success("🎉 Envoyé sur Discord ! Vous pouvez utiliser le fichier joint directement.")
                st.download_button("📥 Télécharger le fichier d'import pur", data=contenu_crlf_pur, file_name="frais_gestion_import_officiel.txt", mime="text/plain")
            else:
                st.error(f"🤖 Erreur Discord : {reponse.status_code}")
                
        except Exception as e:
            st.error(f"⚠️ Erreur lors du traitement : {str(e)}")
