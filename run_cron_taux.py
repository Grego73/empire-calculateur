import os
import sys
import json
from datetime import datetime
import zoneinfo
import firebase_admin
from firebase_admin import credentials

print("==========================================================================")
print("🚀 SCRIPT GITHUB ACTIONS — CRON TAUX LÉGER (NETTOYÉ & FORCÉ)")
print("==========================================================================")

# 1. Trace horaire pour information dans les logs
tz_france = zoneinfo.ZoneInfo("Europe/Paris")
heure_actuelle_france = datetime.now(tz_france)
print(f"[TRACE] Heure système UTC : {datetime.now().strftime('%H:%M:%S')}")
print(f"[TRACE] Heure locale France : {heure_actuelle_france.strftime('%H:%M:%S')}")

# 2. Validation du Secret Firebase
secret_brut = os.environ.get("FIREBASE_CREDENTIALS_JSON", "").strip()
if not secret_brut:
    print("[❌ ERREUR CRITIQUE] Le secret 'FIREBASE_CREDENTIALS_JSON' est introuvable.")
    sys.exit(1)
    
try:
    structure_cles = json.loads(secret_brut)
    print(f"[✅] JSON de connexion valide. Project ID : '{structure_cles.get('project_id')}'")
except Exception as e_json:
    print(f"[❌] Le secret n'est pas un JSON valide : {e_json}")
    sys.exit(1)

# 3. Connexion à Firebase
if not firebase_admin._apps:
    try:
        structure_cles["private_key"] = structure_cles["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(structure_cles)
        firebase_admin.initialize_app(cred)
        print("[✅] Firebase Admin SDK initialisé avec succès.")
    except Exception as e_fb:
        print(f"[❌] Échec d'allumage Firebase : {e_fb}")
        sys.exit(1)

# 4. Exécution systématique du traitement des taux
try:
    sys.path.append(os.path.abspath(os.path.dirname(__file__)))
    from crons.cron_update_taux import executer_mise_a_jour_taux_uniquement
    print("[✅] Lancement du robot de synchronisation des taux...")
    
    journaux_metier = executer_mise_a_jour_taux_uniquement()
    
    print("\n------------------- LOGS INTERNES DU SCRIPT METIER -------------------")
    print("\n".join(journaux_metier) if isinstance(journaux_metier, list) else str(journaux_metier))
    print("-----------------------------------------------------------------------\n")
    
    print("[✅] Fin du processus complet avec succès.")
    sys.exit(0)
except Exception as err_execution:
    print(f"[❌ ERREUR CRITIQUE] Le script s'est arrêté au milieu : {err_execution}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
