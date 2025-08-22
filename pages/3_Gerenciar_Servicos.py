import streamlit as st
from database import add_servico_fixo, view_all_servicos_fixos, update_servico_fixo, delete_servico_fixo

st.set_page_config(page_title="Gerenciar Serviços", layout="wide")
st.title("Gerenciar Serviços Fixos")

# Dicionário para mapear o nome do dia da semana para o número
dias_semana_map = {
    "Domingo": 0, "Segunda-feira": 1, "Terça-feira": 2, 
    "Quarta-feira": 3, "Quinta-feira": 4, "Sexta-feira": 5, "Sábado": 6
}
# Dicionário inverso para exibição
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
            add_servico_fixo(nome_servico, dia_semana_num)
            st.rerun()
        else:
            st.warning("O nome do serviço é obrigatório.")

st.divider()

# Seção para visualizar e editar serviços
st.subheader("Serviços Cadastrados")
df_servicos = view_all_servicos_fixos()

if df_servicos.empty:
    st.info("Nenhum serviço fixo cadastrado ainda.")
else:
    for index, row in df_servicos.iterrows():
        with st.expander(f"{row['nome_servico']} ({dias_semana_inv_map.get(row['dia_da_semana'], 'Dia Inválido')})"):
            with st.form(f"edit_form_{row['id_servico']}"):
                
                edit_nome = st.text_input("Nome do Serviço", value=row['nome_servico'])
                
                dia_atual_nome = dias_semana_inv_map.get(row['dia_da_semana'])
                edit_dia_nome = st.selectbox("Dia da Semana", options=list(dias_semana_map.keys()), index=list(dias_semana_map.keys()).index(dia_atual_nome))
                
                edit_ativo = st.checkbox("Ativo", value=row['ativo'])

                col1, col2 = st.columns([1, 6])
                with col1:
                    if st.form_submit_button("Salvar"):
                        dia_edit_num = dias_semana_map[edit_dia_nome]
                        update_servico_fixo(row['id_servico'], edit_nome, dia_edit_num, edit_ativo)
                        st.rerun()
                with col2:
                    if st.form_submit_button("🗑️ Excluir"):
                        delete_servico_fixo(row['id_servico'])
                        st.rerun()