import streamlit as st
import pandas as pd
import re
from utils import formater_monnaie_empire, convertir_saisie_en_nombre

st.title("🏗️ Analyse des Chantiers & Embellissements")
st.markdown("Identifiez les constructions les plus rentables de l'Empire en extrayant dynamiquement le prix et les charges des terrains.")

def calculer_pourcentage_grands_nombres(numerateur_brut, denominateur_brut):
    """
    Sécurité anti-bug : Réduit l'échelle des nombres géants de l'Empire
    avant la division pour éviter les pourcentages aberrants en milliards.
    """
    if denominateur_brut <= 0:
        return 0.0
    try:
        str_num = str(abs(int(numerateur_brut)))
        str_den = str(abs(int(denominateur_brut)))
        max_len = max(len(str_num), len(str_den))
        
        if max_len > 10:
            facteur = 10 ** (max_len - 7)
            num_reduit = float(int(numerateur_brut) // facteur)
            den_reduit = float(int(denominateur_brut) // facteur)
            return (num_reduit / den_reduit * 100) if den_reduit > 0 else 0.0
        
        return float(numerateur_brut) / float(denominateur_brut) * 100
    except:
        return 0.0

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
            # 1. Extraction des données du Cadre 5
            lignes_l = brut_achat_loc.strip().split('\n')
            idx_l = 0
            if lignes_l and len(lignes_l) > 0:
                if "description" in lignes_l.lower() or "prix" in lignes_l.lower():
                    idx_l = 1
            
            data_locatif = {}
            dictionnaire_terrains_dynamique = {}
            
            for l in lignes_l[idx_l:]:
                if not l.strip(): continue
                cols = [c.strip() for c in l.split('\t') if c.strip()]
                if len(cols) < 5: continue
                
                nom_item = cols
                prix_brut = convertir_saisie_en_nombre(cols)
                loyer_brut = convertir_saisie_en_nombre(cols)
                charges_brutes = convertir_saisie_en_nombre(cols)
                impots_bruts = convertir_saisie_en_nombre(cols)
                
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

            # 2. Extraction des données du Cadre 6
            lignes_c = brut_construction.strip().split('\n')
            idx_c = 0
            if lignes_c and len(lignes_c) > 0:
                if "bâtiment" in lignes_c.lower() or "terrain" in lignes_c.lower():
                    idx_c = 1
                    
            data_construction = {}
            for l in lignes_c[idx_c:]:
                if not l.strip(): continue
                cols = [c.strip() for c in l.split('\t') if c.strip()]
                if len(cols) < 4: continue
                nom = cols
                data_construction[nom] = {
                    "terrain": cols,
                    "cout_chantier": convertir_saisie_en_nombre(cols),
                    "duree_mois": convertir_saisie_en_nombre(cols)
                }

            # 3. Extraction des données du Cadre 7
            data_embellissement = {}
            if brut_embellissement.strip():
                lignes_e = brut_embellissement.strip().split('\n')
                idx_e = 0
                if lignes_e and len(lignes_e) > 0:
                    if "bâtiment" in lignes_e.lower() or "coût" in lignes_e.lower():
                        idx_e = 1
                        
                for l in lignes_e[idx_e:]:
                    if not l.strip(): continue
                    cols = [c.strip() for c in l.split('\t') if c.strip()]
                    if len(cols) < 3: continue
                    nom = cols
                    data_embellissement[nom] = {
                        "cout_e": convertir_saisie_en_nombre(cols),
                        "duree_e": cols
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
                
                if prix_marche > 0:
                    if cout_total_construction < prix_marche:
                        verdict_plan = "🏗️ Construire (Moins cher)"
                    else:
                        verdict_plan = "🛒 Acheter (Moins cher)"
                else:
                    verdict_plan = "🏗️ Construction Seule"
                
                rev_net_mensuel = loc_info["loyer"] - loc_info["charges"] - loc_info["impots"]
                rev_net_annuel = rev_net_mensuel * 12
                
                renta_construction_reelle = calculer_pourcentage_grands_nombres(rev_net_annuel, cout_total_construction)
                economie_construction = prix_marche - cout_total_construction if prix_marche > 0 else 0
                renta_patrimoniale_vs_valeur = calculer_pourcentage_grands_nombres(economie_construction, cout_total_construction)

                rows_comparatives.append({
                    "Bâtiment": bat,
                    "Terrain Requis": type_terrain,
                    "Renta_Const_RAW": renta_construction_reelle,
                    "Renta_Patrimoniale_RAW": renta_patrimoniale_vs_valeur,
                    
                    # CORRECTION MAJEURE : On envoie les valeurs en VRAIS nombres (float) pour que le tri soit 100% numérique
                    "Clé en Main (Achat)": float(prix_marche),
                    "Coût Global Construction": float(cout_total_construction),
                    "Plan le moins cher": verdict_plan,
                    "Économie vs Achat": float(economie_construction),
                    
                    "Rentabilité Locative (%)": renta_construction_reelle,
                    "Rentabilité/Valeur (%)": renta_patrimoniale_vs_valeur,
                    "Coût Embellissement": float(emb_info["cout_e"]),
                    "Durée Chantiers (mois)": duree_chantier
                })

            df_global = pd.DataFrame(rows_comparatives)
            
            # Tri initial par économie décroissante
            df_tri_renta = df_global.sort_values(by="Économie vs Achat", ascending=False)

            # --- VERDICT DE LA HOLDING ---
            st.subheader("🏆 Verdict de la Holding")
            if not df_tri_renta.empty and df_tri_renta.iloc["Renta_Const_RAW"] > 0:
                top_row = df_tri_renta.iloc
                st.success(f"🚀 **Le bien le plus rentable à construire est : {top_row['Bâtiment']}**")
                
                c1, c2 = st.columns(2)
                with c1:
                    st.metric("Coût Global Réel (Frais inclus)", formater_monnaie_empire(top_row["Coût Global Construction"]))
                    st.metric("Rentabilité Locative Net", f"{top_row['Renta_Const_RAW']:.2f}%")
                with c2:
                    st.metric("Prix Clé en main Marché", formater_monnaie_empire(top_row["Clé en Main (Achat)"]))
                    st.metric("Plus-Value à la construction", f"{top_row['Renta_Patrimoniale_RAW']:.2f}%")
            else:
                st.info("💡 Les calculs s'afficheront dès que vos grilles de loyers seront synchronisées.")

            # --- ANALYSE DÉTAILLÉE PAR INFRASTRUCTURE ---
            st.markdown("---")
            st.subheader("🔍 Analyse détaillée par infrastructure")
            choix_bat = st.selectbox("Sélectionnez un bâtiment pour simuler son opération :", options=sorted(list(data_construction.keys())))
            
            if choix_bat:
                row_focus = df_global[df_global["Bâtiment"] == choix_bat].iloc
                bat_c_info = data_construction[choix_bat]
                l_focus = data_locatif.get(choix_bat, {"prix_marche": 0, "loyer": 0, "charges": 0, "impots": 0})
                
                focus_net_mensuel = l_focus["loyer"] - l_focus["charges"] - l_focus["impots"]
                focus_net_annuel = focus_net_mensuel * 12
                t_focus = dictionnaire_terrains_dynamique.get(bat_c_info["terrain"], {"prix": 0, "charges": 0, "impots": 0})
                frais_dormants = (t_focus["charges"] + t_focus["impots"]) * bat_c_info["duree_mois"]
                
                with st.expander("🔍 Décomposition du coût de construction réel de ce bien", expanded=True):
                    st.write(f"• 🏗️ Devis Chantier de base : `{formater_monnaie_empire(bat_c_info['cout_chantier'])}`")
                    st.write(f"• 🗺️ Achat du terrain ({bat_c_info['terrain']}) [extrait du Cadre 5] : `{formater_monnaie_empire(t_focus['prix'])}`")
                    st.write(f"• ⏳ Charges ({t_focus['charges']}€) & Impôts ({t_focus['impots']}€) du terrain cumulés durant les {bat_c_info['duree_mois']} mois de travaux : `{formater_monnaie_empire(frais_dormants)}`")
                    st.write(f"➡️ **Coût Total Réel de l'Opération (Construction) :** `{formater_monnaie_empire(row_focus['Coût Global Construction'])}`")
                    
                    st.markdown("---")
                    st.write(f"• 🛒 **Prix clé en main (Achat direct sur le marché) :** `{formater_monnaie_empire(row_focus['Clé en Main (Achat)'])}`")
                    
                    prix_marche_raw = row_focus['Clé en Main (Achat)']
                    if prix_marche_raw > 0:
                        renta_achat = calculer_pourcentage_grands_nombres(focus_net_annuel, prix_marche_raw)
                        st.write(f"   * *Rendement Locatif si acheté sur le marché : {renta_achat:.2f}%*")
                        st.write(f"   * *Rendement Locatif si construit de A à Z : {row_focus['Rentabilité Locative (%)']:.2f}%*")
                        
                        gain_brut = prix_marche_raw - (bat_c_info['cout_chantier'] + t_focus['prix'] + frais_dormants)
                        if gain_brut > 0:
                            st.markdown(f"🟢 **Bilan : Auto-construire vous fait économiser `{formater_monnaie_empire(gain_brut)}` ({row_focus['Rentabilité/Valeur (%)']:.2f}% de plus-value) !**")
                        else:
                            st.markdown(f"🔴 **Bilan : L'achat direct est moins cher de `{formater_monnaie_empire(abs(gain_brut))}` !**")
                    else:
                        st.write("• ⚠️ Aucun prix d'achat trouvé sur le marché pour ce bien dans le Cadre 5.")

            # --- TABLEAU DE BORD GLOBAL ---
            st.markdown("---")
            st.subheader("📋 Vue d'ensemble comparative")
            recherche = st.text_input("Filtrer le tableau comparatif par mot-clé :", value="", key="recherche_6")
            df_filtre = df_tri_renta[df_tri_renta["Bâtiment"].str.contains(recherche, case=False)]
            
            df_affichage = df_filtre.copy()
            
            # Application des pourcentages
            df_affichage["Rentabilité Locative (%)"] = df_affichage["Rentabilité Locative (%)"].apply(lambda x: f"{x:.2f}%")
            df_affichage["Rentabilité/Valeur (%)"] = df_affichage["Rentabilité/Valeur (%)"].apply(lambda x: f"{x:.2f}%")
            
            # Reformatage textuel final des montants géants pour l'affichage visuel
            df_affichage["Clé en Main (Achat)"] = df_affichage["Clé en Main (Achat)"].apply(lambda x: formater_monnaie_empire(x) if x > 0 else "N/A")
            df_affichage["Coût Global Construction"] = df_affichage["Coût Global Construction"].apply(formater_monnaie_empire)
            df_affichage["Économie vs Achat"] = df_affichage["Économie vs Achat"].apply(formater_monnaie_empire)
            df_affichage["Coût Embellissement"] = df_affichage["Coût Embellissement"].apply(lambda x: formater_monnaie_empire(x) if x > 0 else "Maximum")
            
            # Nettoyage des colonnes techniques internes
            df_affichage = df_affichage.drop(columns=["Renta_Const_RAW", "Renta_Patrimoniale_RAW"])
            
            # Rendu final stable qui maintient l'ordre numérique calculé en amont
            st.dataframe(df_affichage, use_container_width=True)

        except Exception as e:
            st.error(f"⚠️ Erreur lors du croisement des fiches : {str(e)}")

