import streamlit as st
import pandas as pd
import re
from utils import formater_monnaie_empire, convertir_saisie_en_nombre

st.title("🛒 Gestion Achat — Promotions & Cascade")
st.markdown(
    "Renseignez votre **budget** et collez directement le tableau des **promotions** depuis l'Agence d'Empire Immo. "
    "Comparez l'achat **indépendant** (à gauche) et l'achat **en cascade du plus cher au moins cher** (à droite)."
)

# 1. Case pour le budget
budget_saisie = st.text_input(
    "💰 Budget total disponible (chiffres bruts ou format Empire ex: 4 222 912 343 876 788 493 457) :",
    placeholder="Ex: 4 222 912 343 876 788 493 457",
    key="input_budget_achat"
)

# 2. Case pour les 4 promotions
texte_promos = st.text_area(
    "🏷️ Collez ici vos promotions (depuis l'onglet Acheter de l'Agence) :",
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

def analyser_lignes_promos(texte, budget_initial):
    biens_bruts = []
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
                biens_bruts.append({
                    "nom": nom_bien,
                    "prix_unit": prix_unit,
                    "stock_dispo": stock_dispo
                })

    # 1. Calcul INDÉPENDANT (ordre d'origine)
    res_independant = []
    for bien in biens_bruts:
        prix_unit = bien["prix_unit"]
        stock_dispo = bien["stock_dispo"]
        qte_max_budget = budget_initial // prix_unit

        if stock_dispo is not None:
            qte_reelle = min(qte_max_budget, stock_dispo)
            dispo_affiche = f"{stock_dispo:,}".replace(",", " ")
        else:
            qte_reelle = qte_max_budget
            dispo_affiche = "Non détecté"

        cout_total = qte_reelle * prix_unit
        reste_budget = budget_initial - cout_total

        res_independant.append({
            "Bâtiment": bien["nom"],
            "Prix Unitaire": f"{prix_unit:,}".replace(",", " ") + " Ø",
            "Stock Dispo": dispo_affiche,
            "Max Budget": f"{qte_max_budget:,}".replace(",", " "),
            "Quantité à acheter": str(qte_reelle),
            "Coût Total": formater_monnaie_empire(cout_total) + " Ø",
            "Budget Restant": formater_monnaie_empire(reste_budget) + " Ø"
        })

    # 2. Calcul EN CASCADE (trié du PLUS CHER au moins cher)
    biens_tries = sorted(biens_bruts, key=lambda x: x["prix_unit"], reverse=True)
    res_cascade = []
    budget_courant = budget_initial

    for bien in biens_tries:
        prix_unit = bien["prix_unit"]
        stock_dispo = bien["stock_dispo"]
        qte_max_budget = budget_courant // prix_unit

        if stock_dispo is not None:
            qte_cascade = min(qte_max_budget, stock_dispo)
            dispo_affiche = f"{stock_dispo:,}".replace(",", " ")
        else:
            qte_cascade = qte_max_budget
            dispo_affiche = "Non détecté"

        cout_cascade = qte_cascade * prix_unit
        budget_courant -= cout_cascade

        res_cascade.append({
            "Priorité": f"#{len(res_cascade) + 1}",
            "Bâtiment": bien["nom"],
            "Prix Unitaire": f"{prix_unit:,}".replace(",", " ") + " Ø",
            "Stock Dispo": dispo_affiche,
            "Quantité Cascade": str(qte_cascade),
            "Coût Cascade": formater_monnaie_empire(cout_cascade) + " Ø",
            "Reste après achat": formater_monnaie_empire(budget_courant) + " Ø"
        })

    return res_independant, res_cascade, budget_courant

if st.button("🧮 Calculer mes achats possibles", type="primary", use_container_width=True, key="btn_calcul_achat"):
    budget = nettoyer_grand_entier(budget_saisie)

    if budget <= 0:
        st.warning("⚠️ Veuillez entrer un budget valide supérieur à 0.")
    elif not texte_promos.strip():
        st.warning("⚠️ Veuillez coller les lignes de vos promotions.")
    else:
        donnees_indep, donnees_cascade, reliquat_final = analyser_lignes_promos(texte_promos, budget)

        if not donnees_indep:
            st.error("❌ Aucune promotion reconnue. Vérifiez que le texte collé contient bien les prix suivis de 'Ø'.")
        else:
            st.success(f"✅ {len(donnees_indep)} promotion(s) analysée(s) avec succès !")

            # =========================================================
            # 1. DOUBLE BLOC DE COPIE RAPIDE CÔTE À CÔTE
            # =========================================================
            col_gauche, col_droite = st.columns(2, gap="large")

            with col_gauche:
                st.subheader("📋 1. Achat Indépendant (1 seul bien)")
                st.caption("Quantité maximale si vous achetez uniquement ce bâtiment.")
                for item in donnees_indep:
                    c1, c2 = st.columns([3, 2], vertical_alignment="center")
                    with c1:
                        st.write(f"**{item['Bâtiment']}**\n*(Dispo : {item['Stock Dispo']})*")
                    with c2:
                        st.code(item["Quantité à acheter"], language=None)

            with col_droite:
                st.subheader("⚡ 2. Achat en Cascade (du + cher au - cher)")
                st.caption("Achète le max du plus cher, puis utilise le reste sur les suivants.")
                for item in donnees_cascade:
                    c1, c2 = st.columns([3, 2], vertical_alignment="center")
                    with c1:
                        st.write(f"**{item['Priorité']} {item['Bâtiment']}**\n*(Reste : {item['Reste après achat']})*")
                    with c2:
                        st.code(item["Quantité Cascade"], language=None)

            st.markdown("---")

            # =========================================================
            # 2. DOUBLE TABLEAU DÉTAILLÉ EN DESSOUS
            # =========================================================
            st.subheader("📊 Comparatif détaillé : Achat Indépendant")
            df_indep = pd.DataFrame(donnees_indep)
            st.dataframe(
                df_indep[["Bâtiment", "Prix Unitaire", "Stock Dispo", "Max Budget", "Quantité à acheter", "Coût Total", "Budget Restant"]],
                use_container_width=True,
                hide_index=True
            )

            st.subheader("📉 Détail de la déduction en Cascade (ordre décroissant)")
            df_cascade = pd.DataFrame(donnees_cascade)
            st.dataframe(
                df_cascade[["Priorité", "Bâtiment", "Prix Unitaire", "Stock Dispo", "Quantité Cascade", "Coût Cascade", "Reste après achat"]],
                use_container_width=True,
                hide_index=True
            )

            # Métriques récapitulatives de la cascade
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("Budget Initial", formater_monnaie_empire(budget) + " Ø")
            with m2:
                st.metric("Total Dépensé (Cascade)", formater_monnaie_empire(budget - reliquat_final) + " Ø")
            with m3:
                st.metric("Reliquat Final (Brut)", f"{reliquat_final:,}".replace(",", " ") + " Ø")
