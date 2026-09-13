import re

# ÉCHELLE SÉCURISÉE ET CALIBRÉE SUR VOTRE PATRIMOINE (216 Z)
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
            # Division par la vraie puissance de 10 pour afficher la bonne lettre
            reste = abs_n / valeur
            signe = "-" if n < 0 else ""
            return f"{signe}{reste:,.2f} {suffixe}".replace(",", " ")
            
    return f"{n:,}".replace(",", " ")

def convertir_saisie_en_nombre(saisie_texte):
    texte_propre = str(saisie_texte).strip().upper().replace(" ", "").replace("€", "")
    if not texte_propre:
        return 0
        
    match = re.match(r"^([0-9\.,]+)([A-Z]?)$", texte_propre)
    if match:
        nombre_partie = match.group(1).replace(",", ".")
        suffixe_partie = match.group(2)
        
        try:
            valeur_num = float(nombre_partie)
            if suffixe_partie in DICTIONNAIRE_PALIERS:
                return int(valeur_num * DICTIONNAIRE_PALIERS[suffixe_partie])
            return int(valeur_num)
        except:
            return 0
    return 0
