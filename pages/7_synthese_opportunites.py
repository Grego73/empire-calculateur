import streamlit as st
import pandas as pd
import requests
import time
from utils import formater_monnaie_empire, convertir_saisie_en_nombre

st.title("✨ Le Podium des Opportunités de l'Empire")
st.markdown("Ce tableau de bord se connecte automatiquement à l'API officielle pour élire le **Top 3** de chaque stratégie.")

# Configuration de la clé API du Monde 8 récupérée
API_KEY = "eiK8_110b18473efc48e9c63f76b5494ea18f"
URL_WORKS = f"https://empireimmo.com{API_KEY}"
URL_MATERIALS = f"https://empireimmo.com{API_KEY}"

def calculer_ratio_secu(num, den):
    if den <= 0: 
        return 0.0
    try:
        str_num = str(abs(int(num)))
        str_den = str(abs(int(den)))
        max_len = max(len(str_num), len(str_den))
        
        if max_len > 10:
            facteur = 10 ** (max_len - 7)
            num_reduit = float(int(num) // facteur)
            den_reduit = float(int(den) // facteur)
            return (num_reduit / den_reduit * 100) if den_reduit > 0 else 0.0
        
        return float(num) / float(den) * 100
    except:
        return 0.0

# --- SYSTÈME DE CACHE CONFORME À LA CONSTITUTION (4 HEURES / 14400 SECONDES) ---
def charger_donnees_api():
    instant_present = time.time()
    cache_duration = 14400  # 4 heures en secondes
    
    # Vérification de la validité du cache en mémoire de session
    if "last_api_fetch" in st.session_state and (instant_present - st.session_state["last_api_fetch"] < cache_duration):
        return st.session_state["cached_works"], st.session_state["cached_materials"], "💾 Données chargées depuis le cache local."

    try:
        req_works = requests.get(URL_WORKS, timeout=10)
        req_materials = requests.get(URL_MATERIALS, timeout=10)
        
        if req_works.status_code == 200 and req_materials.status_code == 200:
            st.session_state["cached_works"] = req_works.json()
            st.session_state["cached_materials"] = req_materials.json()
            st.session_state["last_api_fetch"] = instant_present
            return st.session_state["cached_works"], st.session_state["cached_materials"], "🌐 Données synchronisées en direct depuis l'API."
        elif req_works.status_code == 429 or req_materials.status_code == 429:
            return None, None, "🚨 Erreur 429 : Limite d'appels API atteinte (Rate Limit). Réessayez plus tard."
        else:
            return None, None, f"❌ Erreur de connexion API (Codes : {req_works.status_code} / {req_materials.status_code})."
    except Exception as e:
        return None, None, f"⚠️ Serveur de l'Empire injoignable : {str(e)}"

# Exécution du chargement
json_works, json_materials, statut_message = charger_donnees_api()

if json_works is None or json_materials is None:
    st.error(statut_message)
    st.warning("⚠️ Impossible de générer les podiums sans accès aux données de l'API.")
else:
    st.caption(statut_message)
    
    try:
        # --- 1. EXTRACTION DE L'API MATÉRIAUX (Prix du marché actuel) ---
        terrains_frais = {}
        # Extraction des données de l'API Matériaux
        liste_materiaux = json_materials.get("materials", [])
        for mat in liste_materiaux:
            nom_mat = mat.get("name", "").strip()
            # Repérage dynamique des coûts des terrains
            if "TERRAIN" in nom_mat.upper() or "PARC" in nom_mat.upper():
                terrains_frais[nom_mat] = {
                    "prix": int(mat.get("price", 0)),
                    "charges": 0, # Les charges/impôts peuvent être complétées via les usines si nécessaire
                    "impots": 0
                }

        # --- 2. EXTRACTION DE L'API TRAVAUX & MONTAJE DES STRATÉGIES ---
        rows_loc = []
        rows_const = []
        
        # Le JSON de l'API travaux fournit deux listes distinctes : "works_perso" et "works_entreprise"
        travaux_liste = json_works.get("works_entreprise", [])
        
        for job in travaux_liste:
            nom_bat = job.get("building_name", "")
            type_travail = job.get("type", "")
            
            # Nous ciblons uniquement les lignes de construction de base
            if type_travail.upper() == "CONSTRUCTION":
                terrain_requis = job.get("terrain_required", "")
                cout_chantier_base = int(job.get("estimated_cost", 0))
                duree_mois = int(job.get("duration", 0))
                
                # Récupération du coût du terrain depuis notre dictionnaire matériaux
                info_terrain = terrains_frais.get(terrain_requis, {"prix": 0})
                cout_total_construction = cout_chantier_base + info_terrain["prix"]
                
                # Note : Pour calculer le rendement locatif exact et la marge pure, l'application 
                # a besoin de croiser ces lignes avec les données de loyer (disponibles dans buildings.json).
                # En attendant, simulation sécurisée basée sur les coûts de chantiers disponibles :
                rows_const.append({
                    "Nom": nom_bat,
                    "Cout_Total": cout_total_construction,
                    "Terrain": terrain_requis
                })

        # ==========================================
        # 🏗️ PILLIER 2 : PODIUM CONSTRUCTION (Trié par coût d'accès)
        # ==========================================
        st.subheader("🏗️ Top 3 Projets de Construction (Budgets de chantiers optimisés)")
        
        if rows_const:
            df_const = pd.DataFrame(rows_const).sort_values(by="Cout_Total", ascending=True).head(3)
            c1, c2, c3 = st.columns(3)
            medailles = ["🥇 1er", "🥈 2e", "🥉 3e"]
            
            for i, (idx, r) in enumerate(df_const.iterrows()):
                with [c1, c2, c3][i]:
                    st.metric(
                        label=f"{medailles[i]} - {r['Nom']}", 
                        value=formater_monnaie_empire(r['Cout_Total']), 
                        delta=f"Terrain : {r['Terrain']}"
                    )
        else:
            st.info("Aucune donnée de construction valide renvoyée par l'API.")

    except Exception as e:
        st.error(f"⚠️ Erreur lors du traitement algorithmique des données API : {str(e)}")
