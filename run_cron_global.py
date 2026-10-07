import os
import sys
from datetime import datetime
import zoneinfo
import firebase_admin
from firebase_admin import credentials

# 1. Analyse du type de déclenchement GitHub
evenement_github = os.environ.get("GITHUB_EVENT_NAME", "").strip().lower()
force_run = (evenement_github == "workflow_dispatch" or evenement_github == "")

# 2. Détermination de l'heure légale en France (Heure du serveur du jeu)
tz_france = zoneinfo.ZoneInfo("Europe/Paris")
heure_actuelle_france = datetime.now(tz_france)

heure_locale = heure_actuelle_france.hour
minute_locale = heure_actuelle_france.minute

print("==========================================================================")
print("🔍 SCRIPT CRON GLOBAL — DIAGNOSTIC HORLOGE")
print("==========================================================================")
print(f"[TRACE] Heure France détectée : {heure_locale}h{minute_locale} (Événement : '{evenement_github}')")

# 3. Validation de la fenêtre cible : 3h du matin (Autorisé entre 3h25 et 3h55)
if force_run or (heure_locale == 3):
    print("🚀 Créneau de 03h30 validé ou Exécution forcée. Démarrage de la mise à jour complète...")
    
    # Lecture du secret d'accès Firebase NoSQL
    secret_credentials = os.environ.get("FIREBASE_CREDENTIALS_JSON", "")
    if not secret_credentials:
        print("❌ Erreur critique : Le secret 'FIREBASE_CREDENTIALS_JSON' est manquant dans les paramètres GitHub.")
        sys.exit(1)

    if not firebase_admin._apps:
        import json
        try:
            info_cles = json.loads(secret_credentials)
            info_cles["private_key"] = info_cles["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(info_cles)
            firebase_admin.initialize_app(cred)
            print("[✅] Connexion établie avec succès à Firebase Cloud Firestore.")
        except Exception as err_json:
            print(f"❌ Erreur lors du chargement de la clé Firebase : {err_json}")
            sys.exit(1)

    # 4. Chargement et exécution de votre script d'origine
    try:
        sys.path.append(os.path.abspath(os.path.dirname(__file__)))
        from crons.cron_update_api import executer_mise_a_jour_cron

        print("[TRACE] Déclenchement du traitement lourd (sans la table 'players')...")
        journaux_execution = executer_mise_a_jour_cron(exclure_players=True)
        
        print("\n------------------- JOURNAUX DU ROBOT GLOBAL -------------------")
        print("\n".join(journaux_execution) if isinstance(journaux_execution, list) else str(journaux_execution))
        print("-----------------------------------------------------------------\n")
        
        print("✅ Base NoSQL entièrement synchronisée (hors players) avec succès.")
        sys.exit(0)
    except Exception as err_cron:
        print(f"💥 Échec critique durant l'exécution du cron global : {err_cron}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
else:
    # Arrêt propre si ce n'est pas la bonne saison horaire
    print(f"💤 Créneau ignoré ({heure_locale}h{minute_locale}). Ce déclenchement correspond à l'autre saison. Veille automatique.")
    sys.exit(0)
