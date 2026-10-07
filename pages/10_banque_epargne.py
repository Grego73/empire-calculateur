import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre

# Configuration de la page
st.set_page_config(page_title="Banque & Épargne - Empire", layout="wide")

st.title("🏛️ Simulateur d'Épargne & Intérêts Composés")
st.markdown("Calculez et comparez le rendement de vos fonds placés sur les Livrets de l'Empire.")

# --- SECTION DES ENTREES (INPUTS) ---
col_input1, col_input2 = st.columns(2)

with col_input1:
    saisie_somme = st.text_input("Somme à épargner (Ex: 1.74Y, 500G, 10T) :", value="1.74 Y")
    capital_brut = convertir_saisie_en_nombre(saisie_somme)
    st.caption(f"💰 Somme interprétée : **{formater_monnaie_empire(capital_brut)} Ø**")

with col_input2:
    taux_annuel = st.number_input("Taux d'intérêt annuel (%) :", min_value=0.0, max_value=500.0, value=100.0, step=5.0)
    st.caption(f"📈 Taux configuré : **{taux_annuel:.2f}% par an**")

st.markdown("---")

if capital_brut <= 0:
    st.warning("⚠️ Veuillez saisir une somme supérieure à 0 pour lancer la simulation bancaire.")
else:
    # --- CALCULS FINANCIERS HAUTE PRECISION (ENTIERS INFINIS PYTHON) ---
    taux_decimal = taux_annuel / 100.0
    taux_journalier = taux_decimal / 365.0
    
    # 🎯 1. Cas Linéaire (Sans y toucher pendant 12 mois)
    interets_terme_lineaire = int(capital_brut * taux_decimal)
    capital_final_lineaire = capital_brut + interets_terme_lineaire
    
    # 🔄 2. Cas Composé Quotidien (Retrait et replacement chaque jour)
    # Formule mathématique : Capital * (1 + r/365)^365. 
    # Pour éviter les limites de taille des floats, on utilise la puissance native sur des floats précis
    facteur_compose = (1.0 + taux_journalier) ** 365
    capital_final_compose = int(capital_brut * facteur_compose)
    interets_terme_compose = capital_final_compose - capital_brut

    # Gains intermédiaires pour l'affichage (Prélèvement anticipé linéaire au prorata)
    gain_journalier_brut = int(capital_brut * taux_journalier)
    gain_mensuel_brut = int(capital_brut * (taux_decimal / 12.0))

    # --- AFFICHAGE DES INDICATEURS CLÉS (KPIs) ---
    st.subheader("📊 Rendement Immédiat (Prorata Temporis)")
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric(label="⚡ Gain Journalier", value=f"{formater_monnaie_empire(gain_journalier_brut)} Ø")
        st.caption("Intérêts générés toutes les 24 heures")
    with m2:
        st.metric(label="📅 Gain Mensuel (30j)", value=f"{formater_monnaie_empire(gain_mensuel_brut)} Ø")
        st.caption("Intérêts générés par mois")
    with m3:
        st.metric(label="🏆 Gain au Terme (12 mois)", value=f"{formater_monnaie_empire(interets_terme_lineaire)} Ø")
        st.caption("Intérêts totaux à échéance fixe")

    st.markdown("---")

    # --- TABLEAU COMPARATIF STRATÉGIQUE ---
    st.subheader("⚖️ Matrice Comparative à 12 Mois (Évolution du Capital)")
    
    donnees_comparatives = [
        {
            "Stratégie d'Épargne": "🎯 1. Blocage 12 mois (Taux Simple)",
            "Capital Initial": formater_monnaie_empire(capital_brut),
            "Intérêts Générés": formater_monnaie_empire(interets_terme_lineaire),
            "Capital Final au Terme": formater_monnaie_empire(capital_final_lineaire),
            "Multiplicateur": f"x {(capital_final_lineaire / capital_brut):.2f}" if capital_brut > 0 else "x 0"
        },
        {
            "Stratégie d'Épargne": "🔄 2. Retrait/Replacement Quotidien (Intérêts Composés)",
            "Capital Initial": formater_monnaie_empire(capital_brut),
            "Intérêts Générés": formater_monnaie_empire(interets_terme_compose),
            "Capital Final au Terme": formater_monnaie_empire(capital_final_compose),
            "Multiplicateur": f"x {(capital_final_compose / capital_brut):.2f}" if capital_brut > 0 else "x 0"
        }
    ]
    
    df_comparatif = pd.DataFrame(donnees_comparatives)
    st.dataframe(df_comparatif, use_container_width=True, hide_index=True)

    # --- GRAPHIC VISUEL D'EVOLUTION THEORIQUE ---
    st.markdown("### 📈 Trajectoire de croissance sur 365 jours")
    
    # Génération d'une courbe simplifiée pour imager l'écart qui se creuse
    points_courbe = []
    for jour in:
        # Évolution Linéaire
        val_lineaire = capital_brut + int(capital_brut * (taux_decimal * (jour / 365.0)))
        # Évolution Composée
        val_composee = int(capital_brut * ((1.0 + taux_journalier) ** jour))
        
        points_courbe.append({
            "Jour": jour,
            "Option Simple (Bloqué)": float(val_lineaire),
            "Option Composée (Quotidien)": float(val_composee)
        })
        
    df_graphique = pd.DataFrame(points_courbe).set_index("Jour")
    st.line_chart(df_graphique, use_container_width=True)
    st.caption("💡 Note : L'écart entre les deux courbes représente le gain net supplémentaire généré en réinvestissant vos intérêts chaque jour.")
