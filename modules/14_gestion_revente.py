import streamlit as st
import pandas as pd
import re
from utils import formater_monnaie_empire

# Ordre officiel du catalogue (du premier au dernier bâtiment)
ORDRE_CATALOGUE = [
    "500m² de bureaux vides", "500m² de bureaux aménagés", "500m² de bureaux tout équipés", "500m² de bureaux grand standing",
    "1300m² de bureaux vides", "1300m² de bureaux aménagés", "1300m² de bureaux tout équipés", "1300m² de bureaux grand standing",
    "2100m² de bureaux vides", "2100m² de bureaux aménagés", "2100m² de bureaux tout équipés", "2100m² de bureaux grand standing",
    "3000m² de bureaux vides", "3000m² de bureaux aménagés", "3000m² de bureaux tout équipés", "3000m² de bureaux grand standing",
    "Immeuble d'entreprise vide", "Immeuble d'entreprise aménagé", "Immeuble d'entreprise tout équipé", "Immeuble d'entreprise grand standing",
    "Gratte-ciel vide", "Gratte-ciel aménagé", "Gratte-ciel tout équipé", "Gratte-ciel grand standing",
    "Local vide", "Local aménagé", "Local tout équipé", "Local de haut standing",
    "Grand local vide", "Grand local aménagé", "Grand local tout équipé", "Grand local de haut standing",
    "Espace commercial vide", "Espace commercial aménagé", "Espace commercial tout équipé", "Espace commercial de haut standing",
    "Centre commercial vide", "Centre commercial aménagé", "Centre commercial tout équipé", "Centre commercial de haut standing",
    "Atelier inexploitable", "Atelier utilisable", "Atelier équipé", "Atelier high-tech",
    "Entrepôt inexploitable", "Entrepôt utilisable", "Entrepôt équipé", "Entrepôt intégralement optimisé",
    "Usine inexploitable", "Usine utilisable", "Usine intégralement équipée", "Usine high-tech",
    "Centre industriel inexploitable", "Centre industriel utilisable", "Centre industriel tout équipé", "Centre industriel high-tech",
    "Petit terrain", "Terrain moyen", "Grand terrain", "Parc", "Grand parc",
    "Réseau FreeCycl' 5 arrêts", "Réseau FreeCycl' 10 arrêts", "Réseau FreeCycl' 15 arrêts", "Réseau FreeCycl' 20 arrêts",
    "Réseau de bus 10 arrêts", "Réseau de bus 25 arrêts", "Réseau de bus 50 arrêts", "Réseau de bus 100 arrêts",
    "Réseau de métro 1 ligne", "Réseau de métro 2 lignes", "Réseau de métro 3 lignes", "Réseau de métro 4 lignes",
    "Gare avec 2 terminaux", "Gare avec 4 terminaux", "Gare avec 10 terminaux", "Gare avec 20 terminaux",
    "Aéroport avec 1 piste", "Aéroport avec 3 pistes", "Aéroport avec 8 pistes", "Aéroport avec 15 pistes",
    "Plate-forme pétrolière vide", "Plate-forme pétrolière aménagée", "Plate-forme pétrolière améliorée", "Plate-forme pétrolière high-tech",
    "Centre de recherche désaffecté", "Centre de recherche régional", "Centre de recherche national", "Centre de recherche international",
    "Zone portuaire désaffectée", "Zone portuaire régionale", "Zone portuaire nationale", "Zone portuaire internationale",
    "Zone nucléaire désaffectée", "Zone nucléaire régionale", "Zone nucléaire nationale", "Zone nucléaire internationale",
    "Zone aérospatiale désaffectée", "Zone aérospatiale régionale", "Zone aérospatiale nationale", "Zone aérospatiale internationale",
    "Technopôle désaffecté", "Technopôle régional", "Technopôle national", "Technopôle international",
    "Technopôle millenium désaffecté", "Technopôle millenium régional", "Technopôle millenium national", "Technopôle millenium international",
    "Technopôle titanium désaffecté", "Technopôle titanium régional", "Technopôle titanium national", "Technopôle titanium international",
    "Technopôle palacium désaffecté", "Technopôle palacium régional", "Technopôle palacium national", "Technopôle palacium international",
    "Mégapôle millenium désaffecté", "Mégapôle millenium régional", "Mégapôle millenium national", "Mégapôle millenium international",
    "Mégapôle titanium désaffecté", "Mégapôle titanium régional", "Mégapôle titanium national", "Mégapôle titanium international",
    "Mégapôle palacium désaffecté", "Mégapôle palacium régional", "Mégapôle palacium national", "Mégapôle palacium international",
    "Station orbitale basique", "Station orbitale équipée", "Station orbitale hightech", "Station orbitale luxueuse"
]

INDEX_ORDRE = {nom.lower(): idx for idx, nom in enumerate(ORDRE_CATALOGUE)}

def obtenir_rang_catalogue(nom_batiment):
    # Nettoie un éventuel tag de promo (-14%, etc.) pour retrouver le nom exact
    nom_propre = re.sub(r"\s*-\d+%$", "", nom_batiment.strip()).lower()
    return INDEX_ORDRE.get(nom_propre, 9999)

# Récupération dynamique du pourcentage avant d'afficher le titre
marge_actuelle = st.session_state.get("input_marge_revente", 15)
signe = "+" if marge_actuelle >= 0 else ""

st.title(f"🏷️ Gestion Revente ({signe}{marge_actuelle} %)")
st.markdown(
    f"Collez directement le tableau de vos propriétés depuis la page **Immobilisation** d'Empire Immo. "
    f"Le module classe vos biens selon **l'ordre officiel du catalogue** et calcule le prix de revente ajusté de **{signe}{marge_actuelle} % (arrondi à l'inférieur)**."
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
                    "_raw_total_lot": total_revente_lot,
                    "_ordre": obtenir_rang_catalogue(nom_bien)
                })
                
    # Tri selon l'ordre exact du catalogue
    resultats.sort(key=lambda x: x["_ordre"])
    return resultats

if st.button("🧮 Calculer les prix de revente", type="primary", use_container_width=True, key="btn_calcul_revente"):
    if not texte_proprietes.strip():
        st.warning("⚠️ Veuillez coller la liste de vos propriétés avant de lancer le calcul.")
    else:
        donnees = analyser_lignes_proprietes(texte_proprietes, marge_pourcent)
        
        if not donnees:
            st.error("❌ Aucun bâtiment reconnu. Vérifiez que les lignes contiennent bien le nom, la quantité et la valeur suivie de 'Ø'.")
        else:
            st.success(f"✅ {len(donnees)} bâtiment(s) analysé(s) et classé(s) selon l'ordre du catalogue !")
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
