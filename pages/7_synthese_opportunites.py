import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, recuperer_derniere_donnee_table

st.title("✨ Le Podium des Opportunités de l'Empire")
st.markdown("Analyse des projets les plus rentables basée sur les dernières données synchronisées dans le Cloud NoSQL.")

# 1. Extraction directe et unique depuis Firebase Cloud Firestore
with st.spinner("Analyse des tables Firebase..."):
    df_travaux = recuperer_derniere_donnee_table("travaux")
    df_materiaux = recuperer_derniere_donnee_table("materiaux")

# 2. Vérification de la présence des données en base
if df_travaux is None or df_materiaux is None or df_travaux.empty or df_materiaux.empty:
    st.error("🚨 Données Firebase incomplètes ou absentes. Veuillez lancer une synchronisation depuis l'Espace Administration ⚙️.")
else:
    st.caption(f"☁️ Source : Google Cloud Firestore | Éléments analysés : `{len(df_travaux)} chantiers`")

    try:
        # 3. Filtrage strict sur les projets de type CONSTRUCTION
        df_const = df_travaux[df_travaux["type_travaux"].str.upper() == "CONSTRUCTION"].copy()

        if df_const.empty:
            st.warning("⚠️ Aucun projet de construction disponible dans la base actuelle.")
        else:
            # 4. Création d'un dictionnaire des prix des matériaux (Terrains inclus)
            # Gère les clés de colonnes flexibles (name/nom, price/prix) selon la structure de votre base
            col_nom_mat = "nom" if "nom" in df_materiaux.columns else "name"
            col_prix_mat = "prix" if "prix" in df_materiaux.columns else "price"
            
            dict_materiaux = dict(zip(df_materiaux[col_nom_mat].str.upper(), df_materiaux[col_prix_mat]))

            # 5. Calcul du coût cumulé (Main d'œuvre + Terrain)
            rows_opportunites = []
            for _, r in df_const.iterrows():
                # Récupération flexible du terrain requis
                terrain_requis = r.get("terrain_requis", r.get("terrain_required", ""))
                if not terrain_requis:
                    continue
                    
                terrain_clean = str(terrain_requis).strip().upper()
                
                # Extraction des coûts financiers de base
                cout_main_oeuvre = int(r.get("cout_estime", r.get("estimated_cost", 0)))
                prix_du_terrain = int(dict_materiaux.get(terrain_clean, 0))
                
                cout_total = cout_main_oeuvre + prix_du_terrain
                nom_batiment = r.get("building_name", r.get("nom", "Infrastructure Inconnue"))

                rows_opportunites.append({
                    "Nom": nom_batiment,
                    "Cout_Total": cout_total,
                    "Terrain": terrain_requis
                })

            if not rows_opportunites:
                st.info("⚪ Aucun projet valide n'a pu être calculé avec les terrains requis actuels.")
            else:
                # 6. Génération et tri du DataFrame final
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
