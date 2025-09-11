import streamlit as st
# Importa as funções do banco de dados, incluindo a de ministérios
from database import add_funcao, view_all_funcoes, update_funcao, delete_funcao, get_all_ministerios
import style

# --- NOVO: Verificação de Login no topo da página ---
# Esta verificação deve ser adicionada em TODAS as páginas, exceto a de Login.
if not st.session_state.get('logged_in'):
    st.switch_page("Login.py")

# Aplica o estilo global
style.apply_style()

def main():
    st.set_page_config(page_title="Gerenciar Funções", layout="wide")
    
    # Pega o ID do ministério que foi salvo no momento do login
    id_ministerio_logado = st.session_state['id_ministerio_logado']
    
    # Busca o nome do ministério para uma mensagem de boas-vindas
    todos_ministerios_df = get_all_ministerios()
    nome_ministerio = todos_ministerios_df[todos_ministerios_df['id_ministerio'] == id_ministerio_logado]['nome_ministerio'].iloc[0]
    
    st.title(f"Funções do Ministério {nome_ministerio}")

    # --- Seção para Gerenciar Funções ---
    st.header("Adicionar e Editar Funções")

    # Formulário para adicionar nova função
    with st.form("nova_funcao_form", clear_on_submit=True):
        novo_nome = st.text_input("Nome da função", placeholder="Ex: Store")
        nova_descricao = st.text_area("Descrição (opcional)")
        submitted = st.form_submit_button("Adicionar Função")
        
        if submitted:
            if novo_nome:
                # A função agora recebe o ID do ministério do usuário logado
                add_funcao(novo_nome, nova_descricao, id_ministerio_logado)
                st.rerun() 
            else:
                st.warning("O nome da função não pode ser vazio.")

    st.divider()

    # --- Seção para Visualizar e Editar Funções Existentes ---
    st.subheader("Funções Existentes")
    
    # A função agora busca apenas as funções do ministério do usuário logado
    df_funcoes = view_all_funcoes(id_ministerio_logado)
    
    if df_funcoes.empty:
        st.info("Nenhuma função cadastrada para este ministério ainda.")
    else:
        # Cria um cabeçalho para nossa lista
        col1, col2, col3 = st.columns([2, 2, 8])
        with col1:
            st.write("**Função**")
        with col2:
            st.write("**Ações**")
        
        # Itera sobre cada função cadastrada para criar os botões
        for index, row in df_funcoes.iterrows():
            id_funcao = row['id_funcao']
            nome_funcao = row['nome_funcao']
            descricao_funcao = row['descricao']

            col1, col2, col3 = st.columns([2, 2, 8])

            with col1:
                st.write(nome_funcao)

            with col2:
                # Botão de Editar abre um pop-up (st.expander)
                with st.expander("✏️ Editar"):
                    with st.form(f"edit_form_{id_funcao}"):
                        novo_nome_edit = st.text_input("Novo nome", value=nome_funcao, key=f"nome_{id_funcao}")
                        nova_descricao_edit = st.text_area("Nova descrição", value=descricao_funcao, key=f"desc_{id_funcao}")
                        
                        if st.form_submit_button("Salvar"):
                            update_funcao(id_funcao, novo_nome_edit, nova_descricao_edit)
                            st.rerun()

            with col3:
                # Botão de Excluir
                if st.button("🗑️ Excluir", key=f"del_{id_funcao}"):
                    delete_funcao(id_funcao)
                    st.rerun()

if __name__ == '__main__':
    main()