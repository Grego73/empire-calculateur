import streamlit as st
import pandas as pd
from utils import formater_monnaie_empire, convertir_saisie_en_nombre

st.title("✨ Le Podium des Opportunités de l'Empire")
st.markdown("Ce tableau de bord extrait automatiquement vos données synchronisées pour élire le **Top 3** de chaque stratégie.")

def calculer_ratio_secu(num, den):
    """
    Sécurité anti-bug : Réduit l'échelle des nombres géants de l'Empire
    avant la division pour éviter les pourcentages aberrants en milliards.
    """
    if den <= 0: 
        return 0.0
    try:
        str_num = str(abs(int(num)))
        str_den = str(abs(int(den)))
        max_len = max(len(str_num), len(str_den))
        
        if max_len > 10:
            facteur = 10 ** (max_len - 7)
            num_reduit = float(int(num) // facteur)
            den_reduit = float(int(den) // facteur)
            return (num_reduit / den_reduit * 100) if den_reduit > 0 else 0.0
        
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
        # --- 1. PARSING DU CADRE 5 (ACHAT / LOCATION) ---
        data_locatif = {}
        terrains_frais = {}
        if brut_achat_loc.strip():
            lignes_l = brut_achat_loc.strip().split('\n')
            idx_l = 1 if ("description" in lignes_l[0].lower() or "prix" in lignes_l[0].lower()) else 0
            
            for l in lignes_l[idx_l:]:
                if not l.strip(): continue
                cols = [c.strip() for c in l.split('\t') if c.strip()]
                if len(cols) < 5: continue
                
                # CORRECTION ICI : On prend le texte pur cols[0] au lieu de la liste cols
                nom = cols[0]
                p = convertir_saisie_en_nombre(cols[1])
                loy = convertir_saisie_en_nombre(cols[2])
                ch = convertir_saisie_en_nombre(cols[3])
                imp = convertir_saisie_en_nombre(cols[4])
                
                data_locatif[nom] = {"prix": p, "loyer": loy, "charges": ch, "impots": imp}
                
                if "TERRAIN" in nom.upper() or "PARC" in nom.upper():
                    terrains_frais[nom] = {"prix": p, "charges": ch, "impots": imp}

        # --- 2. PARSING DU CADRE 6 (CONSTRUCTION) ---
        data_construction = {}
        if brut_construction.strip():
            lignes_c = brut_construction.strip().split('\n')
            idx_c = 1 if ("bâtiment" in lignes_c[0].lower() or "terrain" in lignes_c[0].lower()) else 0
            
            for l in lignes_c[idx_c:]:
                if not l.strip(): continue
                cols = [c.strip() for c in l.split('\t') if c.strip()]
                if len(cols) < 4: continue
                
                nom = cols[0]
                terr = cols[1]
                cout_ch = convertir_saisie_en_nombre(cols[2])
                dur = convertir_saisie_en_nombre(cols[3])
                
                data_construction[nom] = {"terrain": terr, "cout_ch": cout_ch, "duree": dur}

        # --- 3. PARSING DU CADRE 7 (EMBELLISSEMENT) ---
        data_embellissement = {}
        if brut_embellissement.strip():
            lignes_e = brut_embellissement.strip().split('\n')
            idx_e = 1 if ("bâtiment" in lignes_e[0].lower() or "coût" in lignes_e[0].lower()) else 0
            
            for l in lignes_e[idx_e:]:
                if not l.strip(): continue
                cols = [c.strip() for c in l.split('\t') if c.strip()]
                if len(cols) < 3: continue
                
                nom = cols[0]
                cout_e = convertir_saisie_en_nombre(cols[1])
                dur_e = cols[2]
                
                data_embellissement[nom] = {"cout_e": cout_e, "duree_e": dur_e}

        # ==========================================
        # 📊 PILLIER 1 : PODIUM ACHAT / LOCATION
        # ==========================================
        st.subheader("📊 1. Top 3 Achat & Rendement Locatif Nette")
        rows_loc = []
        for nom, info in data_locatif.items():
            if "TERRAIN" in nom.upper() or "PARC" in nom.upper(): continue
            net_m = info["loyer"] - info["charges"] - info["impots"]
            renta_n = calculer_ratio_secu(net_m * 12, info["prix"])
            if info["prix"] > 0 and renta_n > 0:
                rows_loc.append({"Nom": nom, "Renta": renta_n, "Net": formater_monnaie_empire(net_m)})
        
        if rows_loc:
            top_loc = pd.DataFrame(rows_loc).sort_values(by="Renta", ascending=False).head(3)
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
        st.subheader("🏗️ 2. Top 3 Auto-Construction (Plus-value vs Achat Direct)")
        rows_const = []
        for nom, c_info in data_construction.items():
            loc_info = data_locatif.get(nom, {"prix": 0, "loyer": 0, "charges": 0, "impots": 0})
            if loc_info["prix"] > 0:
                t_frais = terrains_frais.get(c_info["terrain"], {"prix": 0, "charges": 0, "impots": 0})
                frais_terrain_chantier = (t_frais["charges"] + t_frais["impots"]) * c_info["duree"]
                total_c = c_info["cout_ch"] + t_frais["prix"] + frais_terrain_chantier
                
                marge_b = loc_info["prix"] - total_c
                marge_pct = calculer_ratio_secu(marge_b, total_c)
                rows_const.append({"Nom": nom, "Marge_Pct": marge_pct, "Marge_Brute": marge_b})
        
        if rows_const:
            top_const = pd.DataFrame(rows_const).sort_values(by="Marge_Pct", ascending=False).head(3)
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
        st.subheader("💅 3. Top 3 Opérations d'Embellissement (Budgets les plus optimisés)")
        rows_emb = []
        for nom, e_info in data_embellissement.items():
            if e_info["cout_e"] > 0:
                rows_emb.append({"Nom": nom, "Cout_Raw": e_info["cout_e"], "Cout_Format": formater_monnaie_empire(e_info["cout_e"])})
        
        if rows_emb:
            # Trie par le coût le plus faible (le plus optimisé pour investir de petites enveloppes)
            top_emb = pd.DataFrame(rows_emb).sort_values(by="Cout_Raw", ascending=True).head(3)
            c1, c2, c3 = st.columns(3)
            medailles = ["🥇 1er", "🥈 2e", "🥉 3e"]
            for i, (idx, r) in enumerate(top_emb.iterrows()):
                with [c1, c2, c3][i]:
                    st.metric(label=f"{medailles[i]} - {r['Nom']}", value=r['Cout_Format'], delta="Frais minimum")
        else:
            st.info("Collez vos fiches d'embellissement pour classer les budgets.")

    except Exception as e:
        st.error(f"⚠️ Erreur lors de la compilation des podiums : {str(e)}")
