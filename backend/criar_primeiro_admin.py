# Arquivo: criar_primeiro_admin.py

import pandas as pd
from getpass import getpass  # Para digitar a senha de forma segura no terminal
from database import get_all_ministerios, criar_usuario

def main():
    print("--- Ferramenta de Criação de Administradores ---")
    
    # 1. Listar os ministérios disponíveis
    ministerios_df = get_all_ministerios()
    if ministerios_df.empty:
        print("\nERRO: Nenhum ministério encontrado no banco de dados.")
        print("Por favor, cadastre um ministério primeiro antes de criar um usuário.")
        return
        
    print("\nMinistérios disponíveis:")
    for _, row in ministerios_df.iterrows():
        print(f"  ID: {row['id_ministerio']} -> Nome: {row['nome_ministerio']}")
        
    # 2. Pedir os dados ao usuário
    try:
        id_ministerio_input = input("\nDigite o ID do ministério para o novo admin: ")
        id_ministerio = int(id_ministerio_input)
        
        # Valida se o ID existe
        if id_ministerio not in ministerios_df['id_ministerio'].values:
            print(f"ERRO: ID de ministério '{id_ministerio}' inválido.")
            return

        username = input("Digite o nome de usuário para o novo admin: ")
        password = getpass("Digite a senha para o novo admin: ")
        password_confirm = getpass("Confirme a senha: ")

        if password != password_confirm:
            print("\nERRO: As senhas não coincidem. Operação cancelada.")
            return
            
        if not username or not password:
            print("\nERRO: Usuário e senha não podem ser vazios. Operação cancelada.")
            return

        # 3. Chamar a função para criar o usuário no banco
        print(f"\nCriando usuário '{username}' para o ministério ID {id_ministerio}...")
        criar_usuario(username, password, id_ministerio)
        print("\nOperação concluída. Verifique a mensagem de sucesso ou erro acima.")

    except ValueError:
        print("\nERRO: O ID do ministério precisa ser um número. Operação cancelada.")
    except Exception as e:
        print(f"\nOcorreu um erro inesperado: {e}")

if __name__ == "__main__":
    main()