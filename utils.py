import os
import re
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd

# 🌐 CONFIGURATION CENTRALE DE L'API EMPIRE IMMO
API_KEY = "eiK8_110b18473efc48e9c63f76b5494ea18f"
BASE_URL = "https://empireimmo.com"

# URLs découpées proprement par endpoint pour vos pages analytiques
URL_WORKS = f"{BASE_URL}/works.json?key={API_KEY}"
URL_MATERIALS = f"{BASE_URL}/materials.json?key={API_KEY}"

# 🏛️ ÉCHELLE MATHÉMATIQUE DE L'EMPIRE
DICTIONNAIRE_PALIERS = {
    "K": 10**3,   "M": 10**6,   "G": 10**9,   "T": 10**12,
    "P": 10**15,  "E": 10**18,  "Z": 10**21,  "Y": 10**24,
    "R": 10**27,  "Q": 10**30,  "U": 10**33,  "S": 10**36,
    "X": 10**39,  "N": 10**42,  "D": 10**45
}

# 🔑 CONNEXION SÉCURISÉE À FIREBASE (CLIENT UNIQUE)
DOSSIER_UTILS = os.path.dirname(os.path.abspath(__file__))
CHEMIN_CLE = os.path.join(DOSSIER_UTILS, "data_cache", "firebase_credentials.json")

if not firebase_admin._apps:
    if os.path.exists(CHEMIN_CLE):
        cred = credentials.Certificate(CHEMIN_CLE)
        firebase_admin.initialize_app(cred)
    else:
        raise FileNotFoundError(f"Le fichier de clés Firebase est introuvable dans : {CHEMIN_CLE}")

db = firestore.client()

# 🧮 FONCTIONS DE TRADUCTION TEXTE <> NOMBRE
def formater_monnaie_empire(nombre):
    try:
        n = int(nombre)
    except:
        return str(nombre)
        
    abs_n = abs(n)
    paliers_tries = sorted(DICTIONNAIRE_PALIERS.items(), key=lambda x: x[1], reverse=True)
    
    for suffixe, valeur in paliers_tries:
        if abs_n >= valeur:
            reste = abs_n / valeur
            signe = "-" if n < 0 else ""
            return f"{signe}{reste:,.2f} {suffixe}".replace(",", " ")
            
    return f"{n:,}".replace(",", " ")

def convertir_saisie_en_nombre(saisie_texte):
    texte_brut = str(saisie_texte).strip().upper().replace(" ", "").replace("€", "")
    if not texte_brut:
        return 0
        
    taux_promo = 0
    if "*" in texte_brut:
        try:
            parties_promo = texte_brut.split("*")
            texte_brut = parties_promo[0]
            taux_promo = int(parties_promo[1])
        except:
            pass

    if "E+" in texte_brut or "E-" in texte_brut or ("E" in texte_brut and any(x in texte_brut for x in ["0","1","2","3","4","5","6","7","8","9"]) and not any(suffixe in texte_brut for suffixe in ["K","M","G","T","P"])):
        try:
            valeur_calculee = int(float(texte_brut))
            if 0 < taux_promo < 100:
                valeur_calculee = int(valeur_calculee / (1 - (taux_promo / 100)))
            return valeur_calculee
        except:
            pass

    match = re.match(r"^([0-9\.,]+)([A-Z]?)$", texte_brut)
    if match:
        nombre_partie = match.group(1).replace(",", ".")
        suffixe_partie = match.group(2)
        
        try:
            if "." not in nombre_partie:
                valeur_num = int(nombre_partie)
            else:
                valeur_num = float(nombre_partie)
                
            if suffixe_partie in DICTIONNAIRE_PALIERS:
                valeur_calculee = int(valeur_num * DICTIONNAIRE_PALIERS[suffixe_partie])
            else:
                valeur_calculee = int(valeur_num)
                
            if 0 < taux_promo < 100:
                valeur_calculee = int(valeur_calculee / (1 - (taux_promo / 100)))
                
            return valeur_calculee
        except:
            return 0
    return 0

def verifier_concordance_rapport(rapport_texte):
    erreurs = []
    data = {"net": 0, "actif": 0}
    if not rapport_texte or not rapport_texte.strip():
        return ["Le rapport est vide."], data
    lignes = rapport_texte.strip().split('\n')
    for ligne in lignes:
        ligne_up = ligne.upper()
        if "RÉSULTAT NET" in ligne_up or "RESULTAT NET" in ligne_up:
            match = re.search(r'([\d.,]+\s*[A-Z]?)', ligne_up)
            if match: data["net"] = convertir_saisie_en_nombre(match.group(1))
        if "TOTAL ACTIF" in ligne_up or "TOTAL PASSIF" in ligne_up:
            match = re.search(r'([\d.,]+\s*[A-Z]?)', ligne_up)
            if match: data["actif"] = convertir_saisie_en_nombre(match.group(1))
    return erreurs, data

# =========================================================
# 📥 LECTEURS CLOUD FIREBASE
# =========================================================

def recuperer_derniere_donnee_table(nom_table):
    """
    Trouve le timestamp de la synchronisation la plus récente dans Firebase
    et extrait toutes les lignes correspondantes sous forme de DataFrame Pandas.
    """
    try:
        from google.cloud.firestore_v1.base_query import Query
        docs_ordre = db.collection(nom_table).order_by("date_extraction", direction=Query.DESCENDING).limit(1).stream()
        
        derniere_date = None
        for doc in docs_ordre:
            derniere_date = doc.to_dict().get("date_extraction")
            
        if not derniere_date:
            return None
            
        docs_complets = db.collection(nom_table).where("date_extraction", "==", derniere_date).stream()
        
        liste_elements = []
        for doc in docs_complets:
            liste_elements.append(doc.to_dict())
            
        return pd.DataFrame(liste_elements) if liste_elements else None
        
    except Exception as e:
        print(f"Erreur extraction Firebase ({nom_table}) : {e}")
        return None

def recuperer_historique_joueur(pseudo="Grego73"):
    """
    Récupère tout l'historique de croissance d'un joueur depuis le cloud.
    """
    try:
        from google.cloud.firestore_v1.base_query import Query
        docs = db.collection("players").where("pseudo", "==", pseudo).order_by("date_extraction", direction=Query.ASCENDING).stream()
        
        liste_historique = []
        for doc in docs:
            liste_historique.append(doc.to_dict())
            
        return pd.DataFrame(liste_historique) if liste_historique else None
    except Exception as e:
        print(f"Erreur historique Firebase pour {pseudo} : {e}")
        return None
