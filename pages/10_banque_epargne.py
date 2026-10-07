import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre, DICTIONNAIRE_PALIERS

# Configuration de la page
st.set_page_config(page_title="Banque Fédérale - Monde 8", layout="wide")

st.title("🏛️ Système Bancaire Central & Cascade Cumulative — Monde 8")
st.info("🕒 Rappel temporel : **1 jour réel = 1 mois de jeu**. Un cycle complet d'épargne (12 mois de jeu) dure **12 jours réels**.")

# =========================================================================
# 📊 ARCHITECTURE DES GRILLES TARIFAIRES OFFICIELLES (ENTIERS TRÈS GRANDS)
# =========================================================================

PLAFOND_LIVRET_I = 6 * DICTIONNAIRE_PALIERS.get("R", 10**27)  # 6 R
PLAFOND_EPARGNE = 4 * DICTIONNAIRE_PALIERS.get("R", 10**27)   # 4 R

# Liste des seuils bruts officiels du jeu pour le calcul cumulatif
seuils_officiels = [
    {"nom": "Palier 1 (Taux 100%)", "seuil_max": 300_000_010 * 10**18, "taux": 100.0},
    {"nom": "Palier 2 (Taux 80%)", "seuil_max": 600_000_010 * 10**18, "taux": 80.0},
    {"nom": "Palier 3 (Taux 60%)", "seuil_max": 2_000_000_100 * 10**18, "taux": 60.0},
    {"nom": "Palier 4 (Taux 40%)", "seuil_max": 5_000_000_100 * 10**18, "taux": 40.0},
    {"nom": "Palier 5 (Taux 20%)", "seuil_max": 10_000_001_000 * 10**18, "taux": 20.0},
    {"nom": "Palier 6 (Taux 10%)", "seuil_max": 15_000_001_000 * 10**18, "taux": 10.0}
]

# Grille brute pour la recherche du taux global unifié
GRILLE_EPARGNE = [
    {"seuil": 0, "taux": 100.0},
    {"seuil": 300_000_010 * 10**18, "taux": 80.0},
    {"seuil": 600_000_010 * 10**18, "taux": 60.0},
    {"seuil": 2_000_000_100 * 10**18, "taux": 40.0},
    {"seuil": 5_000_000_100 * 10**18, "taux": 20.0},
    {"seuil": 10_000_001_000 * 10**18, "taux": 10.0},
    {"seuil": 15_000_001_000 * 10**18, "taux": 2.0}
]

GRILLE_EMPRUNTS = [
    {"seuil": 0, "taux": 2.0},
    {"seuil": 5_000_000_100 * 10**18, "taux": 10.0},
    {"seuil": 6_000_000_100 * 10**18, "taux": 20.0},
    {"seuil": 10_000_001_000 * 10**18, "taux": 35.0},
    {"seuil": 15_000_001_000 * 10**18, "taux": 60.0},
    {"seuil": 20_000_001_000 * 10**18, "taux": 80.0},
    {"seuil": 30_000_001_000 * 10**18, "taux": 100.0}
]

def determiner_taux(capital, grille):
    taux_trouve = grille[0]["taux"]
    for tranche in grille:
        if capital >= tranche["seuil"]:
            taux_trouve = tranche["taux"]
    return taux_trouve

# =========================================================================
# 📥 MODULE DE CONFIGURATION DU CAPITAL
# =========================================================================

saisie_somme = st.text_input("Capital total à placer ou emprunter (Ex: 6R, 4R, 1.74Y) :", value="6 R")
capital_brut = convertir_saisie_en_nombre(saisie_somme)

st.caption(f"💰 Volume financier analysé : **{formater_monnaie_empire(capital_brut)} Ø**")
st.markdown("---")

if capital_brut <= 0:
    st.warning("⚠️ Veuillez entrer une somme valide pour analyser la grille des taux.")
