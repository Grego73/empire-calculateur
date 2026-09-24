import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre

st.title("🏗️ Analyse des Chantiers & Embellissements")
st.markdown("Identifiez les opérations les plus profitables de l'Empire en fonction de votre budget actuel et de la limite des 500M de biens.")

# Limite absolue du jeu
PLAFOND_MAX_BIENS = 500000000

def calculer_pourcentage_grands_nombres(numerateur_brut, denominateur_brut):
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
        st.info("💡 Veuillez remplir au moins le Cadre 5 (Achat/Location) and le Cadre 6 (Construction) sur l'accueil pour activer le comparateur.")
    else:
        try:
            # --- 💵 ZONE BUDGÉTAIRE DYNAMIQUE ---
            st.subheader("💰 1. Capacité d'Investissement de la Holding")
            saisie_capital = st.text_input("Saisissez votre budget disponible pour cette opération (ex: 50G, 10Z) :", value="10G", key="capital_input_6")
            capital_disponible = convertir_saisie_en_nombre(saisie_capital)
            st.caption(f"ℹ️ Enveloppe allouée aux chantiers : **{formater_monnaie_empire(capital_disponible)}**")
            st.markdown("---")

            # 1. Extraction des données du Cadre 5
            lignes_l = brut_achat_loc.strip().split('\n')
            idx_l = 0
            if "description" in brut_achat_loc.lower() or "prix" in brut_achat_loc.lower():
                idx_l = 1
            
            data_locatif = {}
            dictionnaire_terrains_dynamique = {}
            
            keyword_promo_global = st.session_state.get("nom_bien_promo", "").strip().upper()
            taux_promo_global = st.session_state.get("taux_reduction_promo", 0)
            
            for l in lignes_l[idx_l:]:
                if not l.strip(): continue
                cols = [c.strip() for c in l.split('\t') if c.strip()]
                if len(cols) < 5: continue
                
                nom_item = cols[0]
                contient_tag_etoile = "*" in cols[1]
                prix_brut = convertir_saisie_en_nombre(cols[1])
                
                if not contient_tag_etoile and keyword_promo_global and taux_promo_global > 0 and keyword_promo_global in nom_item.upper():
                    prix_brut = int(prix_brut / (1 - (taux_promo_global / 100)))
                
                loyer_brut = convertir_saisie_en_nombre(cols[2])
                charges_brutes = convertir_saisie_en_nombre(cols[3])
                impots_brutes = convertir_saisie_en_nombre(cols[4])
                
                data_locatif[nom_item] = {
                    "prix_marche": prix_brut,
                    "loyer": loyer_brut,
                    "charges": charges_brutes,
                    "impots": impots_brutes
                }
                
                if "TERRAIN" in nom_item.upper() or "PARC" in nom_item.upper():
                    dictionnaire_terrains_dynamique[nom_item] = {
                        "prix": prix_brut,
                        "charges": charges_brutes,
                        "impots": impots_brutes
                    }

            # 2. Extraction des données du Cadre 6
            lignes_c = brut_construction.strip().split('\n')
            idx_c = 0
            if "bâtiment" in brut_construction.lower() or "terrain" in brut_construction.lower():
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

            # 3. Extraction des données du Cadre 7
            data_embellissement = {}
            if brut_embellissement.strip():
                lignes_e = brut_embellissement.strip().split('\n')
                idx_e = 0
                if "bâtiment" in brut_embellissement.lower() or "coût" in brut_embellissement.lower():
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

            # 4. Croisement et calculs financiers volumétriques
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
                    verdict_plan = "🏗️ Construire" if cout_total_construction < prix_marche else "🛒 Acheter"
                else:
                    verdict_plan = "🏗️ Uniquement Const."
                
                # Règle volumétrique
                if cout_total_construction > 0 and capital_disponible > 0:
                    nb_chantiers_possibles = capital_disponible // cout_total_construction
                    if nb_chantiers_possibles > PLAFOND_MAX_BIENS:
                        nb_chantiers_possibles = PLAFOND_MAX_BIENS
                        statut_limite = "⚠️ Bride 500M"
                    else:
                        statut_limite = "💼 Budget"
                else:
                    nb_chantiers_possibles = 0
                    statut_limite = "Fonds insuffisants"

                rev_net_mensuel = loc_info["loyer"] - loc_info["charges"] - loc_info["impots"]
                rev_net_annuel = rev_net_mensuel * 12
                
                renta_construction_reelle = calculer_pourcentage_grands_nombres(rev_net_annuel, cout_total_construction)
                economie_individuelle = prix_marche - cout_total_construction if prix_marche > 0 else 0
                renta_patrimoniale_vs_valeur = calculer_pourcentage_grands_nombres(economie_individuelle, cout_total_construction)
                plus_value_globale_financee = economie_individuelle * nb_chantiers_possibles

                rows_comparatives.append({
                    "Bâtiment": bat,
                    "Terrain Requis": type_terrain,
                    "Plus_Value_Tri": plus_value_globale_financee,
                    "Prix Marché RAW": prix_marche,
                    "Renta_Const_RAW": renta_construction_reelle,
                    "Renta_Patrimoniale_RAW": renta_patrimoniale_vs_valeur,
                    
                    "Achat Marché (Unitaire)": formater_monnaie_empire(prix_marche) if prix_marche > 0 else "N/A",
                    "Coût Global Construction": formater_monnaie_empire(cout_total_construction),
                    "Arbitrage": verdict_plan,
                    "Volume de Chantiers": nb_chantiers_possibles,
                    "Facteur Bride": statut_limite,
                    "Plus-Value Totale Financée RAW": plus_value_globale_financee,
                    "Plus-Value Totale Financée": formater_monnaie_empire(plus_value_globale_financee) if prix_marche > 0 else "N/A",
                    "Rentabilité Locative (%)": renta_construction_reelle,
                    "Rentabilité/Valeur (%)": renta_patrimoniale_vs_valeur,
                    "Coût Embellissement": emb_info["cout_e"],
                    "Durée Chantiers (mois)": duree_chantier
                })

            df_global = pd.DataFrame(rows_comparatives)
            df_tri_renta = df_global.sort_values(by="Plus_Value_Tri", ascending=False)

            # --- VERDICT ---
            st.subheader("🏆 Verdict de la Holding")
            if not df_tri_renta.empty and df_tri_renta.iloc[0]["Renta_Const_RAW"] > 0:
                top_row = df_tri_renta.iloc[0]
                st.success(f"🚀 **Le projet de chantiers le plus profitable pour vos capitaux est : {top_row['Bâtiment']}**")

                c1, c2 = st.columns(2)
                with c1:
                    vol_format = f"{top_row['Volume de Chantiers']:,}".replace(",", " ")
                    st.write(f"• Quantité maximale : {vol_format} unités ({top_row['Facteur Bride']})")
                    st.metric("Plus-Value Générée Finale", top_row["Plus-Value Totale Financée"])
                with c2:
                    st.metric("Coût d'un seul chantier", top_row["Coût Global Construction"])
                    st.metric("Marge unitaire sur valeur", f"{top_row['Renta_Patrimoniale_RAW']:.2f}%")
            else:
                st.info("💡 Les calculs s'afficheront dès que vos grilles de prix seront synchronisées.")

            # --- DISPOSITIF DE RECHERCHE ET FOCUS ---
            st.markdown("---")
            st.subheader("🔍 Analyse détaillée par infrastructure")
            choix_bat = st.selectbox("Sélectionnez un bâtiment pour simuler son opération :", options=sorted(list(data_construction.keys())))
            
            if choix_bat:
                row_focus = df_global[df_global["Bâtiment"] == choix_bat].iloc[0]
                bat_c_info = data_construction[choix_bat]
                l_focus = data_locatif.get(choix_bat, {"prix_marche": 0, "loyer": 0, "charges": 0, "impots": 0})
                focus_net_mensuel = l_focus["loyer"] - l_focus["charges"] - l_focus["impots"]
                focus_net_annuel = focus_net_mensuel * 12
                t_focus = dictionnaire_terrains_dynamique.get(bat_c_info["terrain"], {"prix": 0, "charges": 0, "impots": 0})
                frais_dormants = (t_focus["charges"] + t_focus["impots"]) * bat_c_info["duree_mois"]
                
                with st.expander("🔍 Décomposition du coût de construction réel de ce bien", expanded=True):
                    st.write(f"• 🏗️ Devis Chantier : {formater_monnaie_empire(bat_c_info['cout_chantier'])}")
                    st.write(f"• 🗺️ Achat Terrain ({bat_c_info['terrain']}) : {formater_monnaie_empire(t_focus['prix'])}")
                    st.write(f"• ⏳ Frais terrain dormants ({bat_c_info['duree_mois']} mois) : {formater_monnaie_empire(frais_dormants)}")
                    st.write(f"➡️ Coût Total Réel (Unitaire) : {row_focus['Coût Global Construction']}")
                
                st.markdown("---")
                st.write(f"• 🛒 Prix d'Achat Marché clé en main : {row_focus['Achat Marché (Unitaire)']}")
                prix_marche_raw = row_focus['Prix Marché RAW']
                
                if prix_marche_raw > 0:
                    renta_achat = calculer_pourcentage_grands_nombres(focus_net_annuel, prix_marche_raw)
                    st.write(f" * Rendement Locatif Marché : {renta_achat:.2f}%")
                    st.write(f" * Rendement Locatif Chantier : {row_focus['Rentabilité Locative (%)']:.2f}%")
                    gain_brut = prix_marche_raw - (bat_c_info['cout_chantier'] + t_focus['prix'] + frais_dormants)
                    
                    if gain_brut > 0:
                        st.markdown(f"🟢 Bilan : L'auto-construction économise {formater_monnaie_empire(gain_brut)} / unité ({row_focus['Rentabilité/Valeur (%)']:.2f}% de plus-value).")
                    else:
                        st.markdown(f"🔴 Bilan : L'achat direct marché est moins cheap de {formater_monnaie_empire(abs(gain_brut))} !")

            # --- GRAND TABLEAU FINAL ---
            st.markdown("---")
            st.subheader("📋 Vue d'ensemble comparative")
            recherche = st.text_input("Filtrer par mot-clé :", value="", key="recherche_6")
            df_filtre = df_tri_renta[df_tri_renta["Bâtiment"].str.contains(recherche, case=False)]
            df_affichage = df_filtre.copy()
            df_affichage["Rentabilité Locative (%)"] = df_affichage["Rentabilité Locative (%)"].apply(lambda x: f"{x:.2f}%")
            df_affichage["Rentabilité/Valeur (%)"] = df_affichage["Rentabilité/Valeur (%)"].apply(lambda x: f"{x:.2f}%")
            df_affichage["Volume de Chantiers"] = df_affichage["Volume de Chantiers"].apply(lambda x: f"{x:,}".replace(",", " "))
            df_affichage["Coût Embellissement"] = df_affichage["Coût Embellissement"].apply(lambda x: formater_monnaie_empire(x) if x > 0 else "Maximum")
            df_affichage = df_affichage.drop(columns=["Prix Marché RAW", "Plus_Value_Tri", "Renta_Const_RAW", "Renta_Patrimoniale_RAW", "Plus-Value Totale Financée RAW"])
            st.dataframe(df_affichage, use_container_width=True)

        except Exception as e:
            st.error(f"⚠️ Erreur lors du croisement des fiches : {str(e)}")
