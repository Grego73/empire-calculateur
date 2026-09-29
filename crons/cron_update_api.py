import streamlit as st
import os
import sys
import requests
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# Alignement du chemin d'importation
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if not firebase_admin._apps:
    if "firebase_credentials" in st.secrets:
        info_cles = dict(st.secrets["firebase_credentials"])
        info_cles["private_key"] = info_cles["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(info_cles)
        firebase_admin.initialize_app(cred)
    else:
        DOSSIER_CRON = os.path.dirname(os.path.abspath(__file__))
        RACINE_PROJET = os.path.dirname(DOSSIER_CRON)
        CHEMIN_CLE = os.path.join(RACINE_PROJET, "data_cache", "firebase_credentials.json")
        cred = credentials.Certificate(CHEMIN_CLE)
        firebase_admin.initialize_app(cred)

db = firestore.client()

def executer_mise_a_jour_cron(exclure_players=False):
    logs_session = []
    
    def notifier(texte):
        print(texte)
        logs_session.append(f"[{datetime.now().strftime('%H:%M:%S')}] {texte}")

    notifier("⏰ [CRON CLOUD] Démarrage de la récupération...")
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    timestamp_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 🌐 CONFIGURATION FINALE DU SERVEUR MONDE 8
    API_KEY = "eiK8_110b18473efc48e9c63f76b5494ea18f"
    BASE_URL = "https://empireimmo.com"

    # Limites des entiers signés 64-bits pour Firestore Google Cloud
    MAX_INT64 = 9223372036854775807
    MIN_INT64 = -9223372036854775808

    def securiser_entier(valeur):
        try:
            num = int(float(valeur))
            if num > MAX_INT64: return MAX_INT64
            if num < MIN_INT64: return MIN_INT64
            return num
        except (ValueError, TypeError):
            return 0

    # --- 1. SÉCURISATION DU BLOC MATÉRIAUX & USINES ---
    try:
        url_mat = f"{BASE_URL}/api/materials.json?key={API_KEY}"
        req = requests.get(url_mat, timeout=15)
        
        # Fallback automatique au singulier si 404
        if req.status_code == 404:
            notifier("⚠️ Endpoint 'materials.json' non trouvé (404). Tentative sur 'material.json'...")
            url_mat = f"{BASE_URL}/api/material.json?key={API_KEY}"
            req = requests.get(url_mat, timeout=15)

        notifier(f"📡 API Matériaux — Code : {req.status_code}")
        if req.status_code == 200:
            data_json = req.json()
            taux_materiaux = securiser_entier(data_json.get("taux_promoteur", 0))
            
            payload_mat = {"taux_promoteur_materiaux": taux_materiaux, "date_extraction": date_now}
            db.collection("configuration").document(f"config_{timestamp_id}").set(payload_mat, merge=True)
            db.collection("configuration").document("config_actuelle").set(payload_mat, merge=True)
            
            materials_list = data_json.get("materiaux", data_json.get("materials", []))
            batch = db.batch()
            for m in materials_list:
                nom_brut = m.get('nom', m.get('name', 'Inconnu'))
                doc_id = f"{nom_brut.replace('/', '_')}_{timestamp_id}"
                doc_ref = db.collection("materiaux").document(doc_id)
                batch.set(doc_ref, {
                    "nom": nom_brut, 
                    "prix": securiser_entier(m.get("prix", m.get("price", 0))), 
                    "unite": m.get("unite"), 
                    "date_extraction": date_now
                })
            batch.commit()
            notifier("✅ Collection 'materiaux' synchronisée avec succès.")
            
            factories_list = data_json.get("usines", data_json.get("factories", []))
            batch = db.batch()
            c_batch = 0
            for u in factories_list:
                nom_usine = u.get('usine', u.get('name', 'Usine Inconnue'))
                doc_id = f"{nom_usine.replace('/', '_').replace(' ', '_')}_{timestamp_id}"
                doc_ref = db.collection("usines").document(doc_id)
                batch.set(doc_ref, {
                    "nom": nom_usine,
                    "matiere": u.get("matiere", u.get("material", "Inconnu")),
                    "valeur": securiser_entier(u.get("valeur", u.get("value", 0))),
                    "charge": securiser_entier(u.get("charge", 0)),
                    "impot": securiser_entier(u.get("impot", 0)),
                    "production": securiser_entier(u.get("production", 0)),
                    "date_extraction": date_now
                })
                c_batch += 1
                if c_batch >= 500:
                    batch.commit()
                    batch = db.batch()
                    c_batch = 0
            if c_batch > 0: batch.commit()
            notifier("✅ Collection 'usines' synchronisée.")
        else:
            notifier(f"❌ Erreur API Matériaux : {req.status_code}")
    except Exception as e: notifier(f"💥 Crash Matériaux/Usines : {e}")

    # --- 2. SÉCURISATION DU BLOC BÂTIMENTS ---
    try:
        url_bld = f"{BASE_URL}/api/buildings.json?key={API_KEY}"
        req = requests.get(url_bld, timeout=15)
        
        if req.status_code == 404:
            notifier("⚠️ Endpoint 'buildings.json' non trouvé (404). Tentative sur 'building.json'...")
            url_bld = f"{BASE_URL}/api/building.json?key={API_KEY}"
            req = requests.get(url_bld, timeout=15)

        notifier(f"📡 API Bâtiments — Code : {req.status_code}")
        if req.status_code == 200:
            data_json = req.json()
            taux_batiments = securiser_entier(data_json.get("taux_promoteur", 0))
            
            payload_bld = {"taux_promoteur_batiments": taux_batiments, "date_extraction": date_now}
            db.collection("configuration").document(f"config_{timestamp_id}").set(payload_bld, merge=True)
            db.collection("configuration").document("config_actuelle").set(payload_bld, merge=True)

            liste_perso = data_json.get("batiments_perso", [])
            liste_entreprise = data_json.get("batiments_entreprise", [])
            liste_terrain = data_json.get("batiments_terrain", data_json.get("batiments_terrains", []))
            
            categories_batiments = [("perso", liste_perso), ("entreprise", liste_entreprise), ("terrain", liste_terrain)]
            batch = db.batch()
            c_batch = 0
            for categorie, listes in categories_batiments:
                for b in listes:
                    id_j = b.get('id', 0)
                    doc_id = f"{id_j}_{timestamp_id}"
                    doc_ref = db.collection("batiments").document(doc_id)
                    batch.set(doc_ref, {
                        "id_jeu": int(id_j), 
                        "nom": str(b.get("nom", b.get("name", "Inconnu"))), 
                        "type": str(b.get("type", "Standard")), 
                        "niveau": securiser_entier(b.get("niveau", 0)),
                        "valeur": securiser_entier(b.get("valeur", 0)),
                        "loyer": securiser_entier(b.get("loyer", 0)), 
                        "charge": securiser_entier(b.get("charge", 0)), 
                        "impot": securiser_entier(b.get("impot", 0)), 
                        "promotion": securiser_entier(b.get("promotion", 0)),
                        "construction": securiser_entier(b.get("construction", 0)),
                        "embellissement": securiser_entier(b.get("embellissement", 0)),
                        "reparation": securiser_entier(b.get("reparation", 0)),
                        "categorie": categorie,
                        "date_extraction": date_now
                    })
                    c_batch += 1
                    if c_batch >= 500:
                        batch.commit()
                        batch = db.batch()
                        c_batch = 0
            if c_batch > 0: batch.commit()
            notifier("✅ Collection 'batiments' synchronisée.")
        else:
            notifier(f"❌ Erreur API Bâtiments : {req.status_code}")
    except Exception as e: notifier(f"💥 Crash Bâtiments : {e}")

    # --- 3. SÉCURISATION DU BLOC TRAVAUX ---
    try:
        url_wrk = f"{BASE_URL}/api/works.json?key={API_KEY}"
        req = requests.get(url_wrk, timeout=15)
        
        if req.status_code == 404:
            notifier("⚠️ Endpoint 'works.json' non trouvé (404). Tentative sur 'work.json'...")
            url_wrk = f"{BASE_URL}/api/work.json?key={API_KEY}"
            req = requests.get(url_wrk, timeout=15)

        notifier(f"📡 API Travaux — Code : {req.status_code}")
        if req.status_code == 200:
            data_json = req.json()
            liste_t_perso = data_json.get("travaux_perso", [])
            liste_t_entreprise = data_json.get("travaux_entreprises", data_json.get("travaux_entreprise", []))
            
            categories_travaux = [("perso", liste_t_perso), ("entreprise", liste_t_entreprise)]
            batch = db.batch()
            c_batch = 0
            for categorie, listes in categories_travaux:
                for w in listes:
                    id_w = w.get('id', 0)
                    t_type = w.get('type', 'Construction')
                    b_name = w.get('nom', w.get('name', 'Inconnu'))
                    doc_id = f"{id_w}_{t_type.lower()}_{timestamp_id}"
                    doc_ref = db.collection("travaux").document(doc_id)
                    batch.set(doc_ref, {
                        "id_jeu": int(id_w), "type_travaux": str(t_type), "building_name": str(b_name), 
                        "terrain_requis": str(w.get("terrain", "Aucun")), "cout_estime": securiser_entier(w.get("cout", 0)), 
                        "duree_mois": securiser_entier(w.get("duree", 0)), "categorie": categorie, "date_extraction": date_now
                    })
                    c_batch += 1
                    if c_batch >= 500:
                        batch.commit()
                        batch = db.batch()
                        c_batch = 0
            if c_batch > 0: 
                batch.commit()
            notifier("✅ Collection 'travaux' synchronisée.")
        else:
            notifier(f"❌ Erreur API Travaux : {req.status_code}")
    except Exception as e: 
        notifier(f"💥 Crash Travaux : {e}")

    # --- 4. CLASSEMENT DES JOUEURS ---
    if not exclure_players:
        try:
            url_ply = f"{BASE_URL}/api/players.json?key={API_KEY}"
            req = requests.get(url_ply, timeout=15)
            if req.status_code == 404:
                url_ply = f"{BASE_URL}/api/player.json?key={API_KEY}"
                req = requests.get(url_ply, timeout=15)

            notifier(f"📡 API Players — Code : {req.status_code}")
            if req.status_code == 200:
                players_list = req.json().get("players", [])
                batch = db.batch()
                c_batch = 0
                for p in players_list:
                    pseudo_j = p.get('pseudo', 'Inconnu')
                    doc_id = f"{pseudo_j.replace(' ', '_')}_{timestamp_id}"
                    doc_ref = db.collection("players").document(doc_id)
                    batch.set(doc_ref, {
                        "pseudo": pseudo_j, 
                        "classement": securiser_entier(p.get("classement", 0)),
                        "niveau": securiser_entier(p.get("niveau", 0)), 
                        "points": securiser_entier(p.get("points", 0)), 
                        "date_extraction": date_now
                    })
                    c_batch += 1
                    if c_batch >= 500:
                        batch.commit()
                        batch = db.batch()
                        c_batch = 0
                if c_batch > 0: 
                    batch.commit()
                notifier("✅ Collection 'players' synchronisée.")
        except Exception as e: 
            notifier(f"💥 Crash Players : {e}")
    else:
        notifier("⏭️ Table 'players' volontairement ignorée pour ce créneau quotidien d'optimisation des quotas.")

    notifier("🏁 [CRON CLOUD] Fin du processus de synchronisation.")
    return logs_session

if __name__ == "__main__":
    executer_mise_a_jour_cron()
