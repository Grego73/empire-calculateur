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
    # 🔥 1. MOTEUR DE DÉCOUPAGE EN CASCADE UNIVERSEL (CORRIGÉ ET SÉCURISÉ)
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
            
            # 1. Calcul du découpage ligne par ligne
            for palier in seuils_officiels:
                if capital_restant <= 0:
                    break
                    
                taux_palier = palier["taux"]
                seuil_max_strict = int(palier["seuil_max"])
                
                # Formule cumulative : (Seuil Max - 1) - Déjà placé avant
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

            # Si reliquat massif restant
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

            # Affichage du tableau de bord
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
            else:
                st.info("Aucun livret généré.")
            
            # 2. Calcul autonome du Taux Brut sans dépendance extérieure
            # =========================================================================
            # 🧮 MOTEUR DE CAPITALISATION COMPOSÉE SUR LE FRACTIONNEMENT (12 JOURS)
            # =========================================================================
            total_interets_composes_cascade = 0
            
            # Pour chaque bloc optimisé généré dans la liste, on calcule sa version composée
            for bloc in repartition_livrets:
                # On extrait la valeur brute numérique qui a servi au calcul
                # Note : On ignore l'excédent global ou les lignes sans clé brute numérique directe
                if "Valeur Brute (À COPIER EN JEU)" in bloc:
                    valeur_bloc_brute = int(bloc["Valeur Brute (À COPIER EN JEU)"])
                    taux_bloc_decimal = float(bloc["Taux Garanti"].replace("%", "")) / 100.0
                    taux_bloc_journalier = taux_bloc_decimal / 12.0
                    
                    # Formule des intérêts composés appliqués à ce sous-livret sur 12 jours réels
                    facteur_bloc_compose = (1.0 + taux_bloc_journalier) ** 12
                    solde_bloc_final_compose = int(valeur_bloc_brute * facteur_bloc_compose)
                    
                    # Les intérêts nets générés par ce bloc avec le pivot quotidien
                    interets_bloc_composes = solde_bloc_final_compose - valeur_bloc_brute
                    total_interets_composes_cascade += interets_bloc_composes

            # Différence financière absolue entre l'option composée et l'option bloquée linéaire
            surplus_pivot_quotidien = max(0, total_interets_composes_cascade - total_interets_optimises)

            # =========================================================================
            # 📊 AFFICHAGE DE L'ANALYSE COMPARATIVE SÉCURISÉE (BASCULE TOUTES LETTRES)
            # =========================================================================
            st.markdown("### 📊 Analyse d'Impact Financier : Bloqué vs Pivot Quotidien")
            
            # --- BLOC D'AFFICHAGE AVEC SEUIL DE BASCULE STRICT À 10 000 ---
            paliers_ordonnes = [
                ("Q", 10**30), ("R", 10**27), ("Y", 10**24), ("Z", 10**21),
                ("E", 10**18), ("P", 10**15), ("T", 10**12), ("G", 10**9), ("M", 10**6)
            ]
            
            valeur_repere = max(total_interets_composes_cascade, capital_brut)
            lettre_choisie = "Ø"
            diviseur_choisi = 1
            
            # On parcourt du plus grand au plus petit
            for lettre, valeur_palier in paliers_ordonnes:
                if valeur_repere >= valeur_palier:
                    # 🔥 REGLE UNIVERSELLE DE BASCULE À 10 000 :
                    # On ne passe à la lettre supérieure que si on a au moins "10.00" de cette unité.
                    # Sinon (ex: si on a 1.61 Z), on préfère l'écrire dans l'unité du dessous : "1 610 E".
                    valeur_exprimee = float(valeur_repere) / valeur_palier
                    if valeur_exprimee >= 10.0 or lettre == "M":
                        lettre_choisie = lettre
                        diviseur_choisi = valeur_palier
                        break
                    else:
                        # Si on a moins de 10.0 (ex: 1.61), on force le glissement vers le palier inférieur
                        continue

            # Formatage des 3 compteurs sur la même échelle de lettre
            txt_bloque = f"{float(total_interets_optimises) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " ")
            txt_compose = f"{float(total_interets_composes_cascade) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " ")
            txt_surplus_pivot = f"{float(surplus_pivot_quotidien) / diviseur_choisi:,.2f} {lettre_choisie} Ø".replace(",", " ")

            c_op1, c_op2, c_op3 = st.columns(3)
            with c_op1: 
                st.metric(f"🎯 Option Bloquée Classique (12 jours)", txt_bloque)
                st.caption("Fonds intacts jusqu'au terme du livret")
            with c_op2: 
                st.metric(f"🔄 Option Pivot Quotidien (Composé)", txt_compose)
                st.caption("Retrait, récupération et replacement toutes les 24h")
            with c_op3: 
                st.metric("👑 Surplus Généré par le Pivot", txt_surplus_pivot, "Gain net additionnel si tu fais la manipulation")

        with sub_tab_livret:
            generer_cascade_cumulative(capital_brut, PLAFOND_LIVRET_I, "Livrets I")
        with sub_tab_compte:
            generer_cascade_cumulative(capital_brut, PLAFOND_EPARGNE, "Comptes Épargnes")

    # ---------------------------------------------------------------------
    # 📈 2. COMPTE ÉPARGNE (DÉPÔT UNIQUE & SIMULATEUR DE ROULEMENTS À TERME)
    # ---------------------------------------------------------------------
    with tab_compte_brut:
        st.subheader("📦 Configuration du Nouveau Compte Épargne (Dépôt Unique)")
        
        # 1. Sélection de la durée pour le calcul de base
        choix_duree_jeu = st.selectbox(
            "Sélectionnez la durée de blocage souhaitée pour votre simulation de base :", 
            options=[6, 8, 12, 18, 24, 36, 48], 
            format_func=lambda x: f"{x} mois (jeu) / {x} jours (réels)", 
            index=2
        )
        
        # Déduction des limites du plafond de l'épargne
        dispo_epargne = max(0, PLAFOND_EPARGNE - capital_brut)
        if capital_brut > PLAFOND_EPARGNE:
            st.error(f"🛑 Plafond de 4 R dépassé ! Limite : {formater_monnaie_empire(PLAFOND_EPARGNE)} Ø.")
        else:
            st.success(f"✅ Capacité de dépôt restante : **{formater_monnaie_empire(dispo_epargne)} Ø** sur {formater_monnaie_empire(PLAFOND_EPARGNE)} Ø.")

        st.write(f"Taux d'intérêt de base détecté pour votre tranche (annuel) : **{taux_epargne_auto:.2f}%**")
        
        taux_decimal = taux_epargne_auto / 100.0
        taux_journalier = taux_decimal / 12.0  # 1 jour réel = 1 mois de jeu
        
        # Calcul linéaire pour la durée de base sélectionnée
        interets_terme = int(capital_brut * (taux_journalier * choix_duree_jeu))
        capital_final_lineaire = capital_brut + interets_terme

        st.metric(label=f"🏆 Intérêts générés au terme choisi ({choix_duree_jeu} jours réels)", value=f"{formater_monnaie_empire(interets_terme)} Ø")

        # ---------------------------------------------------------------------
        # 📊 ANALYSE COMPARATIVE DES 7 DURÉES DE ROULEMENT SANS FRAIS DE CASSAGE
        # ---------------------------------------------------------------------
        st.markdown("---")
        st.markdown("##### 📈 Comparatif des 7 durées de roulement à terme (Horizon 48 Jours Réels)")
        st.caption("⚠️ Ce graphique simule uniquement des livrets menés jusqu'à leur terme légal pour éviter les frais de cassage anticipé.")

        durées_officielles = [6, 8, 12, 18, 24, 36, 48]
        points_strategies = []

        # Simulation jour par jour sur l'horizon maximal de 48 jours réels
        for j in range(0, 49):
            donnee_jour = {"Jour Réel (Mois Jeu)": j}
            
            # Référence : Blocage unique direct en 1 fois sur 48 mois (Linéaire)
            donnee_jour["Bloqué 48m Direct"] = float(capital_brut + int(capital_brut * (taux_journalier * j)))
            
            # Génération des trajectoires pour TOUTES les durées officielles menées à terme
            for duree in durées_officielles:
                nb_cycles = j // duree
                reste_jours = j % duree
                capital_temporaire = capital_brut
                
                # On applique la capitalisation (réinvestissement) uniquement aux fins de cycles complets
                for _ in range(nb_cycles):
                    capital_temporaire += int(capital_temporaire * (taux_journalier * duree))
                
                # Ajout du prorata linéaire en cours pour le cycle incomplet
                capital_final_roulement = capital_temporaire + int(capital_temporaire * (taux_journalier * reste_jours))
                
                donnee_jour[f"Roulement {duree} mois"] = float(capital_final_roulement)
            
            points_strategies.append(donnee_jour)

        # Affichage du graphique de courbes Streamlit
        df_strategie_graphique = pd.DataFrame(points_strategies).set_index("Jour Réel (Mois Jeu)")
        st.line_chart(df_strategie_graphique, use_container_width=True)
        
        # --- TABLEAU DE SYNTHÈSE ET CLASSEMENT AUTOMATIQUE DES GAINS ---
        st.markdown("##### 🏆 Bilan et classement des gains nets cumulés au Jour 48")
        
        bilan_final = []
        ligne_finale = df_strategie_graphique.iloc[-1]  # Extraction du point exact à J+48
        
        for col_name in df_strategie_graphique.columns:
            val_finale = int(ligne_finale[col_name])
            gain_net = val_finale - capital_brut
            
            bilan_final.append({
                "Stratégie de Placement": col_name,
                "Trésorerie Finale (J+48)": formater_monnaie_empire(val_finale) + " Ø",
                "Bénéfice Net Généré": formater_monnaie_empire(gain_net) + " Ø",
                "_tri_valeur": gain_net  # Clé technique invisible pour le tri numérique précis
            })
            
        # Tri automatique du plus rentable au moins rentable
        df_bilan = pd.DataFrame(bilan_final).sort_values(by="_tri_valeur", ascending=False)
        st.dataframe(df_bilan.drop(columns=["_tri_valeur"]), use_container_width=True, hide_index=True)
        st.caption("💡 **Verdict Comptable** : Le tableau est automatiquement trié du meilleur au moins bon rendement. Tu peux voir d'un coup d'œil si enchaîner les livrets courts est plus rentable sur le Monde 8 que de tout bloquer d'un coup.")

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

