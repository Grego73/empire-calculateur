# 🏛️ Empire Calculateur — Monde 8

Bienvenue sur le dépôt officiel du **Calculateur Empire**, l'outil stratégique de gestion, d'audit comptable et d'analyse financière pour piloter vos investissements immobiliers sur le **Monde 8** d'Empire Immo.

L'application s'appuie sur une interface utilisateur dynamique, une base de données Cloud résiliente et un écosystème de robots d'extraction totalement automatisés.

---

## 🚀 Architecture Globale

L'écosystème est divisé en trois piliers technologiques majeurs :

1. **Frontend (Interface)** : Développé avec **Streamlit**, offrant un tableau de bord unifié, un outil d'audit instantané pour les filiales, et des modules de calculs en cascade pour l'équilibrage des fonds propres.
2. **Backend (Base de données)** : Propulsé par **Google Cloud Firestore (Firebase)** en mode NoSQL, centralisant l'historique des cours des matériaux et l'état des 529 infrastructures.
3. **Automation (Robots)** : Orchestré par **GitHub Actions**, exécutant des scripts Python asynchrones pour maintenir la base de données à jour sans aucune intervention humaine.

---

## ⏱️ Système d'Automatisation (Chronologies)

Pour préserver les quotas de la base de données et respecter les limites de requêtes de l'API du jeu, l'automatisation est segmentée en deux workflows distincts :

### 1. ⚡ Synchro Légère — Taux du Promoteur (Toutes les 4 heures)
* **Fréquence** : 00h01, 04h01, 08h01, 12h01, 16h01, 20h01 (Heure de Paris).
* **Fichier** : `.github/workflows/cron_taux_4h.yml` ➔ `run_cron_taux.py`.
* **Action** : Interroge les endpoints légers `materials.json` et `buildings.json` pour capturer instantanément l'évolution des deux taux du promoteur et mettre à jour la configuration générale.
* **Saisons** : Géré à 100% automatiquement (Heure d'été / Heure d'hiver) via la bibliothèque Python `zoneinfo`.

### 2. 🗄️ Synchro Lourde — Catalogue des Biens (Quotidien à 03h30)
* **Fréquence** : Une fois par jour à **03h30** du matin.
* **Fichier** : `.github/workflows/cron_global_3h30.yml` ➔ `run_cron_global.py`.
* **Action** : Récupère l'intégralité du catalogue des 529 bâtiments, l'état des chantiers en cours, le cours complet des matériaux sur le marché, et met à jour le classement général des joueurs.

---

## 📂 Arborescence du Projet

```text
empire-calculateur/
├── .github/
│   └── workflows/
│       ├── cron_taux_4h.yml         # Workflow GitHub Actions (Taux léger 4H)
│       └── cron_global_3h30.yml     # Workflow GitHub Actions (Global lourd 24H)
├── crons/
│   ├── cron_update_api.py           # Script d'extraction complet d'origine
│   └── cron_update_taux.py          # Script d'extraction des taux légers
├── pages/
│   ├── 1_frais_gestion.py           # Module d'extraction de l'exploitation
│   ├── 2_primes.py                  # Module de calcul et plafonnement des paies
│   ├── 3_performance.py             # Compilation comptable et suivi du ROI
│   ├── 4_equilibrage.py             # Moteur de calcul d'injections en cascade
│   ├── 5_analyse_locative.py        # Rendement immobilier net par bâtiment
│   ├── 6_chantiers_et_embellissement.py # Arbitrage financier (Achat direct vs Construction)
│   └── 7_synthese_opportunites.py   # Page "Opportunités du Jour" (Biens en Promo)
├── main.py                          # Point d'entrée de la navigation de l'application
├── run_cron_taux.py                 # Lanceur d'horloge pour le cron 4H
├── run_cron_global.py               # Lanceur d'horloge pour le cron de 3h30
├── requirements.txt                 # Dépendances logicielles du projet
└── README.md                        # Manuel d'utilisation
```

---

## 🔒 Sécurité et Variables d'Environnement

Pour s'exécuter en toute sécurité sur les serveurs d'intégration continue de GitHub, le projet utilise les **GitHub Secrets**. Aucun identifiant privé ou clé d'accès Firebase n'est écrit en dur dans le code source.

### Secret requis sur GitHub :
* **`FIREBASE_CREDENTIALS_JSON`** : Contient l'intégralité du bloc JSON généré par la console Firebase lors de la création de votre clé privée de compte de service (`project_id`, `private_key`, etc.).

---

## 🛠️ Installation Locale (Développement)

Pour faire tourner le calculateur et son interface sur votre machine locale :

1. Clonez le dépôt GitHub :
   ```bash
   git clone https://github.com
   cd empire-calculateur
   ```
2. Installez les packages requis :
   ```bash
   pip install -r requirements.txt
   ```
3. Placez votre fichier de clés Firebase `firebase_credentials.json` à la racine ou configurez vos variables locales Streamlit.
4. Lancez le serveur local de l'application :
   ```bash
   streamlit run main.py
   ```

---

## 👑 Crédits & Maintenance
Développé et optimisé pour l'administration de l'Empire de **Grego73** sur le Monde 8.
