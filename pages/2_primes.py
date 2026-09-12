import streamlit as st
import requests

st.title("💰 Extraction des Primes")
st.markdown("Isole la **4ème colonne (Résultat NET)** et l'envoie sur le salon Discord dédié.")

donnees_brutes = st.text_area("Collez votre tableau complet ici :", height=300, key="data_primes")

if st.button("🚀 Envoyer les Primes sur Discord", use_container_width=True):
    if not donnees_brutes.strip():
        st.error("❌ Le tableau est vide.")
    else:
        try:
            # Récupération automatique du Webhook depuis les Secrets
            url_webhook = st.secrets["webhooks"]["primes"]
            
            lignes = donnees_brutes.strip().split('\n')
            lignes_finales = ["Filiale\tPrimes"]
            
            debut_index = 1 if lignes and ("filiale" in lignes[0].lower() or "trésorerie" in lignes[0].lower()) else 0

            for ligne in lignes[debut_index:]:
                if not ligne.strip(): continue
                colonnes = ligne.split('\t')
                if len(colonnes) < 4: continue
                
                nom_filiale = colonnes[0].strip()
                primes = colonnes[3].strip()  # 4ème colonne
                lignes_finales.append(f"{nom_filiale}\t{primes}")

            contenu_crlf = "\r\n".join(lignes_finales) + "\r\n"
            texte_discord = "✅ **Nouveau fichier d'importation des PRIMES !**\n```text\n" + contenu_crlf + "```"

            fichiers = {'file': ('primes_import.txt', contenu_crlf, 'text/plain')}
            reponse = requests.post(url_webhook, data={'content': texte_discord}, files=fichiers)
            
            if reponse.status_code == 200:
                st.success("🎉 Envoyé avec succès dans le salon des Primes !")
                st.download_button("📥 Télécharger localement", data=contenu_crlf, file_name="primes_import.txt", mime="text/plain")
            else:
                st.error(f"🤖 Erreur Discord : {reponse.status_code}. Vérifiez vos Secrets Streamlit.")
        except Exception as e:
            st.error(f"⚠️ Erreur : {str(e)}")
