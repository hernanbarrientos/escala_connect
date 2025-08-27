import streamlit as st
import style


style.apply_style()

st.set_page_config(
    page_title="Home - Escala CONNECT",
    layout="wide"
)

st.title("Bem-vindo ao Sistema de Escalas CONNECT! 👋")

st.sidebar.success("Selecione uma das páginas acima para começar.")

st.markdown(
    """
    Este é o sistema de gerenciamento de escalas para os voluntários do ministério CONNECT.

    **👈 Selecione no menu ao lado a opção que deseja gerenciar:**

    - **Gerenciar Funções:** Para criar, editar ou remover os cargos (ex: Portão, Store, Apoio).
    - **Gerenciar Voluntários:** Para cadastrar e atualizar os dados dos voluntários.

    Em breve, teremos a funcionalidade de gerar e visualizar as escalas!
    """
)