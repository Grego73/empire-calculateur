import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre

# Configuration de la page
st.set_page_config(page_title="Banque & Épargne - Empire", layout="wide")

st.title("🏛️ Simulateur d'Épargne & Échelle Temporelle Monde 8")
st.info("🕒 Règle temporelle : **1 jour réel = 1 mois de jeu**. Un livret complet (12 mois de jeu) dure donc **12 jours réels**.")

# --- SECTION DES ENTREES (INPUTS) ---
col_input1, col_input2 = st.columns(2)

with col_input1:
    saisie_somme = st.text_input("Somme à épargner (Ex: 1.74Y, 500G, 10T) :", value="1.74 Y")
    capital_brut = convertir_saisie_en_nombre(saisie_somme)
    st.caption(f"💰 Somme interprétée : **{formater_monnaie_empire(capital_brut)} Ø**")

with col_input2:
    # Le taux affiché en jeu est pour le terme (12 mois de jeu = 12 jours réels)
    taux_terme = st.number_input("Taux d'intérêt au terme du livret (12 mois de jeu / 12j réels) (%) :", min_value=0.0, max_value=500.0, value=100.0, step=5.0)
    st.caption(f"📈 Taux configuré : **{taux_terme:.2f}% à l'échéance du livret**")

st.markdown("---")

if capital_brut <= 0:
    st.warning("⚠️ Veuillez saisir une somme supérieure à 0 pour lancer la simulation bancaire.")
else:
    # --- CALCULS FINANCIERS BASÉS SUR L'ÉCHELLE DU JEU ---
    # Taux pour 1 mois de jeu (donc 1 jour réel)
    taux_decimal_terme = taux_terme / 100.0
    taux_journalier_reel = taux_decimal_terme / 12.0  # 12 mois de jeu = 12 jours réels
    
    # 🎯 1. Cas Linéaire (Sans y toucher pendant les 12 mois de jeu / 12 jours réels)
    interets_terme_lineaire = int(capital_brut * taux_decimal_terme)
    capital_final_lineaire = capital_brut + interets_terme_lineaire
    
    # 🔄 2. Cas Composé Quotidien (Retrait et replacement chaque jour réel / chaque mois de jeu)
    # Formule : Capital * (1 + taux_mensuel_jeu)^(12 mois)
    facteur_compose = (1.0 + taux_journalier_reel) ** 12
    capital_final_compose = int(capital_brut * facteur_compose)
    interets_terme_compose = capital_final_compose - capital_brut

    # Gains instantanés par paliers temporels réels
    gain_par_jour_reel = int(capital_brut * taux_journalier_reel)

    # --- AFFICHAGE DES INDICATEURS CLÉS (KPIs) ---
    st.subheader("📊 Rendement Immédiat (Prorata Temporis)")
    m1, m2 = st.columns(2)
    with m1:
        st.metric(label="⚡ Gain par Jour Réel (1 mois de jeu)", value=f"{formater_monnaie_empire(gain_par_jour_reel)} Ø")
        st.caption("Intérêts crédités toutes les 24 heures réelles")
    with m2:
        st.metric(label="🏆 Gain au Terme Réel (12 jours réels / 12 mois de jeu)", value=f"{formater_monnaie_empire(interets_terme_lineaire)} Ø")
        st.caption("Intérêts totaux à échéance fixe sans cassage")

    st.markdown("---")

    # --- TABLEAU COMPARATIF STRATÉGIQUE ---
    st.subheader("⚖️ Matrice Comparative au Terme (Échéance de 12 Jours Réels)")
    
    donnees_comparatives = [
        {
            "Stratégie d'Épargne": "🎯 1. Blocage complet (12 jours réels)",
            "Capital Initial": formater_monnaie_empire(capital_brut),
            "Intérêts Générés": formater_monnaie_empire(interets_terme_lineaire),
            "Trésorerie à J+12 Réels": formater_monnaie_empire(capital_final_lineaire),
            "Multiplicateur": f"x {(capital_final_lineaire / capital_brut):.2f}" if capital_brut > 0 else "x 0"
        },
        {
            "Stratégie d'Épargne": "🔄 2. Retrait/Replacement chaque jour réel (Intérêts Composés)",
            "Capital Initial": formater_monnaie_empire(capital_brut),
            "Intérêts Générés": formater_monnaie_empire(interets_terme_compose),
            "Trésorerie à J+12 Réels": formater_monnaie_empire(capital_final_compose),
            "Multiplicateur": f"x {(capital_final_compose / capital_brut):.2f}" if capital_brut > 0 else "x 0"
        }
    ]
    
    df_comparatif = pd.DataFrame(donnees_comparatives)
    st.dataframe(df_comparatif, use_container_width=True, hide_index=True)

    # --- GRAPHISME VISUEL SUR LES 12 JOURS REELS ---
    st.markdown("### 📈 Trajectoire de croissance sur un cycle de Livret (12 Jours Réels)")
    
    points_courbe = []
    for jour_reel in range(0, 13):
        # Évolution Linéaire au prorata des jours réels
        val_lineaire = capital_brut + int(capital_brut * (taux_decimal_terme * (jour_reel / 12.0)))
        # Évolution Composée à chaque jour réel
        val_composee = int(capital_brut * ((1.0 + taux_journalier_reel) ** jour_reel))
        
        points_courbe.append({
            "Jour Réel (Mois Jeu)": f"J+{jour_reel} (Mois {jour_reel})",
            "Tri_Index": jour_reel,
            "Option Simple (Bloqué)": float(val_lineaire),
            "Option Composée (Quotidien)": float(val_composee)
        })
        
    df_graphique = pd.DataFrame(points_courbe).sort_values(by="Tri_Index").set_index("Jour Réel (Mois Jeu)").drop(columns=["Tri_Index"])
    st.line_chart(df_graphique, use_container_width=True)
    st.caption("💡 Astuce : En cassant et replaçant votre argent à chaque mise à jour quotidienne (24h réelles), votre courbe de richesse suit la trajectoire verte exponentielle.")
