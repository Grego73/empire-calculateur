import streamlit as st
import pandas as pd
import re
from utils import formater_monnaie_empire, convertir_saisie_en_nombre

st.title("🛒 Gestion Achat — Promotions & Catalogue")
st.markdown(
    "Renseignez votre **budget** et collez directement le tableau des **4 promotions** depuis l'Agence d'Empire Immo. "
    "Le module met automatiquement en avant **le bien le plus cher accessible** avec votre budget."
)

# 1. Case pour le budget
budget_saisie = st.text_input(
    "💰 Budget total disponible (chiffres bruts ou format Empire ex: 2 583 398 694 930 820 547 495) :",
    placeholder="Ex: 2 583 398 694 930 820 547 495",
    key="input_budget_achat"
)

# 2. Case pour les 4 promotions
texte_promos = st.text_area(
    "🏷️ Collez ici vos 4 promotions (depuis l'onglet Acheter de l'Agence) :",
    height=200,
    placeholder="Prix\tLoyer\tCharges\tImpôts\tDispo\tAcheter\nEntrepôt inexploitable -14%\t295 872 Ø\t0 Ø\t0 Ø\t283 Ø\t7 976...",
    key="textarea_promos_achat"
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
        if not ligne_propre or "Ø" not in ligne_propre:
            continue

        nom_bien = None
        prix_str = ""
        stock_str = ""

        # Découpage par tabulation (format standard navigateur)
        if "\t" in ligne_propre:
            colonnes = [c.strip() for c in ligne_propre.split("\t") if c.strip()]
            if len(colonnes) >= 2 and "Ø" in colonnes[1]:
                nom_bien = colonnes[0]
                prix_str = re.sub(r"[\sØ]+", "", colonnes[1])
                if len(colonnes) >= 6:
                    stock_str = re.sub(r"\s+", "", colonnes[5])

        # Méthode de secours par espaces multiples
        if not nom_bien:
            match = re.search(r"^\s*(.+?)\s{2,}([\d\s]+)\s*Ø", ligne_propre)
            if match:
                nom_bien = match.group(1).strip()
                prix_str = re.sub(r"\s+", "", match.group(2))
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
                    "Budget Restant": formater_monnaie_empire(reste_budget) + " Ø",
                    "_raw_prix": prix_unit,
                    "_raw_qte": qte_achetable_reelle
                })

    # Tri du bâtiment LE PLUS CHER au moins cher
    resultats.sort(key=lambda x: x["_raw_prix"], reverse=True)
    return resultats

if st.button("🧮 Calculer mes achats possibles", type="primary", use_container_width=True, key="btn_calcul_achat"):
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
            # Recherche du bâtiment le plus cher où l'on peut acheter au moins 1 unité
            achetables = [item for item in donnees if item["_raw_qte"] > 0]

            if achetables:
                meilleur_choix = achetables[0]
                st.success(f"🏆 **Meilleur achat possible (le plus cher accessible) : {meilleur_choix['Bâtiment']}**")
                
                c_top1, c_top2 = st.columns([2, 3], vertical_alignment="center")
                with c_top1:
                    st.markdown(
                        f"**Prix unitaire :** {meilleur_choix['Prix Unitaire']}  \n"
                        f"**Coût total :** {meilleur_choix['Coût Total']} *(Reste : {meilleur_choix['Budget Restant']})*"
                    )
                with c_top2:
                    st.code(meilleur_choix["Quantité à acheter"], language=None)
            else:
                st.warning("⚠️ Votre budget actuel ne permet d'acheter aucun de ces bâtiments (quantité = 0 pour tous).")

            st.markdown("---")

            # 1. BLOC RAPIDE : Toutes les promotions triées du plus cher au moins cher
            st.subheader("📋 Quantité à acheter par bâtiment (du plus cher au moins cher)")
            
            h1, h2 = st.columns([2, 3])
            with h1:
                st.markdown("**Nom du bien**")
            with h2:
                st.markdown("**Quantité à saisir dans le jeu**")

            for item in donnees:
                c1, c2 = st.columns([2, 3], vertical_alignment="center")
                with c1:
                    if achetables and item["Bâtiment"] == achetables[0]["Bâtiment"]:
                        st.markdown(f"⭐ **{item['Bâtiment']}** *(Dispo : {item['Stock Dispo']})*")
                    else:
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
