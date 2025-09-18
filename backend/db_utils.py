import psycopg2
import pandas as pd
import toml
import os
from werkzeug.security import generate_password_hash, check_password_hash

# --- LÓGICA DE CONEXÃO UNIVERSAL E PURA ---
_db_credentials = None

def ensure_connection():
    """
    Cria uma conexão com o banco de dados usando a variável de ambiente DATABASE_URL.
    Funciona tanto localmente (lendo o .env) quanto na produção (Render).
    """
    try:
        # Pega a única string de conexão do ambiente.
        db_url = os.environ.get('DATABASE_URL')
        
        if not db_url:
            print("ERRO CRÍTICO: A variável de ambiente DATABASE_URL não foi definida.")
            return None
            
        # Conecta usando a URL, que é o método mais robusto.
        return psycopg2.connect(db_url)
        
    except Exception as e:
        print(f"ERRO DE CONEXÃO: {e}")
        return None

# --- FUNÇÕES DE AUTENTICAÇÃO PURAS ---

def verificar_login_puro(username, password):
    """Verifica o login e retorna o id_ministerio. Sem dependências do Streamlit."""
    conn = ensure_connection()
    if conn is None: return None
    
    id_ministerio = None
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT password_hash, id_ministerio FROM usuarios WHERE username = %s", (username,))
            result = cur.fetchone()
            if result:
                password_hash_from_db, id_ministerio_from_db = result
                if check_password_hash(password_hash_from_db, password):
                    id_ministerio = id_ministerio_from_db
    except Exception as e:
        print(f"Erro durante a verificação de login: {e}")
        return None
    finally:
        if conn: conn.close()
    return id_ministerio

def criar_usuario_puro(username, password, id_ministerio):
    """Cria um novo usuário. Sem dependências do Streamlit."""
    conn = ensure_connection()
    if conn is None: return False
    try:
        with conn.cursor() as cur:
            password_hash = generate_password_hash(password)
            cur.execute(
                "INSERT INTO usuarios (username, password_hash, id_ministerio) VALUES (%s, %s, %s)",
                (username, password_hash, id_ministerio)
            )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Erro ao criar usuário: {e}")
        return False

def get_all_ministerios_puro():
    """Busca todos os ministérios. Sem dependências do Streamlit."""
    conn = ensure_connection()
    if conn is None: return pd.DataFrame()
    try:
        query = "SELECT id_ministerio, nome_ministerio FROM ministerios ORDER BY nome_ministerio"
        return pd.read_sql(query, conn)
    except Exception as e:
        print(f"Erro ao buscar ministérios: {e}")
        return pd.DataFrame()
    finally:
        if conn: conn.close()