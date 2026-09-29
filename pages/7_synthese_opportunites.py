import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, recuperer_derniere_donnee_table

st.title("✨ Le Podium des Opportunités de l'Empire")
st.markdown("Analyse des projets les plus rentables basée sur les dernières données synchronisées dans le Cloud NoSQL.")

# 1. Extraction des données Firebase Cloud Firestore
with st.spinner("Analyse des tables Firebase et de la configuration..."):
    df_travaux = recuperer_derniere_donnee_table("travaux")
    df_materiaux = recuperer_derniere_donnee_table("materiaux")
    df_config = recuperer_derniere_donnee_table("configuration")

# Initialisation des variables de configuration
taux_batiments = 0
taux_materiaux = 0
promos_perso = []
promos_entreprise = []

if df_config is not None and not df_config.empty:
    ligne_config = df_config.iloc[0]
    
    # Récupération des taux
    taux_batiments = int(ligne_config.get("taux_promoteur_batiments", 0))
    taux_materiaux = int(ligne_config.get("taux_promoteur_materiaux", 0))
    
    # Récupération des listes de biens en promotion
    if "promos_perso" in ligne_config:
        promos_perso = [str(x).strip() for x in ligne_config["promos_perso"] if x]
    if "promos_entreprise" in ligne_config:
        promos_entreprise = [str(x).strip() for x in ligne_config["promos_entreprise"] if x]

# =========================================================
# 📊 SECTION VISUELLE : LES GRAPHISTES DE TAUX DU PROMOTEUR
# =========================================================
st.subheader("🏛️ État des Taux du Promoteur")

col_g1, col_g2 = st.columns(2)

with col_g1:
    st.markdown(f"**Taux Promoteur Bâtiment : `{taux_batiments}%`**")
    # Création d'un graphique à barres horizontal pour faire office de jauge de progression
    df_jauge_bat = pd.DataFrame({"Taux (%)": [taux_batiments]}, index=["Bâtiment"])
    st.bar_chart(df_jauge_bat, x_label="", y_label="Pourcentage", color="#FF4B4B", use_container_width=True)

with col_g2:
    st.markdown(f"**Taux Promoteur Matériau : `{taux_materiaux}%`**")
    # Création du deuxième graphique pour le taux matériau
    df_jauge_mat = pd.DataFrame({"Taux (%)": [taux_materiaux]}, index=["Matériau"])
    st.bar_chart(df_jauge_mat, x_label="", y_label="Pourcentage", color="#00C49F", use_container_width=True)


# =========================================================
# 🏷️ SECTION RECHERCHE : BIENS EN PROMOTION DETECTES
# =========================================================
st.markdown("---")
st.subheader("🏷️ Biens actuellement en Promotion")

cp1, cp2 = st.columns(2)

with cp1:
    st.markdown("##### 📦 Promos Perso")
    if promos_perso:
        for p in promos_perso:
            st.markdown(f"• ✨ **{p}**")
    else:
        st.info("⚪ Aucun bien personnel en promotion actuellement.")

with cp2:
    st.markdown("##### 🏢 Promos Entreprise")
    if promos_entreprise:
        for e in promos_entreprise:
            st.markdown(f"• 💼 **{e}**")
    else:
        st.info("⚪ Aucun bien d'entreprise en promotion actuellement.")


# =========================================================
# 🏆 SECTION ALGORITHME : CALCUL ET CALCULATEUR DU PODIUM
# =========================================================
st.markdown("---")

if df_travaux is None or df_materiaux is None or df_travaux.empty or df_materiaux.empty:
    st.error("🚨 Données Firebase incomplètes ou absentes pour le calcul du podium.")
else:
    try:
        # Filtrage des constructions
        df_const = df_travaux[df_travaux["type_travaux"].str.upper() == "CONSTRUCTION"].copy()

        if not df_const.empty:
            # Dictionnaire des prix des matériaux
            col_nom_mat = "nom" if "nom" in df_materiaux.columns else "name"
            col_prix_mat = "prix" if "prix" in df_materiaux.columns else "price"
            dict_materiaux = dict(zip(df_materiaux[col_nom_mat].str.upper(), df_materiaux[col_prix_mat]))

            # Listes en majuscules pour une comparaison robuste
            promos_perso_upper = [x.upper() for x in promos_perso]
            promos_entreprise_upper = [x.upper() for x in promos_entreprise]

            rows_opportunites = []
            for _, r in df_const.iterrows():
                terrain_requis = r.get("terrain_requis", r.get("terrain_required", ""))
                if not terrain_requis:
                    continue
                
                terrain_clean = str(terrain_requis).strip().upper()
                nom_batiment = r.get("building_name", r.get("nom", "Infrastructure Inconnue"))
                nom_batiment_clean = str(nom_batiment).strip().upper()
                
                # Prix de base bruts
                cout_main_oeuvre = int(r.get("cout_estime", r.get("estimated_cost", 0)))
                prix_du_terrain = int(dict_materiaux.get(terrain_clean, 0))
                
                # 🛠️ LOGIQUE CORRIGÉE : Application sélective des promotions
                # 1. Le taux matériau s'applique globalement sur les terrains
                if taux_materiaux > 0:
                    prix_du_terrain = int(prix_du_terrain * (1 - (taux_materiaux / 100)))
                
                # 2. Le taux bâtiment s'applique UNIQUEMENT si le nom est dans les listes de promos relevées
                if nom_batiment_clean in promos_perso_upper or nom_batiment_clean in promos_entreprise_upper:
                    if taux_batiments > 0:
                        cout_main_oeuvre = int(cout_main_oeuvre * (1 - (taux_batiments / 100)))

                cout_total = max(1, cout_main_oeuvre + prix_du_terrain)

                rows_opportunites.append({
                    "Nom": nom_batiment,
                    "Cout_Total": cout_total,
                    "Terrain": terrain_requis
                })

            if rows_opportunites:
                df_opportunites = pd.DataFrame(rows_opportunites).sort_values(by="Cout_Total", ascending=True)

                st.subheader("🏗️ Top 3 Projets de Construction Économiques (Prix Réduits inclus)")
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

                with st.expander("📋 Visualiser le catalogue complet des opportunités triées"):
                    df_complet_visuel = df_opportunites.copy()
                    df_complet_visuel["Coût Total Projet"] = df_complet_visuel["Cout_Total"].apply(formater_monnaie_empire)
                    st.dataframe(
                        df_complet_visuel[["Nom", "Coût Total Projet", "Terrain"]], 
                        use_container_width=True, 
                        hide_index=True
                    )
    except Exception as e:
        st.error(f"⚠️ Erreur lors du calcul des opportunités : {e}")