else:
    taux_epargne_auto = determiner_taux(capital_brut, GRILLE_EPARGNE)
    taux_emprunt_auto = determiner_taux(capital_brut, GRILLE_EMPRUNTS)

    # --- TABS PRINCIPAUX DES PRODUITS BANCAIRES ---
    tab_opti, tab_compte_brut, tab_livret_brut, tab_emprunt = st.tabs([
        "🔥 1. Découpages Optimisés (Cascade)",
        "📈 2. Compte Épargne (Dépôt Unique)", 
        "🔒 3. Livret I (Dépôt Unique)", 
        "🏦 4. Crédits (Emprunts)"
    ])

    # ---------------------------------------------------------------------
    # 🔥 1. MOTEUR DE DÉCOUPAGE EN CASCADE (SOUS-ONGLETS PRODUITS)
    # ---------------------------------------------------------------------
    with tab_opti:
        sub_tab_livret, sub_tab_compte = st.tabs(["🔒 Cascade Livrets I (Max 6 R)", "📈 Cascade Comptes Épargnes (Max 4 R)"])

        def generer_cascade_cumulative(capital_enveloppe, plafond_produit, label_produit):
            capital_restant = min(int(capital_enveloppe), int(plafond_produit))
            
            if int(capital_enveloppe) > int(plafond_produit):
                st.error(f"🛑 L'enveloppe saisie dépasse le plafond autorisé pour ce produit ({formater_monnaie_empire(plafond_produit)} Ø). Le calcul a été bridé au maximum légal.")
            
            repartition_livrets = []
            total_interets_optimises = 0
            capital_deja_place = 0
            
            for palier in seuils_officiels:
                if capital_restant <= 0:
                    break
                    
                taux_palier = palier["taux"]
                seuil_max_strict = int(palier["seuil_max"])
                
                # Formule cumulative Grego73 : (Seuil Max - 1) - Déjà placé avant
                montant_parfait_livret = (seuil_max_strict - 1) - capital_deja_place
                montant_a_placer = min(capital_restant, montant_parfait_livret)
                
                if montant_a_placer > 0:
                    gain_terme = int(montant_a_placer * (taux_palier / 100.0))
                    gain_journalier = gain_terme // 12
                    
                    valeur_brute_lisible = f"{montant_a_placer:,}".replace(",", " ")
                    gain_terme_visuel = f"~ {gain_terme // 10**18:,} E".replace(",", " ") if gain_terme >= 10**18 else f"{gain_terme:,} Ø"
                    gain_jour_visuel = f"~ {gain_journalier // 10**18:,} E".replace(",", " ") if gain_journalier >= 10**18 else f"{gain_journalier:,} Ø"
                    
                    repartition_livrets.append({
                        "Type de Bloc": f"Saturateur ({palier['nom']})",
                        "Valeur Brute (Lisible)": valeur_brute_lisible,
                        "Taux Garanti": f"{taux_palier:.1f}%",
                        "Gain / Jour Réel": gain_jour_visuel,
                        "Gain au Terme (12 mois)": gain_terme_visuel,
                        "Valeur Brute (À COPIER EN JEU)": str(montant_a_placer)
                    })
                    
                    total_interets_optimises += gain_terme
                    capital_restant -= montant_a_placer
                    capital_deja_place += montant_a_placer

            if capital_restant > 0:
                taux_minimum_banque = 2.0
                gain_terme_residu = int(capital_restant * (taux_minimum_banque / 100.0))
                gain_journalier_residu = gain_terme_residu // 12
                
                valeur_residu_lisible = f"{capital_restant:,}".replace(",", " ")
                gain_terme_visuel = f"~ {gain_terme_residu // 10**18:,} E".replace(",", " ") if gain_terme_residu >= 10**18 else f"{gain_terme_residu:,} Ø"
                gain_jour_visuel = f"~ {gain_journalier_residu // 10**18:,} E".replace(",", " ") if gain_journalier_residu >= 10**18 else f"{gain_journalier_residu:,} Ø"
                
                repartition_livrets.append({
                    "Type de Bloc": "Excédent global (Tranche minimale 2.0%)",
                    "Valeur Brute (Lisible)": valeur_residu_lisible,
                    "Taux Garanti": f"{taux_minimum_banque:.1f}%",
                    "Gain / Jour Réel": gain_jour_visuel,
                    "Gain au Terme (12 mois)": gain_terme_visuel,
                    "Valeur Brute (À COPIER EN JEU)": str(capital_restant)
                })
                total_interets_optimises += gain_terme_residu

            if repartition_livrets:
                df_opti_visuel = pd.DataFrame(repartition_livrets)
                st.dataframe(
                    df_opti_visuel,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Valeur Brute (À COPIER EN JEU)": st.column_config.TextColumn(
                            "Valeur Brute (À COPIER EN JEU)",
                            help="Passez votre souris sur la cellule et cliquez sur le bouton de copie à droite !",
                        )
                    }
                )
            
            # --- HARMONISATION DES UNITÉS AVEC SEUIL DE BASCULE À 10 000 ---
            interets_gros_bloc = int(min(capital_brut, plafond_produit) * (taux_epargne_auto / 100.0))
            argent_sauve = max(0, total_interets_optimises - interets_gros_bloc)

            st.markdown("### 📊 Analyse d'Impact Financier (Unités Alignées)")
            
            unite_y = 10**24  # Yotta
            unite_r = 10**27  # Ron
            
            # Formule : On calcule la valeur en Yottas (Y)
            valeur_en_y = float(total_interets_optimises) / unite_y
            
            # 🔥 RÈGLE DE BASCULE : Si la valeur est inférieure à 10 000 Y, on force l'affichage en Y
            if valeur_en_y < 10000.0:
                txt_optimise = f"{valeur_en_y:,.2f} Y Ø".replace(",", " ")
                txt_brut = f"{(float(interets_gros_bloc) / unite_y):,.2f} Y Ø".replace(",", " ")
                txt_sauve = f"{(float(argent_sauve) / unite_y):,.2f} Y Ø".replace(",", " ")
            else:
                # Si on dépasse ou atteint 10 000 Y, on passe proprement à la lettre supérieure (R)
                txt_optimise = f"{(float(total_interets_optimises) / unite_r):,.2f} R Ø".replace(",", " ")
                txt_brut = f"{(float(interets_gros_bloc) / unite_r):,.2f} R Ø".replace(",", " ")
                txt_sauve = f"{(float(argent_sauve) / unite_r):,.2f} R Ø".replace(",", " ")

            c_op1, c_op2, c_op3 = st.columns(3)
            with c_op1: 
                st.metric(f"🎯 Gain OPTIMISÉ {label_produit}", txt_optimise)
            with c_op2: 
                st.metric("🛑 Gain BRUT (1 seul dépôt)", txt_brut, f"Taux écrasé à {taux_epargne_auto}%", delta_color="inverse")
            with c_op3: 
                st.metric("👑 Surplus Net Sauvé", txt_sauve, "Bénéfice additionnel préservé")
        st.metric("👑 Surplus Net Sauvé", txt_sauve, "Bénéfice additionnel préservé")

        with sub_tab_livret:
            generer_cascade_cumulative(capital_brut, PLAFOND_LIVRET_I, "Livrets I")
        with sub_tab_compte:
            generer_cascade_cumulative(capital_brut, PLAFOND_EPARGNE, "Comptes Épargnes")

    # ---------------------------------------------------------------------
    # 📈 2. COMPTE ÉPARGNE (DÉPÔT UNIQUE)
    # ---------------------------------------------------------------------
    with tab_compte_brut:
        st.subheader("📦 Configuration du Nouveau Compte Épargne (Unique)")
        choix_duree_jeu = st.selectbox("Sélectionnez la durée de blocage souhaitée :", options=[6, 8, 12, 18, 24, 36, 48], format_func=lambda x: f"{x} mois (jeu) / {x} jours (réels)", index=2)
        
        dispo_epargne = max(0, PLAFOND_EPARGNE - capital_brut)
        if capital_brut > PLAFOND_EPARGNE:
            st.error(f"🛑 Plafond de 4 R dépassé ! Limite : {formater_monnaie_empire(PLAFOND_EPARGNE)} Ø.")
        else:
            st.success(f"✅ Capacité de dépôt restante : **{formater_monnaie_empire(dispo_epargne)} Ø** sur {formater_monnaie_empire(PLAFOND_EPARGNE)} Ø.")

        taux_decimal = taux_epargne_auto / 100.0
        taux_journalier_reel = taux_decimal / 12.0
        
        interets_terme = int(capital_brut * (taux_journalier_reel * choix_duree_jeu))
        capital_final_lineaire = capital_brut + interets_terme
        facteur_compose = (1.0 + taux_journalier_reel) ** choix_duree_jeu
        capital_final_compose = int(capital_brut * facteur_compose)
        interets_compose = capital_final_compose - capital_brut

        m1, m2 = st.columns(2)
        with m1: st.metric(label=f"⚡ Intérêts au terme ({choix_duree_jeu} jours réels)", value=f"{formater_monnaie_empire(interets_terme)} Ø")
        with m2: st.metric(label="🔄 Gain si Pivot Quotidien", value=f"{formater_monnaie_empire(interets_compose)} Ø")

        points_c = []
        for j in range(0, choix_duree_jeu + 1):
            points_c.append({
                "Jour Réel (Mois Jeu)": j,
                "Option Classique (Bloqué)": float(capital_brut + int(capital_brut * (taux_journalier_reel * j))),
                "Option Pivot Quotidien": float(int(capital_brut * ((1.0 + taux_journalier_reel) ** j)))
            })
        st.line_chart(pd.DataFrame(points_c).set_index("Jour Réel (Mois Jeu)"), use_container_width=True)

    # ---------------------------------------------------------------------
    # 🔒 3. LIVRET I (DÉPÔT UNIQUE)
    # ---------------------------------------------------------------------
    with tab_livret_brut:
        st.subheader("🏛️ Situation de vos Livrets I (Unique)")
        dispo_livret = max(0, PLAFOND_LIVRET_I - capital_brut)
        
        if capital_brut > PLAFOND_LIVRET_I:
            st.error(f"🛑 Plafond de 6 R dépassé ! Tout retrait est définitif : le jeu bloquera toute réouverture. Limite : {formater_monnaie_empire(PLAFOND_LIVRET_I)} Ø.")
        else:
            st.success(f"✅ Statut conforme. Capacité restante : **{formater_monnaie_empire(dispo_livret)} Ø** sur {formater_monnaie_empire(PLAFOND_LIVRET_I)} Ø.")
        
        st.write(f"Taux théorique brut (Dépôt unifié) : **{taux_epargne_auto:.2f}%**")
        
        taux_decimal = taux_epargne_auto / 100.0
        taux_journalier_reel = taux_decimal / 12.0
        
        points_l = []
        for j in range(0, 13):
            points_l.append({
                "Jour Réel (Mois Jeu)": j,
                "Option Bloquée": float(capital_brut + int(capital_brut * (taux_journalier_reel * j))),
                "Option Pivot Quotidien": float(int(capital_brut * ((1.0 + taux_journalier_reel) ** j)))
            })
        st.line_chart(pd.DataFrame(points_l).set_index("Jour Réel (Mois Jeu)"), use_container_width=True)

    # ---------------------------------------------------------------------
    # 🏦 4. CRÉDITS (EMPRUNTS)
    # ---------------------------------------------------------------------
    with tab_emprunt:
        st.subheader("📉 Coût de l'Endettement & Emprunts")
        st.write(f"Taux d'intérêt de l'emprunt pour cette tranche : **{taux_emprunt_auto:.2f}%**")
        
        cout_total_credit = int(capital_brut * (taux_emprunt_auto / 100.0))
        remboursement_total = capital_brut + cout_total_credit
        mensualite_jeu = int(remboursement_total / 12)

        c1, c2, c3 = st.columns(3)
        with c1: st.metric(label="💸 Coût Crédit", value=f"{formater_monnaie_empire(cout_total_credit)} Ø", delta="Intérêts", delta_color="inverse")
        with c2: st.metric(label="🏛️ À Rendre", value=f"{formater_monnaie_empire(remboursement_total)}")
        with c3: st.metric(label="📅 Échéance / Jour Réel", value=f"{formater_monnaie_empire(mensualite_jeu)}")

# =========================================================================
# 🏛 GRILLES DE RÉFÉRENCE NATIVES DU SERVEUR
# =========================================================================
st.markdown("---")
st.subheader("📜 Grilles de Référence du Serveur")

col_t1, col_t2 = st.columns(2)
with col_t1:
    st.markdown("**Tranches Épargne (Livrets & Comptes)**")
    st.dataframe(pd.DataFrame([{"Seuil Minimal": formater_monnaie_empire(t["seuil"]) + " Ø", "Taux Accordé": f"{t['taux']:.1f}%"} for t in GRILLE_EPARGNE]), use_container_width=True, hide_index=True)
with col_t2:
    st.markdown("**Tranches Emprunts (Crédits)**")
    st.dataframe(pd.DataFrame([{"Seuil Minimal": formater_monnaie_empire(t["seuil"]) + " Ø", "Taux Facturé": f"{t['taux']:.1f}%"} for t in GRILLE_EMPRUNTS]), use_container_width=True, hide_index=True)

