import os
import sys
from datetime import datetime
import zoneinfo # Gestion native et automatique des changements d'heure (DST)
import firebase_admin
from firebase_admin import credentials

# 1. Détermination précise de l'heure locale en France (gère l'été/hiver automatiquement)
tz_france = zoneinfo.ZoneInfo("Europe/Paris")
heure_actuelle_france = datetime.now(tz_france)

heure_locale = heure_actuelle_france.hour
minute_locale = heure_actuelle_france.minute

# 2. Sécurité : On autorise le script à s'exécuter UNIQUEMENT si on est dans les heures cibles du jeu
# On accepte une marge entre la minute 0 et 15 pour parer les légers retards de GitHub
heures_cibles_jeu = [0, 4, 8, 12, 16, 20]

# Si on est lancé manuellement (workflow_dispatch), on force l'exécution sans vérifier l'horloge
force_run = os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"

if heure_locale in heures_cibles_jeu and (0 <= minute_locale <= 15) or force_run:
    print(f"⏰ Heure française validée : {heure_locale}h{minute_locale}. Alignement parfait.")
    
    # Initialisation Firebase
    if not firebase_admin._apps:
        import json
        info_cles = json.loads(os.environ["FIREBASE_CREDENTIALS_JSON"])
        info_cles["private_key"] = info_cles["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(info_cles)
        firebase_admin.initialize_app(cred)

    # Lancement du traitement
    sys.path.append(os.path.abspath(os.path.dirname(__file__)))
    from crons.cron_update_taux import executer_mise_a_jour_taux_uniquement

    journaux = executer_mise_a_jour_taux_uniquement()
    print("\n".join(journaux))
else:
    # Si GitHub a lancé la machine pour l'autre saison, le script s'éteint sagement en 1 milliseconde
    print(f"💤 Heure française ignorée ({heure_locale}h{minute_locale}). Ce créneau correspond à l'autre saison. Mise en veille.")
