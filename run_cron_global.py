import os
import sys
import json
from datetime import datetime
import zoneinfo
import firebase_admin
from firebase_admin import credentials

print("==========================================================================")
print("🔍 SCRIPT GITHUB ACTIONS — CRON GLOBAL LOURD 03H30 (SÉCURISÉ)")
print("==========================================================================")

# 1. Détermination de l'heure légale en France
tz_france = zoneinfo.ZoneInfo("Europe/Paris")
heure_actuelle_france = datetime.now(tz_france)

heure_locale = heure_actuelle_france.hour
minute_locale = heure_actuelle_france.minute

evenement_github = os.environ.get("GITHUB_EVENT_NAME", "").strip().lower()
force_run = (evenement_github == "workflow_dispatch" or evenement_github == "")

print(f"[TRACE] Heure système UTC : {datetime.now().strftime('%H:%M:%S')}")
print(f"[TRACE] Heure locale France détectée : {heure_locale}h{minute_locale} (Événement : '{evenement_github}')")

# 2. Validation de la fenêtre cible : Autorisé à 3h du matin (et tolérance à 4h en cas de décalage ou retard GitHub)
heures_autorisees_global = 

if force_run or (heure_locale in heures_autorisees_global):
    print("🚀 Fenêtre horaire confirmée par l'horloge. Démarrage de la mise à jour complète...")
    
    secret_credentials = os.environ.get("FIREBASE_CREDENTIALS_JSON", "")
    if not secret_credentials:
        print("❌ Erreur critique : Le secret 'FIREBASE_CREDENTIALS_JSON' est manquant dans GitHub Secrets.")
        sys.exit(1)

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

    # 3. Chargement et exécution du traitement lourd
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
else:
    print(f"💤 Créneau ignoré ({heure_locale}h{minute_locale}). Ce déclenchement automatique est réservé au créneau de 03h30. Veille automatique.")
    sys.exit(0)
