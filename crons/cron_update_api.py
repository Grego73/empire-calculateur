import os
import sqlite3
from datetime import datetime
import requests

API_KEY = "eiK8_110b18473efc48e9c63f76b5494ea18f"
BASE_URL = "https://empireimmo.com"
DB_NAME = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data_cache", "empire_immo.db"))
# Création du dossier pour la base de données si nécessaire
os.makedirs("data_cache", exist_ok=True)

def initialiser_base_de_donnees():
    """Crée les tables SQL si elles n'existent pas déjà."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Table pour l'API Matériaux
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS materiaux (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT,
            prix INTEGER,
            unite TEXT,
            date_extraction TEXT
        )
    """)
    
    # Table pour l'API Bâtiments (Biens d'entreprise)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS batiments (
            id_jeu INTEGER,
            nom TEXT,
            type TEXT,
            valeur INTEGER,
            loyer INTEGER,
            charge INTEGER,
            impot INTEGER,
            date_extraction TEXT,
            PRIMARY KEY (id_jeu, date_extraction)
        )
    """)
    
    # Table pour l'API Travaux
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS travaux (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type_travaux TEXT,
            building_name TEXT,
            terrain_requis TEXT,
            cout_estime INTEGER,
            duree_mois INTEGER,
            date_extraction TEXT
        )
    """)
    
    conn.commit()
    conn.close()

def executer_mise_a_jour_cron():
    print("⏰ [CRON BDD] Démarrage de la récupération API...")
    initialiser_base_de_donnees()
    
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # --- 1. SYNC MATÉRIAUX ---
    try:
        req = requests.get(f"{BASE_URL}/materials.json?key={API_KEY}", timeout=15)
        if req.status_code == 200:
            data = req.json().get("materials", [])
            for m in data:
                cursor.execute(
                    "INSERT INTO materiaux (nom, prix, unite, date_extraction) VALUES (?, ?, ?, ?)",
                    (m.get("name"), int(m.get("price", 0)), m.get("unit"), date_now)
                )
            print("✅ BDD : Table 'materiaux' actualisée.")
    except Exception as e:
        print(f"⚠️ Erreur matériaux : {e}")

    # --- 2. SYNC BÂTIMENTS ---
    try:
        req = requests.get(f"{BASE_URL}/buildings.json?key={API_KEY}", timeout=15)
        if req.status_code == 200:
            data = req.json().get("buildings_entreprise", [])
            for b in data:
                cursor.execute("""
                    INSERT OR REPLACE INTO batiments (id_jeu, nom, type, valeur, loyer, charge, impot, date_extraction)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (b.get("id"), b.get("name"), b.get("type"), int(b.get("value", 0)), 
                      int(b.get("rent", 0)), int(b.get("charge", 0)), int(b.get("tax", 0)), date_now))
            print("✅ BDD : Table 'batiments' actualisée.")
    except Exception as e:
        print(f"⚠️ Erreur bâtiments : {e}")

    # --- 3. SYNC TRAVAUX ---
    try:
        req = requests.get(f"{BASE_URL}/works.json?key={API_KEY}", timeout=15)
        if req.status_code == 200:
            data = req.json().get("works_entreprise", [])
            for w in data:
                cursor.execute("""
                    INSERT INTO travaux (type_travaux, building_name, terrain_requis, cout_estime, duree_mois, date_extraction)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (w.get("type"), w.get("building_name"), w.get("terrain_required"), 
                      int(w.get("estimated_cost", 0)), int(w.get("duration", 0)), date_now))
            print("✅ BDD : Table 'travaux' actualisée.")
    except Exception as e:
        print(f"⚠️ Erreur travaux : {e}")

    conn.commit()
    conn.close()
    print("🎉 [CRON BDD] Fin de la synchronisation. Base de données à jour.")

if __name__ == "__main__":
    executer_mise_a_jour_cron()
