import streamlit as st
import os
import sys
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from crons.cron_update_api import executer_mise_a_jour_cron
    CRON_DISPONIBLE = True
except ImportError:
    CRON_DISPONIBLE = False

st.title("⚙️ Espace Administration de l'Empire (Cloud)")

MOT_DE_PASSE_ADMIN = "Empire2026" 
saisie_pwd = st.text_input("Mot de passe Administrateur :", type="password")

if not saisie_pwd:
    st.info("🔑 Veuillez vous authentifier.")
elif saisie_pwd != MOT_DE_PASSE_ADMIN:
    st.error("❌ Accès refusé.")
else:
    st.success("🔓 Authentification réussie. Bienvenue Grego73.")
    st.markdown("---")

    st.subheader("📡 Synchronisation Manuelle de l'API vers Firebase")
    if st.button("🔄 Lancer le script de synchronisation (Cron)", use_container_width=True):
        if not CRON_DISPONIBLE:
            st.error("❌ Erreur : Script 'cron_update_api.py' introuvable.")
        else:
            try:
                with st.spinner("Envoi des flux d'API vers Firebase Cloud..."):
                    executer_mise_a_jour_cron()
                st.success("🎉 Le script s'est exécuté avec succès ! Collections rafraîchies.")
                st.balloons()
            except Exception as e: st.error(f"❌ Erreur : {e}")

    st.markdown("---")
    st.subheader("🗄️ État et Diagnostic de la Base de Données Cloud")
    
    try:
        from utils import db
        from google.cloud import firestore
        
        tables = ["materiaux", "batiments", "travaux", "players"]
        stats_tables = []
        
        with st.spinner("Analyse des tables Firestore..."):
            for table in tables:
                docs_ordre = db.collection(table).order_by("date_extraction", direction=firestore.Query.DESCENDING).limit(1).stream()
                derniere_synchro = "Aucune"
                for doc in docs_ordre:
                    derniere_synchro = doc.to_dict().get("date_extraction", "Aucune")
                
                stats_tables.append({
                    "Collection Cloud NoSQL": table,
                    "Statut": "🟢 Connectée & Opérationnelle" if d_synchro != "Aucune" else "⚪ Vide",
                    "Dernière Extraction": derniere_synchro
                })
        st.dataframe(pd.DataFrame(stats_tables), use_container_width=True, hide_index=True)
    except Exception as e: st.error(f"⚠️ Erreur diagnostic Firebase : {e}")
