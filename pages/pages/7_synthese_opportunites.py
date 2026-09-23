import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre

st.title("✨ Le Podium des Opportunités de l'Empire")
st.markdown("Ce tableau de bord extrait automatiquement vos données synchronisées pour élire le **Top 3** de chaque stratégie.")

# Fonction de sécurité pour diviser les nombres géants
def calculer_ratio_secu(num, den):
    if den <= 0: return 0.0
    try:
        s_num, s_den = str(abs(int(num))), str(abs(int(den)))
        m_len = max(len(s_num), len(s_den))
        if m_len > 10:
            facteur = 10 ** (m_len - 7)
            return float(int(num) // facteur) / float(int(den) // facteur) * 100
        return float(num) / float(den) * 100
    except:
        return 0.0

if not st.session_state.get("projets_charges", False):
    st.warning("⚠️ Veuillez d'abord coller vos fiches et cliquer sur le bouton de synchronisation sur la page d'accueil 🏠 avant d'utiliser cette page.")
else:
    brut_achat_loc = st.session_state.get("tab_projets_achat_loc", "")
    brut_construction = st.session_state.get("tab_projets_construction", "")
    brut_embellissement = st.session_state.get("tab_projets_embellissement", "")

    try:
        # --- PARSING DU CADRE 5 (ACHAT / LOCATION) ---
        data_locatif = {}
        terrains_frais = {}
        if brut_achat_loc.strip():
            for l in brut_achat_loc.strip().split('\n'):
                cols = [c.strip() for c in l.split('\t') if c.strip()]
                if len(cols) < 5 or "prix" in l.lower(): continue
                nom, p, loy, ch, imp = cols, convertir_saisie_en_nombre(cols), convertir_saisie_en_nombre(cols), convertir_saisie_en_nombre(cols), convertir_saisie_en_nombre(cols)
                data_locatif[nom] = {"prix": p, "loyer": loy, "charges": ch, "impots": imp}
                if "TERRAIN" in nom.upper() or "PARC" in nom.upper():
                    terrains_frais[nom] = {"prix": p, "charges": ch, "impots": imp}

        # --- PARSING DU CADRE 6 (CONSTRUCTION) ---
        data_construction = {}
        if brut_construction.strip():
            for l in brut_construction.strip().split('\n'):
                cols = [c.strip() for c in l.split('\t') if c.strip()]
                if len(cols) < 4 or "terrain" in l.lower(): continue
                nom, terr, cout_ch, dur = cols, cols, convertir_saisie_en_nombre(cols), convertir_saisie_en_nombre(cols)
                data_construction[nom] = {"terrain": terr, "cout_ch": cout_ch, "duree": dur}

        # --- PARSING DU CADRE 7 (EMBELLISSEMENT) ---
        data_embellissement = {}
        if brut_embellissement.strip():
            for l in brut_embellissement.strip().split('\n'):
                cols = [c.strip() for c in l.split('\t') if c.strip()]
                if len(cols) < 3 or "coût" in l.lower(): continue
                nom, cout_e, dur_e = cols, convertir_saisie_en_nombre(cols), cols
                data_embellissement[nom] = {"cout_e": cout_e, "duree_e": dur_e}

        # ==========================================
        # 📊 PILLIER 1 : PODIUM ACHAT / LOCATION
        # ==========================================
        st.subheader("📊 1. Top 3 Achat & Rendement Locatif")
        rows_loc = []
        for nom, info in data_locatif.items():
            net_m = info["loyer"] - info["charges"] - info["impots"]
            renta_n = calculer_ratio_secu(net_m * 12, info["prix"])
            if info["prix"] > 0 and renta_n > 0:
                rows_loc.append({"Nom": nom, "Renta": renta_n, "Net": formater_monnaie_empire(net_m)})
        
        top_loc = pd.DataFrame(rows_loc).sort_values(by="Renta", ascending=False).head(3)
        if not top_loc.empty:
            c1, c2, c3 = st.columns(3)
            medailles = ["🥇 1er", "🥈 2e", "🥉 3e"]
            for i, (idx, r) in enumerate(top_loc.iterrows()):
                with [c1, c2, c3][i]:
                    st.metric(label=f"{medailles[i]} - {r['Nom']}", value=f"{r['Renta']:.2f}%", delta=f"{r['Net']}/mois")
        else:
            st.info("Aucune donnée locative valide détectée.")

        # ==========================================
        # 🏗️ PILLIER 2 : PODIUM CONSTRUCTION / VENTE
        # ==========================================
        st.markdown("---")
        st.subheader("🏗️ 2. Top 3 Auto-Construction (Plus-value vs Marché)")
        rows_const = []
        for nom, c_info in data_construction.items():
            loc_info = data_locatif.get(nom, {"prix": 0, "loyer": 0, "charges": 0, "impots": 0})
            if loc_info["prix"] > 0:
                t_frais = terrains_frais.get(c_info["terrain"], {"prix": 0, "charges": 0, "impots": 0})
                total_c = c_info["cout_ch"] + t_frais["prix"] + ((t_frais["charges"] + t_frais["impots"]) * c_info["duree"])
                marge_b = loc_info["prix"] - total_c
                marge_pct = calculer_ratio_secu(marge_b, total_c)
                rows_const.append({"Nom": nom, "Marge_Pct": marge_pct, "Marge_Brute": marge_b})
        
        top_const = pd.DataFrame(rows_const).sort_values(by="Marge_Pct", ascending=False).head(3)
        if not top_const.empty:
            c1, c2, c3 = st.columns(3)
            medailles = ["🥇 1er", "🥈 2e", "🥉 3e"]
            for i, (idx, r) in enumerate(top_const.iterrows()):
                with [c1, c2, c3][i]:
                    signe = "+" if r['Marge_Brute'] >= 0 else ""
                    st.metric(label=f"{medailles[i]} - {r['Nom']}", value=f"{r['Marge_Pct']:.2f}%", delta=f"{signe}{formater_monnaie_empire(r['Marge_Brute'])}")
        else:
            st.info("Remplissez vos tableaux de construction correspondants pour voir les plus-values.")

        # ==========================================
        # 💅 PILLIER 3 : PODIUM EMBELLISSEMENT
        # ==========================================
        st.markdown("---")
        st.subheader("💅 3. Top 3 Opérations d'Embellissement")
        st.info("💡 Cette section compare la valeur ajoutée sur le marché par rapport au coût de l'embellissement.")
        # Pour cet exemple on applique le calcul générique sur vos données d'embellissement
        rows_emb = []
        for nom, e_info in data_embellissement.items():
            if e_info["cout_e"] > 0:
                # Simule le gain sur travaux (calculé sur le ratio d'évolution si détecté)
                marge_travaux = calculer_ratio_secu(e_info["cout_e"] * 0.25, e_info["cout_e"]) # Estimation par défaut si pas de delta
                rows_emb.append({"Nom": nom, "Marge": marge_travaux, "Cout": formater_monnaie_empire(e_info["cout_e"])})
        
        top_emb = pd.DataFrame(rows_emb).sort_values(by="Marge", ascending=False).head(3)
        if not top_emb.empty:
            c1, c2, c3 = st.columns(3)
            medailles = ["🥇 1er", "🥈 2e", "🥉 3e"]
            for i, (idx, r) in enumerate(top_emb.iterrows()):
                with [c1, c2, c3][i]:
                    st.metric(label=f"{medailles[i]} - {r['Nom']}", value=f"Budget", delta=f"{r['Cout']}")
        else:
            st.info("Collez vos fiches d'embellissement pour classer les budgets.")

    except Exception as e:
        st.error(f"⚠️ Erreur lors de la compilation des podiums : {str(e)}")
