import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre, DICTIONNAIRE_PALIERS

# Configuration de la page
st.set_page_config(page_title="Banque Fédérale - Monde 8", layout="wide")

st.title("🏛️ Système Bancaire Central — Monde 8")
st.info("🕒 Rappel temporel : **1 jour réel = 1 mois de jeu**. Un cycle complet de livret/épargne (12 mois de jeu) dure **12 jours réels**.")

# =========================================================================
# 📊 ARCHITECTURE DES GRILLES TARIFAIRES OFFICIELLES (ENTIERS TRÈS GRANDS)
# =========================================================================

PLAFOND_LIVRET_I = 6 * DICTIONNAIRE_PALIERS.get("R", 10**27)  # 6 R
PLAFOND_EPARGNE = 4 * DICTIONNAIRE_PALIERS.get("R", 10**27)   # 4 R

# Grille de l'épargne (Livrets I & Comptes Épargnes)
GRILLE_EPARGNE = [
    {"seuil": 0, "taux": 100.0},
    {"seuil": 300_000_010 * 10**18, "taux": 80.0},        # 300_000_010 E
    {"seuil": 600_000_010 * 10**18, "taux": 60.0},        # 600_000_010 E
    {"seuil": 2_000_000_100 * 10**18, "taux": 40.0},      # 2_000_000_100 E
    {"seuil": 5_000_000_100 * 10**18, "taux": 20.0},      # 5_000_000_100 E
    {"seuil": 10_000_001_000 * 10**18, "taux": 10.0},     # 10_000_001_000 E
    {"seuil": 15_000_001_000 * 10**18, "taux": 2.0}       # 15_000_001_000 E
]

# Grille des emprunts
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

saisie_somme = st.text_input("Capital total déposé ou emprunté à la banque (Ex: 1.74Y, 16.61Y, 500G, 4R) :", value="1.74 Y")
capital_brut = convertir_saisie_en_nombre(saisie_somme)

st.caption(f"💰 Volume financier analysé : **{formater_monnaie_empire(capital_brut)} Ø**")

st.markdown("---")

if capital_brut <= 0:
    st.warning("⚠️ Veuillez entrer une somme valide pour analyser la grille des taux.")
