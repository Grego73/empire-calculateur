import os
import sys
import requests
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import time
import streamlit as st  # ✅ Ajouté pour éviter le crash sur st.secrets

def requete_api_securisee(url, headers=None):
    """Effectue l'appel API avec gestion du blocage (Rate Limiting)"""
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 429:
            print("⚠️ [API EMPIRE] Trop de requêtes ! Pause de 5 secondes avant de réessayer...")
            time.sleep(5)
            response = requests.get(url, headers=headers, timeout=15)
        return response
    except Exception as e:
        print(f"💥 Erreur de connexion réseau : {e}")
        return None

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

def executer_mise_a_jour_cron(exclure_players=True):
    import zoneinfo
    logs_session = []
    tz_paris = zoneinfo.ZoneInfo("Europe/Paris")
    
    def notifier(texte):
        heure_france = datetime.now(tz_paris).strftime('%H:%M:%S')
        print(f"[{heure_france}] {texte}")
        logs_session.append(f"[{heure_france}] {texte}")

    notifier("⏰ [CRON CLOUD] Démarrage de la récupération...")
    date_now = datetime.now(tz_paris).strftime("%Y-%m-%d %H:%M:%S")
    timestamp_id = datetime.now(tz_paris).strftime("%Y%m%d_%H%M%S")

    API_KEY = "eiK8_110b18473efc48e9c63f76b5494ea18f"
    BASE_URL = "https://empireimmo.com"
    
    headers_navigation = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Application-Empire-Calculateur",
        "Accept": "application/json"
    }

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

    # --- 1. MATÉRIAUX & USINES ---
    try:
        url_mat = f"{BASE_URL}/api/materials.json?key={API_KEY}"
        notifier("==========================================================================")
        notifier(f"🚀 [ADRESSE APPELÉE EN DIRECT] : {url_mat}")
        notifier("==========================================================================")
        
        req = requete_api_securisee(url_mat, headers=headers_navigation)
        
        if req and req.status_code == 200:
            notifier(f"📡 API Matériaux — Code : {req.status_code}")
            data_json = req.json()
            taux_materiaux = securiser_entier(data_json.get("taux_promoteur", 0))
            
            db.collection("configuration").document(f"config_{timestamp_id}").set({
                "taux_promoteur_materiaux": taux_materiaux,
                "date_extraction": date_now
            }, merge=True)
            db.collection("configuration").document("config_actuelle").set({
                "taux_promoteur_materiaux": taux_materiaux,
                "date_extraction": date_now
            }, merge=True)
            notifier(f"⚙️ Configuration : Taux Promoteur MATÉRIAUX mis à jour ({taux_materiaux}%).")
            
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
            
            factories_list = data_json.get("usines", [])
            notifier(f"🏭 {len(factories_list)} usines détectées. Écriture par paquets...")
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
        elif req and req.status_code == 429:
            notifier("❌ [BLOCAGE] Empire Immo a bloqué notre clé pour cette heure-ci. On réessaiera au prochain cron.")
        else:
            notifier(f"❌ Erreur API : Code {req.status_code if req else 'Inconnu'}")
    except Exception as e: 
        notifier(f"💥 Crash Matériaux/Usines : {e}")

    # --- 2. BÂTIMENTS ---
    try:
        url_bld = f"{BASE_URL}/api/buildings.json?key={API_KEY}"
        notifier("==========================================================================")
        notifier(f"🚀 [ADRESSE APPELÉE EN DIRECT] : {url_bld}")
        notifier("==========================================================================")
        req = requete_api_securisee(url_bld, headers=headers_navigation)
        notifier(f"📡 API Bâtiments — Code : {req.status_code if req else 'Inconnu'}")
        
        if req and req.status_code == 200:
            data_json = req.json()
            taux_batiments = securiser_entier(data_json.get("taux_promoteur", 0))
            
            payload_config = {
                "taux_promoteur_batiments": taux_batiments,
                "date_mise_a_jour": data_json.get("mise a jour", date_now),
                "date_extraction": date_now
            }
            db.collection("configuration").document(f"config_{timestamp_id}").set(payload_config, merge=True)
            db.collection("configuration").document("config_actuelle").set(payload_config, merge=True)
            notifier(f"⚙️ Configuration : Taux Promoteur BÂTIMENTS mis à jour ({taux_batiments}%).")

            categories_batiments = [
                ("perso", data_json.get("batiments_perso", [])),
                ("entreprise", data_json.get("batiments_entreprise", [])),
                ("terrain", data_json.get("batiments_terrain", []))
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
                        "id_jeu": int(id_j), 
                        "nom": str(b.get("nom", "Inconnu")), 
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
                    total_enregistre += 1
                    if c_batch >= 500:
                        batch.commit()
                        batch = db.batch()
                        c_batch = 0
            if c_batch > 0:
                batch.commit()
            notifier(f"✅ Collection 'batiments' entièrement synchronisée ({total_enregistre} lignes).")
        else:
            notifier(f"❌ Erreur API Bâtiments : {req.text[:200] if req else 'Inconnu'}")
    except Exception as e: 
        notifier(f"💥 Crash Bâtiments : {e}")

    # --- 3. TRAVAUX ---
    try:
        url_wrk = f"{BASE_URL}/api/works.json?key={API_KEY}"
        notifier("==========================================================================")
        notifier(f"🚀 [ADRESSE APPELÉE EN DIRECT] : {url_wrk}")
        notifier("==========================================================================")
        req = requete_api_securisee(url_wrk, headers=headers_navigation)
        notifier(f"📡 API Travaux — Code : {req.status_code if req else 'Inconnu'}")
        
        if req and req.status_code == 200:
            data_json = req.json()
            liste_t_perso = data_json.get("travaux_perso", [])
            liste_t_entreprise = data_json.get("travaux_entreprises", [])
            
            notifier(f"🏗️ Détection JSON : {len(liste_t_perso)} travaux personnels, {len(liste_t_entreprise)} travaux entreprises.")
            
            categories_travaux = [
                ("perso", liste_t_perso),
                ("entreprise", liste_t_entreprise)
            ]
            
            batch = db.batch()
            c_batch = 0
            total_travaux_enregistre = 0
            
            for categorie, listes in categories_travaux:
                for w in listes:
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
                    
                    if c_batch >= 500:
                        batch.commit()
                        batch = db.batch()
                        c_batch = 0
            if c_batch > 0:
                batch.commit()
            notifier(f"✅ Collection 'travaux' entièrement synchronisée ({total_travaux_enregistre} lignes).")
        else:
            notifier(f"❌ Erreur API Travaux : {req.status_code if req else 'Inconnu'}")
    except Exception as e: 
        notifier(f"💥 Crash Travaux : {e}")

    # --- 4. CLASSEMENT DES JOUEURS (PLAYERS) ---
    # Soumis au paramètre d'exclusion pour préserver drastiquement les quotas NoSQL Firestore
    if exclure_players:
        notifier("⚠️ [QUOTAS] Le paramètre 'exclure_players' est activé. Saut de la synchronisation du classement.")
    else:
        try:
            url_ply = f"{BASE_URL}/api/players.json?key={API_KEY}"
            notifier("==========================================================================")
            notifier(f"🚀 [ADRESSE APPELÉE EN DIRECT] : {url_ply}")
            notifier("==========================================================================")
            req = requete_api_securisee(url_ply, headers=headers_navigation)
            notifier(f"📡 API Joueurs — Code : {req.status_code if req else 'Inconnu'}")
            
            if req and req.status_code == 200:
                players_list = req.json().get("joueurs", [])
                notifier(f"🏆 {len(players_list)} joueurs détectés dans le classement. Alignement en base...")
                
                batch = db.batch()
                c_batch = 0
                total_players_enregistre = 0
                
                for p in players_list:
                    pseudo_j = p.get('pseudo', 'Inconnu')
                    # Création d'un identifiant stable associant le pseudo à la date d'extraction
                    doc_id = f"{pseudo_j.replace(' ', '_')}_{timestamp_id}"
                    doc_ref = db.collection("players").document(doc_id)
                    
                    batch.set(doc_ref, {
                        "pseudo": str(pseudo_j),
                        "classement": securiser_entier(p.get("classement", 0)),
                        "niveau": securiser_entier(p.get("niveau", 1)),
                        "points": securiser_entier(p.get("points", 0)),
                        "date_extraction": date_now
                    })
                    c_batch += 1
                    total_players_enregistre += 1
                    
                    if c_batch >= 500:
                        batch.commit()
                        batch = db.batch()
                        c_batch = 0
                if c_batch > 0:
                    batch.commit()
                notifier(f"✅ Collection 'players' entièrement rafraîchie ({total_players_enregistre} profils).")
            else:
                notifier(f"❌ Erreur API Joueurs : {req.status_code if req else 'Inconnu'}")
        except Exception as e:
            notifier(f"💥 Crash Classement Joueurs : {e}")

    notifier("🏁 [CRON CLOUD] Fin de la session d'extraction avec succès.")
    return logs_session
