from getpass import getpass
# Importa as funções do novo arquivo db_utils
from db_utils import get_all_ministerios_puro, criar_usuario_puro

def get_script_connection():
    """Lê as credenciais do novo local 'config/secrets.toml'."""
    try:
        # Caminho correto a partir da raiz do projeto
        secrets_path = os.path.join("backend", "config", "secrets.toml")
        secrets = toml.load(secrets_path)
        credentials = secrets["postgres"]
        if 'sslmode' not in credentials:
            credentials['sslmode'] = 'require'
        return psycopg2.connect(**credentials)
    except FileNotFoundError:
        print(f"ERRO: Arquivo de segredos não encontrado em '{secrets_path}'")
        return None
    except Exception as e:
        print(f"ERRO DE CONEXÃO: {e}")
        return None


def main():
    print("--- Ferramenta de Criação de Administradores ---")
    
    ministerios_df = get_all_ministerios_puro()
    if ministerios_df.empty:
        print("\nERRO: Nenhum ministério encontrado. Cadastre um ministério antes de criar um usuário.")
        return
        
    print("\nMinistérios disponíveis:")
    for _, row in ministerios_df.iterrows():
        print(f"  ID: {row['id_ministerio']} -> Nome: {row['nome_ministerio']}")
        
    try:
        id_ministerio = int(input("\nDigite o ID do ministério para o novo admin: "))
        if id_ministerio not in ministerios_df['id_ministerio'].values:
            print(f"ERRO: ID de ministério '{id_ministerio}' inválido.")
            return

        username = input("Digite o nome de usuário para o novo admin: ")
        password = getpass("Digite a senha para o novo admin: ")
        password_confirm = getpass("Confirme a senha: ")

        if password != password_confirm:
            print("\nERRO: As senhas não coincidem.")
            return
            
        if not username or not password:
            print("\nERRO: Usuário e senha não podem ser vazios.")
            return

        print(f"\nCriando usuário '{username}'...")
        sucesso = criar_usuario_puro(username, password, id_ministerio)
        if sucesso:
            print("Usuário criado com sucesso!")
        else:
            print("Falha ao criar usuário. Verifique o log de erro acima.")

    except ValueError:
        print("\nERRO: O ID do ministério precisa ser um número.")
    except Exception as e:
        print(f"\nOcorreu um erro inesperado: {e}")

if __name__ == "__main__":
    main()