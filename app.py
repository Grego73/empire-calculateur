import streamlit as st

# Configuration globale
st.set_page_config(page_title="Calculateur Empire", page_icon="💼", layout="centered")

# INITIALISATION DES VARIABLES DE SESSION (La mémoire de l'application)
if "tab_finance" not in st.session_state: st.session_state["tab_finance"] = ""
if "tab_capital" not in st.session_state: st.session_state["tab_capital"] = ""
if "tab_primes" not in st.session_state: st.session_state["tab_primes"] = ""
if "tab_frais" not in st.session_state: st.session_state["tab_frais"] = ""
if "donnees_chargees" not in st.session_state: st.session_state["donnees_chargees"] = False

# MENU DE SÉLECTION DES PAGES
page_home = st.Page(lambda: home_page(), title="📥 Accueil & Saisie Unique", icon="🏠")
page_frais = st.Page("pages/1_frais_gestion.py", title="Frais de Gestion", icon="📉")
page_primes = st.Page("pages/2_primes.py", title="Gestion des Primes", icon="💰")
page_perf = st.Page("pages/3_performance.py", title="Analyse de Performance", icon="📊")
page_equilibre = st.Page("pages/4_equilibrage.py", title="Équilibrage & Injection", icon="⚖️")

# DÉFINITION DE LA PAGE D'ACCUEIL CENTRALISÉE
def home_page():
    st.title("🏠 Centre de Saisie Unique de l'Empire")
    st.markdown("Collez vos **4 tableaux financiers** ici une seule fois. Ils seront automatiquement envoyés vers les pages de calcul correspondantes.")
    
    # Zones de texte connectées à la mémoire session_state
    st.session_state["tab_finance"] = st.text_area("1. Tableau FINANCE :", value=st.session_state["tab_finance"], height=150)
    st.session_state["tab_capital"] = st.text_area("2. Tableau CAPITAL :", value=st.session_state["tab_capital"], height=150)
    st.session_state["tab_primes"] = st.text_area("3. Tableau DIRECTEURS / PLAFONDS PRIMES :", value=st.session_state["tab_primes"], height=150)
    st.session_state["tab_frais"] = st.text_area("4. Tableau FRAIS DE GESTION (De la veille) :", value=st.session_state["tab_frais"], height=150)
    
    if st.button("🚀 Répartir et synchroniser les données dans tout l'Empire", use_container_width=True):
        if not st.session_state["tab_finance"].strip():
            st.error("❌ Le tableau Finance est obligatoire pour démarrer.")
        else:
            st.session_state["donnees_chargees"] = True
            st.success("🎉 Synchronisation réussie ! Vous pouvez maintenant naviguer dans le menu de gauche. Les calculs sont déjà prêts.")
    st.markdown("---")
    st.subheader("🔍 Outil de Contrôle : Audit d'une filiale")
    st.markdown("Collez le rapport complet d'une filiale (Résultat et Bilan) ci-dessous pour vérifier sa concordance comptable.")
    
    rapport_audit = st.text_area("Collez le rapport de la filiale ici :", height=200, key="audit_input")
    
    if st.button("👁️ Auditer les chiffres de la filiale", use_container_width=True):
        if not rapport_audit.strip():
            st.error("❌ Veuillez coller un rapport à auditer.")
        else:
            from utils import verifier_concordance_rapport, formater_monnaie_empire
            erreurs, data = verifier_concordance_rapport(rapport_audit)
            
            if erreurs:
                st.error("🚨 CONCORDANCE INCORRECTE : Le rapport contient des anomalies comptables !")
                for err in erreurs:
                    st.warning(err)
            else:
                st.success("✅ CONCORDANCE PARFAITE : Les calculs de la filiale sont 100% valides et équilibrés !")
                
                # Petit résumé propre pour l'utilisateur
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**📊 Volet Résultat :**")
                    st.write(f"• Résultat NET : `{formater_monnaie_empire(data.get('net', 0))}`")
                with col2:
                    st.write("**⚖️ Volet Bilan :**")
                    st.write(f"• Total Actif/Passif : `{formater_monnaie_empire(data.get('actif', 0))}`")

# Lancement de la navigation avec la page d'accueil en premier
pg = st.navigation([page_home, page_frais, page_primes, page_perf, page_equilibre])
pg.run()
