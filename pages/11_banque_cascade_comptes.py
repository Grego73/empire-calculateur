import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre, DICTIONNAIRE_PALIERS

# 🔒 Verrouillage plein écran permanent
st.set_page_config(page_title="Cascade Comptes Épargnes - Monde 8", layout="wide", initial_sidebar_state="expanded")

st.markdown("<style>.block-container { max-width: 100% !important; padding: 2rem !important; }</style>", unsafe_allow_html=True)

st.title("📈 Moteur de Cascade : Les Comptes Épargnes")
st.info("🕒 Échelle : **1 jour de jeu = 1 mois réel**. Un livret annuel à terme prend **12 jours de jeu**.")

PLAFOND_EPARGNE = 4 * DICTIONNAIRE_PALIERS.get("R", 10**27)

seuils_officiels = [
    {"nom": "Palier 1 (Taux 100%)", "seuil_max": 300_000_010 * 10**18, "taux": 100.0},
    {"nom": "Palier 2 (Taux 80%)", "seuil_max": 600_000_010 * 10**18, "taux": 80.0},
    {"nom": "Palier 3 (Taux 60%)", "seuil_max": 2_000_000_100 * 10**18, "taux": 60.0},
    {"nom": "Palier 4 (Taux 40%)", "seuil_max": 5_000_000_100 * 10**18, "taux": 40.0},
    {"nom": "Palier 5 (Taux 20%)", "seuil_max": 10_000_001_000 * 10**18, "taux": 20.0},
    {"nom": "Palier 6 (Taux 10%)", "seuil_max": 15_000_001_000 * 10**18, "taux": 10.0}
]

GRILLE_EPARGNE = [
    {"seuil": 0, "taux": 100.0},
    {"seuil": 300_000_010 * 10**18, "taux": 80.0},
    {"seuil": 600_000_010 * 10**18, "taux": 60.0},
    {"seuil": 2_000_000_100 * 10**18, "taux": 40.0},
    {"seuil": 5_000_000_100 * 10**18, "taux": 20.0},
    {"seuil": 10_000_001_000 * 10**18, "taux": 10.0},
    {"seuil": 15_000_001_000 * 10**18, "taux": 2.0}
]

def determiner_taux(capital, grille):
    taux_trouve = grille[0]["taux"]
    for tranche in grille:
        if capital >= tranche["seuil"]:
            taux_trouve = tranche["taux"]
    return taux_trouve

saisie_somme = st.text_input("Capital global à fragmenter (Max 4 R) :", value="4 R", key="somme_cascade_comptes")
capital_brut = convertir_saisie_en_nombre(saisie_somme)
st.caption(f"💰 Volume financier : **{formater_monnaie_empire(capital_brut)} Ø**")

