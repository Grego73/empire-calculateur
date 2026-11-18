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
    
    # Capture [Nom du bien] [Quantité] [Valeur totale] Ø
    pattern = re.compile(r"^\s*(.+?)\s+([\d\s]+?)\s+([\d\s]+)\s*Ø")
    multiplicateur = 100 + int(pourcentage)
    
    for ligne in lignes:
        ligne_propre = ligne.strip()
        if not ligne_propre or "Ø" not in ligne_propre:
            continue
            
        match = pattern.search(ligne_propre)
        if match:
            nom_bien = match.group(1).strip()
            qte_str = re.sub(r"\s+", "", match.group(2))
            val_totale_str = re.sub(r"\s+", "", match.group(3))
            
            if qte_str.isdigit() and val_totale_str.isdigit():
                quantite = int(qte_str)
                valeur_totale = int(val_totale_str)
                
                if quantite > 0:
                    # Arithmétique entière exacte (sans perte de précision sur les grands nombres)
                    prix_unitaire = valeur_totale // quantite
                    prix_revente = (prix_unitaire * multiplicateur) // 100
                    total_revente_lot = prix_revente * quantite
                    
                    resultats.append({
                        "Bâtiment": nom_bien,
                        "Quantité": f"{quantite:,}".replace(",", " "),
                        "Prix Unitaire (Base)": f"{prix_unitaire:,}".replace(",", " ") + " Ø",
                        f"Prix Revente (+{pourcentage}%)": f"{prix_revente:,}".replace(",", " ") + " Ø",
                        "Valeur à copier (sans espace)": str(prix_revente),
                        "Total Lot Revente": formater_monnaie_empire(total_revente_lot) + " Ø",
                        "_raw_revente": str(prix_revente)
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
            
            # Affichage du tableau principal
            st.dataframe(
                df_res[["Bâtiment", "Quantité", "Prix Unitaire (Base)", f"Prix Revente (+{marge_pourcent}%)", "Valeur à copier (sans espace)", "Total Lot Revente"]],
                use_container_width=True,
                hide_index=True
            )
            
            # Bloc de copie rapide en un clic
            st.markdown("---")
            st.subheader("📋 Copie rapide (cliquez sur l'icône à droite de chaque montant)")
            for item in donnees:
                c1, c2 = st.columns([2, 3])
                with c1:
                    st.markdown(f"**{item['Bâtiment']}** *(x{item['Quantité']})*")
                with c2:
                    st.code(item["_raw_revente"], language=None)
