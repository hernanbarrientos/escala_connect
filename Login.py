# Arquivo: Login.py (versão corrigida com st.switch_page)

import streamlit as st
from database import verificar_login
import style
style.apply_style()

st.set_page_config(page_title="Login - Escala Connect", layout="centered")

st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {
            display: none;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Lógica de Redirecionamento Aprimorada ---
# Se o usuário já está logado, ele não deveria nem ver a tela de login.
# Esta verificação no topo redireciona imediatamente para a página Home.
if st.session_state.get('logged_in'):
    st.switch_page("pages/0_Home.py")

st.title("Sistema de Escalas Connect")
st.subheader("Por favor, faça o login para continuar")

with st.form("login_form"):
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    submitted = st.form_submit_button("Entrar")

    if submitted:
        if not username or not password:
            st.warning("Por favor, preencha o usuário e a senha.")
        else:
            id_ministerio_logado = verificar_login(username, password)
            
            if id_ministerio_logado:
                # Se o login for bem-sucedido, salva as informações na sessão
                st.session_state['logged_in'] = True
                st.session_state['id_ministerio_logado'] = id_ministerio_logado
                
                # E imediatamente navega para a página Home, sem precisar de st.rerun()
                st.switch_page("pages/0_Home.py") 
            else:
                st.error("Usuário ou senha inválidos.")