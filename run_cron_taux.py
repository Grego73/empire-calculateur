import os
import sys
import firebase_admin
from firebase_admin import credentials

# 1. Injection sécurisée des identifiants Firebase depuis les secrets GitHub
if not firebase_admin._apps:
    import json
    # GitHub va injecter la clé secrète sous forme de chaîne de caractères
    info_cles = json.loads(os.environ["FIREBASE_CREDENTIALS_JSON"])
    info_cles["private_key"] = info_cles["private_key"].replace("\\n", "\n")
    cred = credentials.Certificate(info_cles)
    firebase_admin.initialize_app(cred)

# 2. Alignement des dossiers pour charger le module de calcul
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from crons.cron_update_taux import executer_mise_a_jour_taux_uniquement

# 3. Lancement de l'extraction
if __name__ == "__main__":
    journaux = executer_mise_a_jour_taux_uniquement()
    print("\n".join(journaux))
