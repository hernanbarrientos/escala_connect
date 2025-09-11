import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
from database import *
import style

# --- Verificação de Login no topo da página ---
if not st.session_state.get('logged_in'):
    st.switch_page("Login.py")

# Aplica o estilo global e a configuração da página
style.apply_style()
st.set_page_config(page_title="Gerenciar Voluntários", layout="wide")

# << NOVO: Dicionário com os meses em português para garantir a tradução >>
meses_pt = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

# Pega o ID do ministério do usuário logado
id_ministerio_logado = st.session_state['id_ministerio_logado']
todos_ministerios_df = get_all_ministerios()
nome_ministerio = todos_ministerios_df[todos_ministerios_df['id_ministerio'] == id_ministerio_logado]['nome_ministerio'].iloc[0]

st.title(f"Voluntários do Ministério {nome_ministerio}")

# --- Abas Principais ---
tab_cadastrar, tab_editar = st.tabs(["Cadastrar Novo Voluntário", "Editar Voluntário Existente"])

# --- ABA DE CADASTRO DE NOVO VOLUNTÁRIO ---
with tab_cadastrar:
    st.header("Formulário de Cadastro")

    # Busca funções e serviços do ministério logado
    todas_as_funcoes_cadastro = view_all_funcoes(id_ministerio_logado)
    todos_os_servicos_cadastro = view_all_servicos_fixos(id_ministerio_logado)

    with st.form(key="form_novo_voluntario", clear_on_submit=True):
        st.subheader("Dados Pessoais")
        coluna_nome, coluna_limite, coluna_experiencia = st.columns(3)
        with coluna_nome:
            novo_nome = st.text_input("Nome Completo*", key="novo_nome")
        with coluna_limite:
            novo_limite_mensal = st.number_input("Limite de escalas por mês*", min_value=1, max_value=10, value=2, key="novo_limite")
        with coluna_experiencia:   
            opcoes_nivel_novo = ["Iniciante", "Intermediário", "Avançado"]
            nivel_experiencia_novo = st.selectbox("Nível de Experiência*", opcoes_nivel_novo, key="novo_nivel")

        st.divider()
        coluna_funcoes, coluna_disponibilidade = st.columns(2)
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
        
        if st.form_submit_button("Cadastrar Voluntário"):
            if not novo_nome:
                st.warning("O campo 'Nome Completo' é obrigatório.")
            else:
                id_novo_voluntario = add_voluntario(novo_nome, int(novo_limite_mensal), nivel_experiencia_novo, id_ministerio_logado)
                if id_novo_voluntario:
                    update_funcoes_of_voluntario(id_novo_voluntario, [int(id) for id in funcoes_selecionadas_ids])
                    update_disponibilidade_of_voluntario(id_novo_voluntario, [int(id) for id in servicos_selecionados_ids])
                    st.success(f"Voluntário {novo_nome} cadastrado com sucesso!")
                    st.rerun()

