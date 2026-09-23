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
    texte_propre = str(saisie_texte).strip().upper().replace(" ", "").replace("€", "")
    if not texte_propre:
        return 0
        
    match = re.match(r"^([0-9\.,]+)([A-Z]?)$", texte_propre)
    if match:
        nombre_partie = match.group(1).replace(",", ".")
        suffixe_partie = match.group(2)
        
        try:
            # Sécurité anti-arrondi : si c'est un entier, on reste en int (précision infinie en Python)
            if "." not in nombre_partie:
                valeur_num = int(nombre_partie)
            else:
                valeur_num = float(nombre_partie)
                
            if suffixe_partie in DICTIONNAIRE_PALIERS:
                return int(valeur_num * DICTIONNAIRE_PALIERS[suffixe_partie])
            return int(valeur_num)
        except:
            return 0
    return 0

def verifier_concordance_rapport(rapport_texte):
    """
    Fonction de secours intégrée pour valider l'appel dans app.py
    Évite le crash de type 'NoneType' si le rapport est mal copié.
    """
    erreurs = []
    data = {"net": 0, "actif": 0}
    
    if not rapport_texte or not rapport_texte.strip():
        return ["Le rapport est vide."], data
        
    # Analyse basique des lignes (Exemple de sécurité à adapter selon vos lignes de texte)
    lignes = rapport_texte.strip().split('\n')
    for ligne in lignes:
        ligne_up = ligne.upper()
        if "RÉSULTAT NET" in ligne_up or "RESULTAT NET" in ligne_up:
            chiffres = "".join(re.findall(r'\d+', ligne))
            if chiffres: data["net"] = convertir_saisie_en_nombre(chiffres)
        if "TOTAL ACTIF" in ligne_up or "TOTAL PASSIF" in ligne_up:
            chiffres = "".join(re.findall(r'\d+', ligne))
            if chiffres: data["actif"] = convertir_saisie_en_nombre(chiffres)
            
    return erreurs, data
