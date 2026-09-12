import streamlit as st
import requests

st.title("💰 Extraction des Primes")
st.markdown("Isole la **4ème colonne (Résultat NET)** de votre tableau pour l'attribution des primes.")

url_webhook = st.text_input("1. Collez l'URL de votre Webhook Discord :", type="password", key="webhook_primes")
donnees_brutes = st.text_area("2. Collez votre tableau complet ici :", height=250, key="data_primes")

if st.button("🚀 Envoyer les Primes sur Discord", use_container_width=True):
    if not url_webhook or "://discord.com" not in url_webhook:
        st.error("❌ URL de Webhook Discord invalide.")
    elif not donnees_brutes.strip():
        st.error("❌ Le tableau est vide.")
    else:
        try:
            lignes = donnees_brutes.strip().split('\n')
            lignes_finales = ["Filiale\tPrimes"]
            
            debut_index = 1 if lignes and ("filiale" in lignes[0].lower() or "trésorerie" in lignes[0].lower()) else 0

            for ligne in lignes[debut_index:]:
                if not ligne.strip(): continue
                colonnes = ligne.split('\t')
                if len(colonnes) < 4: continue  # Vérifie qu'il y a assez de colonnes
                
                nom_filiale = colonnes[0].strip()
                primes = colonnes[3].strip()  # 4ème colonne (Résultat NET)
                lignes_finales.append(f"{nom_filiale}\t{primes}")

            contenu_crlf = "\r\n".join(lignes_finales) + "\r\n"
            texte_discord = "✅ **Nouveau fichier d'importation des PRIMES !**\n```text\n" + contenu_crlf + "```"

            fichiers = {'file': ('primes_import.txt', contenu_crlf, 'text/plain')}
            reponse = requests.post(url_webhook, data={'content': texte_discord}, files=fichiers)
            
            if reponse.status_code == 200:
                st.success("🎉 Primes envoyées sur Discord avec succès !")
                st.download_button("📥 Télécharger localement", data=contenu_crlf, file_name="primes_import.txt", mime="text/plain")
            else:
                st.error(f"🤖 Erreur Discord : {reponse.status_code}")
        except Exception as e:
            st.error(f"⚠️ Erreur : {str(e)}")
