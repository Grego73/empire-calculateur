import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre, DICTIONNAIRE_PALIERS

# Verrouillage plein écran
st.set_page_config(page_title="Cascade Optimisée - Monde 8", layout="wide", initial_sidebar_state="expanded")

st.markdown("<style>.block-container { max-width: 100% !important; padding: 2rem !important; }</style>", unsafe_allow_html=True)

st.title("⚔️ Optimiseur de Rendement : Cascade Cumulative")
st.info("🕒 Échelle : **1 jour de jeu = 1 mois réel**. Un livret annuel à terme prend **12 jours de jeu**.")

PLAFOND_LIVRET_I = 6 * DICTIONNAIRE_PALIERS.get("R", 10**27)
PLAFOND_EPARGNE = 4 * DICTIONNAIRE_PALIERS.get("R", 10**27)

seuils_officiels = [
    {"nom": "Palier 1 (Taux 100%)", "seuil_max": 300_000_010 * 10**18, "taux": 100.0},
    {"nom": "Palier 2 (Taux 80%)", "seuil_max": 600_000_010 * 10**18, "taux": 80.0},
    {"nom": "Palier 3 (Taux 60%)", "seuil_max": 2_000_000_100 * 10**18, "taux": 60.0},
    {"nom": "Palier 4 (Taux 40%)", "seuil_max": 5_000_000_100 * 10**18, "taux": 40.0},
    {"nom": "Palier 5 (Taux 20%)", "seuil_max": 10_000_001_000 * 10**18, "taux": 20.0},
    {"nom": "Palier 6 (Taux 10%)", "seuil_max": 15_000_001_000 * 10**18, "taux": 10.0}
]

# Grille de référence pour le taux global unifié
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

saisie_somme = st.text_input("Capital global à fragmenter (Ex: 6R, 4R, 600Y) :", value="6 R", key="somme_cascade")
capital_brut = convertir_saisie_en_nombre(saisie_somme)
st.caption(f"💰 Volume financier : **{formater_monnaie_empire(capital_brut)} Ø**")

