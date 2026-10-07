import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre, DICTIONNAIRE_PALIERS

# Configuration de la page
st.set_page_config(page_title="Banque Fédérale - Monde 8", layout="wide")

st.title("🏛️ Système Bancaire Central & Optimiseur — Monde 8")
st.info("🕒 Rappel temporel : **1 jour réel = 1 mois de jeu**. Un cycle complet de livret/épargne (12 mois de jeu) dure **12 jours réels**.")

# =========================================================================
# 📊 ARCHITECTURE DES GRILLES TARIFAIRES OFFICIELLES (ENTIERS TRÈS GRANDS)
# =========================================================================

PLAFOND_LIVRET_I = 6 * DICTIONNAIRE_PALIERS.get("R", 10**27)  # 6 R
PLAFOND_EPARGNE = 4 * DICTIONNAIRE_PALIERS.get("R", 10**27)   # 4 R

# Grille de référence pour l'affichage et la recherche de taux brut
GRILLE_EPARGNE = [
    {"seuil": 0, "taux": 100.0},
    {"seuil": 300_000_010 * 10**18, "taux": 80.0},        # 300_000_010 E
    {"seuil": 600_000_010 * 10**18, "taux": 60.0},        # 600_000_010 E
    {"seuil": 2_000_000_100 * 10**18, "taux": 40.0},      # 2_000_000_100 E
    {"seuil": 5_000_000_100 * 10**18, "taux": 20.0},      # 5_000_000_100 E
    {"seuil": 10_000_001_000 * 10**18, "taux": 10.0},     # 10_000_001_000 E
    {"seuil": 15_000_001_000 * 10**18, "taux": 2.0}       # 15_000_001_000 E
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

saisie_somme = st.text_input("Capital total à placer ou emprunter (Ex: 6R, 4R) :", value="6 R")
capital_brut = convertir_saisie_en_nombre(saisie_somme)

st.caption(f"💰 Volume financier analysé : **{formater_monnaie_empire(capital_brut)} Ø**")
st.markdown("---")

if capital_brut <= 0:
    st.warning("⚠️ Veuillez entrer une somme valide pour analyser la grille des taux.")
else:
    taux_epargne_auto = determiner_taux(capital_brut, GRILLE_EPARGNE)
    taux_emprunt_auto = determiner_taux(capital_brut, GRILLE_EMPRUNTS)

    # --- TABS DES PRODUITS BANCAIRES ---
    tab_opti, tab_compte, tab_livret_i, tab_emprunt = st.tabs([
        "🔥 1. Découpage Optimisé (Cascade)",
        "📈 2. Compte Épargne (Dépôt Unique)", 
        "🔒 3. Livret I (Dépôt Unique)", 
        "🏦 4. Crédits (Emprunts)"
    ])

    # ---------------------------------------------------------------------
    # 🔥 1. MOTEUR DE DÉCOUPAGE EN CASCADE (AVEC COPIER-COLLER DIRECT)
    # ---------------------------------------------------------------------
    with tab_opti:
        st.subheader("⚔️ Plan de Répartition anti-décote de l'Empire")
        st.info("Cette matrice découpe automatiquement vos fonds. Utilisez les boutons de copie à droite pour coller les valeurs brutes directement en jeu.")
        
        capital_restant = int(capital_brut)
        repartition_livrets = []
        total_interets_optimises = 0
        
        # Parcours de chaque palier pour extraire des blocs optimisés
        for palier in seuils_stricts:
            limite_seuil_brute = int(palier["limite"])
            montant_parfait_livret = limite_seuil_brute - 1
            taux_palier = palier["taux"]
            
            # Combien de livrets de cette taille peut-on caler dans notre fortune ?
            nb_livrets = capital_restant // montant_parfait_livret
            
            if nb_livrets > 0:
                for _ in range(nb_livrets):
                    gain_livret = int(montant_parfait_livret * (taux_palier / 100.0))
                    
                    val_e = limite_seuil_brute // 10**18
                    gain_e = gain_livret // 10**18
                    
                    repartition_livrets.append({
                        "Type de Bloc": f"Livret optimisé ({palier['nom']})",
                        "Affichage Empire": f"{val_e:,} E - 1 Ø".replace(",", " "),
                        "Taux Garanti": f"{taux_palier:.1f}%",
                        "Gain au Terme (12 mois)": f"~ {gain_e:,} E".replace(",", " "),
                        "Valeur Brute (À COPIER EN JEU)": str(montant_parfait_livret) # Version texte brute pour le copier-coller
                    })
                    total_interets_optimises += gain_livret
                    capital_restant -= montant_parfait_livret

        # Traitement du reliquat résiduel
        if capital_restant > 0:
            taux_residu = determiner_taux(capital_restant, GRILLE_EPARGNE)
            gain_residu = int(capital_restant * (taux_residu / 100.0))
            
            residu_e = capital_restant / 10**18
            gain_residu_e = gain_residu / 10**18
            
            repartition_livrets.append({
                "Type de Bloc": "Reliquat final de l'enveloppe",
                "Affichage Empire": f"{residu_e:,.2f} E".replace(",", " "),
                "Taux Garanti": f"{taux_residu:.1f}%",
                "Gain au Terme (12 mois)": f"{gain_residu_e:,.2f} E".replace(",", " "),
                "Valeur Brute (À COPIER EN JEU)": str(capital_restant) # Version texte brute pour le copier-coller
            })
            total_interets_optimises += gain_residu

        # Rendu du tableau interactif avec bouton copier-coller intégré natively par Streamlit !
        if repartition_livrets:
            df_opti_visuel = pd.DataFrame(repartition_livrets)
            
            # Utilisation de st.data_editor ou st.dataframe configuré pour afficher le bouton de copie
            st.dataframe(
                df_opti_visuel,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Valeur Brute (À COPIER EN JEU)": st.column_config.TextColumn(
                        "Valeur Brute (À COPIER EN JEU)",
                        help="Passez votre souris sur la cellule et cliquez sur le petit bouton de copie qui apparaît à droite !",
                    )
                }
            )
        else:
            st.info("Aucun livret généré.")

        # Matrice d'impact financier du bas
        interets_gros_bloc = int(capital_brut * (taux_epargne_auto / 100.0))
        argent_sauve = max(0, total_interets_optimises - interets_gros_bloc)

        st.markdown("### 📊 Analyse d'Impact Financier")
        c_op1, c_op2, c_op3 = st.columns(3)
        with c_op1:
            st.metric("🎯 Gain OPTIMISÉ Fractionné", f"{formater_monnaie_empire(total_interets_optimises)} Ø")
        with c_op2:
            st.metric("🛑 Gain BRUT (1 seul dépôt)", f"{formater_monnaie_empire(interets_gros_bloc)} Ø", f"Taux écrasé à {taux_epargne_auto}%", delta_color="inverse")
        with c_op3:
            st.metric("👑 Surplus Net Sauvé", f"{formater_monnaie_empire(argent_sauve)} Ø", "Bénéfice additionnel préservé")

    # ---------------------------------------------------------------------
    # 📈 2. COMPTE ÉPARGNE (DÉPÔT UNIQUE)
    # ---------------------------------------------------------------------
    with tab_compte:
        st.subheader("📦 Configuration du Nouveau Compte Épargne")
        
        choix_duree_jeu = st.selectbox(
            "Sélectionnez la durée de blocage souhaitée :",
            options=[6, 8, 12, 18, 24, 36, 48],
            format_func=lambda x: f"{x} mois (jeu) / {x} jours (réels)",
            index=2
        )
        
        dispo_epargne = max(0, PLAFOND_EPARGNE - capital_brut)
        if capital_brut > PLAFOND_EPARGNE:
            st.error(f"🛑 Plafond de 4 R dépassé ! Limite : {formater_monnaie_empire(PLAFOND_EPARGNE)} Ø.")
        else:
            st.success(f"✅ Capacité de dépôt restante : **{formater_monnaie_empire(dispo_epargne)} Ø** sur {formater_monnaie_empire(PLAFOND_EPARGNE)} Ø.")

        st.write(f"Taux d'intérêt de base (annuel) : **{taux_epargne_auto:.2f}%**")
        
        taux_decimal = taux_epargne_auto / 100.0
        taux_journalier_reel = taux_decimal / 12.0
        
        interets_terme = int(capital_brut * (taux_journalier_reel * choix_duree_jeu))
        capital_final_lineaire = capital_brut + interets_terme
        
        facteur_compose = (1.0 + taux_journalier_reel) ** choix_duree_jeu
        capital_final_compose = int(capital_brut * facteur_compose)
        interets_compose = capital_final_compose - capital_brut

        m1, m2 = st.columns(2)
        with m1: st.metric(label=f"⚡ Intérêts au terme ({choix_duree_jeu} jours réels)", value=f"{formater_monnaie_empire(interets_terme)} Ø")
        with m2: st.metric(label="🔄 Gain si Pivot Quotidien (Intérêts Composés)", value=f"{formater_monnaie_empire(interets_compose)} Ø")

        st.markdown("##### ⚖ Royautés d'Épargne (Cycle choisi)")
        donnees_comp_ce = [
            {"Méthode": "🎯 Mode Classique (Échéance Fixe)", "Bénéfice Net": formater_monnaie_empire(interets_terme), "Solde Final": formater_monnaie_empire(capital_final_lineaire), "Performance": f"+{(interets_terme/capital_brut*100):.1f}%" if capital_brut > 0 else "0%"},
            {"Méthode": "🔄 Mode Pivot Quotidien (Composé)", "Bénéfice Net": formater_monnaie_empire(interets_compose), "Solde Final": formater_monnaie_empire(capital_final_compose), "Performance": f"+{((capital_final_compose/capital_brut - 1)*100):.1f}%" if capital_brut > 0 else "0%"}
        ]
        st.dataframe(pd.DataFrame(donnees_comp_ce), use_container_width=True, hide_index=True)

        st.markdown("##### 📈 Courbe d'évolution du capital sur la période")
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
    with tab_livret_i:
        st.subheader("🏛️ Situation de vos Livrets I")
        
        dispo_livret = max(0, PLAFOND_LIVRET_I - capital_brut)
        if capital_brut > PLAFOND_LIVRET_I:
            st.error(f"🛑 Plafond de 6 R dépassé ! Tout retrait est définitif : le jeu bloquera toute réouverture. Limite : {formater_monnaie_empire(PLAFOND_LIVRET_I)} Ø.")
        else:
            st.success(f"✅ Statut conforme. Capacité restante : **{formater_monnaie_empire(dispo_livret)} Ø** sur {formater_monnaie_empire(PLAFOND_LIVRET_I)} Ø.")
        
        st.write(f"Taux théorique brut (Dépôt unifié) : **{taux_epargne_auto:.2f}%**")
        
        taux_decimal = taux_epargne_auto / 100.0
        taux_journalier_reel = taux_decimal / 12.0
        
        # Courbe lissée du Livret I (Axe X en entiers pour bloquer le bug de tri)
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
        with c1: st.metric(label="💸 Coût Brut du Crédit", value=f"{formater_monnaie_empire(cout_total_credit)} Ø", delta="Intérêts Banques", delta_color="inverse")
        with c2: st.metric(label="🏛️ Somme Totale à Rendre", value=f"{formater_monnaie_empire(remboursement_total)}")
        with c3: st.metric(label="📅 Échéance par Jour Réel", value=f"{formater_monnaie_empire(mensualite_jeu)}")

# =========================================================================
# 🏛 Royautés & Barèmes de Référence du Serveur
# =========================================================================
st.markdown("---")
st.subheader("📜 Grilles de Référence du Serveur")

col_t1, col_t2 = st.columns(2)
with col_t1:
    st.markdown("**Tranches Épargne (Livrets & Comptes)**")
    df_ge = pd.DataFrame([{"Seuil Minimal": formater_monnaie_empire(t["seuil"]) + " Ø", "Taux Accordé": f"{t['taux']:.1f}%"} for t in GRILLE_EPARGNE])
    st.dataframe(df_ge, use_container_width=True, hide_index=True)

with col_t2:
    st.markdown("**Tranches Emprunts (Crédits)**")
    df_gc = pd.DataFrame([{"Seuil Minimal": formater_monnaie_empire(t["seuil"]) + " Ø", "Taux Facturé": f"{t['taux']:.1f}%"} for t in GRILLE_EMPRUNTS])
    st.dataframe(df_gc, use_container_width=True, hide_index=True)
