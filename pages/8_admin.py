import streamlit as st
import sqlite3
import os
import sys
import pandas as pd

# Import de la fonction du cron existante
# S'assure que le dossier racine est accessible pour l'import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from crons.cron_update_api import executer_mise_a_jour_cron
    CRON_DISPONIBLE = True
except ImportError:
    CRON_DISPONIBLE = False
    st.error("Impossible de trouver la fonction dans 'cron_update_api.py'.")

st.title("⚙️ Espace Administration de l'Empire")
st.markdown("Zone réservée à la maintenance de la base de données et au déclenchement des requêtes API.")

# --- BARRIÈRE DE SÉCURITÉ : MOT DE PASSE ADMIN ---
# Modifier "Empire2026" par le mot de passe secret de votre choix
MOT_DE_PASSE_ADMIN = "Empire2026" 

saisie_pwd = st.text_input("Saisissez le mot de passe Administrateur :", type="password")

if not saisie_pwd:
    st.info("🔑 Veuillez vous authentifier pour accéder aux commandes de l'infrastructure.")
elif saisie_pwd != MOT_DE_PASSE_ADMIN:
    st.error("❌ Mot de passe incorrect. Accès refusé.")
else:
    st.success("🔓 Authentification réussie. Bienvenue, Grego73.")
    st.markdown("---")

    DB_NAME = "data_cache/empire_immo.db"

# Remplacez ensuite TOUTE la section du bouton (Zone 1) par ce bloc sécurisé :

# =========================================================
# 🚀 ZONE 1 : DÉCLENCHEMENT DU CRON EN DIRECT
# =========================================================
st.subheader("📡 Synchronisation Manuelle de l'API")
st.markdown(
    "Cliquez sur le bouton ci-dessous pour forcer l'exécution du script de mise à jour. "
    "⚠️ *Attention : Respectez la règle des 4 heures pour éviter le blocage automatique (Erreur 429).* "
)

if st.button("🔄 Lancer le script de synchronisation (Cron)", use_container_width=True):
    # 1. Vérification immédiate avant de lancer quoi que ce soit
    if not CRON_DISPONIBLE:
        st.error("❌ Impossible de lancer la synchronisation : Le fichier 'cron_update_api.py' est introuvable ou mal configuré à la racine de votre projet.")
    else:
        try:
            with st.spinner("Connexion aux serveurs d'Empire Immo et écriture en base de données SQL..."):
                executer_mise_a_jour_cron()
                
            # Ce message vert ne s'affichera DÉSORMAIS que si l'exécution a réellement fonctionné !
            st.success("🎉 Le script Cron s'est exécuté avec succès ! Les tables SQL ont été rafraîchies.")
            st.balloons()
        except Exception as e:
            st.error(f"❌ Erreur lors de l'exécution du script : {str(e)}")


    st.markdown("---")

    # =========================================================
    # 💾 ZONE 2 : SAUVEGARDE ET EXPORT DE LA BDD
    # =========================================================
    st.subheader("💾 Sauvegarde de l'Historique")
    st.markdown("Téléchargez une copie physique complète de votre base de données SQLite pour sécuriser vos données de gestion.")
    
    if os.path.exists(DB_NAME):
        try:
            with open(DB_NAME, "rb") as fichier_db:
                donnees_base = fichier_db.read()
                
            st.download_button(
                label="📥 Télécharger la base de données (.db)",
                data=donnees_base,
                file_name=f"sauvegarde_empire_immo_{os.path.basename(DB_NAME)}",
                mime="application/x-sqlite3",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"⚠️ Erreur lors de la préparation du fichier de sauvegarde : {str(e)}")
    else:
        st.info("💡 La base de données n'existe pas encore. Elle apparaîtra après votre première synchronisation API.")

    st.markdown("---")

    # =========================================================
    # 📊 ZONE 3 : ÉTAT DE SANTÉ DE LA BASE DE DONNÉES (AUDIT SQL)
    # =========================================================
    st.subheader("🗄️ État et Diagnostic de la Base de Données")
    
    if os.path.exists(DB_NAME):
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            
            tables = ["materiaux", "batiments", "travaux", "players"]
            stats_tables = []
            
            for table in tables:
                # Vérifie si la table existe avant de lancer le décompte
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if not cursor.fetchone():
                    stats_tables.append({"Table SQL": table, "Total Enregistrements": "0", "Dernière Synchro": "Non initialisée"})
                    continue

                # Compte total des lignes
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                total_lignes = cursor.fetchone()[0]
                
                # Récupération de la date de la dernière entrée
                cursor.execute(f"SELECT MAX(date_extraction) FROM {table}")
                derniere_synchro = cursor.fetchone()[0]
                
                stats_tables.append({
                    "Table SQL": table,
                    "Total Enregistrements": f"{total_lignes:,}".replace(",", " "),
                    "Dernière Synchro": "Aucune" if notCompliance or derniere_synchro is None else str(derniere_synchro)
                })
                
            conn.close()
            
            st.dataframe(pd.DataFrame(stats_tables), use_container_width=True, hide_index=True)
            
        except Exception as e:
            st.error(f"⚠️ Impossible de lire les métadonnées de la BDD : {str(e)}")
    else:
        st.warning("🚨 Le fichier de base de données n'est pas encore présent dans `data_cache/`.")
