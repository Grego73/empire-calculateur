import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre

st.title("📊 Analyse Locative & Rendements")
st.markdown("Optimisez vos investissements en fonction de votre trésorerie actuelle et de la limite absolue des 500M de biens.")

# Limite absolue du jeu
PLAFOND_MAX_BIENS = 500000000

if not st.session_state.get("projets_charges", False):
    st.warning("⚠️ Veuillez d'abord coller vos fiches et cliquer sur le bouton de synchronisation sur la page d'accueil 🏠 avant d'utiliser cette page.")
else:
    donnees_brutes = st.session_state.get("tab_projets_achat_loc", "")

    if not donnees_brutes.strip():
        st.info("💡 Le bloc 5 (Achat du bien et Location) est vide sur la page d'accueil. Collez-y vos données pour activer l'analyse.")
    else:
        try:
            # --- 💵 ZONE FINANCIÈRE DYNAMIQUE ---
            st.subheader("💰 1. Capacité Financière de la Holding")
            saisie_capital = st.text_input("Saisissez votre budget ou trésorerie disponible (ex: 500M, 10G, 5.5Z) :", value="10G", key="capital_input_5")
            capital_disponible = convertir_saisie_en_nombre(saisie_capital)
            st.caption(f"ℹ️ Capital interprété par la Holding : **{formater_monnaie_empire(capital_disponible)}**")
            st.markdown("---")

            lignes = donnees_brutes.strip().split('\n')
            idx_l = 0
            if "description" in donnees_brutes.lower() or "prix" in donnees_brutes.lower():
                idx_l = 1

            rows = []
            for ligne in lignes[idx_l:]:
                if not ligne.strip(): continue
                colonnes = [c.strip() for c in ligne.split('\t') if c.strip()]
                if len(colonnes) < 5: continue
                
                desc = colonnes[0] # Extraction du texte pur
                prix = convertir_saisie_en_nombre(colonnes[1])
                loyer = convertir_saisie_en_nombre(colonnes[2])
                charges = convertir_saisie_en_nombre(colonnes[3])
                impots = convertir_saisie_en_nombre(colonnes[4])
                
                # Exclusion des terrains et parcs qui n'ont pas de loyer
                if "TERRAIN" in desc.upper() or "PARC" in desc.upper(): continue
                
                rev_net_mensuel = loyer - charges - impots
                rev_net_annuel = rev_net_mensuel * 12
                renta_nette = (rev_net_annuel / prix * 100) if prix > 0 else 0
                
                # Calculs basés sur votre budget
                if prix > 0 and capital_disponible > 0:
                    nb_biens_possibles = capital_disponible // prix
                    if nb_biens_possibles > PLAFOND_MAX_BIENS:
                        nb_biens_possibles = PLAFOND_MAX_BIENS
                        statut_limite = "⚠️ Bridé par la place (500M)"
                    else:
                        statut_limite = "💵 Limité par votre budget"
                    gain_mensuel_total = rev_net_mensuel * nb_biens_possibles
                else:
                    nb_biens_possibles = 0
                    gain_mensuel_total = 0
                    statut_limite = "Budget insuffisant"

                if rev_net_annuel > 0:
                    annees_roi = prix / rev_net_annuel
                    roi_texte = f"{int(annees_roi)} ans, {int((annees_roi - int(annees_roi)) * 12)} m"
                else:
                    roi_texte = "Aucun (Vide)"

                rows.append({
                    "Description": desc,
                    "Prix d'Achat": prix,
                    "Rendement Net (%)": renta_nette,
                    "R.O.I": roi_texte,
                    "Quantité Max Achetée": nb_biens_possibles,
                    "Facteur Limitant": statut_limite,
                    "Gain Mensuel Cumulé RAW": gain_mensuel_total,
                    "Gain Mensuel Cumulé": formater_monnaie_empire(gain_mensuel_total),
                    "Revenu Net Unique": formater_monnaie_empire(rev_net_mensuel)
                })

            df = pd.DataFrame(rows)

            st.subheader("🔍 Analyse des meilleures opportunités budgétaires")
            recherche = st.text_input("Filtrer par mot-clé :", value="", key="filtre_locatif")
            df_filtre = df[df["Description"].str.contains(recherche, case=False)].copy()

            df_affichage = df_filtre.sort_values(by="Gain Mensuel Cumulé RAW", ascending=False)

            df_visuel = df_affichage.copy()
            df_visuel["Prix d'Achat"] = df_visuel["Prix d'Achat"].apply(formater_monnaie_empire)
            df_visuel["Rendement Net (%)"] = df_visuel["Rendement Net (%)"].apply(lambda x: f"{x:.2f}%")
            df_visuel["Quantité Max Achetée"] = df_visuel["Quantité Max Achetée"].apply(lambda x: f"{x:,}".replace(",", " "))
            df_visuel = df_visuel.drop(columns=["Gain Mensuel Cumulé RAW"])

            st.dataframe(df_visuel, use_container_width=True)

            if not df_affichage.empty and df_affichage.iloc[0]["Gain Mensuel Cumulé RAW"] > 0:
                top_achat = df_affichage.iloc[0]
                st.success(f"👑 **Stratégie d'achat validée pour votre budget :**")
                st.write(f"En investissant votre capital dans l'achat de **{df_visuel.iloc[0]['Quantité Max Achetée']}** unités de **{top_achat['Description']}**, vous générez le plus gros flux de trésorerie possible avec un gain net global de **{top_achat['Gain Mensuel Cumulé']} /mois**.")

        except Exception as e:
            st.error(f"⚠️ Erreur lors de l'analyse locative : {str(e)}")
