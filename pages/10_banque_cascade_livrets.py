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
    total_interets_paliers_de_base = 0
    capital_deja_place = 0
    
    # 🎯 Calcul de la Cascade Cumulative
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
            total_interets_paliers_de_base += gain_terme
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
        total_interets_paliers_de_base += gain_residu

    st.dataframe(pd.DataFrame(repartition_livrets), use_container_width=True, hide_index=True, column_config={"Valeur Brute (À COPIER EN JEU)": st.column_config.TextColumn("Valeur Brute (À COPIER EN JEU)")})

    # =========================================================================
    # 🧮 CALCUL DES DEUX STRATÉGIES (MÉTHODE 1 PIVOTÉE VS MÉTHODE 2 BLOQUÉE)
    # =========================================================================
    capital_base_calcul = min(int(capital_brut), int(PLAFOND_LIVRET_I))
    gain_jour_fixe_lineaire = total_interets_paliers_de_base // 12
    taux_journalier_moyen_paliers = float(gain_jour_fixe_lineaire) / capital_base_calcul if capital_base_calcul > 0 else 0.0

    suivi_cascade_pivot = []
    suivi_unique_bloque = []
    
    capital_courant_cascade = int(capital_base_calcul)
    total_interets_cascade_compose = 0

    for jour in range(1, 13):
        # 1. Méthode 1 : Cascade Pivotée Quotidiennement (Composée)
        cap_dep_cas = capital_courant_cascade
        int_j_cas = int(cap_dep_cas * taux_journalier_moyen_paliers)
        cap_fin_cas = cap_dep_cas + int_j_cas
        total_interets_cascade_compose += int_j_cas
        
        suivi_cascade_pivot.append({
            "Jour de Jeu (Mois)": f"Mois {jour:02d}",
            "Solde Départ (Ø)": f"{cap_dep_cas:,}".replace(",", " "),
            "Intérêts acquis (Ø)": f"+ {int_j_cas:,}".replace(",", " "),
            "Solde Cumulé (Ø)": f"{cap_fin_cas:,}".replace(",", " ")
        })
        capital_courant_cascade = cap_fin_cas

        # 2. Méthode 2 : Unique Bloqué (Linéaire passive sur les mêmes tranches)
        solde_dep_uni = capital_base_calcul + (gain_jour_fixe_lineaire * (jour - 1))
        solde_fin_uni = capital_base_calcul + (gain_jour_fixe_lineaire * jour)
        
        suivi_unique_bloque.append({
            "Jour de Jeu (Mois)": f"Mois {jour:02d}",
            "Solde Départ (Ø)": f"{int(solde_dep_uni):,}".replace(",", " "),
            "Intérêts acquis (Ø)": f"+ {int(gain_jour_fixe_lineaire):,}".replace(",", " "),
            "Solde Cumulé (Ø)": f"{int(solde_fin_uni):,}".replace(",", " ")
        })

    # Lignes de Totaux
    suivi_cascade_pivot.append({
        "Jour de Jeu (Mois)": "📊 TOTAL CUMULÉ",
        "Solde Départ (Ø)": f"{int(capital_base_calcul):,}".replace(",", " "),
        "Intérêts acquis (Ø)": f"∑ + {int(total_interets_cascade_compose):,}".replace(",", " "),
        "Solde Cumulé (Ø)": f"{int(capital_base_calcul + total_interets_cascade_compose):,}".replace(",", " ")
    })
    suivi_unique_bloque.append({
        "Jour de Jeu (Mois)": "📊 TOTAL CUMULÉ",
        "Solde Départ (Ø)": f"{int(capital_base_calcul):,}".replace(",", " "),
        "Intérêts acquis (Ø)": f"∑ + {int(total_interets_paliers_de_base):,}".replace(",", " "),
        "Solde Cumulé (Ø)": f"{int(capital_base_calcul + total_interets_paliers_de_base):,}".replace(",", " ")
    })

    # =========================================================================
    # 📊 BLOC COMPTABLE DE L'IMPACT FINANCIER (RÈGLE BASCULE DE 10 À 9999)
    # =========================================================================
    argent_sauve = max(0, total_interets_cascade_compose - total_interets_paliers_de_base)

    paliers_ordonnes = [
        ("Q", 10**30), ("R", 10**27), ("Y", 10**24), ("Z", 10**21),
        ("E", 10**18), ("P", 10**15), ("T", 10**12), ("G", 10**9), ("M", 10**6)
    ]
    
    valeur_repere = max(total_interets_cascade_compose, capital_base_calcul)
    lettre_choisie = "Ø"
    diviseur_choisi = 1
    
    # 🔥 APPLICATION DE TA RÈGLE : On parcourt pour trouver la lettre où la valeur est d'au moins 10.00
    for lettre, valeur_palier in paliers_ordonnes:
        if valeur_repere >= valeur_palier:
            valeur_exprimee = float(valeur_repere) / valeur_palier
            if valeur_exprimee >= 10.0 or lettre == "M":
                lettre_choisie = lettre
                diviseur_choisi = valeur_palier
                break
            else:
                continue

    txt_optimise = f"{float(total_interets_cascade_compose) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " ")
    txt_brut = f"{float(total_interets_paliers_de_base) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " ")
    txt_sauve = f"{float(argent_sauve) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " ")

    st.markdown("### 📊 Impact Financier (Ajusté)")
    rendement_reel_cascade = (float(total_interets_cascade_compose) / float(capital_base_calcul) * 100) if capital_base_calcul > 0 else 0.0
    rendement_reel_brut = (float(total_interets_paliers_de_base) / float(capital_base_calcul) * 100) if capital_base_calcul > 0 else 0.0
    
    c_op1, c_op2, c_op3 = st.columns(3)
    with c_op1: st.metric(label="🎯 Gain OPTIMISÉ (Méthode 1 : Cascade Pivotée)", value=txt_optimise, delta=f"📈 Rendement : {rendement_reel_cascade:.2f}%")
    with c_op2: st.metric(label="🛑 Gain BRUT (Méthode 2 : Unique Bloqué)", value=txt_brut, delta=f"📉 Rendement : {rendement_reel_brut:.2f}%", delta_color="inverse")
    with c_op3: st.metric(label="👑 Surplus Net Sauvé par le Pivot", value=txt_sauve, delta=f"🔥 Écart Composé : +{rendement_reel_cascade - rendimiento_reel_brut if 'rendimiento_reel_brut' in locals() else rendement_reel_cascade - rendement_reel_brut:.2f}%")

    st.markdown("##### ⚡ Comparatif des gains d'intérêts moyens par jour réel (24h)")
    cj1, cj2, cj3 = st.columns(3)
    with cj1: st.metric("✨ Intérêts / Jour (Cascade Pivotée)", f"{float(total_interets_cascade_compose // 12) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " "))
    with cj2: st.metric("⏳ Intérêts / Jour (Unique Bloqué)", f"{float(gain_jour_fixe_lineaire) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " "))
    with cj3: st.metric("👑 Surplus Moyen / Jour", f"{float((total_interets_cascade_compose - total_interets_paliers_de_base) // 12) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " "))

    st.markdown("##### 💰 Solde Total Cumulé (Capital + Intérêts)")
    ct1, ct2, ct3 = st.columns(3)
    with ct1: st.metric("🧱 Fortune Finale (Cascade)", f"{float(solde_final_cascade) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " ")), st.caption("Capital + Intérêts découpés")
    with ct2: st.metric("📦 Fortune Finale (Unique)", f"{float(solde_final_brut_unique) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " ")), st.caption("Capital + Intérêts unifiés")
    with ct3: st.metric("👑 Surplus Net sur la Fortune", txt_sauve)

    # =========================================================================
    # 📅 PLAN DE TIR JOURNALIER LINEAIRE CORRECT ET NETTOYÉ (EMPILÉ SANS SCROLL)
    # =========================================================================
    st.markdown("---")
    st.subheader("📅 Plan de Tir Journalier : Comparatif des Gains sur 12 Jours")

    suivi_cascade = []
    suivi_unique = []

    for jour in range(1, 13):
        # 1. Cascade Fractionnée (2.78 R au total)
        solde_dep_cas = capital_base_calcul + (gain_jour_optimise * (jour - 1))
        solde_fin_cas = capital_base_calcul + (gain_jour_optimise * jour)
        suivi_cascade.append({
            "Jour de Jeu (Mois)": f"Mois {jour:02d}",
            "Solde Départ (Ø)": f"{int(solde_dep_cas):,}".replace(",", " "),
            "Intérêts acquis (Ø)": f"+ {int(gain_jour_optimise):,}".replace(",", " "),
            "Solde Cumulé (Ø)": f"{int(solde_fin_cas):,}".replace(",", " ")
        })

        # 2. Unique Direct (0.12 R au total à cause des 2%)
        solde_dep_uni = capital_base_calcul + (gain_jour_brut_unique * (jour - 1))
        solde_fin_uni = capital_base_calcul + (gain_jour_brut_unique * jour)
        suivi_unique.append({
            "Jour de Jeu (Mois)": f"Mois {jour:02d}",
            "Solde Départ (Ø)": f"{int(solde_dep_uni):,}".replace(",", " "),
            "Intérêts acquis (Ø)": f"+ {int(gain_jour_brut_unique):,}".replace(",", " "),
            "Solde Cumulé (Ø)": f"{int(solde_fin_uni):,}".replace(",", " ")
        })

    # Lignes de Totaux strictes et alignées avec l'Impact
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

    st.markdown("#### **🔒 Méthode 1 : Évolution de la Cascade Fractionnée (Gain Protégé par Tranches)**")
    st.dataframe(pd.DataFrame(suivi_cascade), use_container_width=True, hide_index=True, height=500)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### **🛑 Méthode 2 : Évolution du Dépôt Unique (Gain Écrasé par le Barème)**")
    st.dataframe(pd.DataFrame(suivi_unique), use_container_width=True, hide_index=True, height=500)

