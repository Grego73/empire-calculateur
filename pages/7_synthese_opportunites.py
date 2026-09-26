import streamlit as st
import pandas as pd
import requests
import time
from utils import formater_monnaie_empire, URL_WORKS, URL_MATERIALS

st.title("✨ Le Podium des Opportunités de l'Empire")

def charger_donnees_api():
    instant_present = time.time()
    if "last_api_fetch" in st.session_state and (instant_present - st.session_state["last_api_fetch"] < 14400):
        return st.session_state["cached_works"], st.session_state["cached_materials"], "💾 Données chargées depuis le cache local."

    try:
        req_works = requests.get(URL_WORKS, timeout=10)
        req_materials = requests.get(URL_MATERIALS, timeout=10)
        if req_works.status_code == 200 and req_materials.status_code == 200:
            st.session_state["cached_works"] = req_works.json()
            st.session_state["cached_materials"] = req_materials.json()
            st.session_state["last_api_fetch"] = instant_present
            return st.session_state["cached_works"], st.session_state["cached_materials"], "🌐 Synchronisé depuis l'API."
        return None, None, "🚨 Limite d'appels API ou serveur saturé."
    except Exception as e: return None, None, f"⚠️ Erreur de connexion : {e}"

json_works, json_materials, statut_message = charger_donnees_api()

if json_works is None or json_materials is None:
    st.error(statut_message)
else:
    st.caption(statut_message)
    try:
        terrains = {m.get("name").strip(): int(m.get("price", 0)) for m in json_materials.get("materials", []) if "TERRAIN" in m.get("name", "").upper()}
        rows_const = []
        for job in json_works.get("works_entreprise", []):
            if job.get("type", "").upper() == "CONSTRUCTION":
                t_req = job.get("terrain_required", "")
                c_total = int(job.get("estimated_cost", 0)) + terrains.get(t_req, 0)
                rows_const.append({"Nom": job.get("building_name"), "Cout_Total": c_total, "Terrain": t_req})

        st.subheader("🏗️ Top 3 Projets de Construction Économiques")
        if rows_const:
            df_c = pd.DataFrame(rows_const).sort_values(by="Cout_Total", ascending=True).head(3)
            cols_m = st.columns(3)
            medailles = ["🥇 1er", "🥈 2e", "🥉 3e"]
            for i, (_, r) in enumerate(df_c.iterrows()):
                with cols_m[i]: st.metric(label=f"{medailles[i]} - {r['Nom']}", value=formater_monnaie_empire(r['Cout_Total']), delta=f"Terrain: {r['Terrain']}")
    except Exception as e: st.error(f"⚠️ Erreur traitement algorithmique : {e}")