else:
    taux_epargne_auto = determiner_taux(capital_brut, GRILLE_EPARGNE)
    taux_emprunt_auto = determiner_taux(capital_brut, GRILLE_EMPRUNTS)

    # --- AFFICHAGE DES RÉSULTATS PAR PRODUIT ---
    tab_compte, tab_livret_i, tab_emprunt = st.tabs([
        "📈 1. Compte Épargne", 
        "🔒 2. Livret I (Plafond 6 R)", 
        "🏦 3. Crédits (Emprunts)"
    ])

    # ---------------------------------------------------------------------
    # 📈 ONGLET COMPTE ÉPARGNE
    # ---------------------------------------------------------------------
    with tab_compte:
        st.subheader("📦 Configuration du Nouveau Compte Épargne")
        
        # Sélecteur de durée conforme à l'interface du jeu
        choix_duree_jeu = st.selectbox(
            "Sélectionnez la durée de blocage souhaitée :",
            options=[6, 8, 12, 18, 24, 36, 48],
            format_func=lambda x: f"{x} mois (jeu) / {x} jours (réels)",
            index=2  # Par défaut sur 12 mois
        )
        
        dispo_epargne = max(0, PLAFOND_EPARGNE - capital_brut)
        if capital_brut > PLAFOND_EPARGNE:
            st.error(f"🛑 Plafond de 4 R dépassé ! Limite : {formater_monnaie_empire(PLAFOND_EPARGNE)} Ø.")
        else:
            st.success(f"✅ Capacité de dépôt restante : **{formater_monnaie_empire(dispo_epargne)} Ø** sur le maximum de {formater_monnaie_empire(PLAFOND_EPARGNE)} Ø.")

        st.write(f"Taux d'intérêt de base (annuel) : **{taux_epargne_auto:.2f}%**")
        
        taux_decimal = taux_epargne_auto / 100.0
        taux_journalier_reel = taux_decimal / 12.0  # 1 jour réel = 1 mois de jeu
        
        # Calculs selon la durée choisie
        interets_terme = int(capital_brut * (taux_journalier_reel * choix_duree_jeu))
        capital_final_lineaire = capital_brut + interets_terme
        
        facteur_compose = (1.0 + taux_journalier_reel) ** choix_duree_jeu
        capital_final_compose = int(capital_brut * facteur_compose)
        interets_compose = capital_final_compose - capital_brut

        m1, m2 = st.columns(2)
        with m1: st.metric(label=f"⚡ Intérêts au terme ({choix_duree_jeu} jours réels)", value=f"{formater_monnaie_empire(interets_terme)} Ø")
        with m2: st.metric(label="🔄 Gain si Pivot Quotidien (Intérêts Composés)", value=f"{formater_monnaie_empire(interets_compose)} Ø")

        st.markdown("##### ⚖️ Arbitrage Épargne (Cycle choisi)")
        donnees_comp_ce = [
            {"Méthode": "🎯 Mode Classique (Échéance Fixe)", "Bénéfice Net": formater_monnaie_empire(interets_terme), "Solde Final": formater_monnaie_empire(capital_final_lineaire), "Performance": f"+{(interets_terme/capital_brut*100):.1f}%" if capital_brut > 0 else "0%"},
            {"Méthode": "🔄 Mode Pivot Quotidien (Composé)", "Bénéfice Net": formater_monnaie_empire(interets_compose), "Solde Final": formater_monnaie_empire(capital_final_compose), "Performance": f"+{((capital_final_compose/capital_brut - 1)*100):.1f}%" if capital_brut > 0 else "0%"}
        ]
        st.dataframe(pd.DataFrame(donnees_comp_ce), use_container_width=True, hide_index=True)

        st.markdown("##### 📈 Courbe d'évolution du capital sur la période")
        points_c = []
        for j in range(0, choix_duree_jeu + 1):
            points_c.append({
                "Jour Réel (Mois Jeu)": j,  # Utilisation d'un entier pur pour bloquer le tri alphabétique
                "Option Classique (Bloqué)": float(capital_brut + int(capital_brut * (taux_journalier_reel * j))),
                "Option Pivot Quotidien": float(int(capital_brut * ((1.0 + taux_journalier_reel) ** j)))
            })
        
        df_graphique_ce = pd.DataFrame(points_c).set_index("Jour Réel (Mois Jeu)")
        st.line_chart(df_graphique_ce, use_container_width=True)
    # ---------------------------------------------------------------------
    # 🔒 ONGLET LIVRET I
    # ---------------------------------------------------------------------
    with tab_livret_i:
        st.subheader("🏛️ Situation de vos Livrets I")
        
        dispo_livret = max(0, PLAFOND_LIVRET_I - capital_brut)
        if capital_brut > PLAFOND_LIVRET_I:
            st.error(f"🛑 Plafond de 6 R dépassé ! Tout retrait est définitif : le jeu bloquera toute réouverture. Limite : {formater_monnaie_empire(PLAFOND_LIVRET_I)} Ø.")
        else:
            st.success(f"✅ Statut conforme. Capacité de dépôt restante : **{formater_monnaie_empire(dispo_livret)} Ø** sur le maximum de {formater_monnaie_empire(PLAFOND_LIVRET_I)} Ø.")
        
        st.write(f"Taux théorique sur cette tranche : **{taux_epargne_auto:.2f}%**")
        
        taux_decimal = taux_epargne_auto / 100.0
        taux_journalier_reel = taux_decimal / 12.0
        
        # Remplacement de la courbe du Livret I
        points_l = []
        for j in range(0, 13):
            points_l.append({
                "Jour Réel (Mois Jeu)": j,
                "Option Bloquée": float(capital_brut + int(capital_brut * (taux_journalier_reel * j))),
                "Option Pivot Quotidien": float(int(capital_brut * ((1.0 + taux_journalier_reel) ** j)))
            })
        
        df_graphique_l = pd.DataFrame(points_l).set_index("Jour Réel (Mois Jeu)")
        st.line_chart(df_graphique_l, use_container_width=True)

    # ---------------------------------------------------------------------
    # 🏦 ONGLET EMPRUNTS
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
# 🏛️ AFFICHAGE GLOBAL DES BAREMES BANCAIRES DU MONDE 8
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
