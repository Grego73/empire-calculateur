import os
import sys
import json
from datetime import datetime
import zoneinfo

print("==========================================================================")
print("🔍 LOGS DE DIAGNOSTIC AVANCÉ ET ULTRA-PRÉCIS")
print("==========================================================================")

# 1. TRACE HORAIRE
tz_france = zoneinfo.ZoneInfo("Europe/Paris")
dt_france = datetime.now(tz_france)
print(f"[TRACE] Heure système UTC : {datetime.now().strftime('%H:%M:%S')}")
print(f"[TRACE] Heure locale France : {dt_france.strftime('%H:%M:%S')}")

evenement = os.environ.get("GITHUB_EVENT_NAME", "").strip().lower()
force_run = (evenement == "workflow_dispatch" or evenement == "")
print(f"[TRACE] Type d'événement GitHub détecté : '{evenement}' (Force run = {force_run})")

# 2. ARCHITECTURE DES DOSSIERS
print(f"[TRACE] Dossier de travail actuel : {os.getcwd()}")
print(f"[TRACE] Liste des fichiers à la racine : {os.listdir('.')}")
if os.path.exists("crons"):
    print(f"[TRACE] Liste des fichiers dans /crons : {os.listdir('crons')}")
else:
    print("[ALERT] Le dossier '/crons' n'existe pas à la racine du dépôt GitHub !")

# 3. VÉRIFICATION DU SECRET SECURE
secret_brut = os.environ.get("FIREBASE_CREDENTIALS_JSON", "").strip()
if not secret_brut:
    print("[❌ ERREUR] Le secret 'FIREBASE_CREDENTIALS_JSON' est introuvable ou vide dans GitHub Settings.")
    sys.exit(1)
else:
    print(f"[TRACE] Taille du secret détecté : {len(secret_brut)} caractères.")
    try:
        structure_cles = json.loads(secret_brut)
        print(f"[✅ COMPORTEMENT] JSON valide. Clés détectées : {list(structure_cles.keys())}")
        print(f"[TRACE] Project ID associé : '{structure_cles.get('project_id')}'")
    except Exception as e_json:
        print(f"[❌ ERREUR] Le secret n'est pas un JSON valide. Erreur de parsing : {e_json}")
        sys.exit(1)

# 4. INITIALISATION FIREBASE
print("[TRACE] Initialisation de l'instance Firebase Admin...")
import firebase_admin
from firebase_admin import credentials

if not firebase_admin._apps:
    try:
        structure_cles["private_key"] = structure_cles["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(structure_cles)
        firebase_admin.initialize_app(cred)
        print("[✅ COMPORTEMENT] Firebase Admin SDK initialisé avec succès.")
    except Exception as e_fb:
        print(f"[❌ ERREUR] Échec d'allumage Firebase : {e_fb}")
        sys.exit(1)

# 5. EXECUTION ET TRACE DU CRON METIER
print("[TRACE] Importation du module 'crons.cron_update_taux'...")
try:
    sys.path.append(os.path.abspath(os.path.dirname(__file__)))
    from crons.cron_update_taux import executer_mise_a_jour_taux_uniquement
    print("[✅ COMPORTEMENT] Module importé avec succès. Lancement de la fonction...")
    
    journaux_metier = executer_mise_a_jour_taux_uniquement()
    
    print("\n------------------- LOGS INTERNES DU SCRIPT METIER -------------------")
    print("\n".join(journaux_metier))
    print("-----------------------------------------------------------------------\n")
    
    print("[✅ COMPORTEMENT] Fin du processus complet avec succès.")
    sys.exit(0)
except Exception as err_execution:
    print(f"[❌ ERREUR CRITIQUE] Le script s'est arrêté au milieu de son exécution : {err_execution}")
    import traceback
    print("[TRACE] Traceback complet de l'erreur :")
    traceback.print_exc()
    sys.exit(1)
