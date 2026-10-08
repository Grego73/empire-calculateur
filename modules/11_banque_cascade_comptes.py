import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre, DICTIONNAIRE_PALIERS

# 🔒 Verrouillage plein écran permanent
st.set_page_config(page_title="Cascade Comptes Épargnes - Monde 8", layout="wide", initial_sidebar_state="expanded")
st.markdown("<style>.block-container { max-width: 100% !important; padding: 2rem !important; }</style>", unsafe_allow_html=True)

st.title("📈 Moteur de Cascade : Les Comptes Épargnes")
st.info("🕒 Règle temporelle : **1 mois de jeu = 1 jour réel**. Les intérêts travaillent lors du renouvellement automatique à échéance.")

PLAFOND_EPARGNE = 4 * DICTIONNAIRE_PALIERS.get("R", 10**27)

seuils_officiels = [
    {"nom": "Palier 1 (Taux 100%)", "seuil_max": 300_000_010 * 10**18, "taux": 100.0},
    {"nom": "Palier 2 (Taux 80%)", "seuil_max": 600_000_010 * 10**18, "taux": 80.0},
    {"nom": "Palier 3 (Taux 60%)", "seuil_max": 2_000_000_100 * 10**18, "taux": 60.0},
    {"nom": "Palier 4 (Taux 40%)", "seuil_max": 5_000_000_100 * 10**18, "taux": 40.0},
    {"nom": "Palier 5 (Taux 20%)", "seuil_max": 10_000_001_000 * 10**18, "taux": 20.0},
    {"nom": "Palier 6 (Taux 10%)", "seuil_max": 15_000_001_000 * 10**18, "taux": 10.0}
]

# Zone de configuration des montants et des délais de l'Empire
col_cfg1, col_col_cfg2 = st.columns(2)
with col_cfg1:
    saisie_somme = st.text_input("Capital global à fragmenter (Max 4 R) :", value="4 R", key="somme_cascade_comptes")
    capital_brut = convertir_saisie_en_nombre(saisie_somme)
with col_col_cfg2:
    # 🔥 INTÉGRATION DE TOUS LES DÉLAIS OFFICIELS DU JEU
    choix_delai_roulement = st.selectbox(
        "Sélectionnez le délai de blocage de votre stratégie de roulement :",
        options=[6, 8, 12, 18, 24, 36, 48],
        format_func=lambda x: f"{x} mois de jeu ({x} jours réels)",
        index=0,
        key="delai_epargne_roulement"
    )

st.caption(f"💰 Volume financier : **{formater_monnaie_empire(capital_brut)} Ø**")

