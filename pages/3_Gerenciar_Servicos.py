import streamlit as st
from database import (
    add_servico_fixo, view_all_servicos_fixos, update_servico_fixo, delete_servico_fixo,
    view_all_funcoes, get_cotas_for_servico, update_cotas_servico, get_all_ministerios
)
import style

# --- NOVO: Verificação de Login no topo da página ---
if not st.session_state.get('logged_in'):
    st.error("Acesso negado. Por favor, faça o login primeiro.")
    st.stop()

style.apply_style()

st.set_page_config(page_title="Gerenciar Serviços", layout="wide")

# --- NOVO: Pega dados do usuário logado ---
id_ministerio_logado = st.session_state['id_ministerio_logado']
todos_ministerios_df = get_all_ministerios()
nome_ministerio = todos_ministerios_df[todos_ministerios_df['id_ministerio'] == id_ministerio_logado]['nome_ministerio'].iloc[0]

st.title(f"Serviços e Cotas do Ministério {nome_ministerio}")

# Dicionário para mapear o nome do dia da semana para o número
dias_semana_map = {
    "Domingo": 0, "Segunda-feira": 1, "Terça-feira": 2, 
    "Quarta-feira": 3, "Quinta-feira": 4, "Sexta-feira": 5, "Sábado": 6
}
dias_semana_inv_map = {v: k for k, v in dias_semana_map.items()}

# Formulário para adicionar novo serviço
with st.form("novo_servico_form", clear_on_submit=True):
    st.subheader("Adicionar Novo Serviço Fixo")
    nome_servico = st.text_input("Nome do Serviço*", placeholder="Ex: Culto de Domingo - Manhã")
    dia_semana_nome = st.selectbox("Dia da Semana*", options=list(dias_semana_map.keys()))
    
    submitted = st.form_submit_button("Adicionar Serviço")
    if submitted:
        if nome_servico:
            dia_semana_num = dias_semana_map[dia_semana_nome]
            # << ALTERADO: Passa o id_ministerio_logado para a função
            add_servico_fixo(nome_servico, dia_semana_num, id_ministerio_logado)
            st.rerun() 
        else:
            st.warning("O nome do serviço é obrigatório.")

st.divider()

# Seção para visualizar e editar serviços e cotas
st.header("Serviços Cadastrados")

# << ALTERADO: Busca serviços e funções filtrando pelo ministério logado
df_servicos = view_all_servicos_fixos(id_ministerio_logado)
df_funcoes = view_all_funcoes(id_ministerio_logado)

if df_servicos.empty:
    st.info("Nenhum serviço fixo cadastrado para este ministério.")
else:
    for _, servico in df_servicos.iterrows():
        # Expander para cada serviço
        expander_title = f"{servico['nome_servico']} ({dias_semana_inv_map.get(servico['dia_da_semana'], 'Dia Inválido')})"
        with st.expander(expander_title):
            
            with st.form(f"form_edit_servico_{servico['id_servico']}"):
                st.subheader("Editar Dados do Serviço")
                
                edit_nome = st.text_input("Nome do Serviço", value=servico['nome_servico'])
                dia_atual_nome = dias_semana_inv_map.get(servico['dia_da_semana'])
                edit_dia_nome = st.selectbox(
                    "Dia da Semana", 
                    options=list(dias_semana_map.keys()), 
                    index=list(dias_semana_map.keys()).index(dia_atual_nome)
                )
                edit_ativo = st.checkbox("Serviço Ativo", value=servico['ativo'])
                
                st.divider()
                st.subheader("Cotas de Funções (Quantas pessoas são necessárias)")
                
                # Busca as cotas atuais para este serviço
                cotas_atuais = get_cotas_for_servico(servico['id_servico'])
                cotas_para_salvar = {}

                # Cria um campo numérico para cada função existente no ministério
                for _, funcao in df_funcoes.iterrows():
                    quantidade_atual = cotas_atuais.get(funcao['id_funcao'], 0)
                    cotas_para_salvar[funcao['id_funcao']] = st.number_input(
                        f"Nº de vagas para '{funcao['nome_funcao']}'", 
                        min_value=0, 
                        max_value=20, 
                        value=quantidade_atual, 
                        key=f"cota_{servico['id_servico']}_{funcao['id_funcao']}"
                    )

                # Botões de ação
                col1, col2, col3 = st.columns([2, 2, 8])
                with col1:
                    if st.form_submit_button("Salvar Todas as Alterações"):
                        dia_edit_num = dias_semana_map[edit_dia_nome]
                        # Atualiza os dados do serviço E as cotas
                        update_servico_fixo(servico['id_servico'], edit_nome, dia_edit_num, edit_ativo)
                        update_cotas_servico(servico['id_servico'], cotas_para_salvar)
                        st.rerun() 
                with col2:
                    if st.form_submit_button("🗑️ Excluir Serviço"):
                        delete_servico_fixo(servico['id_servico'])
                        st.rerun()