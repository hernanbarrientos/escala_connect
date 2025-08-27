import streamlit as st
import pandas as pd
from datetime import datetime
from database import (
    add_voluntario, view_all_voluntarios, get_voluntario_by_id, update_voluntario,
    view_all_funcoes, get_funcoes_of_voluntario, update_funcoes_of_voluntario,
    view_all_servicos_fixos, get_disponibilidade_of_voluntario, update_disponibilidade_of_voluntario,
    check_indisponibilidade, set_indisponibilidade
)
import style


style.apply_style()


st.set_page_config(page_title="Gerenciar Voluntários", layout="wide")
st.title("Cadastro e Gestão de Voluntários")

# --- CRIAÇÃO DAS ABAS ---
tab_cadastrar, tab_editar = st.tabs(["Cadastrar Novo Voluntário", "Editar Voluntário Existente"])

# --- ABA DE CADASTRO ---
with tab_cadastrar:
    st.header("Formulário de Cadastro")

    all_funcoes_df_cad = view_all_funcoes()
    all_servicos_df_cad = view_all_servicos_fixos()

    with st.form(key="form_novo_voluntario", clear_on_submit=True):
        st.subheader("Dados Pessoais")
        # --- DADOS PESSOAIS EM COLUNAS ---
        col_nome, col_tel, col_limite = st.columns(3)
        with col_nome:
            nome = st.text_input("Nome Completo*")
        with col_tel:
            telefone = st.text_input("Telefone")
        with col_limite:
            limite_mes = st.number_input("Limite de escalas por mês*", min_value=1, max_value=10, value=2)

        st.divider()

        # --- LAYOUT EM COLUNAS PARA CHECKBOXES ---
        col_funcoes, col_disponibilidade, col_status = st.columns(3)
        with col_funcoes:
            st.subheader("Funções que pode exercer")
            funcoes_selecionadas_ids = []
            for func_row in all_funcoes_df_cad.itertuples():
                if st.checkbox(func_row.nome_funcao, key=f"new_func_{func_row.id_funcao}"):
                    funcoes_selecionadas_ids.append(func_row.id_funcao)

        with col_disponibilidade:
            st.subheader("Disponibilidade Padrão")
            servicos_selecionados_ids = []
            for serv_row in all_servicos_df_cad.itertuples():
                if st.checkbox(serv_row.nome_servico, key=f"new_disp_{serv_row.id_servico}"):
                    servicos_selecionados_ids.append(serv_row.id_servico)
        
        with col_status:
            st.subheader("Status do Voluntário")
            st.info("O status inicial é sempre 'Ativo'. A indisponibilidade mensal pode ser definida após o cadastro na aba de edição.")

        if st.form_submit_button("Cadastrar Voluntário"):
            if not nome:
                st.warning("O campo 'Nome Completo' é obrigatório.")
            else:
                add_voluntario(nome, telefone, int(limite_mes))
                novo_voluntario_df = view_all_voluntarios()
                id_novo_voluntario = int(novo_voluntario_df[novo_voluntario_df['nome_voluntario'] == nome]['id_voluntario'].iloc[0])
                
                update_funcoes_of_voluntario(id_novo_voluntario, [int(id) for id in funcoes_selecionadas_ids])
                update_disponibilidade_of_voluntario(id_novo_voluntario, [int(id) for id in servicos_selecionados_ids])
                
                st.success(f"Voluntário {nome} cadastrado com sucesso!")

