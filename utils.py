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
        
    # --- AJOUT SÉCURITÉ : Gestion des biens en PROMO à la volée via le tag * ---
    # Détecte si le texte contient un astérisque (ex: 482618382*20 pour 20% de promo)
    taux_promo = 0
    if "*" in texte_brut:
        try:
            parties_promo = texte_brut.split("*")
            texte_brut = parties_promo[0] # On garde la partie prix pour la suite du calcul
            taux_promo = int(parties_promo[1]) # On extrait le pourcentage (ex: 20)
        except:
            pass

    # --- Détection de la notation scientifique Excel (ex: 2.88E+23) ---
    if "E+" in texte_brut or "E-" in texte_brut or ("E" in texte_brut and any(x in texte_brut for x in ["0","1","2","3","4","5","6","7","8","9"]) and not any(suffixe in texte_brut for suffixe in ["K","M","G","T","P"])):
        try:
            valeur_calculee = int(float(texte_brut))
            if taux_promo > 0 and taux_promo < 100:
                valeur_calculee = int(valeur_calculee / (1 - (taux_promo / 100)))
            return valeur_calculee
        except:
            pass

    # --- Analyse classique pour vos suffixes personnalisés de l'Empire ---
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
                
            # Application de l'annulation de la promo si un taux a été détecté
            if taux_promo > 0 and taux_promo < 100:
                valeur_calculee = int(valeur_calculee / (1 - (taux_promo / 100)))
                
            return valeur_calculee
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
