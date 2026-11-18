import streamlit as st
import pandas as pd
import re
from utils import formater_monnaie_empire

# Récupération dynamique du pourcentage avant d'afficher le titre
marge_actuelle = st.session_state.get("input_marge_revente", 15)
signe = "+" if marge_actuelle >= 0 else ""

st.title(f"🏷️ Gestion Revente ({signe}{marge_actuelle} %)")
st.markdown(
    f"Collez directement le tableau de vos propriétés depuis la page **Immobilisation** d'Empire Immo. "
    f"Le module calcule le prix unitaire exact et le prix de revente ajusté de **{signe}{marge_actuelle} % (arrondi à l'inférieur)**."
)

# Zone de saisie
texte_proprietes = st.text_area(
    "📋 Collez ici la liste de vos biens (Nom, Quantité, Valeur totale Ø) :",
    height=220,
    placeholder="Zone aérospatiale internationale\t293\t5 479 256 642 733 534 Ø\n+12,1 %\tInactif...",
    key="textarea_revente_proprietes"
)

col_param1, col_param2 = st.columns([1, 2])
with col_param1:
    marge_pourcent = st.number_input(
        "Pourcentage d'ajustement (%)", 
        min_value=-99, 
        max_value=500, 
        value=15, 
        step=1, 
        key="input_marge_revente"
    )

def analyser_lignes_proprietes(texte, pourcentage):
    resultats = []
    lignes = texte.strip().split('\n')
    multiplicateur = 100 + int(pourcentage)
    signe_col = "+" if pourcentage >= 0 else ""
    
    pattern_espaces = re.compile(r"^\s*(.+?)\s{2,}([\d\s]+?)\s{2,}([\d\s]+)\s*Ø")
    
    for ligne in lignes:
        ligne_propre = ligne.strip()
        if not ligne_propre or "Ø" not in ligne_propre:
            continue
            
        nom_bien = None
        qte_str = ""
        val_totale_str = ""
        
        if "\t" in ligne_propre:
            colonnes = [c.strip() for c in ligne_propre.split("\t") if c.strip()]
            if len(colonnes) >= 3 and "Ø" in colonnes[2]:
                nom_bien = colonnes[0]
                qte_str = re.sub(r"\s+", "", colonnes[1])
                val_totale_str = re.sub(r"[\sØ]+", "", colonnes[2])
        
        if not nom_bien:
            match = pattern_espaces.search(ligne_propre)
            if match:
                nom_bien = match.group(1).strip()
                qte_str = re.sub(r"\s+", "", match.group(2))
                val_totale_str = re.sub(r"\s+", "", match.group(3))
                
        if nom_bien and qte_str.isdigit() and val_totale_str.isdigit():
            quantite = int(qte_str)
            valeur_totale = int(val_totale_str)
            
            if quantite > 0:
                prix_unitaire = valeur_totale // quantite
                prix_revente = (prix_unitaire * multiplicateur) // 100
                total_revente_lot = prix_revente * quantite
                
                resultats.append({
                    "Bâtiment": nom_bien,
                    "Quantité": f"{quantite:,}".replace(",", " "),
                    "Prix Unitaire (Base)": f"{prix_unitaire:,}".replace(",", " ") + " Ø",
                    f"Prix Revente ({signe_col}{pourcentage}%)": f"{prix_revente:,}".replace(",", " ") + " Ø",
                    "Valeur à copier": str(prix_revente),
                    "Total Lot Revente": formater_monnaie_empire(total_revente_lot) + " Ø",
                    "_raw_qte": quantite,
                    "_raw_total_lot": total_revente_lot
                })
                
    return resultats

if st.button("🧮 Calculer les prix de revente", type="primary", use_container_width=True, key="btn_calcul_revente"):
    if not texte_proprietes.strip():
        st.warning("⚠️ Veuillez coller la liste de vos propriétés avant de lancer le calcul.")
    else:
        donnees = analyser_lignes_proprietes(texte_proprietes, marge_pourcent)
        
        if not donnees:
            st.error("❌ Aucun bâtiment reconnu. Vérifiez que les lignes contiennent bien le nom, la quantité et la valeur suivie de 'Ø'.")
        else:
            st.success(f"✅ {len(donnees)} bâtiment(s) analysé(s) avec succès !")
            signe_tab = "+" if marge_pourcent >= 0 else ""
            
            # 1. PREMIERE PARTIE : Liste avec rectangle et icône de copie en 1 clic
            st.subheader("📋 Copie rapide (cliquez sur l'icône à droite du rectangle)")
            
            h1, h2 = st.columns([2, 3])
            with h1:
                st.markdown("**Nom du bien**")
            with h2:
                st.markdown("**Valeur à copier**")
                
            for item in donnees:
                c1, c2 = st.columns([2, 3], vertical_alignment="center")
                with c1:
                    st.write(item["Bâtiment"])
                with c2:
                    st.code(item["Valeur à copier"], language=None)
            
            st.markdown("---")
            
            # 2. SECOND TABLEAU : Détail complet avec ligne TOTAL
            st.subheader("📊 Tableau détaillé")
            
            total_qte_globale = sum(item["_raw_qte"] for item in donnees)
            total_revente_globale = sum(item["_raw_total_lot"] for item in donnees)
            
            lignes_tableau = [
                {
                    "Bâtiment": item["Bâtiment"],
                    "Quantité": item["Quantité"],
                    "Prix Unitaire (Base)": item["Prix Unitaire (Base)"],
                    f"Prix Revente ({signe_tab}{marge_pourcent}%)": item[f"Prix Revente ({signe_tab}{marge_pourcent}%)"],
                    "Total Lot Revente": item["Total Lot Revente"]
                }
                for item in donnees
            ]
            
            lignes_tableau.append({
                "Bâtiment": "TOTAL GÉNÉRAL",
                "Quantité": f"{total_qte_globale:,}".replace(",", " "),
                "Prix Unitaire (Base)": "—",
                f"Prix Revente ({signe_tab}{marge_pourcent}%)": "—",
                "Total Lot Revente": formater_monnaie_empire(total_revente_globale) + " Ø"
            })
            
            df_res = pd.DataFrame(lignes_tableau)
            st.dataframe(
                df_res,
                use_container_width=True,
                hide_index=True
            )
