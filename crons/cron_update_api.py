import os
import sys
import requests
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# Alignement du chemin d'importation NoSQL
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

# RÈGLE ARCHITECTURALE : Sécurisé par défaut à True pour préserver les quotas NoSQL
def executer_mise_a_jour_cron(exclure_players=True):
    import zoneinfo
    logs_session = []
    
    # Configuration du fuseau horaire de l'Empire
    tz_paris = zoneinfo.ZoneInfo("Europe/Paris")
    
    def notifier(texte):
        heure_france = datetime.now(tz_paris).strftime('%H:%M:%S')
        print(f"[{heure_france}] {texte}")
        logs_session.append(f"[{heure_france}] {texte}")

    notifier("⏰ [CRON CLOUD] Démarrage de la récupération...")
    
    date_now = datetime.now(tz_paris).strftime("%Y-%m-%d %H:%M:%S")
    timestamp_id = datetime.now(tz_paris).strftime("%Y%m%d_%H%M%S")

    # 🌐 CONFIGURATION FINALE DU SERVEUR MONDE 8
    API_KEY = "eiK8_110b18473efc48e9c63f76b5494ea18f"
    BASE_URL = "https://empireimmo.com"
    
    # En-tête obligatoire requis par la charte d'extraction du jeu
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
        req = requests.get(url_mat, headers=headers_navigation, timeout=15)
        notifier(f"📡 API Matériaux — Code : {req.status_code}")
        
        if req.status_code == 200:
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
        else:
            notifier(f"❌ Erreur API Matériaux : {req.text[:200]}")
    except Exception as e: 
        notifier(f"💥 Crash Matériaux/Usines : {e}")

    # --- 2. BÂTIMENTS ---
    try:
        url_bld = f"{BASE_URL}/api/buildings.json?key={API_KEY}"
        notifier("==========================================================================")
        notifier(f"🚀 [ADRESSE APPELÉE EN DIRECT] : {url_bld}")
        notifier("==========================================================================")
        req = requests.get(url_bld, headers=headers_navigation, timeout=15)
        notifier(f"📡 API Bâtiments — Code : {req.status_code}")
        
        if req.status_code == 200:
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

            liste_perso = data_json.get("batiments_perso", [])
            liste_entreprise = data_json.get("batiments_entreprise", [])
            liste_terrain = data_json.get("batiments_terrain", [])
            
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
            notifier(f"❌ Erreur API Bâtiments : {req.text[:200]}")
    except Exception as e: 
        notifier(f"💥 Crash Bâtiments : {e}")

    # --- 3. TRAVAUX ---
    try:
        url_wrk = f"{BASE_URL}/api/works.json?key={API_KEY}"
        notifier("==========================================================================")
        notifier(f"🚀 [ADRESSE APPELÉE EN DIRECT] : {url_wrk}")
        notifier("==========================================================================")
        req = requests.get(url_wrk, headers=headers_navigation, timeout=15)
        notifier(f"📡 API Travaux — Code : {req.status_code}")
        
        if req.status_code == 200:
            data_json = req.json()
            liste_t_perso = data_json.get("travaux_perso", [])
