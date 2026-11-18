import streamlit as st
import pandas as pd
import re
from utils import formater_monnaie_empire

st.title("🏷️ Gestion Revente (+15 %)")
st.markdown(
    "Collez directement le tableau de vos propriétés depuis la page **Immobilisation** d'Empire Immo. "
    "Le module calcule le prix unitaire exact et le prix de revente majoré de **+15 % (arrondi à l'inférieur)**."
)

# Zone de saisie
texte_proprietes = st.text_area(
    "📋 Collez ici la liste de vos biens (Nom, Quantité, Valeur totale Ø) :",
    height=220,
    placeholder="Zone aérospatiale internationale\t293\t5 479 256 642 733 534 Ø\n+12,1 %\tInactif..."
)

col_param1, col_param2 = st.columns(2)
with col_param1:
    marge_pourcent = st.number_input("Pourcentage de majoration (%)", min_value=0, max_value=500, value=15, step=1)

def analyser_lignes_proprietes(texte, pourcentage):
    resultats = []
    lignes = texte.strip().split('\n')
    multiplicateur = 100 + int(pourcentage)
    
    # Expression régulière de secours (si pas de tabulations) : cherche 2 espaces ou plus entre colonnes
    pattern_espaces = re.compile(r"^\s*(.+?)\s{2,}([\d\s]+?)\s{2,}([\d\s]+)\s*Ø")
    
    for ligne in lignes:
        ligne_propre = ligne.strip()
        if not ligne_propre or "Ø" not in ligne_propre:
            continue
            
        nom_bien = None
        qte_str = ""
        val_totale_str = ""
        
        # 1. Méthode prioritaire : découpage exact par tabulation (copier-coller navigateur)
        if "\t" in ligne_propre:
            colonnes = [c.strip() for c in ligne_propre.split("\t") if c.strip()]
            if len(colonnes) >= 3 and "Ø" in colonnes:
                nom_bien = colonnes
                qte_str = re.sub(r"\s+", "", colonnes)
                val_totale_str = re.sub(r"[\sØ]+", "", colonnes)
        
        # 2. Méthode de secours : si les tabulations ont été remplacées par plusieurs espaces
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
                # Arithmétique entière exacte
                prix_unitaire = valeur_totale // quantite
                prix_revente = (prix_unitaire * multiplicateur) // 100
                total_revente_lot = prix_revente * quantite
                
                resultats.append({
                    "Bâtiment": nom_bien,
                    "Quantité": f"{quantite:,}".replace(",", " "),
                    "Prix Unitaire (Base)": f"{prix_unitaire:,}".replace(",", " ") + " Ø",
                    f"Prix Revente (+{pourcentage}%)": f"{prix_revente:,}".replace(",", " ") + " Ø",
                    "Valeur à copier": str(prix_revente),
                    "Total Lot Revente": formater_monnaie_empire(total_revente_lot) + " Ø"
                })
                
    return resultats

if st.button("🧮 Calculer les prix de revente", type="primary", use_container_width=True):
    if not texte_proprietes.strip():
        st.warning("⚠️ Veuillez coller la liste de vos propriétés avant de lancer le calcul.")
    else:
        donnees = analyser_lignes_proprietes(texte_proprietes, marge_pourcent)
        
        if not donnees:
            st.error("❌ Aucun bâtiment reconnu. Vérifiez que les lignes contiennent bien le nom, la quantité et la valeur suivie de 'Ø'.")
        else:
            st.success(f"✅ {len(donnees)} bâtiment(s) analysé(s) avec succès !")
            df_res = pd.DataFrame(donnees)
            
            # 1. PREMIER TABLEAU : Uniquement Nom du bien et Valeur à copier
            st.subheader("📋 Tableau rapide (Copier-Coller)")
            st.dataframe(
                df_res[["Bâtiment", "Valeur à copier"]],
                use_container_width=True,
                hide_index=True
            )
            
            st.markdown("---")
            
            # 2. SECOND TABLEAU : Détail complet
            st.subheader("📊 Tableau détaillé")
            st.dataframe(
                df_res[["Bâtiment", "Quantité", "Prix Unitaire (Base)", f"Prix Revente (+{marge_pourcent}%)", "Total Lot Revente"]],
                use_container_width=True,
                hide_index=True
            )
