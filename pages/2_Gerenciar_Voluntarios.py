import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar
import locale
from database import (
    view_all_funcoes,
    view_all_servicos_fixos,
    add_voluntario,
    view_all_voluntarios,
    update_funcoes_of_voluntario,
    update_disponibilidade_of_voluntario,
    get_voluntario_by_id,
    get_funcoes_of_voluntario,
    get_disponibilidade_of_voluntario,
    get_events_for_month,
    get_indisponibilidade_eventos,
    update_voluntario,
    update_indisponibilidade_eventos
)
import style

# Aplica o estilo global e a configuração da página
style.apply_style()
st.set_page_config(page_title="Gerenciar Voluntários", layout="wide")

# Tenta configurar o idioma da aplicação para Português do Brasil
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    # Se o locale não estiver instalado, o app continua, mas pode mostrar nomes em inglês.
    pass

st.title("Cadastro e Gestão de Voluntários")

# --- Abas Principais ---
tab_cadastrar, tab_editar = st.tabs(["Cadastrar Novo Voluntário", "Editar Voluntário Existente"])

# --- ABA DE CADASTRO DE NOVO VOLUNTÁRIO ---
with tab_cadastrar:
    st.header("Formulário de Cadastro")

    # Busca as opções de funções e serviços do banco de dados
    todas_as_funcoes_cadastro = view_all_funcoes()
    todos_os_servicos_cadastro = view_all_servicos_fixos()

    with st.form(key="form_novo_voluntario", clear_on_submit=True):
        st.subheader("Dados Pessoais")
        coluna_nome, coluna_telefone, coluna_limite = st.columns(3)
        with coluna_nome:
            novo_nome = st.text_input("Nome Completo*")
        with coluna_telefone:
            novo_telefone = st.text_input("Telefone")
        with coluna_limite:
            novo_limite_mensal = st.number_input("Limite de escalas por mês*", min_value=1, max_value=10, value=2)

        st.divider()

        coluna_funcoes, coluna_disponibilidade, coluna_status = st.columns(3)
        with coluna_funcoes:
            st.subheader("Funções que pode exercer")
            funcoes_selecionadas_ids = []
            for funcao in todas_as_funcoes_cadastro.itertuples():
                if st.checkbox(funcao.nome_funcao, key=f"novo_voluntario_funcao_{funcao.id_funcao}"):
                    funcoes_selecionadas_ids.append(funcao.id_funcao)

        with coluna_disponibilidade:
            st.subheader("Disponibilidade Padrão")
            servicos_selecionados_ids = []
            for servico in todos_os_servicos_cadastro.itertuples():
                if st.checkbox(servico.nome_servico, key=f"novo_voluntario_servico_{servico.id_servico}"):
                    servicos_selecionados_ids.append(servico.id_servico)
        
        with coluna_status:
            st.subheader("Status do Voluntário")
            st.info("O status inicial é sempre 'Ativo'.")

        if st.form_submit_button("Cadastrar Voluntário"):
            if not novo_nome:
                st.warning("O campo 'Nome Completo' é obrigatório.")
            else:
                add_voluntario(novo_nome, novo_telefone, int(novo_limite_mensal))
                # Busca o ID do voluntário recém-criado para associar as funções e disponibilidades
                voluntarios_recentes = view_all_voluntarios(include_inactive=True)
                id_novo_voluntario = int(voluntarios_recentes[voluntarios_recentes['nome_voluntario'] == novo_nome]['id_voluntario'].iloc[0])
                
                update_funcoes_of_voluntario(id_novo_voluntario, [int(id) for id in funcoes_selecionadas_ids])
                update_disponibilidade_of_voluntario(id_novo_voluntario, [int(id) for id in servicos_selecionados_ids])
                
                st.success(f"Voluntário {novo_nome} cadastrado com sucesso!")
                st.rerun()

