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
                    historique_logs = executer_mise_a_jour_cron()
                
                st.success("🎉 Le script s'est exécuté ! Consultez le journal ci-dessous :")
                texte_journal = "\n".join(historique_logs)
                st.code(texte_journal, language="text")
                st.balloons()
                
            except Exception as e: 
                st.error(f"❌ Erreur générale d'exécution : {e}")

    st.markdown("---")
    st.subheader("🗄️ État et Diagnostic de la Base de Données Cloud")
    
    try:
        from utils import db
        tables = ["materiaux", "usines", "batiments", "travaux"]
        stats_tables = []
        
        with st.spinner("Analyse des tables Firestore..."):
            for table in tables:
                docs_ordre = db.collection(table).order_by("date_extraction", direction="DESCENDING").limit(1).stream()
                derniere_synchro = "Aucune"
                for doc in docs_ordre:
                    derniere_synchro = doc.to_dict().get("date_extraction", "Aucune")
                
                stats_tables.append({
                    "Collection Cloud NoSQL": table,
                    "Statut": "🟢 Connectée & Opérationnelle" if derniere_synchro != "Aucune" else "⚪ Vide",
                    "Dernière Extraction": derniere_synchro
                })

        st.dataframe(pd.DataFrame(stats_tables), use_container_width=True, hide_index=True)
    except Exception as e: st.error(f"⚠️ Erreur diagnostic Firebase : {e}")

    st.markdown("---")
    st.subheader("🔮 Explorateur de Tables Firebase (Vue brute)")
    tables_disponibles = ["batiments", "materiaux", "travaux", "usines", "players"]
    table_selectionnee = st.selectbox("📁 Choisissez la table à inspecter :", options=tables_disponibles, index=0)
    
    if table_selectionnee:
        with st.spinner(f"Lecture de la table '{table_selectionnee}'..."):
            try:
                docs_bruts = db.collection(table_selectionnee).stream()
                liste_documents = [doc.to_dict() for doc in docs_bruts]
                
                if not liste_documents:
                    st.info(f"⚪ La table '{table_selectionnee}' est actuellement vide ou n'a pas encore été synchronisée.")
                else:
                    df_exploration = pd.DataFrame(liste_documents)
                    total_lignes = len(df_exploration)
                    total_colonnes = len(df_exploration.columns)
                    
                    m_db1, m_db2 = st.columns(2)
                    with m_db1: st.metric(label="📊 Nombre d'entrées (Documents)", value=f"{total_lignes} lignes")
                    with m_db2: st.metric(label="⚙️ Attributs détectés", value=f"{total_colonnes} colonnes")
                    
                    st.markdown("##### 🔍 Recherche rapide dans la table")
                    terme_recherche = st.text_input("Filtrer par mot-clé (Nom, Date, ID...) :", key=f"search_{table_selectionnee}").strip()
                    
                    if terme_recherche:
                        masque_recherche = df_exploration.astype(str).apply(
                            lambda x: x.str.contains(terme_recherche, case=False, na=False)
                        ).any(axis=1)
                        df_filtre = df_exploration[masque_recherche]
                        st.caption(f"🎯 {len(df_filtre)} résultat(s) trouvé(s) pour '{terme_recherche}'")
                    else:
                        df_filtre = df_exploration
                    
                    st.markdown("##### 📄 Table de données interactive")
                    st.dataframe(df_filtre, use_container_width=True, hide_index=False)
                    
                    st.download_button(
                        label=f"📥 Exporter la table {table_selectionnee} en CSV",
                        data=df_exploration.to_csv(index=False).encode('utf-8'),
                        file_name=f"export_admin_{table_selectionnee}.csv",
                        mime="text/csv",
                        key=f"dl_{table_selectionnee}"
                    )
            except Exception as e:
                st.error(f"💥 Impossible de charger la table '{table_selectionnee}' : {e}")
