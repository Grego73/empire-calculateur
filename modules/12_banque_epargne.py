import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre, DICTIONNAIRE_PALIERS

st.set_page_config(page_title="Simulateur d'Épargne - Monde 8", layout="wide", initial_sidebar_state="expanded")
st.markdown("<style>.block-container { max-width: 100% !important; padding: 2rem !important; }</style>", unsafe_allow_html=True)

st.title("📈 Simulateur d'Épargne Progressive & Roulements")
st.info("🕒 Règle : **1 mois réel = 1 jour de jeu** (Vitesse accélérée pour vos versements mensuels).")

PLAFOND_EPARGNE = 4 * DICTIONNAIRE_PALIERS.get("R", 10**27)

saisie_somme = st.text_input("Apport initial (Dépôt unique) :", value="1.74 Y", key="somme_unique")
capital_brut = convertir_saisie_en_nombre(saisie_somme)

col1, col2 = st.columns(2)
with col1:
    choix_duree = st.selectbox("Durée théorique du livret de base :", options=[6, 8, 12, 18, 24, 36, 48], index=2, key="dur_ce")
with col2:
    saisie_inj = st.text_input("Montant à verser en plus à chaque nouveau jour de jeu :", value="0 Ø", key="inj_ce")
    injection_quotidienne = convertir_saisie_en_nombre(saisie_inj)

if capital_brut > 0:
    taux_auto = 100.0 if capital_brut < 300_000_010 * 10**18 else 40.0 # Approximation tranche
    taux_par_jour_jeu = (taux_auto / 100.0) / 12.0

    # Simulation linéaire de base (Conforme Section 6.5)
    int_base = 0
    cap_base = int(capital_brut)
    for _ in range(1, choix_duree + 1):
        int_base += int(cap_base * taux_par_jour_jeu)
        cap_base += int(injection_quotidienne)
    st.metric(label=f"🏆 Intérêts générés au terme choisi ({choix_duree} jours de jeu)", value=f"{formater_monnaie_empire(int_base)} Ø")

    # Matrice comparative des 7 durées à terme
    st.markdown("---")
    st.markdown("##### 📈 Courbes de richesse cumulée (Horizon : Horizon maximal de 48 jours de jeu)")
    
    durées_officielles = [6, 8, 12, 18, 24, 36, 48]
    points_strategies = []
    historique_capital = {d: int(capital_brut) for d in durées_officielles}
    base_cycle_capital = {d: int(capital_brut) for d in durées_officielles}

    for j in range(0, 49):
        donnee_jour = {"Jour de Jeu": j}
        for d in durées_officielles:
            if j == 0:
                donnee_jour[f"Roulement {d} mois"] = float(capital_brut)
            else:
                cap_courant = historique_capital[d] + int(injection_quotidienne)
                if j % d == 0:
                    cap_courant += int(base_cycle_capital[d] * (taux_par_jour_jeu * d))
                    base_cycle_capital[d] = cap_courant
                historique_capital[d] = cap_courant
                donnee_jour[f"Roulement {d} mois"] = float(cap_courant)
        points_strategies.append(donnee_jour)

    st.line_chart(pd.DataFrame(points_strategies).set_index("Jour de Jeu"), use_container_width=True)

    # Tableau final de bilan trié
    st.markdown("##### 🏆 Bilan et classement des gains nets cumulés au Jour 48 de jeu")
    df_res = pd.DataFrame(points_strategies).set_index("Jour de Jeu")
    ligne_f = df_res.iloc[-1]
    total_apport_perso = int(capital_brut) + (int(injection_quotidienne) * 48)
    
    bilan = []
    for col in df_res.columns:
        val_f = int(ligne_f[col])
        gain_net = val_f - total_apport_perso
        bilan.append({"Stratégie": col, "Trésorerie Finale (J+48)": formater_monnaie_empire(val_f) + " Ø", "Bénéfice Net Réel": formater_monnaie_empire(gain_net) + " Ø", "_tri": gain_net})
    
    st.dataframe(pd.DataFrame(bilan).sort_values(by="_tri", ascending=False).drop(columns=["_tri"]), use_container_width=True, hide_index=True)
    st.caption(f"💡 Total des fonds injectés de votre poche sur 48 jours de jeu : **{formater_monnaie_empire(total_apport_perso)} Ø**.")
