import os
import re
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import Query # Centralisé ici
import pandas as pd
import streamlit as st  
from datetime import datetime

# 🌐 CONFIGURATION CENTRALE DU MONDE 8 (SÉCURISÉE)
# Cherche d'abord dans st.secrets, sinon utilise la valeur par défaut
API_KEY = st.secrets.get("GAME_API_KEY", "eiK8_110b18473efc48e9c63f76b5494ea18f")
BASE_URL = "https://empireimmo.com"

URL_WORKS = f"{BASE_URL}/api/works.json?key={API_KEY}"
URL_MATERIALS = f"{BASE_URL}/api/materials.json?key={API_KEY}"

# 🏛️ ÉCHELLE MATHÉMATIQUE DE L'EMPIRE
DICTIONNAIRE_PALIERS = {
    "K": 10**3,   "M": 10**6,   "G": 10**9,   "T": 10**12,
    "P": 10**15,  "E": 10**18,  "Z": 10**21,  "Y": 10**24,
    "R": 10**27,  "Q": 10**30,  "U": 10**33,  "S": 10**36,
    "X": 10**39,  "N": 10**42,  "D": 10**45
}

# 🔑 CONNEXION SÉCURISÉE À FIREBASE
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

    if "E+" in texte_brut or "E-" in texte_brut or ("E" in texte_brut and any(x in texte_brut for x in "0123456789") and not any(suffixe in texte_brut for suffixe in ["K","M","G","T","P"])):
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
            valeur_num = float(nombre_partie) if "." in nombre_partie else int(nombre_partie)
                
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

    if not net_trouve:
        erreurs.append("Impossible de trouver la ligne 'Résultat Net' dans le texte.")
    if not actif_trouve:
        erreurs.append("Impossible de trouver la ligne 'Total Actif' ou 'Total Passif'.")
        
    if net_trouve and actif_trouve and data["net"] > data["actif"]:
        erreurs.append("Anomalie comptable : Le Résultat Net est supérieur au Total Actif.")

    return erreurs, data

# =========================================================
# 📥 LECTEURS CLOUD FIREBASE
# =========================================================

def recuperer_derniere_donnee_table(nom_table):
    try:
        docs_ordre = db.collection(nom_table).order_by("date_extraction", direction=Query.DESCENDING).limit(1).stream()
        
        derniere_date = None
        for doc in docs_ordre:
            derniere_date = doc.to_dict().get("date_extraction")
            
        if not derniere_date:
            print(f"⚪ Firebase : La collection '{nom_table}' est introuvable ou vide.")
            return None
            
        docs_complets = db.collection(nom_table).where("date_extraction", "==", derniere_date).stream()
        liste_elements = [doc.to_dict() for doc in docs_complets]
        
        if not liste_elements:
            return None
            
        df = pd.DataFrame(liste_elements)
        
        colonnes_argent = ["valeur", "loyer", "charge", "impot", "cout_estime"]
        for col in colonnes_argent:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                
        return df
        
    except Exception as e:
        print(f"💥 Erreur extraction Firebase ({nom_table}) : {e}")
        return None

def recuperer_historique_joueur(pseudo="Grego73"):
    try:
        docs = db.collection("players").where("pseudo", "==", pseudo).order_by("date_extraction", direction=Query.ASCENDING).stream()
        liste_historique = [doc.to_dict() for doc in docs]
        return pd.DataFrame(liste_historique) if liste_historique else None
    except Exception as e:
        print(f"Erreur historique Firebase pour {pseudo} : {e}")
        return None

def recuperer_historique_materiaux():
    try:
        docs = db.collection("materiaux").stream()
        donnees = []
        for doc in docs:
            d = doc.to_dict()
            if "nom" in d and "prix" in d and "date_extraction" in d:
                try:
                    dt = datetime.strptime(d["date_extraction"], "%Y-%m-%d %H:%M:%S")
                    date_formatee = dt.strftime("%d/%m %H:%M")
                except:
                    date_formatee = d["date_extraction"]
                    
                donnees.append({
                    "Matériau": d["nom"],
                    "Prix": d["prix"],
                    "Date": date_formatee,
                    "Brute": d["date_extraction"]
                })
        
        if not donnees:
            return None
            
        df = pd.DataFrame(donnees).sort_values(by="Brute")
        return df
    except Exception as e:
        print(f"Erreur lors de la récupération de l'historique matériaux : {e}")
        return None

def calculer_repartitions_equilibrage(df_filiales, montant_total_dispo=0):
    try:
        from decimal import Decimal
        df_calcul = df_filiales.copy()
        df_calcul["Montant_Num"] = df_calcul["Montant_RAW"].apply(lambda x: Decimal(str(x)))
        
        total_requis = df_calcul["Montant_Num"].sum()
        montant_holding = Decimal(str(montant_total_dispo))
        nb_filiales = max(len(df_calcul), 1)
        
        rep_strict = df_calcul[["Filiale", "Montant_Num"]].copy()
        rep_strict["Montant"] = rep_strict["Montant_Num"]
        
        rep_egal = df_calcul[["Filiale"]].copy()
        rep_egal["Montant"] = montant_holding / Decimal(nb_filiales)
        
        rep_prop = df_calcul[["Filiale", "Montant_Num"]].copy()
        
        if montant_holding >= total_requis:
            reste_a_partager = montant_holding - total_requis
            part_du_reste = reste_a_partager / Decimal(nb_filiales)
            rep_prop["Montant"] = rep_prop["Montant_Num"] + part_du_reste
        else:
            if total_requis > 0:
                rep_prop["Montant"] = rep_prop["Montant_Num"].apply(lambda x: (x / total_requis) * montant_holding)
            else:
                rep_prop["Montant"] = montant_holding / Decimal(nb_filiales)
            
        rep_strict["Montant"] = rep_strict["Montant"].astype(float)
        rep_egal["Montant"] = rep_egal["Montant"].astype(float)
        rep_prop["Montant"] = rep_prop["Montant"].astype(float)
        
        return float(total_requis), rep_strict[["Filiale", "Montant"]], rep_egal[["Filiale", "Montant"]], rep_prop[["Filiale", "Montant"]]
        
    except Exception as e:
        print(f"Erreur calcul répartition cascade : {e}")
        return 0.0, None, None, None

def recuperer_derniers_taux_configuration():
    try:
        docs = db.collection("configuration").order_by("date_extraction", direction=Query.DESCENDING).limit(1).stream()
        for doc in docs:
            d = doc.to_dict()
            return {
                "batiments": d.get("taux_promoteur_batiments", 0),
                "materiaux": d.get("taux_promoteur_materiaux", 0)
            }
        return {"batiments": 0, "materiaux": 0}
    except:
        return {"batiments": 0, "materiaux": 0}
