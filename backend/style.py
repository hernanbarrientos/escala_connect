# Arquivo: style.py (versão corrigida e inteligente)

import streamlit as st
# Adicionamos esta importação para poder buscar o nome do ministério
from database import get_all_ministerios

def apply_style():
    """
    Aplica o estilo CSS em todas as páginas e exibe a sidebar de navegação
    APENAS se o usuário estiver logado.
    """
    # --- PARTE 1: INJEÇÃO DE CSS (Roda em todas as páginas) ---
    try:
        with open('.streamlit/style.css') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error("Arquivo de estilo não encontrado. Certifique-se que o 'style.css' está na pasta '.streamlit'.")

    # --- PARTE 2: LÓGICA DA SIDEBAR (Só roda se o usuário estiver logado) ---
    if st.session_state.get('logged_in'):
        with st.sidebar:
            # Pega o nome do ministério do usuário logado para exibir
            id_ministerio_logado = st.session_state.get('id_ministerio_logado')
            if id_ministerio_logado:
                ministerios_df = get_all_ministerios()
                # Usamos .get() para evitar erro caso o ministério não seja encontrado
                nome_ministerio = ministerios_df[ministerios_df['id_ministerio'] == id_ministerio_logado]['nome_ministerio'].iloc[0]
                st.title(f"Ministério {nome_ministerio}")
            
            st.write("Bem-vindo(a), Administrador!")
            st.header("Menu do Administrador")
            
            # Links de navegação atualizados para st.page_link
            st.page_link("pages/0_Home.py", label="Dashboard / Home", icon="🏠")
            st.page_link("pages/4_Gerar_Escala.py", label="Gerar e Editar Escala", icon="🗓️")
            st.page_link("pages/2_Gerenciar_Voluntarios.py", label="Gerenciar Voluntários", icon="👥")
            st.page_link("pages/1_Gerenciar_Funcoes.py", label="Gerenciar Funções", icon="🛠️")
            st.page_link("pages/3_Gerenciar_Servicos.py", label="Gerenciar Serviços", icon="📝")
            st.page_link("pages/5_Gerenciar_Vinculos.py", label="Gerenciar Vínculos", icon="🔗")
            
            st.divider()
            
            if st.button("Sair (Logout)"):
                # Limpa todos os dados da sessão
                st.session_state.clear()
                # Redireciona para a página de login
                st.switch_page("Login.py")