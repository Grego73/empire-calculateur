import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre

st.title("📊 Analyse Locative & Rendements")
st.markdown("Calculez les revenus nets réels et le temps d'amortissement (R.O.I) des infrastructures à partir de votre saisie unique.")

# Vérification de la synchronisation de l'accueil
if not st.session_state.get("donnees_chargees", False):
    st.warning("⚠️ Veuillez d'abord coller vos fiches et cliquer sur le bouton de synchronisation sur la page d'accueil 🏠 avant d'utiliser cette page.")
else:
    # Récupération de la zone de texte 5 de l'accueil
    donnees_brutes = st.session_state.get("tab_projets_construction", "")

    if not donnees_brutes.strip():
        st.info("💡 Le bloc 5 (Fiches Construction / Locatif) est vide sur la page d'accueil. Collez-y vos données pour activer l'analyse.")
    else:
        try:
            lignes = donnees_brutes.strip().split('\n')
            
            # Détection et exclusion automatique de l'en-tête (Description, Prix, Loyer...)
            debut_index = 0
            if "description" in lignes[0].lower() or "prix" in lignes[0].lower():
                debut_index = 1

            rows = []
            for ligne in lignes[debut_index:]:
                if not ligne.strip(): continue
                colonnes = [c.strip() for c in ligne.split('\t') if c.strip()]
                if len(colonnes) < 5: continue  # Sécurité s'il manque des colonnes
                
                desc = colonnes[0]
                prix = convertir_saisie_en_nombre(colonnes[1])
                loyer = convertir_saisie_en_nombre(colonnes[2])
                charges = convertir_saisie_en_nombre(colonnes[3])
                impots = convertir_saisie_en_nombre(colonnes[4])
                
                # Moteur de calcul Empire
                rev_net_mensuel = loyer - charges - impots
                rev_net_annuel = rev_net_mensuel * 12
                renta_nette = (rev_net_annuel / prix * 100) if prix > 0 else 0
                renta_brute = (loyer * 12 / prix * 100) if prix > 0 else 0
                
                if rev_net_annuel > 0:
                    annees_roi = prix / rev_net_annuel
                    roi_texte = f"{int(annees_roi)} ans, {int((annees_roi - int(annees_roi)) * 12)} m"
                else:
                    roi_texte = "Aucun (Vide)"

                rows.append({
                    "Description": desc,
                    "Prix d'Achat": prix,
                    "Loyer Brut /mois": loyer,
                    "Revenu Net /mois": rev_net_mensuel,
                    "Rendement Brut (%)": round(renta_brute, 2),
                    "Rendement Net (%)": round(renta_nette, 2),
                    "R.O.I (Amortissement)": roi_texte,
                    "Renta_Tri": renta_nette  # Colonne technique invisible pour le tri
                })

            df = pd.DataFrame(rows)

            st.subheader("🔍 Moteur de Recherche holding")
            recherche = st.text_input("Filtrer par mot-clé (ex: Bureaux, Local, Usine) :", value="")
            df_filtre = df[df["Description"].str.contains(recherche, case=False)].copy()

            # Tri automatique par le meilleur rendement Net
            df_affichage = df_filtre.sort_values(by="Renta_Tri", ascending=False).drop(columns=["Renta_Tri"])

            # Application du formatage visuel officiel
            df_visuel = df_affichage.copy()
            df_visuel["Prix d'Achat"] = df_visuel["Prix d'Achat"].apply(formater_monnaie_empire)
            df_visuel["Loyer Brut /mois"] = df_visuel["Loyer Brut /mois"].apply(formater_monnaie_empire)
            df_visuel["Revenu Net /mois"] = df_visuel["Revenu Net /mois"].apply(formater_monnaie_empire)
            df_visuel["Rendement Brut (%)"] = df_visuel["Rendement Brut (%)"].apply(lambda x: f"{x:.2f}%")
            df_visuel["Rendement Net (%)"] = df_visuel["Rendement Net (%)"].apply(lambda x: f"{x:.2f}%")

            st.dataframe(df_visuel, use_container_width=True)

            # Recommandation automatique
            if not df_affichage.empty and df_affichage.iloc[0]["Rendement Net (%)"] > 0:
                top_opportunite = df_affichage.iloc[0]
                st.info(f"🏆 **Opportunité n°1 détectée :** `{top_opportunite['Description']}` dégage un rendement net de **{top_opportunite['Rendement Net (%)']:.2f}%**.")

        except Exception as e:
            st.error(f"⚠️ Erreur lors de l'analyse du tableau locatif : {str(e)}")
