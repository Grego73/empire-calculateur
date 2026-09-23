import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre

st.title("🏗️ Chantiers & Embellissements")
st.markdown("Comparez dynamiquement les coûts et les durées de vos projets de construction et de rénovation.")

if not st.session_state.get("projets_charges", False):
    st.warning("⚠️ Veuillez d'abord coller vos fiches et cliquer sur le bouton de synchronisation sur la page d'accueil 🏠 avant d'utiliser cette page.")
else:
    # Récupération des deux blocs saisis sur l'accueil
    brut_construction = st.session_state.get("tab_projets_construction", "")
    brut_embellissement = st.session_state.get("tab_projets_embellissement", "")
    if not brut_construction.strip() or not brut_embellissement.strip():
        st.info("💡 Pour utiliser ce comparateur, veillez à remplir à la fois le bloc 5 (Construction) et le bloc 6 (Embellissement) sur la page d'accueil.")
    else:
        try:
            # 1. Parsing du tableau Construction
            lignes_c = brut_construction.strip().split('\n')
            idx_c = 1 if "bâtiment" in lignes_c[0].lower() or "terrain" in lignes_c[0].lower() else 0
            
            data_construction = {}
            for l in lignes_c[idx_c:]:
                if not l.strip(): continue
                cols = [c.strip() for c in l.split('\t') if c.strip()]
                if len(cols) < 4: continue
                
                nom_batiment = cols[0]
                data_construction[nom_batiment] = {
                    "terrain": cols[1],
                    "cout_c": convertir_saisie_en_nombre(cols[2]),
                    "duree_c": cols[3]
                }

            # 2. Parsing du tableau Embellissement
            lignes_e = brut_embellissement.strip().split('\n')
            idx_e = 1 if "bâtiment" in lignes_e[0].lower() or "coût" in lignes_e[0].lower() else 0
            
            data_embellissement = {}
            for l in lignes_e[idx_e:]:
                if not l.strip(): continue
                cols = [c.strip() for c in l.split('\t') if c.strip()]
                if len(cols) < 3: continue
                
                nom_batiment = cols[0]
                data_embellissement[nom_batiment] = {
                    "cout_e": convertir_saisie_en_nombre(cols[1]),
                    "duree_e": cols[2]
                }

            # 3. Fusion et création du tableau comparatif
            rows_comparatives = []
            for bat, c_info in data_construction.items():
                e_info = data_embellissement.get(bat, {"cout_e": 0, "duree_e": "0"})
                
                rows_comparatives = rows_comparatives
                rows_comparatives.append({
                    "Nom de l'Infrastructure": bat,
                    "Terrain requis": c_info["terrain"],
                    "Coût Construction RAW": c_info["cout_c"],
                    "Coût Construction": formater_monnaie_empire(c_info["cout_c"]),
                    "Durée Const. (j)": c_info["duree_c"],
                    "Coût Rénovation (Emb.)": formater_monnaie_empire(e_info["cout_e"]) if e_info["cout_e"] > 0 else "Niveau Max",
                    "Durée Emb. (j)": e_info["duree_e"]
                })

            df_global = pd.DataFrame(rows_comparatives)

            # Sélection par liste déroulante d'un seul bâtiment
            st.subheader("🔍 Focus sur un projet immobilier")
            choix_bat = st.selectbox("Sélectionnez un bâtiment pour isoler ses coûts :", options=sorted(list(data_construction.keys())))
            
            if choix_bat:
                c_focus = data_construction[choix_bat]
                e_focus = data_embellissement.get(choix_bat, {"cout_e": 0, "duree_e": "0"})
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("##### 🏗️ Plan Neuf")
                    st.caption(f"Terrain : {c_focus['terrain']}")
                    st.metric("Budget Chantier", formater_monnaie_empire(c_focus['cout_c']))
                    st.caption(f"Temps requis : {c_focus['duree_c']} jours")
                with col2:
                    st.markdown("##### 💅 Plan Rénovation / Embellissement")
                    if e_focus['cout_e'] > 0:
                        st.metric("Budget Amélioration", formater_monnaie_empire(e_focus['cout_e']))
                        st.caption(f"Temps requis : {e_focus['duree_e']} jours")
                    else:
                        st.write("🛑 Bâtiment au niveau maximum. Aucun embellissement listé dans votre fiche.")

            # Affichage du tableau complet filtrable
            st.markdown("---")
            st.subheader("📋 Vue d'ensemble comparative")
            recherche = st.text_input("Filtrer le grand tableau par mot-clé :", value="")
            df_filtre = df_global[df_global["Nom de l'Infrastructure"].str.contains(recherche, case=False)]
            
            df_affichage = df_filtre.sort_values(by="Coût Construction RAW", ascending=False).drop(columns=["Coût Construction RAW"])
            st.dataframe(df_affichage, use_container_width=True)

        except Exception as e:
            st.error(f"⚠️ Erreur lors du croisement des fiches chantiers : {str(e)}")
