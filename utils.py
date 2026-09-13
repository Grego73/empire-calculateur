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
def verifier_concordance_rapport(texte_rapport):
    lines = texte_rapport.strip().split('\n')
    data = {}
    
    # Extraction chirurgicale des chiffres en ignorant les textes et symboles Ø
    for line in lines:
        if not line.strip(): continue
        # Nettoyage des espaces doubles pour éviter les décalages
        line_clean = " ".join(line.split())
        
        # Correspondance des lignes clés
        if "Résultat avant impôts" in line_clean:
            data["avant_impots"] = int("".join(filter(str.isdigit, line_clean)))
        elif "Impôts sur le résultat" in line_clean or "Impôt sur le résultat" in line_clean:
            data["impots"] = int("".join(filter(str.isdigit, line_clean)))
        elif "Résultat NET" in line_clean:
            data["net"] = int("".join(filter(str.isdigit, line_clean)))
        elif "Total Actif" in line_clean:
            data["actif"] = int("".join(filter(str.isdigit, line_clean)))
        elif "Total Passif" in line_clean:
            data["passif"] = int("".join(filter(str.isdigit, line_clean)))
            
    # Vérification des règles comptables
    erreurs = []
    if "avant_impots" in data and "impots" in data and "net" in data:
        calcul_net = data["avant_impots"] - data["impots"]
        if abs(calcul_net - data["net"]) > 10: # Tolérance de 10 unités pour les arrondis du jeu
            erreurs.append(f"❌ Écart Résultat : Avant Impôts - Impôts devrait faire {calcul_net:,}, mais le rapport indique {data['net']:,}")
            
    if "actif" in data and "passif" in data:
        if abs(data["actif"] - data["passif"]) > 10:
            erreurs.append(f"❌ Écart Bilan : Le Total Actif ({data['actif']:,}) n'est pas égal au Total Passif ({data['passif']:,})")
            
    return erreurs, data
