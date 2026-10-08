import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre

st.set_page_config(page_title="Emprunts & Crédits - Monde 8", layout="wide", initial_sidebar_state="expanded")
st.markdown("<style>.block-container { max-width: 100% !important; padding: 2rem !important; }</style>", unsafe_allow_html=True)

st.title("🏦 Gestion de l'Endettement & Simulateur d'Emprunts")
st.markdown("Calculez la faisabilité de vos demandes de financement auprès de la Banque Fédérale.")

saisie_pret = st.text_input("Montant de l'emprunt souhaité (Ex: 500M, 2G, 10T) :", value="100 M", key="somme_credit")
montant_pret = convertir_saisie_en_nombre(saisie_pret)

st.caption(f"💰 Somme du crédit demandée : **{formater_monnaie_empire(montant_pret)} Ø**")
st.markdown("---")

if montant_pret > 0:
    # Barème officiel des taux d'emprunts Monde 8
    taux_emprunt = 2.0
    if montant_pret >= 5_000_000_100 * 10**18: taux_emprunt = 10.0
    if montant_pret >= 6_000_000_100 * 10**18: taux_emprunt = 20.0
    if montant_pret >= 10_000_001_000 * 10**18: taux_emprunt = 35.0
    if montant_pret >= 15_000_001_000 * 10**18: taux_emprunt = 60.0
    if montant_pret >= 20_000_001_000 * 10**18: taux_emprunt = 80.0
    if montant_pret >= 30_000_001_000 * 10**18: taux_emprunt = 100.0

    st.write(f"📊 Tranche de taux d'intérêt détectée : **{taux_emprunt:.2f}% / an**")

    # Choix de la durée (Section 6.3)
    duree_credit = st.slider("Sélectionnez la durée de remboursement (en mois de jeu / jours réels) :", 6, 48, 12, 1)

    # Calcul simplifié conforme charte
    cout_interets_bruts = int(montant_pret * (taux_emprunt / 100.0) * (duree_credit / 12.0))
    total_a_rembourser = montant_pret + cout_interets_bruts
    mensualite_daily = total_a_rembourser // duree_credit

    c1, c2, c3 = st.columns(3)
    with c1: st.metric("💸 Coût global des intérêts", f"{formater_monnaie_empire(cout_interets_bruts)} Ø", delta="Frais de Banque", delta_color="inverse")
    with c2: st.metric("🏛️ Capital total à rembourser", f"{formater_monnaie_empire(total_a_rembourser)} Ø")
    with c3: st.metric("📅 Mensualité par Jour Réel", f"{formater_monnaie_empire(mensualite_daily)} Ø")
    
    st.caption("💡 **Règle de remboursement anticipé (Section 6.3)** : Tout remboursement anticipé (10% min du capital restant dû) entraîne une pénalité réglementaire équivalente à 6 mois d'intérêts sur la somme remboursée.")
