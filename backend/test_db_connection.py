import os
import psycopg2
from psycopg2 import OperationalError

def test_connection(db_url):
    print(f"\n--- Testando conexão com: {db_url} ---")
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print("✅ Conexão bem-sucedida!")
        print("Versão do PostgreSQL:", version)
        cur.close()
        conn.close()
    except OperationalError as e:
        print("❌ Erro de conexão:", e)

if __name__ == "__main__":
    # Testa URL do ambiente (Render → Environment Variable)
    db_url_env = os.getenv("DATABASE_URL")
    if db_url_env:
        test_connection(db_url_env)
    else:
        print("⚠️ Variável DATABASE_URL não encontrada.")

    # Testa manualmente as duas portas (5432 e 6543) para comparar
    db_url_direct = "postgresql://USUARIO:SENHA@aws-1-sa-east-1.supabase.com:5432/postgres"
    db_url_pool = "postgresql://USUARIO:SENHA@aws-1-sa-east-1.pooler.supabase.com:6543/postgres?sslmode=require"

    test_connection(db_url_direct)
    test_connection(db_url_pool)
