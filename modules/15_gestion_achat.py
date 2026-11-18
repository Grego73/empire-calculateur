import streamlit as st
import pandas as pd
import re
import utils

st.title("🛒 Gestion Achat — Promotions & Catalogue")
st.markdown(
    "Renseignez votre **budget**. Les promotions du jour sont chargées automatiquement depuis la base "
    "et mises à jour dès que vous en collez de nouvelles."
)

# Chargement sécurisé des promotions enregistrées en base
promos_enregistrees = ""
date_derniere_maj = ""
if hasattr(utils, "charger_promos_jour"):
    promos_enregistrees, date_derniere_maj = utils.charger_promos_jour()

if date_derniere_maj:
    st.info(f"📅 Promotions en mémoire (dernière mise à jour : **{date_derniere_maj}**)")

# 1. Case pour le budget
budget_saisie = st.text_input(
    "💰 Budget total disponible (chiffres bruts ou format Empire ex: 2 583 398 694 930 820 547 495) :",
    placeholder="Ex: 2 583 398 694 930 820 547 495",
    key="input_budget_achat"
)

# 2. Case pour les 4 promotions (pré-remplie avec la base)
texte_promos = st.text_area(
    "🏷️ Promotions du jour (modifiez ou collez les nouvelles pour écraser l'ancienne liste) :",
    value=promos_enregistrees,
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
    return int(utils.convertir_saisie_en_nombre(valeur_str))

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
            if len(colonnes) >= 2 and "Ø" in colonnes:
                nom_bien = colonnes
                prix_str = re.sub(r"[\sØ]+", "", colonnes)
                if len(colonnes) >= 6:
                    stock_str = re.sub(r"\s+", "", colonnes)

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
                    "Coût Total": utils.formater_monnaie_empire(cout_total) + " Ø",
                    "Budget Restant": utils.formater_monnaie_empire(reste_budget) + " Ø",
                    "_raw_prix": prix_unit,
                    "_raw_qte": qte_achetable_reelle
                })

    # Tri du bâtiment LE PLUS CHER au moins cher
    resultats.sort(key=lambda x: x["_raw_prix"], reverse=True)
    return resultats

if st.button("🧮 Calculer mes achats possibles", type="primary", use_container_width=True, key="btn_calcul_achat"):
    budget = nettoyer_grand_entier(budget_saisie)

    if not texte_promos.strip():
        st.warning("⚠️ Veuillez coller les lignes de vos 4 promotions.")
    else:
        donnees_test = analyser_lignes_promos(texte_promos, budget if budget > 0 else 1)

        if not donnees_test:
            st.error("❌ Aucune promotion reconnue. Vérifiez que le texte collé contient bien les prix suivis de 'Ø'.")
        else:
            # Si le texte a changé par rapport à la base, on écrase l'ancienne sauvegarde
            if texte_promos.strip() != promos_enregistrees.strip() and hasattr(utils, "sauvegarder_promos_jour"):
                if utils.sauvegarder_promos_jour(texte_promos.strip()):
                    st.toast("💾 Nouvelles promotions enregistrées en base !")

            if budget <= 0:
                st.warning("⚠️ Promotions sauvegardées. Entrez maintenant un budget supérieur à 0 pour voir les quantités.")
            else:
                donnees = analyser_lignes_promos(texte_promos, budget)
                achetables = [item for item in donnees if item["_raw_qte"] > 0]

                if achetables:
                    meilleur_choix = achetables
                    st.success(f"🏆 **Meilleur achat possible (le plus cher accessible) : {meilleur_choix['Bâtiment']}**")
                    
                    c_top1, c_top2 = st.columns(, vertical_alignment="center")
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
                
                h1, h2 = st.columns()
                with h1:
                    st.markdown("**Nom du bien**")
                with h2:
                    st.markdown("**Quantité à saisir dans le jeu**")

                for item in donnees:
                    c1, c2 = st.columns(, vertical_alignment="center")
                    with c1:
                        if achetables and item["Bâtiment"] == achetables["Bâtiment"]:
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
