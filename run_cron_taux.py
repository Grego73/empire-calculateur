import os
import sys
from datetime import datetime
import zoneinfo  # Gestion automatique été/hiver
import firebase_admin
from firebase_admin import credentials

# 1. Analyse du type de déclenchement GitHub Actions
evenement_github = os.environ.get("GITHUB_EVENT_NAME", "").strip().lower()

# Le run est forcé si vous cliquez sur "Run workflow" ou si vous le lancez localement
force_run = (evenement_github == "workflow_dispatch" or evenement_github == "")

# 2. Détermination de l'heure légale en France
tz_france = zoneinfo.ZoneInfo("Europe/Paris")
heure_actuelle_france = datetime.now(tz_france)

heure_locale = heure_actuelle_france.hour
minute_locale = heure_actuelle_france.minute

# Les heures cibles où l'API du jeu actualise ses taux
heures_cibles_jeu = [0, 4, 8, 12, 16, 20]

print(f"📋 Diagnostic Horloge — Heure France : {heure_locale}h{minute_locale} | Événement GitHub : '{evenement_github}' | Run Forcé : {force_run}")

# 3. Validation du créneau : soit l'heure est pile dans la cible automatique, soit le run est forcé manuellement
if force_run or (heure_locale in heures_cibles_jeu and 0 <= minute_locale <= 25):
    print("🚀 Autorisation accordée. Initialisation du processus de synchronisation...")
    
    # Lecture et vérification du secret d'accès Firebase NoSQL
    secret_credentials = os.environ.get("FIREBASE_CREDENTIALS_JSON", "")
    if not secret_credentials:
        print("❌ Erreur critique : Le secret 'FIREBASE_CREDENTIALS_JSON' est vide ou introuvable dans les paramètres GitHub.")
        sys.exit(1)

    if not firebase_admin._apps:
        import json
        try:
            info_cles = json.loads(secret_credentials)
            info_cles["private_key"] = info_cles["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(info_cles)
            firebase_admin.initialize_app(cred)
            print("🔑 Connexion Firebase Cloud Firestore établie.")
        except Exception as err_json:
            print(f"❌ Erreur lors du parsing du fichier JSON des credentials : {err_json}")
            sys.exit(1)

    # Exécution de la mise à jour des taux
    try:
        sys.path.append(os.path.abspath(os.path.dirname(__file__)))
        from crons.cron_update_taux import executer_mise_a_jour_taux_uniquement

        journaux_execution = executer_mise_a_jour_taux_uniquement()
        print("\n".join(journaux_execution))
        print("✅ Script exécuté jusqu'au terme de sa logique.")
        sys.exit(0)
    except Exception as err_cron:
        print(f"💥 Échec durant l'import ou l'appel de executer_mise_a_jour_taux_uniquement : {err_cron}")
        sys.exit(1)
else:
    # Si le créneau correspond au fuseau horaire de l'autre saison, arrêt propre
    print(f"💤 Créneau ignoré ({heure_locale}h{minute_locale}). Ce déclenchement est réservé à l'autre saison. Veille automatique.")
    sys.exit(0)