# --- ABA DE EDIÇÃO DE VOLUNTÁRIO EXISTENTE ---
with tab_editar:
    st.header("Edição de Voluntários")

    mostrar_inativos = st.checkbox("Mostrar voluntários inativos na lista")
    # Busca voluntários do ministério logado
    voluntarios_para_editar_df = view_all_voluntarios(id_ministerio_logado, include_inactive=mostrar_inativos)
    
    if voluntarios_para_editar_df.empty:
        st.info("Nenhum voluntário cadastrado para este ministério.")
    else:
        lista_nomes_voluntarios = sorted(voluntarios_para_editar_df['nome_voluntario'].tolist())
        OPCAO_SELECIONE = "--- Selecione um voluntário ---"
        lista_nomes_voluntarios.insert(0, OPCAO_SELECIONE)

        voluntario_selecionado_nome = st.selectbox(
            "Selecione um voluntário para editar seus dados:",
            options=lista_nomes_voluntarios,
            key="seletor_voluntario_edicao"
        )

        if voluntario_selecionado_nome != OPCAO_SELECIONE:
            id_voluntario_atual = int(voluntarios_para_editar_df[voluntarios_para_editar_df['nome_voluntario'] == voluntario_selecionado_nome]['id_voluntario'].iloc[0])
            dados_voluntario = get_voluntario_by_id(id_voluntario_atual)
            
            # Busca funções e serviços do ministério logado
            todas_as_funcoes_edicao = view_all_funcoes(id_ministerio_logado)
            todos_os_servicos_edicao = view_all_servicos_fixos(id_ministerio_logado)

            with st.form(key=f"form_edicao_{id_voluntario_atual}"):
                st.header(f"Editando: {dados_voluntario['nome_voluntario']}")
                
                # ... (campos do formulário de edição)
                st.subheader("Dados Pessoais")
                coluna_nome_edicao, coluna_limite_edicao, coluna_experiencia_edicao = st.columns(3)
                with coluna_nome_edicao:
                    nome_editado = st.text_input("Nome Completo*", value=dados_voluntario['nome_voluntario'], key=f"edicao_nome_{id_voluntario_atual}")
                with coluna_limite_edicao:
                    limite_mensal_editado = st.number_input("Limite de escalas por mês*", min_value=1, max_value=10, value=int(dados_voluntario['limite_escalas_mes']), key=f"edicao_limite_{id_voluntario_atual}")
                with coluna_experiencia_edicao:    
                    opcoes_nivel = ["Iniciante", "Intermediário", "Avançado"]
                    nivel_atual = dados_voluntario.get('nivel_experiencia', 'Iniciante')
                    indice_atual = opcoes_nivel.index(nivel_atual) if nivel_atual in opcoes_nivel else 0
                    nivel_experiencia_editado = st.selectbox("Nível de Experiência*", opcoes_nivel, index=indice_atual, key=f"edicao_nivel_{id_voluntario_atual}")
                
                st.divider()
                # ... (resto dos campos)
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
                status_ativo_editado = st.checkbox("Voluntário Ativo", value=dados_voluntario['ativo'], key=f"edicao_ativo_{id_voluntario_atual}")

                if st.form_submit_button("Salvar Alterações"):
                    id_voluntario_inteiro = int(id_voluntario_atual)
                    update_voluntario(id_voluntario_inteiro, nome_editado, int(limite_mensal_editado), status_ativo_editado, nivel_experiencia_editado)
                    atualizar_funcoes_do_voluntario(id_voluntario_inteiro, funcoes_selecionadas_edicao)
                    update_disponibilidade_of_voluntario(id_voluntario_inteiro, servicos_selecionados_edicao)
                    st.success(f"Dados de {nome_editado} atualizados com sucesso!")
                    st.rerun()

            st.divider()
            st.subheader("Indisponibilidade Específica no Mês")
            
            coluna_mes, coluna_ano = st.columns(2)
            with coluna_mes:
                mes_para_ver = st.selectbox("Selecione o Mês", range(1, 13), index=datetime.now().month - 1, format_func=lambda mes: meses_pt[mes].capitalize(), key=f"seletor_mes_{id_voluntario_atual}")
            with coluna_ano:
                ano_para_ver = st.number_input("Selecione o Ano", min_value=datetime.now().year, max_value=datetime.now().year + 5, value=datetime.now().year, key=f"seletor_ano_{id_voluntario_atual}")
            
            with st.form(key=f"form_indisponibilidade_{id_voluntario_atual}"):
                st.markdown("**Marque os serviços em que o voluntário NÃO poderá servir:**")
                
                eventos_do_mes_df = get_events_for_month(ano_para_ver, mes_para_ver, id_ministerio_logado)
                # ... (resto da lógica de indisponibilidade)
                disponibilidade_padrao_ids = get_disponibilidade_of_voluntario(id_voluntario_atual)
                eventos_filtrados_df = eventos_do_mes_df[eventos_do_mes_df['id_servico_fixo'].isin(disponibilidade_padrao_ids)].copy()
                if not eventos_filtrados_df.empty:
                    eventos_filtrados_df['data_evento'] = pd.to_datetime(eventos_filtrados_df['data_evento'])
                
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
                            eventos_deste_servico = eventos_filtrados_df[eventos_filtrados_df['nome_servico'] == nome_servico].sort_values('data_evento')
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