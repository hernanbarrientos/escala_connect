import streamlit as st
# Importa as novas funções que criamos
from database import add_funcao, view_all_funcoes, update_funcao, delete_funcao

def main():
    st.set_page_config(page_title="Gestão de Voluntários", layout="wide")
    st.title("Sistema de Escala de Voluntários - CONNECT")

    # --- Seção para Gerenciar Funções ---
    st.header("Gerenciar Funções")

    # Formulário para adicionar nova função
    with st.form("nova_funcao_form", clear_on_submit=True):
        novo_nome = st.text_input("Nome da função", placeholder="Ex: Store")
        nova_descricao = st.text_area("Descrição (opcional)")
        submitted = st.form_submit_button("Adicionar Função")
        
        if submitted:
            if novo_nome:
                add_funcao(novo_nome, nova_descricao)
                # st.rerun() é o novo st.experimental_rerun(), atualiza a página
                st.rerun() 
            else:
                st.warning("O nome da função não pode ser vazio.")

    st.divider()

    # --- Seção para Visualizar e Editar Funções Existentes ---
    st.subheader("Funções Existentes")
    
    df_funcoes = view_all_funcoes()
    
    if df_funcoes.empty:
        st.info("Nenhuma função cadastrada ainda.")
    else:
        # Cria um cabeçalho para nossa lista
        col1, col2, col3 = st.columns([1, 2, 5])
        with col1:
            st.write("**Função**")
        with col2:
            st.write("**Ações**")
        
        # Itera sobre cada função cadastrada para criar os botões
        for index, row in df_funcoes.iterrows():
            id_funcao = row['id_funcao']
            nome_funcao = row['nome_funcao']
            descricao_funcao = row['descricao']

            col1, col2, col3 = st.columns([1, 2, 5])

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