import streamlit as st
import pandas as pd
from database import (
    view_all_voluntarios, create_grupo_vinculado, get_all_grupos_com_membros,
    get_voluntarios_in_grupo, update_grupo_vinculado, delete_grupo_vinculado
)

st.set_page_config(page_title="Gerenciar Vínculos", layout="wide")
st.title("🔗 Gerenciar Vínculos entre Voluntários")
st.write("Crie grupos de voluntários que devem ser escalados sempre no mesmo dia (ex: famílias, casais, caronas).")

# --- ABA DE CADASTRO DE GRUPO ---
with st.expander("➕ Criar Novo Grupo de Vínculo", expanded=False):
    with st.form("form_novo_grupo", clear_on_submit=True):
        st.subheader("Novo Grupo")
        nome_novo_grupo = st.text_input("Nome do Grupo*", placeholder="Ex: Família Silva, Turma da Carona")
        
        # Seleciona voluntários que ainda não estão em nenhum grupo
        df_voluntarios_sem_grupo = view_all_voluntarios()
        df_voluntarios_sem_grupo = df_voluntarios_sem_grupo[df_voluntarios_sem_grupo['id_grupo'].isna()]
        
        membros_selecionados_ids = st.multiselect(
            "Selecione os voluntários para vincular*",
            options=df_voluntarios_sem_grupo['id_voluntario'],
            format_func=lambda id: df_voluntarios_sem_grupo[df_voluntarios_sem_grupo['id_voluntario'] == id]['nome_voluntario'].iloc[0]
        )
        
        if st.form_submit_button("Criar Grupo"):
            if not nome_novo_grupo or not membros_selecionados_ids:
                st.warning("O nome do grupo e a seleção de pelo menos dois voluntários são obrigatórios.")
            elif len(membros_selecionados_ids) < 2:
                st.warning("Um grupo precisa ter pelo menos dois voluntários.")
            else:
                create_grupo_vinculado(nome_novo_grupo, [int(id) for id in membros_selecionados_ids])
                st.rerun()

st.divider()

# --- VISUALIZAÇÃO E EDIÇÃO DOS GRUPOS EXISTENTES ---
st.header("Grupos Existentes")

df_grupos = get_all_grupos_com_membros()

if df_grupos.empty:
    st.info("Nenhum grupo de vínculo criado ainda.")
else:
    for _, grupo in df_grupos.iterrows():
        st.subheader(f"Grupo: {grupo['nome_grupo']}")
        st.write(f"**Membros:** {grupo['membros']}")
        
        with st.expander("Editar ou Desvincular Membros"):
            with st.form(f"form_edit_grupo_{grupo['id_grupo']}"):
                
                nome_edit_grupo = st.text_input("Editar Nome do Grupo", value=grupo['nome_grupo'])
                
                # Para editar, mostramos todos os voluntários: os que já estão no grupo e os que não têm grupo
                df_voluntarios_disponiveis = view_all_voluntarios()
                df_voluntarios_disponiveis = df_voluntarios_disponiveis[
                    (df_voluntarios_disponiveis['id_grupo'].isna()) | 
                    (df_voluntarios_disponiveis['id_grupo'] == grupo['id_grupo'])
                ]
                
                ids_membros_atuais = get_voluntarios_in_grupo(grupo['id_grupo'])
                
                membros_edit_selecionados_ids = st.multiselect(
                    "Selecione os voluntários para este grupo",
                    options=df_voluntarios_disponiveis['id_voluntario'],
                    default=ids_membros_atuais,
                    format_func=lambda id: df_voluntarios_disponiveis[df_voluntarios_disponiveis['id_voluntario'] == id]['nome_voluntario'].iloc[0],
                    key=f"multiselect_edit_{grupo['id_grupo']}"
                )
                
                # Botões de Salvar e Excluir
                col1, col2, col3 = st.columns([1, 1, 5])
                with col1:
                    if st.form_submit_button("Salvar"):
                        if not nome_edit_grupo or len(membros_edit_selecionados_ids) < 2:
                            st.warning("O nome do grupo e pelo menos dois membros são obrigatórios.")
                        else:
                            update_grupo_vinculado(grupo['id_grupo'], nome_edit_grupo, [int(id) for id in membros_edit_selecionados_ids])
                            st.rerun()
                with col2:
                    if st.form_submit_button("Excluir"):
                        delete_grupo_vinculado(grupo['id_grupo'])
                        st.rerun()