# pages/0_Home.py

import streamlit as st
from database import get_all_voluntarios_com_detalhes, get_all_grupos_com_membros, get_events_for_month, get_all_ministerios

# --- Verificação de Login ---
if not st.session_state.get('logged_in'):
    st.error("Acesso negado. Por favor, faça o login primeiro.")
    st.stop()

st.set_page_config(page_title="Dashboard", layout="wide")

# --- Coleta de Dados ---
id_ministerio_logado = st.session_state['id_ministerio_logado']
ministerios_df = get_all_ministerios()
nome_ministerio = ministerios_df[ministerios_df['id_ministerio'] == id_ministerio_logado]['nome_ministerio'].iloc[0]

# Busca os dados específicos do ministério logado
voluntarios_df = get_all_voluntarios_com_detalhes(id_ministerio_logado)
grupos_df = get_all_grupos_com_membros(id_ministerio_logado)
eventos_mes_atual_df = get_events_for_month(st.session_state.get('ano', 2025), st.session_state.get('mes', 9), id_ministerio_logado)

# --- Título e Boas-vindas ---
st.title(f"Painel do Ministério {nome_ministerio}")
st.write("Bem-vindo ao seu painel de controle. Aqui você tem uma visão geral da sua equipe e escalas.")

st.divider()

# --- Métricas Principais ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Voluntários Ativos", value=len(voluntarios_df))
with col2:
    st.metric(label="Grupos (Vínculos)", value=len(grupos_df))
with col3:
    st.metric(label="Eventos no Mês Selecionado", value=len(eventos_mes_atual_df))

st.divider()

# --- Ações Rápidas ---
st.subheader("Ações Rápidas")
st.info("Utilize os menus na barra lateral esquerda para navegar entre as funcionalidades do sistema.")

# Você pode adicionar botões aqui no futuro, se desejar, por exemplo:
# if st.button("Ir para Gerar Escala"):
#     st.switch_page("pages/4_Gerar_Escala.py")