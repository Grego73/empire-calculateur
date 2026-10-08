import os
import sys
import json
from datetime import datetime
import zoneinfo
import firebase_admin
from firebase_admin import credentials

print("==========================================================================")
print("🚀 SCRIPT GITHUB ACTIONS — CRON GLOBAL LOURD (NETTOYÉ & FORCÉ)")
print("==========================================================================")

# 1. Trace horaire pour information dans les logs
tz_france = zoneinfo.ZoneInfo("Europe/Paris")
heure_actuelle_france = datetime.now(tz_france)
print(f"[TRACE] Heure système UTC : {datetime.now().strftime('%H:%M:%S')}")
print(f"[TRACE] Heure locale France : {heure_actuelle_france.strftime('%H:%M:%S')}")

# 2. Validation du Secret Firebase
secret_credentials = os.environ.get("FIREBASE_CREDENTIALS_JSON", "")
if not secret_credentials:
    print("❌ Erreur critique : Le secret 'FIREBASE_CREDENTIALS_JSON' est manquant dans GitHub Secrets.")
    sys.exit(1)

# 3. Connexion à Firebase
if not firebase_admin._apps:
    try:
        info_cles = json.loads(secret_credentials)
        info_cles["private_key"] = info_cles["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(info_cles)
        firebase_admin.initialize_app(cred)
        print("[✅] Connexion établie avec Firebase Cloud Firestore.")
    except Exception as err_json:
        print(f"❌ Erreur lors du chargement de la clé Firebase : {err_json}")
        sys.exit(1)

# 4. Exécution systématique du traitement complet
try:
    sys.path.append(os.path.abspath(os.path.dirname(__file__)))
    from crons.cron_update_api import executer_mise_a_jour_cron

    print("[TRACE] Déclenchement du traitement global (Exclure_players = True pour économiser les quotas NoSQL)...")
    journaux_execution = executer_mise_a_jour_cron(exclure_players=True)
    
    print("\n------------------- JOURNAUX DU ROBOT GLOBAL -------------------")
    print("\n".join(journaux_execution) if isinstance(journaux_execution, list) else str(journaux_execution))
    print("-----------------------------------------------------------------\n")
    
    print("✅ Base NoSQL entièrement synchronisée avec succès.")
    sys.exit(0)
except Exception as err_cron:
    print(f"💥 Échec critique durant l'exécution du cron global : {err_cron}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
