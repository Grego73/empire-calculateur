import re


# ÉCHELLE UNIQUE ET SÉCURISÉE DE L'EMPIRE
DICTIONNAIRE_PALIERS = {
    "K": 10**3,   "M": 10**6,   "G": 10**9,   "T": 10**12,
    "P": 10**15,  "E": 10**18,  "Z": 10**21,  "Y": 10**24,
    "R": 10**27,  "Q": 10**30,  "U": 10**33,  "S": 10**36,
    "X": 10**39,  "N": 10**42,  "D": 10**45
}

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
    # Nettoyage initial de la chaîne
    texte_brut = str(saisie_texte).strip().upper().replace(" ", "").replace("€", "")
    if not texte_brut:
        return 0
        
    # --- GESTION DES PROMOS INDIVIDUELLES VIA LE TAG * ---
    taux_promo = 0
    if "*" in texte_brut:
        try:
            parties_promo = texte_brut.split("*")
            texte_brut = parties_promo[0]
            taux_promo = int(parties_promo[1])
        except:
            pass

    # --- DÉTECTION DE LA NOTATION SCIENTIFIQUE EXCEL ---
    if "E+" in texte_brut or "E-" in texte_brut or ("E" in texte_brut and any(x in texte_brut for x in ["0","1","2","3","4","5","6","7","8","9"]) and not any(suffixe in texte_brut for suffixe in ["K","M","G","T","P"])):
        try:
            valeur_calculee = int(float(texte_brut))
            if taux_promo > 0 and taux_promo < 100:
                valeur_calculee = int(valeur_calculee / (1 - (taux_promo / 100)))
            return valeur_calculee
        except:
            pass

    # --- ANALYSE DES SUFFIXES DE L'EMPIRE ---
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
                
            if taux_promo > 0 and taux_promo < 100:
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
            # Capture les chiffres, les points, les virgules et la lettre de palier à la fin
            match = re.search(r'([\d.,]+\s*[A-Z]?)', ligne_up)
            if match: data["net"] = convertir_saisie_en_nombre(match.group(1))
        if "TOTAL ACTIF" in ligne_up or "TOTAL PASSIF" in ligne_up:
            match = re.search(r'([\d.,]+\s*[A-Z]?)', ligne_up)
            if match: data["actif"] = convertir_saisie_en_nombre(match.group(1))
    return erreurs, data

import os
import json

DATA_DIR = "data_cache"

def lire_donnees_locales_empire(endpoint):
    """
    Lit de manière sécurisée les données de l'Empire rafraîchies par le Cron.
    endpoint peut être : 'buildings', 'works', 'materials' ou 'players'
    """
    chemin_fichier = os.path.join(DATA_DIR, f"{endpoint}.json")
    
    if not os.path.exists(chemin_fichier):
        return None
        
    try:
        with open(chemin_fichier, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

import sqlite3
import pandas as pd

DB_NAME = "data_cache/empire_immo.db"

def recuperer_derniere_donnee_table(nom_table):
    """
    Se connecte à la BDD et extrait les dernières données insérées 
    par le Cron sous forme de DataFrame Pandas.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        # Étape 1 : Trouver la date de la dernière mise à jour globale dans cette table
        query_date = f"SELECT MAX(date_extraction) FROM {nom_table}"
        derniere_date = pd.read_sql_query(query_date, conn).iloc[0, 0]
        
        if derniere_date is None:
            conn.close()
            return None
            
        # Étape 2 : Récupérer toutes les lignes correspondant à cette mise à jour précise
        query_data = f"SELECT * FROM {nom_table} WHERE date_extraction = '{derniere_date}'"
        df = pd.read_sql_query(query_data, conn)
        
        conn.close()
        return df
    except Exception as e:
        print(f"Erreur lors de la lecture BDD : {e}")
        return None

def recuperer_historique_joueur(pseudo="Grego73"):
    """
    Récupère toutes les lignes d'historique enregistrées par le Cron 
    pour un joueur spécifique afin de suivre son évolution.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        query = f"SELECT points, classement, niveau, date_extraction FROM players WHERE pseudo = '{pseudo}' ORDER BY date_extraction ASC"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        print(f"Erreur historique joueur : {e}")
        return None
