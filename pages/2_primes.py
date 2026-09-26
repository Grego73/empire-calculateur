import streamlit as st
import pandas as pd
import requests
from utils import formater_monnaie_empire, convertir_saisie_en_nombre

st.title("💰 Gestion & Contrôle des Primes")

if not st.session_state.get("holding_chargee", False):
    st.warning("⚠️ Veuillez synchroniser vos tableaux sur l'accueil 🏠.")
else:
    donnees_exploitation = st.session_state.get("tab_finance", "")
    donnees_plafonds = st.session_state.get("tab_primes", "")

    col1, col2 = st.columns(2)
    with col1: pct_holding = st.slider("Pourcentage Holding (%)", 0, 100, 50, 5)
    with col2: 
        pct_prime = 100 - pct_holding
        st.metric("Pourcentage Primes (%)", f"{pct_prime}%")

    forcer_zero = st.checkbox("🛑 Forcer à zéro", value=False)

    if st.button("🚀 Calculer et Envoyer sur Discord", use_container_width=True):
        try:
            url_webhook = st.secrets["webhooks"]["primes"]
            plafonds_extraits = {}
            
            if not forcer_zero:
                lignes_p = donnees_plafonds.strip().split('\n')
                idx_p = 1 if "poste" in donnees_plafonds.lower() else 0
                for l in lignes_p[idx_p:]:
                    if not l.strip(): continue
                    cols = l.split('\t')
                    if len(cols) < 4: continue
                    if cols[1].upper() == "PDG" and cols[2].upper() != "GREGO73" and "CONSTRUCTIONS" not in cols[0].upper():
                        plafonds_extraits[cols[0].strip()] = convertir_saisie_en_nombre(cols[3].strip())

            lignes_e = donnees_exploitation.strip().split('\n')
            import_primes = ["Filiale\tPrimes"]
            lignes_tab = []
            idx_e = 1 if lignes_e and "filiale" in lignes_e[0].lower() else 0

            for l in lignes_e[idx_e:]:
                if not l.strip(): continue
                cols = l.split('\t')
                if len(cols) < 3: continue
                nom = cols[0].strip()
                
                if forcer_zero:
                    import_primes.append(f"{nom}\t0")
                    lignes_tab.append({"Filiale": nom, "Prime": "0", "Statut": "Zéro Forcé"})
                else:
                    if nom not in plafonds_extraits: continue
                    val_exp = convertir_saisie_en_nombre(cols[2].strip())
                    val_prime = int(val_exp * (pct_prime / 100))
                    p_max = plafonds_extraits[nom]
                    
                    final_p = min(val_prime, p_max)
                    statut = "🚨 Plafonné" if val_prime > p_max else "✅ Conforme"
                    
                    import_primes.append(f"{nom}\t{final_p}")
                    lignes_tab.append({"Filiale": nom, "Prime": formater_monnaie_empire(final_p), "Statut": statut})

            crlf_pur = "\r\n".join(import_primes) + "\r\n"
            msg = f"📊 **Rapport Primes ({pct_prime}%)**\n```text\n{crlf_pur}```"
            
            reponse = requests.post(url_webhook, data={'content': msg}, files={'file': ('primes.txt', crlf_pur, 'text/plain')})
            
            # CONDITION CORRIGÉE ET SÉCURISÉE ICI
            if reponse.status_code in:
                st.success("🎉 Rapport Primes envoyé !")
                st.dataframe(pd.DataFrame(lignes_tab), use_container_width=True, hide_index=True)
                st.code(crlf_pur, language="text")
        except Exception as e: st.error(f"⚠️ Erreur : {e}")
