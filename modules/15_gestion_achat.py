import streamlit as st
import pandas as pd
import re
from utils import formater_monnaie_empire, convertir_saisie_en_nombre

st.title("🛒 Gestion Achat — Promotions & Catalogue")
st.markdown(
    "Renseignez votre **budget** et collez directement le tableau des **4 promotions** depuis l'Agence d'Empire Immo. "
    "Le module calcule votre capacité d'achat en tenant compte du **stock disponible**."
)

# 1. Case pour le budget
budget_saisie = st.text_input(
    "💰 Budget total disponible (chiffres bruts ou format Empire ex: 2 583 398 694 930 820 547 495) :",
    placeholder="Ex: 2 583 398 694 930 820 547 495"
)

# 2. Case pour les 4 promotions
texte_promos = st.text_area(
    "🏷️ Collez ici vos 4 promotions (depuis l'onglet Acheter de l'Agence) :",
    height=200,
    placeholder="Prix\tLoyer\tCharges\tImpôts\tDispo\tAcheter\nEntrepôt inexploitable -14%\t295 872 Ø\t0 Ø\t0 Ø\t283 Ø\t7 976..."
)

def nettoyer_grand_entier(valeur_str):
    if not valeur_str:
        return 0
    propre = re.sub(r"[\sØ€]+", "", str(valeur_str))
    if propre.isdigit():
        return int(propre)
    return int(convertir_saisie_en_nombre(valeur_str))

def analyser_lignes_promos(texte, budget):
    resultats = []
    lignes = texte.strip().split('\n')

    for ligne in lignes:
        ligne_propre = ligne.strip()
        # Ignore les lignes vides, les en-têtes et les lignes contenant uniquement "0"
        if not ligne_propre or "Ø" not in ligne_propre:
            continue

        nom_bien = None
        prix_str = ""
        stock_str = ""

        # Découpage par tabulation (format standard du copier-coller navigateur)
        if "\t" in ligne_propre:
            colonnes = [c.strip() for c in ligne_propre.split("\t") if c.strip()]
            # Structure attendue : [Nom, Prix Ø, Loyer Ø, Charges Ø, Impôts Ø, Dispo]
            if len(colonnes) >= 2 and "Ø" in colonnes[1]:
                nom_bien = colonnes[0]
                prix_str = re.sub(r"[\sØ]+", "", colonnes[1])
                if len(colonnes) >= 6:
                    stock_str = re.sub(r"\s+", "", colonnes[5])

        # Méthode de secours si séparé par plusieurs espaces
        if not nom_bien:
            match = re.search(r"^\s*(.+?)\s{2,}([\d\s]+)\s*Ø", ligne_propre)
            if match:
                nom_bien = match.group(1).strip()
                prix_str = re.sub(r"\s+", "", match.group(2))
                # Cherche le dernier bloc de chiffres en fin de ligne pour le stock
                match_fin = re.search(r"Ø\s+([\d\s]+)$", ligne_propre)
                if match_fin:
                    stock_str = re.sub(r"\s+", "", match_fin.group(1))

        if nom_bien and prix_str.isdigit():
            prix_unit = int(prix_str)
            stock_dispo = int(stock_str) if stock_str.isdigit() else None

            if prix_unit > 0:
                qte_max_budget = budget // prix_unit
                
                if stock_dispo is not None:
                    qte_achetable_reelle = min(qte_max_budget, stock_dispo)
                    dispo_affiche = f"{stock_dispo:,}".replace(",", " ")
                else:
                    qte_achetable_reelle = qte_max_budget
                    dispo_affiche = "Non détecté"

                cout_total = qte_achetable_reelle * prix_unit
                reste_budget = budget - cout_total

                resultats.append({
                    "Bâtiment": nom_bien,
                    "Prix Unitaire": f"{prix_unit:,}".replace(",", " ") + " Ø",
                    "Stock Dispo": dispo_affiche,
                    "Max Budget": f"{qte_max_budget:,}".replace(",", " "),
                    "Quantité à acheter": str(qte_achetable_reelle),
                    "Coût Total": formater_monnaie_empire(cout_total) + " Ø",
                    "Budget Restant": formater_monnaie_empire(reste_budget) + " Ø"
                })

    return resultats

if st.button("🧮 Calculer mes achats possibles", type="primary", use_container_width=True):
    budget = nettoyer_grand_entier(budget_saisie)

    if budget <= 0:
        st.warning("⚠️ Veuillez entrer un budget valide supérieur à 0.")
    elif not texte_promos.strip():
        st.warning("⚠️ Veuillez coller les lignes de vos 4 promotions.")
    else:
        donnees = analyser_lignes_promos(texte_promos, budget)

        if not donnees:
            st.error("❌ Aucune promotion reconnue. Vérifiez que le texte collé contient bien les prix suivis de 'Ø'.")
        else:
            st.success(f"✅ {len(donnees)} promotion(s) analysée(s) avec succès !")

            # 1. BLOC RAPIDE : Quantité réelle à copier en 1 clic
            st.subheader("📋 Quantité à acheter (cliquez sur l'icône à droite du rectangle)")
            
            h1, h2 = st.columns([2, 1])
            with h1:
                st.markdown("**Nom du bien**")
            with h2:
                st.markdown("**Quantité à saisir dans le jeu**")

            for item in donnees:
                c1, c2 = st.columns([2, 1], vertical_alignment="center")
                with c1:
                    st.write(f"{item['Bâtiment']} *(Dispo : {item['Stock Dispo']})*")
                with c2:
                    st.code(item["Quantité à acheter"], language=None)

            st.markdown("---")

            # 2. TABLEAU DÉTAILLÉ
            st.subheader("📊 Comparatif détaillé par bâtiment")
            df_promos = pd.DataFrame(donnees)
            st.dataframe(
                df_promos[["Bâtiment", "Prix Unitaire", "Stock Dispo", "Max Budget", "Quantité à acheter", "Coût Total", "Budget Restant"]],
                use_container_width=True,
                hide_index=True
            )
