import re

# ÉCHELLE DE RÉFÉRENCE DE L'EMPIRE
DICTIONNAIRE_PALIERS = {
    "K": 10**3,   "M": 10**6,   "G": 10**9,   "T": 10**12,
    "P": 10**15,  "E": 10**18,  "Z": 10**21,  "Y": 10**24,
    "R": 10**27,  "Q": 10**30,  "U": 10**33,  "S": 10**36,
    "X": 10**39,  "N": 10**42,  "D": 10**45
}

# 1. TRADUCTEUR : NOMBRE ENTIER -> TEXTE ABREGÉ (ex: 1000000000 -> 1.00 G)
def formater_monnaie_empire(nombre):
    try:
        n = int(nombre)
    except:
        return str(nombre)
        
    abs_n = abs(n)
    
    # Tri inversé pour tester les plus grands paliers en premier
    paliers_tries = sorted(DICTIONNAIRE_PALIERS.items(), key=lambda x: x[1], reverse=True)
    
    for suffixe, valeur in paliers_tries:
        if abs_n >= valeur:
            reste = abs_n / valeur
            signe = "-" if n < 0 else ""
            return f"{signe}{reste:,.2f} {suffixe}".replace(",", " ")
            
    return f"{n:,}".replace(",", " ")

# 2. TRADUCTEUR INVERSÉ : TEXTE ABREGÉ -> NOMBRE ENTIER PUR (ex: 100Y -> 100 * 10^24)
def convertir_saisie_en_nombre(saisie_texte):
    texte_propre = str(saisie_texte).strip().upper().replace(" ", "").replace("€", "")
    if not texte_propre:
        return 0
        
    # Regex pour isoler le chiffre (entier ou décimal) et la lettre finale
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
