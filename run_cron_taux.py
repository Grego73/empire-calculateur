import os
import sys
import json
from datetime import datetime
import zoneinfo
import firebase_admin
from firebase_admin import credentials

print("==========================================================================")
print("🔍 SCRIPT GITHUB ACTIONS — CRON TAUX LÉGER 4H (OPTIMISÉ ÉTÉ/HIVER)")
print("==========================================================================")

# 1. TRACE HORAIRE & FUSEAU DE L'EMPIRE
tz_france = zoneinfo.ZoneInfo("Europe/Paris")
heure_actuelle_france = datetime.now(tz_france)

heure_locale = heure_actuelle_france.hour
minute_locale = heure_actuelle_france.minute

print(f"[TRACE] Heure système UTC : {datetime.now().strftime('%H:%M:%S')}")
print(f"[TRACE] Heure locale France : {heure_actuelle_france.strftime('%H:%M:%S')}")

evenement_github = os.environ.get("GITHUB_EVENT_NAME", "").strip().lower()
force_run = (evenement_github == "workflow_dispatch" or evenement_github == "")
print(f"📋 Diagnostic Horloge — Heure France : {heure_locale}h{minute_locale} | Événement GitHub : '{evenement_github}' | Run Forcé : {force_run}")

# 2. ARCHITECTURE DES DOSSIERS
print(f"[TRACE] Dossier de travail actuel : {os.getcwd()}")
print(f"[TRACE] Liste des fichiers à la racine : {os.listdir('.')}")

# Heures cibles de l'API + Heures de bascule saisonnière pour couvrir à 100% les crons de GitHub (01 min)
heures_autorisees_jeu = [0, 1, 4, 5, 8, 9, 12, 13, 16, 17, 20, 21, 23]

# 3. VALIDATION DU CRÉNEAU HORAIRE
if force_run or (heure_locale in heures_autorisees_jeu):
    print("🚀 Autorisation accordée par l'horloge. Initialisation du processus...")
    
    # 4. VÉRIFICATION DU SECRET SECURE
    secret_brut = os.environ.get("FIREBASE_CREDENTIALS_JSON", "").strip()
    if not secret_brut:
        print("[❌ ERREUR CRITIQUE] Le secret 'FIREBASE_CREDENTIALS_JSON' est introuvable dans GitHub Settings.")
        sys.exit(1)
        
    try:
        structure_cles = json.loads(secret_brut)
        print(f"[✅ COMPORTEMENT] JSON de connexion valide. Project ID : '{structure_cles.get('project_id')}'")
    except Exception as e_json:
        print(f"[❌ ERREUR] Le secret n'est pas un JSON valide : {e_json}")
        sys.exit(1)

    # 5. INITIALISATION FIREBASE
    if not firebase_admin._apps:
        try:
            structure_cles["private_key"] = structure_cles["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(structure_cles)
            firebase_admin.initialize_app(cred)
            print("[✅ COMPORTEMENT] Firebase Admin SDK initialisé avec succès.")
        except Exception as e_fb:
            print(f"[❌ ERREUR] Échec d'allumage Firebase : {e_fb}")
            sys.exit(1)

    # 6. EXECUTION DU CRON METIER
    try:
        sys.path.append(os.path.abspath(os.path.dirname(__file__)))
        from crons.cron_update_taux import executer_mise_a_jour_taux_uniquement
        print("[✅ COMPORTEMENT] Module crons.cron_update_taux importé. Lancement du robot...")
        
        journaux_metier = executer_mise_a_jour_taux_uniquement()
        
        print("\n------------------- LOGS INTERNES DU SCRIPT METIER -------------------")
        print("\n".join(journaux_metier))
        print("-----------------------------------------------------------------------\n")
        
        print("[✅ COMPORTEMENT] Fin du processus complet avec succès.")
        sys.exit(0)
    except Exception as err_execution:
        print(f"[❌ ERREUR CRITIQUE] Le script s'est arrêté au milieu de son exécution : {err_execution}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
else:
    print(f"💤 Créneau ignoré ({heure_locale}h{minute_locale}). Ce déclenchement automatique est réservé à l'autre saison. Veille automatique.")
    sys.exit(0)
