import os
import re
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import streamlit as st  # Ajoutez-le tout en haut si manquant

# 🌐 CONFIGURATION CENTRALE DU MONDE 8 (CORRIGÉE)
API_KEY = "eiK8_110b18473efc48e9c63f76b5494ea18f"
BASE_URL = "https://monde8.empireimmo.com"

# URLs découpées proprement pour vos pages analytiques
URL_WORKS = f"{BASE_URL}/api/works.json?key={API_KEY}"
URL_MATERIALS = f"{BASE_URL}/api/materials.json?key={API_KEY}"

# 🏛️ ÉCHELLE MATHÉMATIQUE DE L'EMPIRE
DICTIONNAIRE_PALIERS = {
    "K": 10**3,   "M": 10**6,   "G": 10**9,   "T": 10**12,
    "P": 10**15,  "E": 10**18,  "Z": 10**21,  "Y": 10**24,
    "R": 10**27,  "Q": 10**30,  "U": 10**33,  "S": 10**36,
    "X": 10**39,  "N": 10**42,  "D": 10**45
}

# 🔑 CONNEXION SÉCURISÉE À FIREBASE (CLIENT COMPATIBLE PC ET CLOUD)
DOSSIER_UTILS = os.path.dirname(os.path.abspath(__file__))
CHEMIN_CLE = os.path.join(DOSSIER_UTILS, "data_cache", "firebase_credentials.json")

# Mettez à jour ce bloc d'initialisation :
if not firebase_admin._apps:
    if "firebase_credentials" in st.secrets:
        info_cles = dict(st.secrets["firebase_credentials"])
        info_cles["private_key"] = info_cles["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(info_cles)
        firebase_admin.initialize_app(cred)
    else:
        # Repli local au cas où
        DOSSIER_CRON = os.path.dirname(os.path.abspath(__file__))
        RACINE_PROJET = os.path.dirname(DOSSIER_CRON)
        CHEMIN_CLE = os.path.join(RACINE_PROJET, "data_cache", "firebase_credentials.json")
        cred = credentials.Certificate(CHEMIN_CLE)
        firebase_admin.initialize_app(cred)

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
    net_trouve = False
    actif_trouve = False
    
    for ligne in lignes:
        ligne_up = ligne.upper()
        if "RÉSULTAT NET" in ligne_up or "RESULTAT NET" in ligne_up:
            match = re.search(r'([\d.,]+\s*[A-Z]?)', ligne_up)
            if match: 
                data["net"] = convertir_saisie_en_nombre(match.group(1))
                net_trouve = True
        if "TOTAL ACTIF" in ligne_up or "TOTAL PASSIF" in ligne_up:
            match = re.search(r'([\d.,]+\s*[A-Z]?)', ligne_up)
            if match: 
                data["actif"] = convertir_saisie_en_nombre(match.group(1))
                actif_trouve = True

    # 🚨 BLOC DE VÉRIFICATION MANQUANT
    if not net_trouve:
        erreurs.append("Impossible de trouver la ligne 'Résultat Net' dans le texte.")
    if not actif_trouve:
        erreurs.append("Impossible de trouver la ligne 'Total Actif' ou 'Total Passif'.")
        
    # Exemple de règle métier (à adapter selon les règles de votre jeu) :
    # Si le résultat net ne doit pas dépasser une certaine proportion de l'actif par exemple
    if net_trouve and actif_trouve and data["net"] > data["actif"]:
        erreurs.append("Anomalie comptable : Le Résultat Net est supérieur au Total Actif.")

    return erreurs, data


# =========================================================
# 📥 LECTEURS CLOUD FIREBASE
# =========================================================

def recuperer_derniere_donnee_table(nom_table):
    """
    Récupère l'extraction la plus récente pour une table donnée.
    S'adapte automatiquement à la structure sans filtre bloquant.
    """
    try:
        from google.cloud.firestore_v1.base_query import Query
        
        # 1. On cherche le document le plus récent pour trouver la dernière date d'extraction
        docs_ordre = db.collection(nom_table).order_by("date_extraction", direction=Query.DESCENDING).limit(1).stream()
        
        derniere_date = None
        for doc in docs_ordre:
            derniere_date = doc.to_dict().get("date_extraction")
            
        if not derniere_date:
            print(f"⚪ Firebase : La collection '{nom_table}' est vide en base.")
            return None
            
        # 2. On télécharge toutes les infrastructures extraites à cette date précise
        docs_complets = db.collection(nom_table).where("date_extraction", "==", derniere_date).stream()
        liste_elements = [doc.to_dict() for doc in docs_complets]
        
        if not liste_elements:
            return None
            
        # 3. Conversion propre en DataFrame pour vos tableaux Streamlit
        df = pd.DataFrame(liste_elements)
        
        # Sécurité Nettoyage : Si les colonnes financières ont été sauvées en texte, 
        # on les remet en nombres pour éviter les bugs de calcul de ROI dans vos pages
        colonnes_argent = ["valeur", "loyer", "charge", "impot", "cout_estime"]
        for col in colonnes_argent:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                
        return df
        
    except Exception as e:
        print(f"💥 Erreur extraction Firebase ({nom_table}) : {e}")
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

def recuperer_historique_materiaux():
    """
    Récupère l'historique des prix de tous les matériaux 
    pour alimenter le graphique de l'accueil.
    """
    try:
        # Extraction de tous les documents de la collection materiaux
        docs = db.collection("materiaux").stream()
        
        donnees = []
        for doc in docs:
            d = doc.to_dict()
            # Sécurité : On s'assure que le document contient les clés nécessaires
            if "nom" in d and "prix" in d and "date_extraction" in d:
                # Extraction uniquement de l'heure et du jour pour un affichage plus propre (JJ/MM HH:mm)
                try:
                    dt = datetime.strptime(d["date_extraction"], "%Y-%m-%d %H:%M:%S")
                    date_formatee = dt.strftime("%d/%m %H:%M")
                except:
                    date_formatee = d["date_extraction"]
                    
                donnees.append({
                    "Matériau": d["nom"],
                    "Prix ($)": d["prix"],
                    "Date": date_formatee,
                    "Brute": d["date_extraction"] # Gardé pour le tri chronologique
                })
        
        if not donnees:
            return None
            
        # Conversion en DataFrame Pandas
        df = pd.DataFrame(donnees)
        # Tri par ordre chronologique pour que la courbe aille de gauche à droite
        df = df.sort_values(by="Brute")
        return df
        
    except Exception as e:
        print(f"Erreur lors de la récupération de l'historique matériaux : {e}")
        return None