if capital_brut > 0:
    capital_base_calcul = min(int(capital_brut), int(PLAFOND_EPARGNE))
    if int(capital_brut) > int(PLAFOND_EPARGNE):
        st.error(f"🛑 Enveloppe bridée au plafond maximum légal des comptes : {formater_monnaie_empire(PLAFOND_EPARGNE)} Ø.")
    
    repartition_livrets = []
    total_interets_paliers_de_base = 0
    capital_deja_place = 0
    
    # Calcul de la saturation des paliers par tranches cumulatives (Règle d'origine)
    for palier in seuils_officiels:
        if capital_base_calcul <= capital_deja_place:
            break
        montant_parfait = (int(palier["seuil_max"]) - 1) - capital_deja_place
        montant_a_placer = min(capital_base_calcul - capital_deja_place, montant_parfait)
        
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
            capital_deja_place += montant_a_placer

    capital_restant_exc = capital_base_calcul - capital_deja_place
    if capital_restant_exc > 0:
        gain_residu = int(capital_restant_exc * 0.02)
        gain_journalier_residu = gain_residu // 12
        repartition_livrets.append({
            "Type de Bloc": "Excédent (Tranche minimale 2.0%)",
            "Valeur Brute (Lisible)": f"{capital_restant_exc:,}".replace(",", " "),
            "Taux Garanti": "2.0%",
            "Gain / Jour Réel": f"{gain_journalier_residu:,} Ø",
            "Gain au Terme (12 mois)": f"{gain_residu:,} Ø",
            "Valeur Brute (À COPIER EN JEU)": str(capital_restant_exc)
        })
        total_interets_paliers_de_base += gain_residu

    st.dataframe(pd.DataFrame(repartition_livrets), use_container_width=True, hide_index=True, column_config={"Valeur Brute (À COPIER EN JEU)": st.column_config.TextColumn("Valeur Brute (À COPIER EN JEU)")})

    # =========================================================================
    # 🧮 SIMULATION DYNAMIQUE ADAPTÉE AU DÉLAI SÉLECTIONNÉ SUR L'HORIZON GLOBAL
    # =========================================================================
    # Horizon fixe d'analyse poussé au maximum de 48 jours réels
    HORIZON_SIMULATION = 48
    
    gain_jour_fixe_lineaire = total_interets_paliers_de_base // 12
    taux_journalier_moyen_paliers = float(gain_jour_fixe_lineaire) / capital_base_calcul if capital_base_calcul > 0 else 0.0

    suivi_cascade_pivot = []
    suivi_unique_bloque = []
    
    # État initial de la Méthode 1 (Roulement glissant à échéance)
    capital_courant_m1 = int(capital_base_calcul)
    base_cycle_courant_m1 = int(capital_base_calcul)
    gain_journalier_courant_m1 = int(gain_jour_fixe_lineaire)
    total_interets_m1_cumules = 0

    for jour in range(1, HORIZON_SIMULATION + 1):
        # --- STRATÉGIE 1 : Capitalisation des intérêts au terme du délai choisi ---
        solde_dep_m1 = capital_courant_m1
        int_acquis_ce_jour_m1 = gain_journalier_courant_m1
        solde_fin_m1 = solde_dep_m1 + int_acquis_ce_jour_m1
        total_interets_m1_cumules += int_acquis_ce_jour_m1
        
        # Si on atteint un multiple exact du délai choisi (Ex: Jour 6, 12, 18 ou 8, 16, 24...)
        if jour % choix_delai_roulement == 0:
            # L'argent est disponible : on valide et on fusionne la cagnotte avec le capital
            capital_courant_m1 = solde_fin_m1
            base_cycle_courant_m1 = solde_fin_m1
            # Recalcul du nouveau rendement quotidien sur la base augmentée de l'Empire
            gain_journalier_courant_m1 = int(capital_courant_m1 * taux_journalier_moyen_paliers)
        else:
            capital_courant_m1 = solde_fin_m1

        suivi_cascade_pivot.append({
            "Jour de Jeu (Mois)": f"Mois {jour:02d}",
            "Solde Départ": solde_dep_m1,
            "Intérêts acquis": int_acquis_ce_jour_m1,
            "Solde Cumulé": solde_fin_m1
        })

        # --- STRATÉGIE 2 : Dépôt Unique bloqué passif linéaire sur toute la durée ---
        solde_dep_m2 = capital_base_calcul + (gain_jour_fixe_lineaire * (jour - 1))
        solde_fin_m2 = capital_base_calcul + (gain_jour_fixe_lineaire * jour)
        
        suivi_unique_bloque.append({
            "Jour de Jeu (Mois)": f"Mois {jour:02d}",
            "Solde Départ": solde_dep_m2,
            "Intérêts acquis": gain_jour_fixe_lineaire,
            "Solde Cumulé": solde_fin_m2
        })

    # =========================================================================
    # 📊 IMPACT FINANCIER & RÈGLE DE BASCULE EN MILLIERS (10 À 9999.99)
    # =========================================================================
    interets_total_m2_lineaire = gain_jour_fixe_lineaire * HORIZON_SIMULATION
    argent_sauve = max(0, total_interets_m1_cumules - interets_total_m2_lineaire)

    paliers_ordonnes = [
        ("Q", 10**30), ("R", 10**27), ("Y", 10**24), ("Z", 10**21),
        ("E", 10**18), ("P", 10**15), ("T", 10**12), ("G", 10**9), ("M", 10**6)
    ]
    valeur_repere = max(total_interets_m1_cumules, capital_base_calcul)
    lettre_choisie, diviseur_choisi = "Ø", 1
    
    for lettre, valeur_palier in paliers_ordonnes:
        if valeur_repere >= valeur_palier:
            valeur_exprimee = float(valeur_repere) / valeur_palier
            if valeur_exprimee >= 10.0 or lettre == "M":
                lettre_choisie, diviseur_choisi = lettre, valeur_palier
                break

    txt_optimise = f"{float(total_interets_m1_cumules) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " ")
    txt_brut = f"{float(interets_total_m2_lineaire) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " ")
    txt_sauve = f"{float(argent_sauve) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " ")

    st.markdown("### 📊 Impact Financier Global (Projection sur 48 Mois)")
    rendement_m1 = (float(total_interets_m1_cumules) / float(capital_base_calcul) * 100) if capital_base_calcul > 0 else 0.0
    rendement_m2 = (float(interets_total_m2_lineaire) / float(capital_base_calcul) * 100) if capital_base_calcul > 0 else 0.0
    
    c_op1, c_op2, c_op3 = st.columns(3)
    with c_op1: st.metric(label=f"🎯 Méthode 1 : Roulement cumulé ({choix_delai_roulement}m)", value=txt_optimise, delta=f"📈 Rendement : {rendement_m1:.2f}%")
    with c_op2: st.metric(label="🛑 Méthode 2 : Unique Bloqué passif", value=txt_brut, delta=f"📉 Rendement : {rendement_m2:.2f}%", delta_color="inverse")
    with c_op3: st.metric(label="👑 Surplus Net créé par le Réinvestissement", value=txt_sauve, delta=f"🔥 Écart de rendement : +{rendement_m1 - rendement_m2:.2f}%")

    st.markdown("##### ⚡ Comparatif des gains d'intérêts moyens par mois (jour réel)")
    cj1, cj2, cj3 = st.columns(3)
    with cj1: st.metric("✨ Intérêts / Mois moyen (Méthode 1)", f"{float(total_interets_m1_cumules // HORIZON_SIMULATION) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " "))
    with cj2: st.metric("⏳ Intérêts / Mois moyen (Méthode 2)", f"{float(gain_jour_fixe_lineaire) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " "))
    with cj3: st.metric("👑 Surplus Moyen / Mois", f"{float(argent_sauve // HORIZON_SIMULATION) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " "))

    st.markdown("##### 💰 Solde Total Cumulé au terme de la projection (Capital + Intérêts)")
    solde_final_m1 = capital_base_calcul + total_interets_m1_cumules
    solde_final_m2 = capital_base_calcul + interets_total_m2_lineaire

    ct1, ct2, ct3 = st.columns(3)
    with ct1: 
        st.metric(
            label="🧱 Fortune Finale (Méthode 1)", 
            value=f"{float(solde_final_m1) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " ")
        )
        st.caption(f"Capital + Intérêts réinvestis tous les {choix_delai_roulement} jours")
    with ct2: 
        st.metric(
            label="📦 Fortune Finale (Méthode 2)", 
            value=f"{float(solde_final_m2) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " ")
        )
        st.caption("Capital + Intérêts bloqués passifs sans roulement")
    with ct3: 
        st.metric(
            label="👑 Surplus Net sur la Fortune", 
            value=txt_sauve
        )
        st.caption("Trésorerie nette bonus créée")

    # Formatage final complet des tableaux en milliers de 10.00 à 9 999.99
    suivi_cascade_formate = []
    suivi_unique_formate = []

    for r in suivi_cascade_pivot:
        suivi_cascade_formate.append({
            "Mois de Jeu (Jour Réel)": r["Jour de Jeu (Mois)"],
            "Solde Départ (Ø)": f"{float(r['Solde Départ']) / diviseur_choisi:,.2f} {lettre_choisie}".replace(",", " "),
            "Intérêts acquis (Ø)": f"+ {float(r['Intérêts acquis']) / diviseur_choisi:,.2f} {lettre_choisie}".replace(",", " "),
            "Solde Cumulé (Ø)": f"{float(r['Solde Cumulé']) / diviseur_choisi:,.2f} {lettre_choisie}".replace(",", " ")
        })

    for r in suivi_unique_bloque:
        suivi_unique_formate.append({
            "Mois de Jeu (Jour Réel)": r["Jour de Jeu (Mois)"],
            "Solde Départ (Ø)": f"{float(r['Solde Départ']) / diviseur_choisi:,.2f} {lettre_choisie}".replace(",", " "),
            "Intérêts acquis (Ø)": f"+ {float(r['Intérêts acquis']) / diviseur_choisi:,.2f} {lettre_choisie}".replace(",", " "),
            "Solde Cumulé (Ø)": f"{float(r['Solde Cumulé']) / diviseur_choisi:,.2f} {lettre_choisie}".replace(",", " ")
        })

    # Ajout des lignes de Totaux formatées en fin de tableaux
    suivi_cascade_formate.append({
        "Mois de Jeu (Jour Réel)": "📊 TOTAL CUMULÉ",
        "Solde Départ (Ø)": f"{float(capital_base_calcul) / diviseur_choisi:,.2f} {lettre_choisie}".replace(",", " "),
        "Intérêts acquis (Ø)": f"∑ + {float(total_interets_m1_cumules) / diviseur_choisi:,.2f} {lettre_choisie}".replace(",", " "),
        "Solde Cumulé (Ø)": f"{float(capital_base_calcul + total_interets_m1_cumules) / diviseur_choisi:,.2f} {lettre_choisie}".replace(",", " ")
    })
    suivi_unique_formate.append({
        "Mois de Jeu (Jour Réel)": "📊 TOTAL CUMULÉ",
        "Solde Départ (Ø)": f"{float(capital_base_calcul) / diviseur_choisi:,.2f} {lettre_choisie}".replace(",", " "),
        "Intérêts acquis (Ø)": f"∑ + {float(interets_total_m2_lineaire) / diviseur_choisi:,.2f} {lettre_choisie}".replace(",", " "),
        "Solde Cumulé (Ø)": f"{float(capital_base_calcul + interets_total_m2_lineaire) / diviseur_choisi:,.2f} {lettre_choisie}".replace(",", " ")
    })

    st.markdown("---")
    st.subheader(f"📅 Plan de Tir Comptable (Horizon 48 Mois — Échéance de roulement : {choix_delai_roulement}m)")
    
    st.markdown(f"#### **🔒 Méthode 1 : Évolution du Roulement à Échéance Fixe de {choix_delai_roulement} Jours**")
    st.dataframe(pd.DataFrame(suivi_cascade_formate), use_container_width=True, hide_index=True, height=500)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### **🛑 Méthode 2 : Évolution du Dépôt Unique (Bloqué Passif Linéaire)**")
    st.dataframe(pd.DataFrame(suivi_unique_formate), use_container_width=True, hide_index=True, height=500)
