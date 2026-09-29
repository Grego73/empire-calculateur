import os
import sys
from datetime import datetime
import zoneinfo  # Gestion native des fuseaux horaires
import firebase_admin
from firebase_admin import credentials

# 1. Détermination précise de l'heure locale en France
tz_france = zoneinfo.ZoneInfo("Europe/Paris")
heure_actuelle_france = datetime.now(tz_france)

heure_locale = heure_actuelle_france.hour
minute_locale = heure_actuelle_france.minute

# 2. Définition des fenêtres d'exécution du jeu
heures_cibles_jeu = [0, 4, 8, 12, 16, 20]

# Détection si le lancement est un clic manuel sur GitHub
event_github = os.environ.get("GITHUB_EVENT_NAME", "")
force_run = (event_github == "workflow_dispatch" or event_github == "")

# 3. Condition de validation de l'horloge
if (heure_locale in heures_cibles_jeu and 0 <= minute_locale <= 20) or force_run:
    print(f"⏰ Heure française validée : {heure_locale}h{minute_locale}. Alignement parfait ou run forcé.")
    
    # Initialisation sécurisée de Firebase NoSQL avec le secret GitHub
    if not firebase_admin._apps:
        import json
        try:
            info_cles = json.loads(os.environ["FIREBASE_CREDENTIALS_JSON"])
            info_cles["private_key"] = info_cles["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(info_cles)
            firebase_admin.initialize_app(cred)
        except Exception as err_env:
            print(f"❌ Erreur critique : Le secret FIREBASE_CREDENTIALS_JSON est mal configuré ou introuvable : {err_env}")
            sys.exit(1) # Arrêt sur erreur réelle

    # Chargement et exécution de la synchronisation des taux
    try:
        sys.path.append(os.path.abspath(os.path.dirname(__file__)))
        from crons.cron_update_taux import executer_mise_a_jour_taux_uniquement

        journaux = executer_mise_a_jour_taux_uniquement()
        print("\n".join(journaux))
        sys.exit(0) # Succès total
    except Exception as err_run:
        print(f"💥 Erreur lors de l'exécution du module cron_update_taux : {err_run}")
        sys.exit(1)
else:
    # ✨ CORRECTION : Si GitHub s'allume pour le créneau de l'autre saison, on quitte avec un code 0 (Succès)
    print(f"💤 Heure française ignorée ({heure_locale}h{minute_locale}). Ce créneau correspond à l'autre saison. Mise en veille propre.")
    sys.exit(0)
