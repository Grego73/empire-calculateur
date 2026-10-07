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

saisie_somme = st.text_input("Capital global à fragmenter (Max 4 R) :", value="4 R", key="somme_cascade_comptes")
capital_brut = convertir_saisie_en_nombre(saisie_somme)
st.caption(f"💰 Volume financier : **{formater_monnaie_empire(capital_brut)} Ø**")

if capital_brut > 0:
    capital_base_calcul = min(int(capital_brut), int(PLAFOND_EPARGNE))
    if int(capital_brut) > int(PLAFOND_EPARGNE):
        st.error(f"🛑 Enveloppe bridée au plafond maximum légal des comptes : {formater_monnaie_empire(PLAFOND_EPARGNE)} Ø.")
    
    repartition_livrets = []
    total_interets_paliers_de_base = 0
    capital_deja_place = 0
    
    # 🎯 Calcul de la Cascade Cumulative
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
    # 🧮 IMPACT FINANCIER SÉCURISÉ CONTRE LE BLOCAGE DU APPORT (4 R)
    # =========================================================================
    interets_gros_bloc = total_interets_paliers_de_base
    bloque_par_le_plafond = (capital_base_calcul >= PLAFOND_EPARGNE)

    if bloque_par_le_plafond:
        st.error("🚨 **ALERTE SÉCURITÉ COMPTE ÉPARGNE** : Vous avez atteint le plafond absolu de **4 R**. Tout retrait ou clôture anticipée bloquera définitivement vos droits de dépôt ! Le pivot quotidien est IMPOSSIBLE.")
        total_interets_cascade_simulee = total_interets_paliers_de_base
        gain_jour_optimise = total_interets_paliers_de_base // 12
    else:
        gain_jour_fixe_lineaire = interets_gros_bloc // 12
        taux_journalier_moyen_paliers = float(gain_jour_fixe_lineaire) / capital_base_calcul if capital_base_calcul > 0 else 0.0
        
        total_interets_cascade_simulee = 0
        capital_courant_cascade = int(capital_base_calcul)
        for jour in range(1, 13):
            int_j_cas = int(capital_courant_cascade * taux_journalier_moyen_paliers)
            total_interets_cascade_simulee += int_j_cas
            capital_courant_cascade += int_j_cas
        gain_jour_optimise = total_interets_cascade_simulee // 12

    gain_jour_brut_unique = interets_gros_bloc // 12
    argent_sauve = max(0, total_interets_cascade_simulee - interets_gros_bloc)

    # Règle de bascule des lettres (10 à 9999.99)
    paliers_ordonnes = [
        ("Q", 10**30), ("R", 10**27), ("Y", 10**24), ("Z", 10**21),
        ("E", 10**18), ("P", 10**15), ("T", 10**12), ("G", 10**9), ("M", 10**6)
    ]
    valeur_repere = max(total_interets_cascade_simulee, capital_base_calcul)
    lettre_choisie, diviseur_choisi = "Ø", 1
    for lettre, valeur_palier in paliers_ordonnes:
        if valeur_repere >= valeur_palier:
            valeur_exprimee = float(valeur_repere) / valeur_palier
            if valeur_exprimee >= 10.0 or lettre == "M":
                lettre_choisie, diviseur_choisi = lettre, valeur_palier
                break

    txt_optimise = f"{float(total_interets_cascade_simulee) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " ")
    txt_brut = f"{float(interets_gros_bloc) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " ")
    txt_sauve = f"{float(argent_sauve) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " ")

    st.markdown("### 📊 Impact Financier (Ajusté)")
    rendement_reel_cascade = (float(total_interets_cascade_simulee) / float(capital_base_calcul) * 100) if capital_base_calcul > 0 else 0.0
    rendement_reel_brut = (float(interets_gros_bloc) / float(capital_base_calcul) * 100) if capital_base_calcul > 0 else 0.0
    
    c_op1, c_op2, c_op3 = st.columns(3)
    with c_op1: st.metric(label="🎯 Gain OPTIMISÉ (Cascade)", value=txt_optimise, delta=f"📈 Rendement : {rendement_reel_cascade:.2f}%")
    with c_op2: st.metric(label="🛑 Gain BRUT (Unique Bloqué)", value=txt_brut, delta=f"📉 Rendement : {rendement_reel_brut:.2f}%", delta_color="inverse")
    with c_op3: st.metric(label="👑 Surplus Net Sauvé", value=txt_sauve, delta=f"🔥 Écart : +{rendement_reel_cascade - rendement_reel_brut:.2f}%")

    st.markdown("##### ⚡ Comparatif des gains d'intérêts moyens par jour réel (24h)")
    cj1, cj2, cj3 = st.columns(3)
    with cj1: st.metric("✨ Intérêts / Jour (Cascade)", f"{float(gain_jour_optimise) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " "))
    with cj2: st.metric("⏳ Intérêts / Jour (Unique Bloqué)", f"{float(gain_jour_brut_unique) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " "))
    with cj3: st.metric("👑 Surplus Moyen / Jour", f"{float((total_interets_cascade_simulee - interets_gros_bloc) // 12) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " "))

    st.markdown("##### 💰 Solde Total Cumulé (Capital + Intérêts)")
    solde_final_cascade = capital_base_calcul + total_interets_cascade_simulee
    solde_final_brut_unique = capital_base_calcul + interets_gros_bloc

    ct1, ct2, ct3 = st.columns(3)
    with ct1: 
        st.metric(label="🧱 Fortune Finale (Cascade)", value=f"{float(solde_final_cascade) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " "))
        st.caption("Capital + Intérêts découpés")
    with ct2: 
        st.metric(label="📦 Fortune Finale (Unique)", value=f"{float(solde_final_brut_unique) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " "))
        st.caption("Capital + Intérêts unifiés")
    with ct3: 
        st.metric(label="👑 Surplus Net sur la Fortune", value=txt_sauve)
        st.caption("Trésorerie bonus créée")

    # Re-génération des structures de grilles linéaires
    suivi_cascade_formate = []
    suivi_unique_formate = []

    for jour in range(1, 13):
        cas_dep = capital_base_calcul + (gain_jour_optimise * (jour - 1))
        cas_fin = capital_base_calcul + (gain_jour_optimise * jour)
        suivi_cascade_formate.append({
            "Jour de Jeu (Mois)": f"Mois {jour:02d}",
            "Solde Départ (Ø)": f"{float(cas_dep) / diviseur_choisi:,.2f} {lettre_choisie}".replace(",", " "),
            "Intérêts acquis (Ø)": f"+ {float(gain_jour_optimise) / diviseur_choisi:,.2f} {lettre_choisie}".replace(",", " "),
            "Solde Cumulé (Ø)": f"{float(cas_fin) / diviseur_choisi:,.2f} {lettre_choisie}".replace(",", " ")
        })

        uni_dep = capital_base_calcul + (gain_jour_brut_unique * (jour - 1))
        uni_fin = capital_base_calcul + (gain_jour_brut_unique * jour)
        suivi_unique_formate.append({
            "Jour de Jeu (Mois)": f"Mois {jour:02d}",
            "Solde Départ (Ø)": f"{float(uni_dep) / diviseur_choisi:,.2f} {lettre_choisie}".replace(",", " "),
            "Intérêts acquis (Ø)": f"+ {float(gain_jour_brut_unique) / diviseur_choisi:,.2f} {lettre_choisie}".replace(",", " "),
            "Solde Cumulé (Ø)": f"{float(uni_fin) / diviseur_choisi:,.2f} {lettre_choisie}".replace(",", " ")
        })

    # Lignes de Totaux formatées et alignées avec l'Impact Central
    suivi_cascade_formate.append({
        "Jour de Jeu (Mois)": "📊 TOTAL CUMULÉ",
        "Solde Départ (Ø)": f"{float(capital_base_calcul) / diviseur_choisi:,.2f} {lettre_choisie}".replace(",", " "),
        "Intérêts acquis (Ø)": f"∑ + {float(total_interets_cascade_simulee) / diviseur_choisi:,.2f} {lettre_choisie}".replace(",", " "),
        "Solde Cumulé (Ø)": f"{float(capital_base_calcul + total_interets_cascade_simulee) / diviseur_choisi:,.2f} {lettre_choisie}".replace(",", " ")
    })
    suivi_unique_formate.append({
        "Jour de Jeu (Mois)": "📊 TOTAL CUMULÉ",
        "Solde Départ (Ø)": f"{float(capital_base_calcul) / diviseur_choisi:,.2f} {lettre_choisie}".replace(",", " "),
        "Intérêts acquis (Ø)": f"∑ + {float(interets_gros_bloc) / diviseur_choisi:,.2f} {lettre_choisie}".replace(",", " "),
        "Solde Cumulé (Ø)": f"{float(capital_base_calcul + interets_gros_bloc) / diviseur_choisi:,.2f} {lettre_choisie}".replace(",", " ")
    })

    st.markdown("---")
    st.subheader("📅 Plan de Tir Journalier : Comparatif des Gains sur 12 Jours")
    
    st.markdown("#### **🔒 Méthode 1 : Évolution de la Cascade Fractionnée (Statut Bloqué si ≥ 4 R)**")
    st.dataframe(pd.DataFrame(suivi_cascade_formate), use_container_width=True, hide_index=True, height=500)
    
    st.markdown("<br>", unsafe_allow_html=True) # Espace propre entre les deux blocs
    
    st.markdown("#### **🛑 Méthode 2 : Évolution du Dépôt Unique (Bloqué 12 mois avec saturation)**")
    st.dataframe(pd.DataFrame(suivi_unique_formate), use_container_width=True, hide_index=True, height=500)
