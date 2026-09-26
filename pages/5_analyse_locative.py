import streamlit as st
import pandas as pd
import requests
import time
from utils import formater_monnaie_empire, convertir_saisie_en_nombre

st.title("📊 Analyse Locative & Rendements via API")
st.markdown("Optimisez vos investissements en temps réel grâce aux données directes du marché de l'Empire.")

PLAFOND_MAX_BIENS = 500000000
API_KEY = "eiK8_110b18473efc48e9c63f76b5494ea18f"
URL_BUILDINGS = f"https://empireimmo.com{API_KEY}"

# --- FONCTION DE CACHE LOCAL SÉCURISÉ ---
def charger_buildings_api():
    instant_present = time.time()
    if "last_fetch_buildings" in st.session_state and (instant_present - st.session_state["last_fetch_buildings"] < 14400):
        return st.session_state["cached_buildings"], "💾 Données chargées depuis le cache local (Mise à jour toutes les 4h)."
    
    try:
        req = requests.get(URL_BUILDINGS, timeout=10)
        if req.status_code == 200:
            st.session_state["cached_buildings"] = req.json()
            st.session_state["last_fetch_buildings"] = instant_present
            return st.session_state["cached_buildings"], "🌐 Données synchronisées en direct depuis l'API."
        elif req.status_code == 429:
            return None, "🚨 Limite d'appels API atteinte (Rate Limit). Usage du dernier cache disponible."
        return None, f"❌ Erreur de connexion API (Code {req.status_code})."
    except Exception as e:
        return None, f"⚠️ Serveur de l'Empire injoignable : {str(e)}"

json_buildings, statut_msg = charger_buildings_api()

if json_buildings is None:
    st.error(statut_msg)
else:
    st.caption(statut_msg)
    
    # --- 💵 ZONE FINANCIÈRE DYNAMIQUE ---
    st.subheader("💰 1. Capacité Financière de la Holding")
    saisie_capital = st.text_input("Saisissez votre budget ou trésorerie disponible (ex: 500M, 10G, 5.5Z) :", value="10G", key="capital_input_5")
    capital_disponible = convertir_saisie_en_nombre(saisie_capital)
    st.caption(f"ℹ️ Capital interprété par la Holding : **{formater_monnaie_empire(capital_disponible)}**")
    st.markdown("---")

    try:
        # L'API sépare les bâtiments selon 3 listes : "buildings_perso", "buildings_entreprise", "buildings_terrain"
        liste_biens = json_buildings.get("buildings_entreprise", [])
        rows = []
        
        for bien in liste_biens:
            desc = bien.get("name", "").strip()
            if "TERRAIN" in desc.upper() or "PARC" in desc.upper(): 
                continue
                
            prix = int(bien.get("value", 0))
            loyer = int(bien.get("rent", 0))
            charges = int(bien.get("charge", 0))
            impots = int(bien.get("tax", 0))
            
            rev_net_mensuel = loyer - charges - impots
            rev_net_annuel = rev_net_mensuel * 12
            renta_nette = (rev_net_annuel / prix * 100) if prix > 0 else 0
            
            if prix > 0 and capital_disponible > 0:
                nb_biens_possibles = capital_disponible // prix
                if nb_biens_possibles > PLAFOND_MAX_BIENS:
                    nb_biens_possibles = PLAFOND_MAX_BIENS
                    statut_limite = "⚠️ Bridé par la place (500M)"
                else:
                    statut_limite = "💵 Limité par votre budget"
                gain_mensuel_total = rev_net_mensuel * nb_biens_possibles
            else:
                nb_biens_possibles = 0
                gain_mensuel_total = 0
                statut_limite = "Budget insuffisant"

            roi_texte = f"{int(prix / rev_net_annuel)} ans" if rev_net_annuel > 0 else "Aucun"

            rows.append({
                "Description": desc,
                "Prix d'Achat": prix,
                "Rendement Net (%)": renta_nette,
                "R.O.I": roi_texte,
                "Quantité Max Achetée": nb_biens_possibles,
                "Facteur Limitant": statut_limite,
                "Gain Mensuel Cumulé RAW": gain_mensuel_total,
                "Gain Mensuel Cumulé": formater_monnaie_empire(gain_mensuel_total),
                "Revenu Net Unique": formater_monnaie_empire(rev_net_mensuel)
            })

        df = pd.DataFrame(rows)
        st.subheader("🔍 Analyse des meilleures opportunités budgétaires")
        df_affichage = df.sort_values(by="Gain Mensuel Cumulé RAW", ascending=False)

        df_visuel = df_affichage.copy()
        df_visuel["Prix d'Achat"] = df_visuel["Prix d'Achat"].apply(formater_monnaie_empire)
        df_visuel["Rendement Net (%)"] = df_visuel["Rendement Net (%)"].apply(lambda x: f"{x:.2f}%")
        df_visuel = df_visuel.drop(columns=["Gain Mensuel Cumulé RAW"])

        st.dataframe(df_visuel, use_container_width=True)

        if not df_affichage.empty and df_affichage.iloc[0]["Gain Mensuel Cumulé RAW"] > 0:
            st.success(f"👑 **Stratégie d'achat recommandée :** Investissez dans **{df_visuel.iloc[0]['Description']}** pour dégager jusqu'à **{df_visuel.iloc[0]['Gain Mensuel Cumulé']} /mois**.")

    except Exception as e:
        st.error(f"⚠️ Erreur lors du calcul de l'analyse locative : {str(e)}")
