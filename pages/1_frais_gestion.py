import streamlit as st
import requests
from utils import formater_monnaie_empire, convertir_saisie_en_nombre

st.title("📉 Extraction des Frais de Gestion")
st.markdown("Cette page utilise automatiquement le tableau **Finance** collé sur l'accueil pour isoler la colonne d'exploitation.")

if not st.session_state.get("donnees_chargees", False):
    st.warning("⚠️ Veuillez d'abord coller vos tableaux et cliquer sur le bouton de synchronisation sur la page d'accueil 🏠 avant d'utiliser cette page.")
else:
    donnees_brutes = st.session_state.get("tab_finance", "")

    with st.expander("🔍 Voir le tableau Finance récupéré depuis l'accueil"):
        st.text(donnees_brutes)

    if st.button("🚀 Extraire et Envoyer les Frais sur Discord", use_container_width=True):
        try:
            url_webhook = st.secrets["webhooks"]["frais_gestion"]
            lignes = donnees_brutes.strip().split('\n')
            lignes_finales = ["Filiale\tFrais de gestion"]
            
            debut_index = 0
            if lignes and len(lignes) > 0:
                if "filiale" in lignes[0].lower() or "trésorerie" in lignes[0].lower():
                    debut_index = 1

            for ligne in lignes[debut_index:]:
                if not ligne.strip(): continue
                colonnes = ligne.split('\t')
                if len(colonnes) < 3: continue
                
                nom_filiale = colonnes[0].strip()
                raw_frais = colonnes[2].strip()
                
                # Conversion sécurisée par utils.py
                frais_numerique = convertir_saisie_en_nombre(raw_frais)
                if frais_numerique < 0:
                    frais_numerique = 0
                
                lignes_finales.append(f"{nom_filiale}\t{frais_numerique}")

            contenu_crlf_pur = "\r\n".join(lignes_finales) + "\r\n"
            texte_discord = "✅ **Nouveau fichier d'importation des FRAIS DE GESTION !**\n"
            
            if len(texte_discord) + len(contenu_crlf_pur) < 1900:
                texte_discord += f"```text\n{contenu_crlf_pur}```"
            else:
                texte_discord += "⚠️ *Le tableau est trop long pour être affiché en texte sur Discord. Utilisez le fichier joint.*"

            fichiers = {'file': ('frais_gestion_import_officiel.txt', contenu_crlf_pur, 'text/plain')}
            reponse = requests.post(url_webhook, data={'content': texte_discord}, files=fichiers)
            
            if reponse.status_code in:
                st.success("🎉 Traitement réussi et envoyé sur Discord !")
                st.code(contenu_crlf_pur, language="text")
                st.download_button(label="📥 Télécharger le fichier .txt", data=contenu_crlf_pur, file_name="frais_gestion_import_officiel.txt", mime="text/plain")
            else:
                st.error(f"🤖 Erreur Discord : {reponse.status_code}")
                
        except Exception as e:
            st.error(f"⚠️ Erreur lors du traitement : {str(e)}")
