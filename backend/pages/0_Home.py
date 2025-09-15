import streamlit as st
import pandas as pd
import plotly.express as px
from database import *
import backend.style as style

# --- Verificação de Login ---
if not st.session_state.get('logged_in'):
    st.switch_page("Login.py")

st.set_page_config(page_title="Dashboard", layout="wide")
style.apply_style()

# --- COLETA E CÁLCULO DE DADOS ---
id_ministerio_logado = st.session_state['id_ministerio_logado']

# Busca os dados base
ministerios_df = get_all_ministerios()
voluntarios_df = get_all_voluntarios_com_detalhes(id_ministerio_logado)
grupos_df = get_all_grupos_com_membros(id_ministerio_logado)
funcoes_df = view_all_funcoes(id_ministerio_logado)
eventos_mes_atual_df = get_events_for_month(datetime.now().year, datetime.now().month, id_ministerio_logado)
cotas_df = get_cotas_all_servicos()

# Calcula o total de vagas no mês
total_vagas_mes = 0
if not eventos_mes_atual_df.empty:
    for _, evento in eventos_mes_atual_df.iterrows():
        total_vagas_mes += cotas_df[cotas_df['id_servico'] == evento['id_servico_fixo']]['quantidade_necessaria'].sum()

# Pega o nome do ministério para o título
nome_ministerio = ministerios_df[ministerios_df['id_ministerio'] == id_ministerio_logado]['nome_ministerio'].iloc[0]


# --- TÍTULO E BOAS-VINDAS ---
st.title(f"Painel do Ministério {nome_ministerio}")
st.write("Bem-vindo(a) ao seu painel de controle. Aqui você tem uma visão geral da sua equipe e escalas.")
st.divider()

# --- MÉTRICAS PRINCIPAIS (KPIs) ---
st.subheader("Visão Geral do Mês Atual")

col1, col2, col3, col4 = st.columns(4)

with col1:
    with st.container(border=True):
        st.metric(label="👥 Voluntários Ativos", value=len(voluntarios_df))

with col2:
    with st.container(border=True):
        st.metric(label="🔗 Grupos (Vínculos)", value=len(grupos_df))

with col3:
    with st.container(border=True):
        st.metric(label="🗓️ Eventos no Mês", value=len(eventos_mes_atual_df))

with col4:
    with st.container(border=True):
        st.metric(label="🎯 Total de Vagas no Mês", value=int(total_vagas_mes))

st.divider()

# --- ANÁLISE VISUAL (GRÁFICOS) ---
st.header("Análise da Equipe")
col1, col2 = st.columns(2)

with col1:
    # Gráfico de Pizza: Distribuição de Voluntários por Nível de Experiência
    if not voluntarios_df.empty:
        niveis_contagem = voluntarios_df['nivel_experiencia'].value_counts().reset_index()
        niveis_contagem.columns = ['nivel_experiencia', 'contagem']
        fig_niveis = px.pie(
            niveis_contagem,
            names='nivel_experiencia',
            values='contagem',
            title='Distribuição por Nível de Experiência',
            color_discrete_sequence=px.colors.sequential.Blues_r
        )

        # << ALTERADO: Adicionado 'margin' para alinhar o gráfico à esquerda >>
        fig_niveis.update_layout(
            # title_x=0.5, # Centraliza o título
            margin=dict(l=0, r=120, t=50, b=50), # Define as margens (l=esquerda, r=direita)
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.1,
                xanchor="center",
                x=0.5
            )
        )
        
        st.plotly_chart(fig_niveis, use_container_width=True)
    else:
        st.info("Nenhum voluntário cadastrado para gerar gráfico de experiência.")


with col2:
    # Gráfico de Barras: Quantidade de Voluntários por Função
    if not voluntarios_df.empty and not funcoes_df.empty:
        funcoes_map = funcoes_df.set_index('id_funcao')['nome_funcao'].to_dict()
        contagem_funcoes = defaultdict(int)
        for funcoes_lista in voluntarios_df['funcoes']:
            for id_funcao in funcoes_lista:
                nome_funcao = funcoes_map.get(id_funcao)
                if nome_funcao:
                    contagem_funcoes[nome_funcao] += 1
        
        if contagem_funcoes:
            df_contagem_funcoes = pd.DataFrame(list(contagem_funcoes.items()), columns=['Função', 'Nº de Voluntários']).sort_values('Nº de Voluntários', ascending=False)
            fig_funcoes = px.bar(
                df_contagem_funcoes,
                x='Função',
                y='Nº de Voluntários',
                title='Nº de Voluntários Aptos por Função',
                text_auto=True
            )
            st.plotly_chart(fig_funcoes, use_container_width=True)
        else:
            st.info("Nenhuma função atribuída aos voluntários para gerar gráfico.")
    else:
        st.info("Dados insuficientes para gerar gráfico de funções.")

st.divider()

# --- VOLUNTÁRIOS INATIVOS E PONTOS DE ATENÇÃO ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Voluntários Inativos")
    
    # Busca todos os voluntários do ministério, incluindo os inativos
    todos_voluntarios_com_inativos_df = view_all_voluntarios(id_ministerio_logado, include_inactive=True)
    
    # Filtra o DataFrame para encontrar apenas os que estão com a coluna 'ativo' = False
    voluntarios_inativos = todos_voluntarios_com_inativos_df[todos_voluntarios_com_inativos_df['ativo'] == False]

    if not voluntarios_inativos.empty:
        # Usa um container para agrupar visualmente a lista
        with st.container(border=True):
            st.warning(f"Você possui {len(voluntarios_inativos)} voluntário(s) inativo(s).")
            # Lista os nomes dos voluntários inativos
            for nome in voluntarios_inativos['nome_voluntario']:
                st.markdown(f"- {nome}")
            
            st.caption("") # Adiciona um pequeno espaço
            
            # Botão contextual que leva para a página de gerenciamento
            if st.button("Gerenciar voluntários", use_container_width=True):
                st.switch_page("pages/2_Gerenciar_Voluntarios.py")
    else:
        st.success("Ótimo! Nenhum voluntário inativo no momento.")

with col2:
    st.subheader("Pontos de Atenção")
    
    # Esta parte permanece como estava, verificando voluntários ATIVOS sem função
    voluntarios_sem_funcao = voluntarios_df[voluntarios_df['funcoes'].apply(lambda x: len(x) == 0)]
    
    if not voluntarios_sem_funcao.empty:
        with st.container(border=True):
            st.error("Existem voluntários ATIVOS sem nenhuma função definida!")
            for nome in voluntarios_sem_funcao['nome_voluntario']:
                st.markdown(f"- {nome}")
    else:
        st.success("Todos os voluntários ativos possuem pelo menos uma função.")


