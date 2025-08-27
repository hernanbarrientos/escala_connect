import streamlit as st

def apply_style():
    # --- NOVO: LÓGICA PARA LER O ARQUIVO CSS ---
    # Esta função lê o arquivo style.css e o injeta na aplicação.
    # Isso é executado antes do resto da página, evitando o "piscar".
    try:
        with open('.streamlit/style.css') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error("Arquivo de estilo não encontrado. Certifique-se que o 'style.css' está na pasta '.streamlit'.")

    # --- LÓGICA DA SIDEBAR ---
    # Esta parte continua igual, desenhando o conteúdo da nossa sidebar customizada.
    with st.sidebar:
        st.title("Ministério Connect")
        st.write("Bem-vindo(a), Administrador!")
        st.header("Menu do Administrador")
        
        st.page_link("pages/4_Gerar_Escala.py", label="Gerar e Editar Escala", icon="🗓️")
        st.page_link("pages/2_Gerenciar_Voluntarios.py", label="Gerenciar Voluntários", icon="👥")
        st.page_link("pages/1_Gerenciar_Funcoes.py", label="Gerenciar Funções", icon="🛠️")
        st.page_link("pages/3_Gerenciar_Servicos.py", label="Gerenciar Serviços", icon="⛪")
        st.page_link("pages/5_Gerenciar_Vinculos.py", label="Gerenciar Vínculos", icon="🔗")
        
        st.write("---")
        
        if st.button("Sair (Logout)"):
            st.info("Funcionalidade de Logout a ser implementada com o portal.")