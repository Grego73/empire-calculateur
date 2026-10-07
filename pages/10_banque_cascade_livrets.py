import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre, DICTIONNAIRE_PALIERS

# 🔒 Verrouillage plein écran permanent
st.set_page_config(page_title="Cascade Livrets I - Monde 8", layout="wide", initial_sidebar_state="expanded")

st.markdown("<style>.block-container { max-width: 100% !important; padding: 2rem !important; }</style>", unsafe_allow_html=True)

st.title("🔒 Moteur de Cascade : Les Livrets I")
st.info("🕒 Échelle : **1 jour de jeu = 1 mois réel**. Un livret annuel à terme prend **12 jours de jeu**.")

PLAFOND_LIVRET_I = 6 * DICTIONNAIRE_PALIERS.get("R", 10**27)

seuils_officiels = [
    {"nom": "Palier 1 (Taux 100%)", "seuil_max": 300_000_010 * 10**18, "taux": 100.0},
    {"nom": "Palier 2 (Taux 80%)", "seuil_max": 600_000_010 * 10**18, "taux": 80.0},
    {"nom": "Palier 3 (Taux 60%)", "seuil_max": 2_000_000_100 * 10**18, "taux": 60.0},
    {"nom": "Palier 4 (Taux 40%)", "seuil_max": 5_000_000_100 * 10**18, "taux": 40.0},
    {"nom": "Palier 5 (Taux 20%)", "seuil_max": 10_000_001_000 * 10**18, "taux": 20.0},
    {"nom": "Palier 6 (Taux 10%)", "seuil_max": 15_000_001_000 * 10**18, "taux": 10.0}
]

saisie_somme = st.text_input("Capital global à fragmenter (Max 6 R) :", value="6 R", key="somme_cascade_livrets")
capital_brut = convertir_saisie_en_nombre(saisie_somme)
st.caption(f"💰 Volume financier : **{formater_monnaie_empire(capital_brut)} Ø**")

