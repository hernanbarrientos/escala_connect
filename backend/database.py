import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from dotenv import load_dotenv # <--- ADICIONE ISSO

# Força o Python a ler o .env onde quer que ele esteja
load_dotenv() 

# --- GERENCIAMENTO DE CONEXÃO ---
def get_db_connection():
    """Cria uma conexão nova com o banco."""
    try:
        # Tenta ler a variável. Se load_dotenv() funcionou, vai achar.
        db_url = os.environ.get('DATABASE_URL')
        
        if not db_url:
            # DEBUG: Se der erro, mostre onde ele está procurando
            print(f"ERRO: Não encontrei DATABASE_URL. Estou procurando na pasta: {os.getcwd()}")
            raise Exception("DATABASE_URL não configurada no .env")
            
        return psycopg2.connect(db_url)
    except Exception as e:
        print(f"Erro ao conectar no banco: {e}")
        return None

@contextmanager
def get_cursor():
    """
    Generator que entrega um cursor pronto para uso e fecha a conexão automaticamente depois.
    Usa RealDictCursor para retornar resultados como Dicionários (JSON Friendly).
    """
    conn = get_db_connection()
    if conn is None:
        yield None
        return

    try:
        # RealDictCursor faz o SELECT retornar {'nome': 'Joao', 'id': 1} ao invés de (1, 'Joao')
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Erro na transação SQL: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()

# --- FUNÇÕES DE CONSULTA GENÉRICAS (PARA REUTILIZAR) ---
def execute_select(query, params=None):
    """Executa SELECT e retorna lista de dicionários."""
    with get_cursor() as cur:
        if cur is None: return []
        cur.execute(query, params or ())
        return cur.fetchall()

def execute_select_one(query, params=None):
    """Executa SELECT e retorna apenas um item (ou None)."""
    with get_cursor() as cur:
        if cur is None: return None
        cur.execute(query, params or ())
        return cur.fetchone()

def execute_modify(query, params=None):
    """Executa INSERT, UPDATE, DELETE. Retorna ID gerado (se houver) ou True."""
    with get_cursor() as cur:
        if cur is None: return False
        cur.execute(query, params or ())
        # Tenta pegar o ID se foi um INSERT ... RETURNING id
        try:
            return cur.fetchone()
        except psycopg2.ProgrammingError:
            return True

# --- FUNÇÕES ESPECÍFICAS DO RENOVO HUB ---

def verificar_login_v2(email):
    """
    Busca usuário pelo email para o login.
    Retorna dados do usuário + dados da igreja dele.
    """
    query = """
        SELECT 
            u.id_usuario, u.nome, u.email, u.senha_hash, u.role, u.id_igreja,
            i.nome as nome_igreja, i.slug as slug_igreja
        FROM usuarios u
        JOIN igrejas i ON u.id_igreja = i.id_igreja
        WHERE u.email = %s AND u.ativo = TRUE
    """
    return execute_select_one(query, (email,))

def get_ministerios_da_igreja(id_igreja):
    """Lista simples de ministérios para o menu lateral."""
    query = """
        SELECT id_ministerio, nome, cor_hex 
        FROM ministerios 
        WHERE id_igreja = %s AND ativo = TRUE
        ORDER BY nome ASC
    """
    return execute_select(query, (id_igreja,))

def get_dashboard_stats(id_igreja):
    """
    Exemplo de como o SQL faz o trabalho pesado de contagem (antes era o Pandas).
    """
    # Conta voluntários ativos
    q_vol = "SELECT COUNT(*) as total FROM voluntario_vinculos vv JOIN ministerios m ON vv.id_ministerio = m.id_ministerio WHERE m.id_igreja = %s AND vv.ativo = TRUE"
    
    # Conta eventos no mês atual
    q_evt = "SELECT COUNT(*) as total FROM eventos e JOIN ministerios m ON e.id_ministerio = m.id_ministerio WHERE m.id_igreja = %s AND EXTRACT(MONTH FROM data_evento) = EXTRACT(MONTH FROM CURRENT_DATE)"
    
    total_voluntarios = execute_select_one(q_vol, (id_igreja,))
    total_eventos = execute_select_one(q_evt, (id_igreja,))
    
    return {
        "total_voluntarios": total_voluntarios['total'] if total_voluntarios else 0,
        "total_eventos": total_eventos['total'] if total_eventos else 0
    }

# ==============================================================================
# ÁREA DE VOLUNTÁRIOS (RENOVO HUB)
# ==============================================================================

def get_voluntarios_do_ministerio(id_ministerio):
    """
    Busca todos os voluntários vinculados a um ministério específico.
    Retorna nome, funções e status.
    """
    query = """
        SELECT 
            v.id_voluntario,
            v.nome_voluntario,
            v.email,
            vv.id_vinculo,
            vv.nivel_experiencia,
            vv.ativo,
            vv.funcoes_ids
        FROM voluntario_vinculos vv
        JOIN voluntarios v ON vv.id_voluntario = v.id_voluntario
        WHERE vv.id_ministerio = %s
        ORDER BY v.nome_voluntario ASC
    """
    return execute_select(query, (id_ministerio,))

def get_funcoes_ministerio(id_ministerio):
    """Lista as funções (cargos) disponíveis naquele ministério."""
    query = "SELECT id_funcao, nome_funcao FROM funcoes WHERE id_ministerio = %s"
    return execute_select(query, (id_ministerio,))

def adicionar_voluntario_vinculo(id_ministerio, id_igreja, dados):
    """
    A Lógica Inteligente:
    1. Verifica se o voluntário já existe na IGREJA (pelo email ou nome exato).
    2. Se existir, apenas cria o VÍNCULO com o ministério.
    3. Se não existir, cria o VOLUNTÁRIO e depois o VÍNCULO.
    """
    # 1. Tenta achar o voluntário na igreja
    q_busca = "SELECT id_voluntario FROM voluntarios WHERE email = %s AND id_igreja = %s"
    voluntario_existente = execute_select_one(q_busca, (dados.email, id_igreja))

    id_voluntario = None

    if voluntario_existente:
        id_voluntario = voluntario_existente['id_voluntario']
    else:
        # Cria novo voluntário
        q_cria = """
            INSERT INTO voluntarios (id_igreja, nome_voluntario, email, telefone)
            VALUES (%s, %s, %s, %s) RETURNING id_voluntario
        """
        novo = execute_modify(q_cria, (id_igreja, dados.nome, dados.email, dados.telefone))
        if novo: id_voluntario = novo['id_voluntario']

    if not id_voluntario:
        return None # Falha ao criar ou achar

    # 2. Cria o Vínculo (Se já não existir)
    q_vinculo = """
        INSERT INTO voluntario_vinculos (id_voluntario, id_ministerio, nivel_experiencia, funcoes_ids)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (id_voluntario, id_ministerio) DO NOTHING
        RETURNING id_vinculo
    """
    # Converte a lista de funções [1, 2] para o formato array do Postgres '{1,2}'
    return execute_modify(q_vinculo, (
        id_voluntario, 
        id_ministerio, 
        dados.nivel, 
        dados.funcoes_ids
    ))

def get_servicos_ministerio(id_ministerio):
    """Busca os dias/serviços fixos (ex: Domingo 18h) do ministério."""
    query = """
        SELECT id_servico, nome_servico, dia_semana, hora_inicio 
        FROM servicos_fixos 
        WHERE id_ministerio = %s
        ORDER BY id_servico ASC
    """
    return execute_select(query, (id_ministerio,))