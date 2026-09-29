import streamlit as st
import pandas as pd
from utils import (
    formater_monnaie_empire, 
    recuperer_derniere_donnee_table
)

st.title("✨ Le Podium des Opportunités de l'Empire")
st.markdown("Analyse des projets les plus rentables basée sur les dernières données synchronisées dans le Cloud NoSQL.")

# 1. Extraction directe des tables nécessaires depuis Firebase Cloud Firestore
with st.spinner("Analyse des tables Firebase et de la configuration..."):
    df_travaux = recuperer_derniere_donnee_table("travaux")
    df_materiaux = recuperer_derniere_donnee_table("materiaux")
    df_config = recuperer_derniere_donnee_table("configuration")

# Initialisation des variables de configuration par défaut
taux_batiments = 0
taux_materiaux = 0
promos_perso = []
promos_entreprise = []

if df_config is not None and not df_config.empty:
    ligne_config = df_config.iloc[0]
    
    # Relevé des taux du promoteur
    taux_batiments = int(ligne_config.get("taux_promoteur_batiments", 0))
    taux_materiaux = int(ligne_config.get("taux_promoteur_materiaux", 0))
    
    # Relevé des listes de biens en promotion
    if "promos_perso" in ligne_config:
        promos_perso = [str(x).strip().upper() for x in ligne_config["promos_perso"] if x]
    if "promos_entreprise" in ligne_config:
        promos_entreprise = [str(x).strip().upper() for x in ligne_config["promos_entreprise"] if x]

# 2. Section d'affichage des informations de promotion relevées pour l'utilisateur
st.sidebar.markdown("### 🏛️ Statut du Promoteur")
st.sidebar.metric("Taux Promoteur Bâtiments", f"{taux_batiments}%")
st.sidebar.metric("Taux Promoteur Matériaux", f"{taux_materiaux}%")

if promos_perso or promos_entreprise:
    with st.sidebar.expander("🏷️ Voir les biens en promotion"):
        if promos_perso:
            st.markdown("**Promos Perso :**")
            for p in promos_perso: st.write(f"• {p}")
        if promos_entreprise:
            st.markdown("**Promos Entreprises :**")
            for e in promos_entreprise: st.write(f"• {e}")

# 3. Vérification de la présence des données de chantiers et matériaux en base
if df_travaux is None or df_materiaux is None or df_travaux.empty or df_materiaux.empty:
    st.error("🚨 Données Firebase incomplètes ou absentes. Veuillez lancer une synchronisation depuis l'Espace Administration ⚙️.")
else:
    st.caption(f"☁️ Source : Google Cloud Firestore | Éléments analysés : `{len(df_travaux)} chantiers`")

    try:
        # 4. Filtrage strict sur les projets de type CONSTRUCTION
        df_const = df_travaux[df_travaux["type_travaux"].str.upper() == "CONSTRUCTION"].copy()

        if df_const.empty:
            st.warning("⚠️ Aucun projet de construction disponible dans la base actuelle.")
        else:
            # 5. Création du dictionnaire des prix des matériaux
            col_nom_mat = "nom" if "nom" in df_materiaux.columns else "name"
            col_prix_mat = "prix" if "prix" in df_materiaux.columns else "price"
            dict_materiaux = dict(zip(df_materiaux[col_nom_mat].str.upper(), df_materiaux[col_prix_mat]))

            # 6. Calcul des coûts avec intégration des promotions relevées
            rows_opportunites = []
            for _, r in df_const.iterrows():
                terrain_requis = r.get("terrain_requis", r.get("terrain_required", ""))
                if not terrain_requis:
                    continue
                    
                terrain_clean = str(terrain_requis).strip().upper()
                nom_batiment = r.get("building_name", r.get("nom", "Infrastructure Inconnue"))
                nom_batiment_clean = str(nom_batiment).strip().upper()
                
                # Coûts de base (Bruts)
                cout_main_oeuvre = int(r.get("cout_estime", r.get("estimated_cost", 0)))
                prix_du_terrain = int(dict_materiaux.get(terrain_clean, 0))
                
                # 🔥 APPLICATION DES RÉDUCTIONS DU PROMOTEUR (CORRIGÉE)
                if taux_materiaux > 0:
                    prix_du_terrain = int(prix_du_terrain * (1 - (taux_materiaux / 100)))
                
                if nom_batiment_clean in promos_perso or nom_batiment_clean in promos_entreprise:
                    if taux_batiments > 0:
                        cout_main_oeuvre = int(cout_main_oeuvre * (1 - (taux_batiments / 100)))
                
                # Calcul final sécurisé contre les valeurs négatives
                cout_total = max(0, cout_main_oeuvre + prix_du_terrain)

                rows_opportunites.append({
                    "Nom": nom_batiment,
                    "Cout_Total": cout_total,
                    "Terrain": terrain_requis
                })

            if not rows_opportunites:
                st.info("⚪ Aucun projet valide n'a pu être calculé.")
            else:
                df_opportunites = pd.DataFrame(rows_opportunites).sort_values(by="Cout_Total", ascending=True)

                # --- 🏆 RENDU VISUEL : LE PODIUM (TOP 3) ---
                st.subheader("🏗️ Top 3 Projets de Construction Économiques")
                df_top3 = df_opportunites.head(3)
                
                cols_m = st.columns(3)
                medailles = ["🥇 1er", "🥈 2e", "🥉 3e"]
                
                for i, (_, r) in enumerate(df_top3.iterrows()):
                    with cols_m[i]: 
                        st.metric(
                            label=f"{medailles[i]} - {r['Nom']}", 
                            value=formater_monnaie_empire(r['Cout_Total']), 
                            delta=f"Terrain : {r['Terrain']}",
                            delta_color="off"
                        )

                # --- 📋 RENDU VISUEL : LE CLASSEMENT COMPLET ---
                st.markdown("---")
                with st.expander("📋 Visualiser le catalogue complet des opportunités du Monde 8", expanded=False):
                    df_complet_visuel = df_opportunites.copy()
                    df_complet_visuel["Coût Total Projet"] = df_complet_visuel["Cout_Total"].apply(formater_monnaie_empire)
                    
                    st.dataframe(
                        df_complet_visuel[["Nom", "Coût Total Projet", "Terrain"]], 
                        use_container_width=True, 
                        hide_index=True
                    )

    except Exception as e:
        st.error(f"⚠️ Erreur lors de l'exécution de l'algorithme d'opportunités : {e}")
