import sys
# Adiciona o diretório atual ao path para encontrar os módulos
sys.path.append(".") 

from backend.auth import get_password_hash
from backend.database import execute_modify, execute_select_one

print("--- CRIANDO ADMIN (RENOVO HUB) ---")

slug_igreja = 'renovo-sede'

# 1. Verifica se a igreja já existe
sql_check = "SELECT id_igreja FROM igrejas WHERE slug = %s"
igreja_existente = execute_select_one(sql_check, (slug_igreja,))

if igreja_existente:
    id_igreja = igreja_existente['id_igreja']
    print(f"✅ Igreja encontrada (ID: {id_igreja}). Usando ela.")
else:
    # Se não existe, cria
    print("Igreja não encontrada. Criando nova...")
    sql_igreja = "INSERT INTO igrejas (nome, slug, cidade) VALUES (%s, %s, %s) RETURNING id_igreja"
    res_igreja = execute_modify(sql_igreja, ('Igreja Renovo', slug_igreja, 'São Paulo'))
    if not res_igreja:
        print("Erro fatal ao criar igreja.")
        exit()
    id_igreja = res_igreja['id_igreja']
    print(f"✅ Igreja criada com sucesso (ID: {id_igreja})")

# 2. Criar Usuário Admin
email = input("Digite o Email do Admin: ")

# Verifica se o usuário já existe para evitar outro erro de duplicidade
user_check = execute_select_one("SELECT id_usuario FROM usuarios WHERE email = %s", (email,))

if user_check:
    print(f"❌ Erro: O usuário {email} já existe neste banco.")
else:
    senha = input("Digite a Senha do Admin: ")
    senha_hash = get_password_hash(senha)
    
    sql_user = """
        INSERT INTO usuarios (id_igreja, nome, email, senha_hash, role)
        VALUES (%s, %s, %s, %s, 'ADMIN_GERAL')
        RETURNING id_usuario
    """
    res_user = execute_modify(sql_user, (id_igreja, 'Admin', email, senha_hash))
    
    if res_user:
        print(f"🚀 SUCESSO! Usuário Admin criado (ID: {res_user['id_usuario']}).")
        print("Agora você pode rodar o backend e fazer login.")
    else:
        print("Erro ao criar usuário.")