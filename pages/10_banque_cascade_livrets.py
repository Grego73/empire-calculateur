import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre, DICTIONNAIRE_PALIERS

# 🔒 Verrouillage plein écran permanent
st.set_page_config(page_title="Cascade Livrets I - Monde 8", layout="wide", initial_sidebar_state="expanded")

st.markdown("<style>.block-container { max-width: 100% !important; padding: 2rem !important; }</style>", unsafe_allow_html=True)

st.title("🔒 Moteur de Cascade : Les Livrets I")
st.info("🕒 Échelle : **1 jour de jeu = 1 mois réel**. Un livret annuel à terme prend **12 jours de jeu**.")

PLAFOND_LIVRET_I = 6 * DICTIONNAIRE_PALIERS.get("R", 10**27)
SEUIL_PALIER_1 = 300_000_010 * 10**18  # La taille maximale d'un livret à 100%

saisie_somme = st.text_input("Capital global à fragmenter (Max 6 R) :", value="6 R", key="somme_cascade_livrets")
capital_brut = convertir_saisie_en_nombre(saisie_somme)
st.caption(f"💰 Volume financier : **{formater_monnaie_empire(capital_brut)} Ø**")

if capital_brut > 0:
    capital_restant = min(int(capital_brut), int(PLAFOND_LIVRET_I))
    if int(capital_brut) > int(PLAFOND_LIVRET_I):
        st.error(f"🛑 Enveloppe bridée au plafond maximum légal des livrets : {formater_monnaie_empire(PLAFOND_LIVRET_I)} Ø.")
    
    repartition_livrets = []
    total_interets_optimises = 0
    
    # 🎯 TA FORMULE EXACTE : On ouvre autant de livrets max à 100% que possible pour saturer les 6 R
    montant_parfait_livret = SEUIL_PALIER_1 - 1
    nb_livrets_pleins = capital_restant // montant_parfait_livret
    
    # 1. Génération des livrets optimisés à taux plein (100%)
    for i in range(1, nb_livrets_pleins + 1):
        gain_terme = montant_parfait_livret  # 100% d'intérêts = le capital double
        gain_journalier = gain_terme // 12
        
        repartition_livrets.append({
            "Type de Bloc": f"Livret Optimisé n°{i} (Palier 1)",
            "Valeur Brute (Lisible)": f"{montant_parfait_livret:,}".replace(",", " "),
            "Taux Garanti": "100.0%",
            "Gain / Jour Réel": f"~ {gain_journalier // 10**18:,} E".replace(",", " ") if gain_journalier >= 10**18 else f"{gain_journalier:,} Ø",
            "Gain au Terme (12 mois)": f"~ {gain_terme // 10**18:,} E".replace(",", " ") if gain_terme >= 10**18 else f"{gain_terme:,} Ø",
            "Valeur Brute (À COPIER EN JEU)": str(montant_parfait_livret)
        })
        total_interets_optimises += gain_terme
        capital_restant -= montant_parfait_livret

    # 2. Placement du reliquat final (toujours à 100% car inférieur au seuil critique)
    if capital_restant > 0:
        gain_terme_residu = capital_restant
        gain_journalier_residu = gain_terme_residu // 12
        
        repartition_livrets.append({
            "Type de Bloc": "Reliquat final de l'enveloppe",
            "Valeur Brute (Lisible)": f"{capital_restant:,}".replace(",", " "),
            "Taux Garanti": "100.0%",
            "Gain / Jour Réel": f"~ {gain_journalier_residu // 10**18:,} E".replace(",", " ") if gain_journalier_residu >= 10**18 else f"{gain_journalier_residu:,} Ø",
            "Gain au Terme (12 mois)": f"~ {gain_terme_residu // 10**18:,} E".replace(",", " ") if gain_terme_residu >= 10**18 else f"{gain_terme_residu:,} Ø",
            "Valeur Brute (À COPIER EN JEU)": str(capital_restant)
        })
        total_interets_optimises += gain_terme_residu

    st.dataframe(pd.DataFrame(repartition_livrets), use_container_width=True, hide_index=True, column_config={"Valeur Brute (À COPIER EN JEU)": st.column_config.TextColumn("Valeur Brute (À COPIER EN JEU)")})

    # 🧮 IMPACT FINANCIER PARFAIT
    capital_base_calcul = min(int(capital_brut), int(PLAFOND_LIVRET_I))
    
    # Mode Unique Brut (Si tu mettais tout d'un coup, le jeu t'écraserait au taux minimal de 2%)
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
    # 📅 PLAN DE TIR JOURNALIER DIRECT ET LINÉAIRE
    # =========================================================================
    st.markdown("---")
    st.subheader("📅 Plan de Tir Journalier : Comparatif des Gains sur 12 Jours")

    suivi_cascade = []
    suivi_unique = []

    for jour in range(1, 13):
        # 1. Cascade 100% Linéaire Parfaite
        solde_dep_cas = capital_base_calcul + (gain_jour_optimise * (jour - 1))
        solde_fin_cas = capital_base_calcul + (gain_jour_optimise * jour)
        suivi_cascade.append({
            "Jour de Jeu (Mois)": f"Mois {jour:02d}",
            "Solde Départ (Ø)": f"{int(solde_dep_cas):,}".replace(",", " "),
            "Intérêts acquis (Ø)": f"+ {int(gain_jour_optimise):,}".replace(",", " "),
            "Solde Cumulé (Ø)": f"{int(solde_fin_cas):,}".replace(",", " ")
        })

        # 2. Unique Direct (Taux écrasé)
        solde_dep_uni = capital_base_calcul + (gain_jour_brut_unique * (jour - 1))
        solde_fin_uni = capital_base_calcul + (gain_jour_brut_unique * jour)
        suivi_unique.append({
            "Jour de Jeu (Mois)": f"Mois {jour:02d}",
            "Solde Départ (Ø)": f"{int(solde_dep_uni):,}".replace(",", " "),
            "Intérêts acquis (Ø)": f"+ {int(gain_jour_brut_unique):,}".replace(",", " "),
            "Solde Cumulé (Ø)": f"{int(solde_fin_uni):,}".replace(",", " ")
        })

    # Lignes de Totaux parfaits en bas des deux grilles empilées
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

    st.markdown("#### **🔒 Méthode 1 : Évolution de la Cascade Fractionnée (100% de Taux Verrouillé)**")
    st.dataframe(pd.DataFrame(suivi_cascade), use_container_width=True, hide_index=True, height=500)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### **🛑 Méthode 2 : Évolution du Dépôt Unique (Taux écrasé à 2% sans Cascade)**")
    st.dataframe(pd.DataFrame(suivi_unique), use_container_width=True, hide_index=True, height=500)