if capital_brut > 0:
    capital_restant = min(int(capital_brut), int(PLAFOND_EPARGNE))
    if int(capital_brut) > int(PLAFOND_EPARGNE):
        st.error(f"🛑 Enveloppe bridée au plafond maximum légal des comptes : {formater_monnaie_empire(PLAFOND_EPARGNE)} Ø.")
    
    repartition_livrets = []
    total_interets_optimises = 0
    capital_deja_place = 0
    
    for palier in seuils_officiels:
        if capital_restant <= 0:
            break
        montant_parfait = (int(palier["seuil_max"]) - 1) - capital_deja_place
        montant_a_placer = min(capital_restant, montant_parfait)
        
        if montant_a_placer > 0:
            gain_terme = int(montant_a_placer * (palier["taux"] / 100.0))
            gain_journalier = gain_terme // 12
            
            repartition_livrets.append({
                "Type de Bloc": f"Saturateur ({palier['nom']})",
                "Valeur Brute (Lisible)": f"{montant_a_placer:,}".replace(",", " "),
                "Taux Garanti": f"{palier['taux']:.1f}%",
                "Gain / Jour Réel": f"~ {gain_journalier // 10**18:,} E".replace(",", " ") if gain_journalier >= 10**18 else f"{gain_journalier:,} Ø",
                "Gain au Terme (12 mois)": f"~ {gain_terme // 10**18:,} E".replace(",", " ") if gain_terme >= 10**18 else f"{gain_terme:,} Ø",
                "Valeur Brute (À COPIER EN JEU)": str(montant_a_placer)
            })
            total_interets_optimises += gain_terme
            capital_restant -= montant_a_placer
            capital_deja_place += montant_a_placer

    if capital_restant > 0:
        gain_residu = int(capital_restant * 0.02)
        gain_journalier_residu = gain_residu // 12
        repartition_livrets.append({
            "Type de Bloc": "Excédent (Tranche minimale 2.0%)",
            "Valeur Brute (Lisible)": f"{capital_restant:,}".replace(",", " "),
            "Taux Garanti": "2.0%",
            "Gain / Jour Réel": f"{gain_journalier_residu:,} Ø",
            "Gain au Terme (12 mois)": f"{gain_residu:,} Ø",
            "Valeur Brute (À COPIER EN JEU)": str(capital_restant)
        })
        total_interets_optimises += gain_residu

    st.dataframe(pd.DataFrame(repartition_livrets), use_container_width=True, hide_index=True, column_config={"Valeur Brute (À COPIER EN JEU)": st.column_config.TextColumn("Valeur Brute (À COPIER EN JEU)")})

    # 🧮 IMPACT FINANCIER
    capital_base_calcul = min(int(capital_brut), int(PLAFOND_EPARGNE))
    taux_base_brut = determiner_taux(capital_base_calcul, GRILLE_EPARGNE)
    interets_gros_bloc = int(capital_base_calcul * (taux_base_brut / 100.0))
    argent_sauve = max(0, total_interets_optimises - interets_gros_bloc)

    paliers_ordonnes = [("Q", 10**30), ("R", 10**27), ("Y", 10**24), ("Z", 10**21), ("E", 10**18)]
    valeur_repere = max(total_interets_optimises, capital_base_calcul)
    lettre_choisie, diviseur_choisi = "Ø", 1
    for lettre, valeur_palier in paliers_ordonnes:
        if valeur_repere >= valeur_palier:
            if (float(valeur_repere) / valeur_palier) < 10000.0:
                lettre_choisie, diviseur_choisi = lettre, valeur_palier
                break

    txt_optimise = f"{float(total_interets_optimises) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " ")
    txt_brut = f"{float(interets_gros_bloc) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " ")
    txt_sauve = f"{float(argent_sauve) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " ")

    st.markdown("### 📊 Impact Financier (Ajusté)")
    rendement_reel_cascade = (float(total_interets_optimises) / float(capital_base_calcul) * 100) if capital_base_calcul > 0 else 0.0
    rendement_reel_brut = (float(interets_gros_bloc) / float(capital_base_calcul) * 100) if capital_base_calcul > 0 else 0.0
    
    c_op1, c_op2, c_op3 = st.columns(3)
    with c_op1: st.metric(label="🎯 Gain OPTIMISÉ Comptes Épargnes", value=txt_optimise, delta=f"📈 Rendement : {rendement_reel_cascade:.2f}%")
    with c_op2: st.metric(label="🛑 Gain BRUT (1 seul bloc)", value=txt_brut, delta=f"📉 Rendement : {rendement_reel_brut:.2f}%", delta_color="inverse")
    with c_op3: st.metric(label="👑 Surplus Net Sauvé", value=txt_sauve, delta=f"🔥 Gain de Taux : +{rendement_reel_cascade - rendement_reel_brut:.2f}%")

    st.markdown("##### ⚡ Comparatif des gains d'intérêts moyens par jour réel (24h)")
    cj1, cj2, cj3 = st.columns(3)
    with cj1: st.metric("✨ Intérêts / Jour (Cascade)", f"{float(total_interets_optimises // 12) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " "))
    with cj2: st.metric("⏳ Intérêts / Jour (Unique)", f"{float(interets_gros_bloc // 12) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " "))
    with cj3: st.metric("👑 Surplus Moyen / Jour", f"{float((total_interets_optimises - interets_gros_bloc) // 12) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " "))

    st.markdown("##### 💰 Solde Total Cumulé (Capital + Intérêts)")
    ct1, ct2, ct3 = st.columns(3)
    with ct1: st.metric("🧱 Fortune Finale (Cascade)", f"{float(capital_base_calcul + total_interets_optimises) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " "))
    with ct2: st.metric("📦 Fortune Finale (Unique)", f"{float(capital_base_calcul + interets_gros_bloc) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " "))
    with ct3: st.metric("👑 Surplus Net sur la Fortune", txt_sauve)
