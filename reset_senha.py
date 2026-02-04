import sys
sys.path.append(".") 

from backend.auth import get_password_hash
from backend.database import execute_modify

print("--- RESET DE SENHA (MIGRAÇÃO ARGON2) ---")

email = input("Digite o email do Admin (ex: admin@renovo.com): ")
nova_senha = input("Digite a nova senha: ")

# 1. Gera o hash novo usando Argon2 (agora configurado no auth.py)
novo_hash = get_password_hash(nova_senha)

# 2. Atualiza no banco
query = "UPDATE usuarios SET senha_hash = %s WHERE email = %s RETURNING id_usuario"
result = execute_modify(query, (novo_hash, email))

if result:
    print(f"✅ Sucesso! Senha atualizada para o usuário {email}.")
    print("Pode tentar logar no frontend agora.")
else:
    print("❌ Erro: Usuário não encontrado ou falha no banco.")