# --- ABA DE EDIÇÃO ---
# --- ABA DE EDIÇÃO ---
with tab_editar:
    st.header("Edição de Voluntários")

    # --- NOVO CHECKBOX DE FILTRO ---
    show_inactive = st.checkbox("Mostrar voluntários inativos na lista")

    # Usa o checkbox para decidir quais voluntários buscar
    df_voluntarios_edit = view_all_voluntarios(include_inactive=show_inactive)
    lista_nomes_voluntarios = sorted(df_voluntarios_edit['nome_voluntario'].tolist())
    
    OPCAO_SELECIONE = "--- Selecione um voluntário ---"
    lista_nomes_voluntarios.insert(0, OPCAO_SELECIONE)

    voluntario_selecionado_nome = st.selectbox(
        "Selecione um voluntário para editar seus dados:",
        options=lista_nomes_voluntarios
    )

    if voluntario_selecionado_nome != OPCAO_SELECIONE:
        
        id_voluntario_atual = int(df_voluntarios_edit[df_voluntarios_edit['nome_voluntario'] == voluntario_selecionado_nome]['id_voluntario'].iloc[0])
        voluntario_data = get_voluntario_by_id(id_voluntario_atual)
        
        all_funcoes_df_edit = view_all_funcoes()
        all_servicos_df_edit = view_all_servicos_fixos()

        with st.form(key=f"form_edit_{id_voluntario_atual}"):
            st.subheader(f"Editando: {voluntario_data['nome_voluntario']}")

            # --- DADOS PESSOAIS EM COLUNAS ---
            col_nome_edit, col_tel_edit, col_limite_edit = st.columns(3)
            with col_nome_edit:
                nome_edit = st.text_input("Nome Completo*", value=voluntario_data['nome_voluntario'])
            with col_tel_edit:
                telefone_edit = st.text_input("Telefone", value=voluntario_data['telefone'])
            with col_limite_edit:
                limite_mes_edit = st.number_input("Limite de escalas por mês*", min_value=1, max_value=10, value=int(voluntario_data['limite_escalas_mes']))

            st.divider()

            # --- LAYOUT EM COLUNAS PARA CHECKBOXES ---
            col_funcoes_edit, col_disponibilidade_edit, col_status_edit = st.columns(3)
            with col_funcoes_edit:
                st.subheader("Funções que pode exercer")
                funcoes_atuais_ids = get_funcoes_of_voluntario(id_voluntario_atual)
                funcoes_selecionadas_edit = []
                for func_row in all_funcoes_df_edit.itertuples():
                    is_checked = func_row.id_funcao in funcoes_atuais_ids
                    if st.checkbox(func_row.nome_funcao, value=is_checked, key=f"edit_func_{id_voluntario_atual}_{func_row.id_funcao}"):
                        funcoes_selecionadas_edit.append(func_row.id_funcao)
            
            with col_disponibilidade_edit:
                st.subheader("Disponibilidade Padrão")
                disponibilidade_atual_ids = get_disponibilidade_of_voluntario(id_voluntario_atual)
                servicos_selecionados_edit = []
                for serv_row in all_servicos_df_edit.itertuples():
                    is_checked = serv_row.id_servico in disponibilidade_atual_ids
                    if st.checkbox(serv_row.nome_servico, value=is_checked, key=f"edit_disp_{id_voluntario_atual}_{serv_row.id_servico}"):
                        servicos_selecionados_edit.append(serv_row.id_servico)

            with col_status_edit:
                st.subheader("Status do Voluntário")
                ativo_edit = st.checkbox("Voluntário Ativo", value=voluntario_data['ativo'])
                
                mes_ano_atual = datetime.now().strftime('%Y-%m')
                nome_mes_pt = "Agosto"
                
                indisponivel_mes_atual = check_indisponibilidade(id_voluntario_atual, mes_ano_atual)
                nao_escalar_mes = st.checkbox(f"Não escalar em {nome_mes_pt}/{datetime.now().year}", value=indisponivel_mes_atual)
            
            if st.form_submit_button("Salvar Alterações"):
                id_voluntario_int = int(id_voluntario_atual)
                update_voluntario(id_voluntario_int, nome_edit, telefone_edit, int(limite_mes_edit), ativo_edit)
                update_funcoes_of_voluntario(id_voluntario_int, [int(id) for id in funcoes_selecionadas_edit])
                update_disponibilidade_of_voluntario(id_voluntario_int, [int(id) for id in servicos_selecionados_edit])
                set_indisponibilidade(id_voluntario_int, mes_ano_atual, nao_escalar_mes)
                st.success(f"Dados de {nome_edit} atualizados com sucesso!")
                st.rerun()