if capital_brut > 0:
    sub_tab_livret, sub_tab_compte = st.tabs(["🔒 Cascade Livrets I (Max 6 R)", "📈 Cascade Comptes Épargnes (Max 4 R)"])

    def generer_rendu_cascade(capital_enveloppe, plafond_produit, label_produit):
        capital_restant = min(int(capital_enveloppe), int(plafond_produit))
        if int(capital_enveloppe) > int(plafond_produit):
            st.error(f"🛑 Enveloppe bridée au plafond maximum légal de {formater_monnaie_empire(plafond_produit)} Ø.")
        
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
                repartition_livrets.append({
                    "Type de Bloc": f"Saturateur ({palier['nom']})",
                    "Valeur Brute (Lisible)": f"{montant_a_placer:,}".replace(",", " "),
                    "Taux Garanti": f"{palier['taux']:.1f}%",
                    "Gain / Jour Réel": f"~ {gain_terme // 12 // 10**18:,} E".replace(",", " ") if gain_terme >= 10**19 else f"{gain_terme // 12:,} Ø",
                    "Gain au Terme (12m)": f"~ {gain_terme // 10**18:,} E".replace(",", " ") if gain_terme >= 10**18 else f"{gain_terme:,} Ø",
                    "Valeur Brute (À COPIER EN JEU)": str(montant_a_placer)
                })
                total_interets_optimises += gain_terme
                capital_restant -= montant_a_placer
                capital_deja_place += montant_a_placer

        if capital_restant > 0:
            gain_residu = int(capital_restant * 0.02)
            repartition_livrets.append({
                "Type de Bloc": "Excédent (Tranche minimale 2.0%)",
                "Valeur Brute (Lisible)": f"{capital_restant:,}".replace(",", " "),
                "Taux Garanti": "2.0%",
                "Gain / Jour Réel": f"{gain_residu // 12:,} Ø",
                "Gain au Terme (12m)": f"{gain_residu:,} Ø",
                "Valeur Brute (À COPIER EN JEU)": str(capital_restant)
            })
            total_interets_optimises += gain_residu

        st.dataframe(
            pd.DataFrame(repartition_livrets), 
            use_container_width=True, 
            hide_index=True, 
            column_config={
                "Valeur Brute (À COPIER EN JEU)": st.column_config.TextColumn(
                    "Valeur Brute (À COPIER EN JEU)",
                    help="Passez la souris et cliquez sur copier !"
                )
            }
        )

        # 🧮 CALCUL ANALYSE D'IMPACT (BRUT VS COMPOSÉ ET CASCADE)
        taux_base_brut = determiner_taux(min(capital_brut, plafond_produit), GRILLE_EPARGNE)
        interets_gros_bloc = int(min(capital_brut, plafond_produit) * (taux_base_brut / 100.0))
        argent_sauve = max(0, total_interets_optimises - interets_gros_bloc)

        # Règle universelle de bascule à 10 000 pour toutes les lettres
        paliers_ordonnes = [
            ("Q", 10**30), ("R", 10**27), ("Y", 10**24), ("Z", 10**21),
            ("E", 10**18), ("P", 10**15), ("T", 10**12), ("G", 10**9), ("M", 10**6)
        ]
        
        valeur_repere = max(total_interets_optimises, capital_brut)
        lettre_choisie = "Ø"
        diviseur_choisi = 1
        
        for lettre, valeur_palier in paliers_ordonnes:
            if valeur_repere >= valeur_palier:
                if (float(valeur_repere) / valeur_palier) < 10000.0:
                    lettre_choisie = lettre
                    diviseur_choisi = valeur_palier
                    break
                else:
                    continue

        txt_optimise = f"{float(total_interets_optimises) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " ")
        txt_brut = f"{float(interets_gros_bloc) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " ")
        txt_sauve = f"{float(argent_sauve) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " ")

        st.markdown("### 📊 Impact Financier (Ajusté)")
        # --- CALCUL DES TAUX DE RENDEMENT RÉELS GLOBAUX ---
        rendement_reel_cascade = (float(total_interets_optimises) / float(capital_brut) * 100) if capital_brut > 0 else 0.0
        rendement_reel_brut = (float(interets_gros_bloc) / float(capital_brut) * 100) if capital_brut > 0 else 0.0
        surplus_rendement = rendement_reel_cascade - rendement_reel_brut

        st.markdown("### 📊 Impact Financier (Ajusté)")
        c_op1, c_op2, c_op3 = st.columns(3)
        with c_op1: 
            st.metric(
                label=f"🎯 Gain OPTIMISÉ {label_produit}", 
                value=txt_optimise, 
                delta=f"📈 Rendement : {rendement_reel_cascade:.2f}%"
            )
        with c_op2: 
            st.metric(
                label="🛑 Gain BRUT (1 dépôt unique / 12m)", 
                value=txt_brut, 
                delta=f"📉 Rendement : {rendement_reel_brut:.2f}%", 
                delta_color="inverse"
            )
        with c_op3: 
            st.metric(
                label="👑 Surplus Net Sauvé", 
                value=txt_sauve, 
                delta=f"🔥 Gain de Taux : +{surplus_rendement:.2f}%"
            )


        # --- 🔥 NOUVEAU BLOC : COMPARAISON DES GAINS MOYENS PAR JOUR RÉEL ---
        st.markdown("##### ⚡ Comparatif des gains d'intérêts moyens par jour réel (24h)")
        
        # Calcul des gains journaliers bruts
        gain_jour_optimise = total_interets_optimises // 12
        gain_jour_brut_unique = interets_gros_bloc // 12
        surplus_jour = gain_jour_optimise - gain_jour_brut_unique
        
        # Formatage avec la même lettre (règle des 10 000)
        txt_j_opti = f"{float(gain_jour_optimise) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " ")
        txt_j_brut = f"{float(gain_jour_brut_unique) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " ")
        txt_j_surplus = f"{float(surplus_jour) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " ")
        
        cj1, cj2, cj3 = st.columns(3)
        with cj1:
            st.metric("✨ Intérêts / Jour (Cascade)", txt_j_opti)
            st.caption("Gain moyen toutes les 24h avec fractionnement")
        with cj2:
            st.metric("⏳ Intérêts / Jour (Unique)", txt_j_brut)
            st.caption("Gain moyen toutes les 24h sans fractionnement")
        with cj3:
            st.metric("👑 Surplus Moyen / Jour", txt_j_surplus, "Gagné en plus chaque jour")


        # Plan de Tir Journalier (Suivi sur 12 jours)
        st.markdown("---")
        st.subheader("📅 Plan de Tir Journalier : Évolution du Pivot sur 12 Jours")
        suivi_jours = []
        cap_sim = int(min(capital_enveloppe, plafond_produit))
        tx_j_moyen = float(total_interets_optimises // 12) / cap_sim if cap_sim > 0 else 0.0

        for jour in range(1, 13):
            cap_dep = cap_sim
            int_j = int(cap_dep * tx_j_moyen)
            cap_fin = cap_dep + int_j
            suivi_jours.append({
                "Jour Réel": f"Jour {jour}",
                "Capital Initial (Ø)": f"{cap_dep:,}".replace(",", " "),
                "Intérêts Gagnés (24h) (Ø)": f"+ {int_j:,}".replace(",", " "),
                "Capital Final (Reinvesti) (Ø)": f"{cap_fin:,}".replace(",", " ")
            })
            cap_sim = cap_fin
        st.dataframe(pd.DataFrame(suivi_jours), use_container_width=True, hide_index=True)

    with sub_tab_livret: 
        generer_rendu_cascade(capital_brut, PLAFOND_LIVRET_I, "Livrets I")
    with sub_tab_compte: 
        generer_rendu_cascade(capital_brut, PLAFOND_EPARGNE, "Comptes Épargnes")