# --- ABA DE EDIÇÃO DE VOLUNTÁRIO EXISTENTE ---
with tab_editar:
    st.header("Edição de Voluntários")

    mostrar_inativos = st.checkbox("Mostrar voluntários inativos na lista")
    voluntarios_para_editar_df = view_all_voluntarios(include_inactive=mostrar_inativos)
    lista_nomes_voluntarios = sorted(voluntarios_para_editar_df['nome_voluntario'].tolist())
    
    OPCAO_SELECIONE = "--- Selecione um voluntário ---"
    lista_nomes_voluntarios.insert(0, OPCAO_SELECIONE)

    voluntario_selecionado_nome = st.selectbox(
        "Selecione um voluntário para editar seus dados:",
        options=lista_nomes_voluntarios
    )

    if voluntario_selecionado_nome != OPCAO_SELECIONE:
        
        id_voluntario_atual = int(voluntarios_para_editar_df[voluntarios_para_editar_df['nome_voluntario'] == voluntario_selecionado_nome]['id_voluntario'].iloc[0])
        dados_voluntario = get_voluntario_by_id(id_voluntario_atual)
        
        todas_as_funcoes_edicao = view_all_funcoes()
        todos_os_servicos_edicao = view_all_servicos_fixos()

        st.header(f"Editando: {dados_voluntario['nome_voluntario']}")

        # --- FORMULÁRIO 1: DADOS PRINCIPAIS ---
        with st.form(key=f"form_dados_principais_{id_voluntario_atual}"):
            st.subheader("Dados Pessoais e Funções")
            
            coluna_nome_edicao, coluna_telefone_edicao, coluna_limite_edicao = st.columns(3)
            with coluna_nome_edicao:
                nome_editado = st.text_input("Nome Completo*", value=dados_voluntario['nome_voluntario'])
            with coluna_telefone_edicao:
                telefone_editado = st.text_input("Telefone", value=dados_voluntario['telefone'])
            with coluna_limite_edicao:
                limite_mensal_editado = st.number_input("Limite de escalas por mês*", min_value=1, max_value=10, value=int(dados_voluntario['limite_escalas_mes']))

            st.divider()

            coluna_funcoes_edicao, coluna_disponibilidade_edicao = st.columns(2)
            with coluna_funcoes_edicao:
                st.subheader("Funções que pode exercer")
                funcoes_atuais_ids = get_funcoes_of_voluntario(id_voluntario_atual)
                funcoes_selecionadas_edicao = []
                for funcao in todas_as_funcoes_edicao.itertuples():
                    selecionado = funcao.id_funcao in funcoes_atuais_ids
                    if st.checkbox(funcao.nome_funcao, value=selecionado, key=f"edicao_funcao_{id_voluntario_atual}_{funcao.id_funcao}"):
                        funcoes_selecionadas_edicao.append(funcao.id_funcao)
            
            with coluna_disponibilidade_edicao:
                st.subheader("Disponibilidade Padrão")
                disponibilidade_atual_ids = get_disponibilidade_of_voluntario(id_voluntario_atual)
                servicos_selecionados_edicao = []
                for servico in todos_os_servicos_edicao.itertuples():
                    selecionado = servico.id_servico in disponibilidade_atual_ids
                    if st.checkbox(servico.nome_servico, value=selecionado, key=f"edicao_servico_{id_voluntario_atual}_{servico.id_servico}"):
                        servicos_selecionados_edicao.append(servico.id_servico)
            
            st.divider()
            st.subheader("Status do Voluntário")
            status_ativo_editado = st.checkbox("Voluntário Ativo", value=dados_voluntario['ativo'])

            if st.form_submit_button("Salvar Alterações do Perfil"):
                id_voluntario_inteiro = int(id_voluntario_atual)
                update_voluntario(id_voluntario_inteiro, nome_editado, telefone_editado, int(limite_mensal_editado), status_ativo_editado)
                update_funcoes_of_voluntario(id_voluntario_inteiro, funcoes_selecionadas_edicao)
                update_disponibilidade_of_voluntario(id_voluntario_inteiro, servicos_selecionados_edicao)
                st.success(f"Dados de {nome_editado} atualizados com sucesso!")
                st.rerun()


        # --- SEÇÃO DINÂMICA (FORA DO FORMULÁRIO) ---
        st.subheader("Indisponibilidade Específica no Mês")
        
        coluna_mes, coluna_ano = st.columns(2)
        with coluna_mes:
            mes_para_ver = st.selectbox(
                "Selecione o Mês", 
                range(1, 13), 
                index=datetime.now().month - 1,
                format_func=lambda mes: calendar.month_name[mes].capitalize(),
                key=f"seletor_mes_{id_voluntario_atual}"
            )
        with coluna_ano:
            ano_para_ver = st.number_input(
                "Selecione o Ano", 
                min_value=datetime.now().year, 
                max_value=datetime.now().year + 5, 
                value=datetime.now().year,
                key=f"seletor_ano_{id_voluntario_atual}"
            )

        # --- FORMULÁRIO 2: INDISPONIBILIDADES ---
        with st.form(key=f"form_indisponibilidade_{id_voluntario_atual}"):
            st.markdown("**Marque os serviços em que o voluntário NÃO poderá servir:**")
            
            eventos_do_mes_df = get_events_for_month(ano_para_ver, mes_para_ver)
            disponibilidade_padrao_ids = get_disponibilidade_of_voluntario(id_voluntario_atual)
            eventos_filtrados_df = eventos_do_mes_df[eventos_do_mes_df['id_servico_fixo'].isin(disponibilidade_padrao_ids)].copy()
            if not eventos_filtrados_df.empty:
                eventos_filtrados_df['data_evento'] = pd.to_datetime(eventos_filtrados_df['data_evento'])
            
            eventos_por_servico = eventos_filtrados_df.groupby('nome_servico')
            eventos_ja_indisponiveis_ids = get_indisponibilidade_eventos(id_voluntario_atual, ano_para_ver, mes_para_ver)
            eventos_indisponiveis_selecionados_ids = []

            if eventos_filtrados_df.empty:
                st.info("Não há eventos neste mês para os serviços em que este voluntário está disponível.")
            else:
                servicos_disponiveis = sorted(eventos_filtrados_df['nome_servico'].unique())
                colunas_servicos = st.columns(len(servicos_disponiveis) or 1)
                for indice, nome_servico in enumerate(servicos_disponiveis):
                    with colunas_servicos[indice]:
                        st.markdown(f"**{nome_servico}**")
                        eventos_deste_servico = eventos_por_servico.get_group(nome_servico).sort_values('data_evento')
                        for _, evento in eventos_deste_servico.iterrows():
                            rotulo = evento['data_evento'].strftime('%d/%m')
                            selecionado = evento['id_evento'] in eventos_ja_indisponiveis_ids
                            if st.checkbox(rotulo, value=selecionado, key=f"indisponibilidade_{evento['id_evento']}"):
                                eventos_indisponiveis_selecionados_ids.append(evento['id_evento'])
            
            if st.form_submit_button("Salvar Indisponibilidades"):
                id_voluntario_inteiro = int(id_voluntario_atual)
                update_indisponibilidade_eventos(id_voluntario_inteiro, ano_para_ver, mes_para_ver, eventos_indisponiveis_selecionados_ids)
                st.success("Indisponibilidades salvas com sucesso!")
                st.rerun()
