import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre

st.title("🏗️ Analyse des Chantiers & Embellissements")
st.markdown("Identifiez les constructions les plus rentables de l'Empire en extrayant dynamiquement le prix et les charges des terrains.")

if not st.session_state.get("projets_charges", False):
    st.warning("⚠️ Veuillez d'abord coller vos fiches et cliquer sur le bouton de synchronisation sur la page d'accueil 🏠 avant d'utiliser cette page.")
else:
    brut_achat_loc = st.session_state.get("tab_projets_achat_loc", "")
    brut_construction = st.session_state.get("tab_projets_construction", "")
    brut_embellissement = st.session_state.get("tab_projets_embellissement", "")

    if not brut_achat_loc.strip() or not brut_construction.strip():
        st.info("💡 Veuillez remplir au moins le Cadre 5 (Achat/Location) et le Cadre 6 (Construction) sur l'accueil pour activer le comparateur.")
    else:
        try:
            # 1. Extraction des données du Cadre 5 (Achat du bien et Location)
            lignes_l = brut_achat_loc.strip().split('\n')
            
            # CORRECTION ICI : On teste uniquement la première ligne [0] et pas la liste complète
            idx_l = 0
            if lignes_l and len(lignes_l) > 0:
                if "description" in lignes_l[0].lower() or "prix" in lignes_l[0].lower():
                    idx_l = 1
            
            data_locatif = {}
            dictionnaire_terrains_dynamique = {}
            
            for l in lignes_l[idx_l:]:
                if not l.strip(): continue
                cols = [c.strip() for c in l.split('\t') if c.strip()]
                if len(cols) < 5: continue
                
                nom_item = cols[0]
                prix_brut = convertir_saisie_en_nombre(cols[1])
                loyer_brut = convertir_saisie_en_nombre(cols[2])
                charges_brutes = convertir_saisie_en_nombre(cols[3])
                impots_bruts = convertir_saisie_en_nombre(cols[4])
                
                data_locatif[nom_item] = {
                    "prix_marche": prix_brut,
                    "loyer": loyer_brut,
                    "charges": charges_brutes,
                    "impots": impots_bruts
                }
                
                nom_item_upper = nom_item.upper()
                if "TERRAIN" in nom_item_upper or "PARC" in nom_item_upper:
                    dictionnaire_terrains_dynamique[nom_item] = {
                        "prix": prix_brut,
                        "charges": charges_brutes,
                        "impots": impots_bruts
                    }

            # 2. Extraction des données du Cadre 6 (Construction)
            lignes_c = brut_construction.strip().split('\n')
            
            # CORRECTION ICI : Test sur la première ligne [0]
            idx_c = 0
            if lignes_c and len(lignes_c) > 0:
                if "bâtiment" in lignes_c[0].lower() or "terrain" in lignes_c[0].lower():
                    idx_c = 1
                    
            data_construction = {}
            for l in lignes_c[idx_c:]:
                if not l.strip(): continue
                cols = [c.strip() for c in l.split('\t') if c.strip()]
                if len(cols) < 4: continue
                nom = cols[0]
                data_construction[nom] = {
                    "terrain": cols[1],
                    "cout_chantier": convertir_saisie_en_nombre(cols[2]),
                    "duree_mois": convertir_saisie_en_nombre(cols[3])
                }

            # 3. Extraction des données du Cadre 7 (Embellissement)
            data_embellissement = {}
            if brut_embellissement.strip():
                lignes_e = brut_embellissement.strip().split('\n')
                
                # CORRECTION ICI : Test sur la première ligne [0]
                idx_e = 0
                if lignes_e and len(lignes_e) > 0:
                    if "bâtiment" in lignes_e[0].lower() or "coût" in lignes_e[0].lower():
                        idx_e = 1
                        
                for l in lignes_e[idx_e:]:
                    if not l.strip(): continue
                    cols = [c.strip() for c in l.split('\t') if c.strip()]
                    if len(cols) < 3: continue
                    nom = cols[0]
                    data_embellissement[nom] = {
                        "cout_e": convertir_saisie_en_nombre(cols[1]),
                        "duree_e": cols[2]
                    }

            # 4. Croisement et calculs financiers réels
            rows_comparatives = []
            for bat, c_info in data_construction.items():
                loc_info = data_locatif.get(bat, {"prix_marche": 0, "loyer": 0, "charges": 0, "impots": 0})
                emb_info = data_embellissement.get(bat, {"cout_e": 0, "duree_e": "0"})
                
                type_terrain = c_info["terrain"]
                t_frais = dictionnaire_terrains_dynamique.get(type_terrain, {"prix": 0, "charges": 0, "impots": 0})
                
                duree_chantier = c_info["duree_mois"]
                frais_terrain_pendant_chantier = (t_frais["charges"] + t_frais["impots"]) * duree_chantier
                
                cout_total_construction = c_info["cout_chantier"] + t_frais["prix"] + frais_terrain_pendant_chantier
                
                prix_marche = loc_info["prix_marche"]
                economie_construction = prix_marche - cout_total_construction if prix_marche > 0 else 0
                
                rev_net_mensuel = loc_info["loyer"] - loc_info["charges"] - loc_info["impots"]
                rev_net_annuel = rev_net_mensuel * 12
                renta_construction_reelle = (rev_net_annuel / cout_total_construction * 100) if cout_total_construction > 0 else 0

                rows_comparatives.append({
                    "Bâtiment": bat,
                    "Terrain Requis": type_terrain,
                    "Prix Marché RAW": prix_marche,
                    "Coût Réel Const RAW": cout_total_construction,
                    "Renta_Const_RAW": renta_construction_reelle,
                    "Prix Clé en Main (Achat)": formater_monnaie_empire(prix_marche) if prix_marche > 0 else "N/A",
                    "Coût Global Construction": formater_monnaie_empire(cout_total_construction),
                    "Économie vs Achat": formater_monnaie_empire(economie_construction) if prix_marche > 0 else "N/A",
                    "Rentabilité à la Const. (%)": renta_construction_reelle,
                    "Coût Embellissement": formater_monnaie_empire(emb_info["cout_e"]) if emb_info["cout_e"] > 0 else "Maximum",
                    "Durée Chantiers (mois)": duree_chantier
                })

            df_global = pd.DataFrame(rows_comparatives)

            # --- AFFICHAGE DU VERDICT DE LA HOLDING ---
            df_tri_renta = df_global.sort_values(by="Renta_Const_RAW", ascending=False)
            
            st.subheader("🏆 Verdict de la Holding")
            if not df_tri_renta.empty and df_tri_renta.iloc[0]["Renta_Const_RAW"] > 0:
                top_row = df_tri_renta.iloc[0]
                st.success(f"🚀 **Le bien le plus rentable à construire est : {top_row['Bâtiment']}**")
                
                c1, c2 = st.columns(2)
                with c1:
                    st.metric("Coût Global Réel (Terrain + Frais inclus)", top_row["Coût Global Construction"])
                    st.metric("Rentabilité Net Réelle", f"{top_row['Renta_Const_RAW']:.2f}%")
                with c2:
                    st.metric("Prix Clé en main Marché", top_row["Prix Clé en Main (Achat)"])
                    st.metric("Gain / Économie si construit", top_row["Économie vs Achat"])
            else:
                st.info("💡 Les calculs s'afficheront dès que vos grilles de loyers seront synchronisées.")

            # --- ANALYSE DÉTAILLÉE PAR INFRASTRUCTURE ---
            st.markdown("---")
            st.subheader("🔍 Analyse détaillée par infrastructure")
            choix_bat = st.selectbox("Sélectionnez un bâtiment pour simuler son opération :", options=sorted(list(data_construction.keys())))
            
            if choix_bat:
                row_focus = df_global[df_global["Bâtiment"] == choix_bat].iloc[0]
                bat_c_info = data_construction[choix_bat]
                
                t_focus = dictionnaire_terrains_dynamique.get(bat_c_info["terrain"], {"prix": 0, "charges": 0, "impots": 0})
                frais_dormants = (t_focus["charges"] + t_focus["impots"]) * bat_c_info["duree_mois"]
                
                with st.expander("🔍 Décomposition du coût de construction réel de ce bien", expanded=True):
                    st.write(f"• 🏗️ Devis Chantier de base : `{formater_monnaie_empire(bat_c_info['cout_chantier'])}`")
                    st.write(f"• 🗺️ Achat du terrain ({bat_c_info['terrain']}) [extrait du Cadre 5] : `{formater_monnaie_empire(t_focus['prix'])}`")
                    st.write(f"• ⏳ Charges ({t_focus['charges']}€) & Impôts ({t_focus['impots']}€) du terrain cumulés durant les {bat_c_info['duree_mois']} mois de travaux : `{formater_monnaie_empire(frais_dormants)}`")
                    st.write(f"➡️ **Coût Total Réel de l'Opération :** `{row_focus['Coût Global Construction']}`")

            # --- TABLEAU DE BORD GLOBAL ---
            st.markdown("---")
            st.subheader("📋 Vue d'ensemble comparative")
            recherche = st.text_input("Filtrer le tableau comparatif par mot-clé :", value="")
            df_filtre = df_tri_renta[df_tri_renta["Bâtiment"].str.contains(recherche, case=False)]
            
            df_affichage = df_filtre.copy()
            df_affichage["Rentabilité à la Const. (%)"] = df_affichage["Rentabilité à la Const. (%)"].apply(lambda x: f"{x:.2f}%")
            df_affichage = df_affichage.drop(columns=["Prix Marché RAW", "Coût Réel Const RAW", "Renta_Const_RAW"])
            
            st.dataframe(df_affichage, use_container_width=True)

        except Exception as e:
            st.error(f"⚠️ Erreur lors du croisement des fiches : {str(e)}")
