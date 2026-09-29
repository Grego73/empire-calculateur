import streamlit as st
import os
import sys
import requests
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# Alignement du chemin d'importation
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils import API_KEY, BASE_URL

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

def executer_mise_a_jour_cron():
    logs_session = []
    
    def notifier(texte):
        print(texte)
        logs_session.append(f"[{datetime.now().strftime('%H:%M:%S')}] {texte}")

    notifier("⏰ [CRON CLOUD] Démarrage de la récupération...")
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    timestamp_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Limites des entiers signés 64-bits pour Firestore Google Cloud
    MAX_INT64 = 9223372036854775807
    MIN_INT64 = -9223372036854775808

    def securiser_entier(valeur):
        """Convertit proprement en int réel et sature aux limites 64-bits si besoin"""
        try:
            num = int(float(valeur))
            if num > MAX_INT64: return MAX_INT64
            if num < MIN_INT64: return MIN_INT64
            return num
        except (ValueError, TypeError):
            return 0

    # --- 1. MATÉRIAUX & USINES (JSON) ---
    try:
        req = requests.get(f"{BASE_URL}/api/materials.json?key={API_KEY}", timeout=15)
        notifier(f"📡 API Matériaux — Code : {req.status_code}")
        if req.status_code == 200:
            data_json = req.json()
            
            # 🎯 Extraction du taux promoteur MATÉRIAUX
            taux_materiaux = securiser_entier(data_json.get("taux_promoteur", 0))
            
            # Enregistrement ou mise à jour du document de configuration du run actuel
            db.collection("configuration").document(f"config_{timestamp_id}").set({
                "taux_promoteur_materiaux": taux_materiaux,
                "date_extraction": date_now
            }, merge=True) # merge=True évite d'écraser si le document existe déjà
            notifier(f"⚙️ Configuration : Taux Promoteur MATÉRIAUX mis à jour ({taux_materiaux}%).")
            
            # A. Traitement des Matériaux
            materials_list = data_json.get("materiaux", [])
            notifier(f"📦 {len(materials_list)} matériaux détectés dans le flux API.")
            batch = db.batch()
            for m in materials_list:
                nom_brut = m.get('nom', 'Inconnu')
                doc_id = f"{nom_brut.replace('/', '_')}_{timestamp_id}"
                doc_ref = db.collection("materiaux").document(doc_id)
                batch.set(doc_ref, {
                    "nom": nom_brut, 
                    "prix": securiser_entier(m.get("prix", 0)), 
                    "unite": m.get("unite"), 
                    "date_extraction": date_now
                })
            batch.commit()
            notifier("✅ Collection 'materiaux' synchronisée avec succès.")
            
            # B. Traitement des Usines (Nouveau Bloc Monde 8)
            factories_list = data_json.get("usines", [])
            notifier(f"🏭 {len(factories_list)} usines détectées dans le flux API. Écriture par paquets...")
            batch = db.batch()
            c_batch = 0
            for u in factories_list:
                nom_usine = u.get('usine', 'Usine Inconnue')
                doc_id = f"{nom_usine.replace('/', '_').replace(' ', '_')}_{timestamp_id}"
                doc_ref = db.collection("usines").document(doc_id)
                batch.set(doc_ref, {
                    "nom": nom_usine,
                    "matiere": u.get("matiere"),
                    "valeur": securiser_entier(u.get("valeur", 0)),
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
            if c_batch > 0:
                batch.commit()
            notifier("✅ Collection 'usines' synchronisée avec succès.")
            
        else:
            notifier(f"❌ Erreur API Matériaux : {req.text[:200]}")
    except Exception as e: 
        notifier(f"💥 Crash Matériaux/Usines : {e}")

    # --- 2. BÂTIMENTS (AVEC SÉPARATION DES 3 CATÉGORIES ET TAUX PROMOTEUR) ---
    try:
        req = requests.get(f"{BASE_URL}/api/buildings.json?key={API_KEY}", timeout=15)
        notifier(f"📡 API Bâtiments — Code : {req.status_code}")
        if req.status_code == 200:
            data_json = req.json()
            
            # 🎯 Extraction du taux promoteur BÂTIMENTS
            taux_batiments = securiser_entier(data_json.get("taux_promoteur", 0))
            
            # Fusion dans le même document de configuration du run actuel
            db.collection("configuration").document(f"config_{timestamp_id}").set({
                "taux_promoteur_batiments": taux_batiments,
                "date_mise_a_jour": data_json.get("mise a jour", date_now),
                "date_extraction": date_now
            }, merge=True)
            notifier(f"⚙️ Configuration : Taux Promoteur BÂTIMENTS mis à jour ({taux_batiments}%).")
            
            liste_perso = data_json.get("batiments_perso", [])
            liste_entreprise = data_json.get("batiments_entreprise", [])
            liste_terrain = data_json.get("batiments_terrain", [])
            
            notifier(f"🏢 Détection JSON : {len(liste_perso)} personnels, {len(liste_entreprise)} entreprises, {len(liste_terrain)} terrains.")
            
            categories_batiments = [
                ("perso", liste_perso),
                ("entreprise", liste_entreprise),
                ("terrain", liste_terrain)
            ]
            
            batch = db.batch()
            c_batch = 0
            total_enregistre = 0
            
            for categorie, liste in categories_batiments:
                for b in liste:
                    id_j = b.get('id', 0)
                    doc_id = f"{id_j}_{timestamp_id}"
                    doc_ref = db.collection("batiments").document(doc_id)
                    
                    batch.set(doc_ref, {
                        "id_jeu": id_j, 
                        "nom": b.get("nom", "Inconnu"), 
                        "type": b.get("type", "Standard"), 
                        "valeur": securiser_entier(b.get("valeur", 0)),
                        "loyer": securiser_entier(b.get("loyer", 0)), 
                        "charge": securiser_entier(b.get("charge", 0)), 
                        "impot": securiser_entier(b.get("impot", 0)), 
                        "categorie": categorie,
                        "date_extraction": date_now
                    })
                    
                    c_batch += 1
                    total_enregistre += 1
                    if c_batch >= 500:
                        batch.commit()
                        batch = db.batch()
                        c_batch = 0
                        
            if c_batch > 0:
                batch.commit()
                
            notifier(f"✅ Collection 'batiments' entièrement synchronisée ({total_enregistre} lignes enregistrées avec tags).")
        else:
            notifier(f"❌ Erreur API Bâtiments : {req.text[:200]}")
    except Exception as e: 
        notifier(f"💥 Crash Bâtiments : {e}")

    # --- 3. TRAVAUX (ALIGNEMENT ET SYNCHRONISATION MONDE 8) ---
    try:
        req = requests.get(f"{BASE_URL}/api/works.json?key={API_KEY}", timeout=15)
        notifier(f"📡 API Travaux — Code : {req.status_code}")
        if req.status_code == 200:
            data_json = req.json()
            
            # 💡 Correction des clés d'API au pluriel pour le Monde 8
            liste_t_perso = data_json.get("travaux_perso", [])
            liste_t_entreprise = data_json.get("travaux_entreprises", []) # ◄--- 'entreprises' au pluriel
            
            notifier(f"🏗️ Détection JSON : {len(liste_t_perso)} travaux personnels, {len(liste_t_entreprise)} travaux entreprises.")
            
            categories_travaux = [
                ("perso", liste_t_perso),
                ("entreprise", liste_t_entreprise)
            ]
            
            batch = db.batch()
            c_batch = 0
            total_travaux_enregistre = 0
            
            for categorie, liste in categories_travaux:
                for w in liste:
                    id_w = w.get('id', 0)
                    t_type = w.get('type', 'Construction')
                    b_name = w.get('nom', 'Inconnu')
                    
                    doc_id = f"{id_w}_{t_type.lower()}_{timestamp_id}"
                    doc_ref = db.collection("travaux").document(doc_id)
                    
                    batch.set(doc_ref, {
                        "id_jeu": int(id_w),
                        "type_travaux": str(t_type), 
                        "building_name": str(b_name), 
                        "terrain_requis": str(w.get("terrain", "Aucun")),
                        "cout_estime": securiser_entier(w.get("cout", 0)), 
                        "duree_mois": securiser_entier(w.get("duree", 0)), 
                        "categorie": categorie,
                        "date_extraction": date_now
                    })
                    
                    c_batch += 1
                    total_travaux_enregistre += 1
                    
                    # 💡 Alignement de l'indentation de l'écriture par paquets (20 espaces de décalage)
                    if c_batch >= 500:
                        batch.commit()
                        batch = db.batch()
                        c_batch = 0
                    
            if c_batch > 0:
                batch.commit()
                
            notifier(f"✅ Collection 'travaux' entièrement synchronisée ({total_travaux_enregistre} lignes enregistrées avec tags).")
        else:
            notifier(f"❌ Erreur API Travaux : {req.text[:200]}")
    except Exception as e: 
        notifier(f"💥 Crash Travaux : {e}")


    notifier("🏁 [CRON CLOUD] Fin du processus de synchronisation.")
    return logs_session

if __name__ == "__main__":
    executer_mise_a_jour_cron()
