import streamlit as st
import time
import pandas as pd
from database import (
    get_all_voluntarios_com_detalhes, get_voluntarios_sem_grupo, get_all_grupos_com_membros,
    create_grupo, get_voluntarios_do_grupo, update_grupo, delete_grupo,
    view_all_servicos_fixos, update_apenas_disponibilidade # Novas importações
)
import style


style.apply_style()

st.set_page_config(page_title="Gerenciar Vínculos", layout="wide")
st.title("🔗 Gerenciar Vínculos (Grupos)")
st.info("Crie e edite grupos de voluntários que devem ser escalados sempre no mesmo dia. Limite de 4 pessoas por grupo.")

# --- FUNÇÃO DE VALIDAÇÃO ---
def validar_disponibilidade_comum(ids_selecionados, df_voluntarios):
    if len(ids_selecionados) < 2: return True
    disponibilidades = []
    for vol_id in ids_selecionados:
        disponibilidade_vol = df_voluntarios[df_voluntarios['id_voluntario'] == vol_id]['disponibilidade'].iloc[0]
        if disponibilidade_vol is None: return False
        disponibilidades.append(set(disponibilidade_vol))
    return len(set.intersection(*disponibilidades)) > 0

# Carrega dados essenciais uma vez
todos_voluntarios_df = get_all_voluntarios_com_detalhes()
todos_servicos_df = view_all_servicos_fixos()

# --- FORMULÁRIO DE CRIAÇÃO DE GRUPO ---
with st.expander("➕ Criar Novo Grupo", expanded=True):
    with st.form("form_novo_grupo"):
        nome_grupo = st.text_input("Nome do Grupo*", placeholder="Ex: Família Silva")
        voluntarios_sem_grupo = get_voluntarios_sem_grupo()
        
        membros_selecionados = st.multiselect(
            "Selecione de 2 a 4 voluntários para o grupo*",
            options=voluntarios_sem_grupo['id_voluntario'],
            format_func=lambda id: voluntarios_sem_grupo[voluntarios_sem_grupo['id_voluntario'] == id]['nome_voluntario'].iloc[0]
        )
        
        if st.form_submit_button("Criar Grupo"):
            if not nome_grupo or not (2 <= len(membros_selecionados) <= 4):
                st.warning("O nome do grupo e a seleção de 2 a 4 membros são obrigatórios.")
            elif not validar_disponibilidade_comum(membros_selecionados, todos_voluntarios_df):
                st.warning("Os membros selecionados não possuem um dia em comum. Ajuste as disponibilidades abaixo.")
                # Guarda os dados para o "modal" de correção
                st.session_state.correcao_necessaria = True
                st.session_state.membros_para_corrigir = membros_selecionados
                st.session_state.nome_grupo_pendente = nome_grupo
                st.rerun()
            else:
                create_grupo(nome_grupo, [int(id) for id in membros_selecionados])
                st.session_state.correcao_necessaria = False
                st.rerun()