if capital_brut > 0:
    capital_restant = min(int(capital_brut), int(PLAFOND_LIVRET_I))
    if int(capital_brut) > int(PLAFOND_LIVRET_I):
        st.error(f"🛑 Enveloppe bridée au plafond maximum légal des livrets : {formater_monnaie_empire(PLAFOND_LIVRET_I)} Ø.")
    
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

    # 🧮 IMPACT FINANCIER ÉPURÉ
    capital_base_calcul = min(int(capital_brut), int(PLAFOND_LIVRET_I))
    
    # Pour le Livret I brut unique sans cascade, la banque applique le taux minimum de la grille (2.0%) à cause de la masse totale
    taux_base_brut = 2.0  
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
    with c_op1: st.metric(label="🎯 Gain OPTIMISÉ Livrets I", value=txt_optimise, delta=f"📈 Rendement : {rendement_reel_cascade:.2f}%")
    with c_op2: st.metric(label="🛑 Gain BRUT (1 seul bloc)", value=txt_brut, delta=f"📉 Rendement : {rendement_reel_brut:.2f}%", delta_color="inverse")
    with c_op3: st.metric(label="👑 Surplus Net Sauvé", value=txt_sauve, delta=f"🔥 Gain de Taux : +{rendement_reel_cascade - rendement_reel_brut:.2f}%")

    st.markdown("##### ⚡ Comparatif des gains d'intérêts moyens par jour réel (24h)")
    gain_jour_optimise = total_interets_optimises // 12
    gain_jour_brut_unique = interets_gros_bloc // 12
    surplus_jour = gain_jour_optimise - gain_jour_brut_unique

    cj1, cj2, cj3 = st.columns(3)
    with cj1: st.metric("✨ Intérêts / Jour (Cascade)", f"{float(gain_jour_optimise) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " "))
    with cj2: st.metric("⏳ Intérêts / Jour (Unique)", f"{float(gain_jour_brut_unique) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " "))
    with cj3: st.metric("👑 Surplus Moyen / Jour", f"{float(surplus_jour) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " "))

    st.markdown("##### 💰 Solde Total Cumulé (Capital + Intérêts)")
    solde_final_cascade = capital_base_calcul + total_interets_optimises
    solde_final_brut_unique = capital_base_calcul + interets_gros_bloc
    
    ct1, ct2, ct3 = st.columns(3)
    with ct1: st.metric("🧱 Fortune Finale (Cascade)", f"{float(solde_final_cascade) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " "))
    with ct2: st.metric("📦 Fortune Finale (Unique)", f"{float(solde_final_brut_unique) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " "))
    with ct3: st.metric("👑 Surplus Net sur la Fortune", txt_sauve)

    # =========================================================================
    # 📅 PLAN DE TIR JOURNALIER : LES 2 TABLEAUX EN PROGRESSION LINÉAIRE STRICTE
    # =========================================================================
    st.markdown("---")
    st.subheader("📅 Plan de Tir Journalier : Comparatif des Gains sur 12 Jours")
    st.caption("Ces tableaux simulent l'évolution linéaire et réelle de votre trésorerie, mois par mois (jour après jour), jusqu'au terme des livrets.")

    # Calcul des gains quotidiens fixes et stricts (Aucun pivot composé)
    gain_jour_fixe_cascade = total_interets_optimises // 12
    gain_jour_fixe_unique = interets_gros_bloc // 12

    suivi_cascade = []
    suivi_unique = []

    # Simulation de l'accumulation passive jour après jour
    for jour in range(1, 13):
        # 1. Tableau Cascade Fractionnée (Linéaire)
        solde_dep_cas = capital_base_calcul + (gain_jour_fixe_cascade * (jour - 1))
        solde_fin_cas = capital_base_calcul + (gain_jour_fixe_cascade * jour)
        
        suivi_cascade.append({
            "Jour de Jeu (Mois)": f"Mois {jour:02d}",
            "Solde Départ (Ø)": f"{int(solde_dep_cas):,}".replace(",", " "),
            "Intérêts acquis (Ø)": f"+ {int(gain_jour_fixe_cascade):,}".replace(",", " "),
            "Solde Cumulé (Ø)": f"{int(solde_fin_cas):,}".replace(",", " ")
        })

        # 2. Tableau Placement Direct Unique (Linéaire)
        solde_dep_uni = capital_base_calcul + (gain_jour_fixe_unique * (jour - 1))
        solde_fin_uni = capital_base_calcul + (gain_jour_fixe_unique * jour)
        
        suivi_unique.append({
            "Jour de Jeu (Mois)": f"Mois {jour:02d}",
            "Solde Départ (Ø)": f"{int(solde_dep_uni):,}".replace(",", " "),
            "Intérêts acquis (Ø)": f"+ {int(gain_jour_fixe_unique):,}".replace(",", " "),
            "Solde Cumulé (Ø)": f"{int(solde_fin_uni):,}".replace(",", " ")
        })

    # Ajout de la ligne de Total strict en fin de tableau
    suivi_cascade.append({
        "Jour de Jeu (Mois)": "📊 TOTAL CUMULÉ",
        "Solde Départ (Ø)": f"{int(capital_base_calcul):,}".replace(",", " "),
        "Intérêts acquis (Ø)": f"∑ + {int(total_interets_optimises):,}".replace(",", " "),
        "Solde Cumulé (Ø)": f"{int(capital_base_calcul + total_interets_optimises):,}".replace(",", " ")
    })

    suivi_unique.append({
        "Jour de Jeu (Mois)": "📊 TOTAL CUMULÉ",
        "Solde Départ (Ø)": f"{int(capital_base_calcul):,}".replace(",", " "),
        "Intérêts acquis (Ø)": f"∑ + {int(interets_gros_bloc):,}".replace(",", " "),
        "Solde Cumulé (Ø)": f"{int(capital_base_calcul + interets_gros_bloc):,}".replace(",", " ")
    })

    # Affichage empilé verticalement avec hauteur fixe pour dérouler les 13 lignes d'un coup
    st.markdown("#### **🔒 Méthode 1 : Évolution de la Cascade Fractionnée (Livrets Bloqués à Terme)**")
    st.dataframe(pd.DataFrame(suivi_cascade), use_container_width=True, hide_index=True, height=500)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("#### **🛑 Méthode 2 : Évolution du Dépôt Unique (Un seul gros bloc Bloqué à Terme)**")
    st.dataframe(pd.DataFrame(suivi_unique), use_container_width=True, hide_index=True, height=500)
