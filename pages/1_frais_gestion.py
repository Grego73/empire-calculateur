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
            
            # On détecte l'en-tête pour ne pas l'inclure
            debut_index = 1 if lignes and ("filiale" in lignes[0].lower() or "trésorerie" in lignes[0].lower()) else 0

            for ligne in lignes[debut_index:]:
                if not ligne.strip(): continue
                
                # Découpage par n'importe quel groupe d'espaces ou tabulations d'origine
                elements = [el.strip() for el in ligne.split() if el.strip()]
                if len(elements) < 2: continue
                
                # Le montant est TOUJOURS le dernier élément
                frais = elements[-1].replace(" ", "").replace("€", "")
                if not frais.isdigit(): continue
                
                # Le nom de la filiale est TOUT ce qui précède le montant
                # Exemple : "ATAV00", "-", "Exorciste11" devient "ATAV00 - Exorciste11"
                nom_filiale = " ".join(elements[:-1])
                
                # On assemble STRICTEMENT avec un vrai caractère tabulation \t
                lignes_finales.append(f"{nom_filiale}\t{frais}")

            # Génération au format CRLF demandé par la fiche (\r\n)
            contenu_crlf_pur = "\r\n".join(lignes_finales) + "\r\n"
            
            # Message Discord réduit au strict minimum pour éviter que Discord ne modifie le format
            texte_discord = "✅ **Fichier d'importation des FRAIS DE GESTION prêt**"

            fichiers = {'file': ('frais_gestion_import_officiel.txt', contenu_crlf_pur, 'text/plain')}
            reponse = requests.post(url_webhook, data={'content': texte_discord}, files=fichiers)
            
            if reponse.status_code == 200:
                st.success("🎉 Envoyé sur Discord ! ÉVITEZ de copier le texte sur Discord. Téléchargez directement le fichier ci-dessous :")
                # Le bouton de téléchargement garantit à 100% que le fichier contiendra la vraie tabulation
                st.download_button(
                    label="📥 TÉLÉCHARGER LE FICHIER .TXT OFFICIEL", 
                    data=contenu_crlf_pur, 
                    file_name="frais_gestion_import_officiel.txt", 
                    mime="text/plain"
                )
            else:
                st.error(f"🤖 Erreur Discord : {reponse.status_code}")
                
        except Exception as e:
            st.error(f"⚠️ Erreur lors du traitement : {str(e)}")