# --- "MODAL" DE CORREÇÃO DE DISPONIBILIDADE ---
if st.session_state.get("correcao_necessaria", False):
    st.divider()
    with st.container(border=True):
        st.subheader("⚠️ Ação Necessária: Corrigir Disponibilidades")
        st.write("Para criar o grupo, todos os membros devem ter pelo menos um dia de disponibilidade em comum. Ajuste abaixo:")

        membros_df = todos_voluntarios_df[todos_voluntarios_df['id_voluntario'].isin(st.session_state.membros_para_corrigir)]
        
        disponibilidades_atualizadas = {}

        for _, membro in membros_df.iterrows():
            st.markdown(f"**{membro['nome_voluntario']}**")
            disponibilidade_atual = membro['disponibilidade'] if membro['disponibilidade'] is not None else []
            
            cols = st.columns(len(todos_servicos_df))
            disponibilidade_nova = []
            for i, servico in todos_servicos_df.iterrows():
                with cols[i]:
                    if st.checkbox(servico['nome_servico'], value=(servico['id_servico'] in disponibilidade_atual), key=f"corr_{membro['id_voluntario']}_{servico['id_servico']}"):
                        disponibilidade_nova.append(servico['id_servico'])
            disponibilidades_atualizadas[membro['id_voluntario']] = disponibilidade_nova

        if st.button("Salvar Disponibilidades e Tentar Criar Grupo Novamente", type="primary"):
            # Salva as novas disponibilidades
            for vol_id, disp_ids in disponibilidades_atualizadas.items():
                update_apenas_disponibilidade(vol_id, disp_ids)
            
            # Limpa o estado e tenta criar o grupo de novo
            st.session_state.correcao_necessaria = False
            # Recarrega os dados para a nova validação
            todos_voluntarios_df_recarregado = get_all_voluntarios_com_detalhes()

            if validar_disponibilidade_comum(st.session_state.membros_para_corrigir, todos_voluntarios_df_recarregado):
                create_grupo(st.session_state.nome_grupo_pendente, [int(id) for id in st.session_state.membros_para_corrigir])
                st.success(f"Grupo '{st.session_state.nome_grupo_pendente}' criado com sucesso após o ajuste!")
                # Limpa os dados pendentes
                del st.session_state.membros_para_corrigir
                del st.session_state.nome_grupo_pendente
                st.rerun()
            else:
                st.error("Ainda não há um dia em comum. Verifique as seleções.")
                st.session_state.correcao_necessaria = True # Mantém o modal aberto
                st.rerun()

st.divider()

# --- VISUALIZAÇÃO E EDIÇÃO DOS GRUPOS EXISTENTES ---
# (O código para editar grupos existentes continua o mesmo)
st.header("Grupos Existentes")

# --- AQUI ESTÁ A CORREÇÃO ---
# Chamamos a função com o parâmetro de quebra de cache
df_grupos = get_all_grupos_com_membros(_cache_buster=time.time())

if df_grupos.empty:
    st.info("Nenhum grupo cadastrado.")
else:
    for _, grupo in df_grupos.iterrows():
        st.subheader(f"Editando Grupo: {grupo['nome_grupo']}")
        st.write(f"**Membros Atuais:** {grupo['membros']}")

        with st.form(f"form_edit_{grupo['id_grupo']}"):
            novo_nome = st.text_input("Editar nome do grupo", value=grupo['nome_grupo'])
            
            membros_atuais_df = get_voluntarios_do_grupo(grupo['id_grupo'])
            voluntarios_disponiveis_df = pd.concat([membros_atuais_df, get_voluntarios_sem_grupo()]).drop_duplicates().reset_index(drop=True)
            
            membros_edit_selecionados = st.multiselect(
                "Editar membros (selecione de 2 a 4)",
                options=voluntarios_disponiveis_df['id_voluntario'],
                default=membros_atuais_df['id_voluntario'].tolist(),
                format_func=lambda id: voluntarios_disponiveis_df[voluntarios_disponiveis_df['id_voluntario'] == id]['nome_voluntario'].iloc[0]
            )
            
            col1, col2 = st.columns([1, 5])
            with col1:
                if st.form_submit_button("Salvar"):
                    if not novo_nome or not (2 <= len(membros_edit_selecionados) <= 4):
                        st.warning("O nome do grupo e a seleção de 2 a 4 membros são obrigatórios.")
                    elif not validar_disponibilidade_comum(membros_edit_selecionados, todos_voluntarios_df):
                        st.error("Erro: Os membros selecionados não possuem nenhum dia de disponibilidade em comum.")
                    else:
                        update_grupo(grupo['id_grupo'], novo_nome, [int(id) for id in membros_edit_selecionados])
                        st.rerun()
            with col2:
                if st.form_submit_button("Excluir Grupo"):
                    delete_grupo(grupo['id_grupo'])
                    st.rerun()
        st.divider()