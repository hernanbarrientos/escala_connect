# database.py - VERSÃO FINAL (V30 - FASES HIERÁRQUICAS)


import psycopg2
import pandas as pd
from collections import defaultdict
from datetime import datetime, date
import calendar
import random
from werkzeug.security import generate_password_hash, check_password_hash
from dataclasses import dataclass, field
from typing import List, Set
import os
import toml

# --- LÓGICA DE CONEXÃO UNIVERSAL E PURA ---


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
        
# --- CORREÇÃO FINAL EM verificar_login ---
def verificar_login(username, password):
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
    finally:
        if conn: conn.close()
    return id_ministerio

def criar_usuario(username, password, id_ministerio):
    conn = ensure_connection()
    if conn is None: return False
    try:
        with conn.cursor() as cur:
            password_hash = generate_password_hash(password)
            cur.execute("INSERT INTO usuarios (username, password_hash, id_ministerio) VALUES (%s, %s, %s)", (username, password_hash, id_ministerio))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Erro ao criar usuário: {e}")
        return False
    finally:
        if conn: conn.close()

# def verificar_login(username, password):
#     """Verifica o login e retorna o id_ministerio se for válido."""
#     conn = ensure_connection()
#     if conn is None: return None
    
#     id_ministerio = None # Valor padrão
#     try:
#         with conn.cursor() as cur:
#             cur.execute("SELECT password_hash, id_ministerio FROM usuarios WHERE username = %s", (username,))
#             result = cur.fetchone()
#             if result:
#                 password_hash_from_db, id_ministerio_from_db = result
#                 # A verificação crucial acontece aqui
#                 if check_password_hash(password_hash_from_db, password):
#                     id_ministerio = id_ministerio_from_db # SUCESSO!
#     except Exception as e:
#         print(f"Erro durante a verificação de login: {e}")
#         # Retorna None em caso de qualquer erro
#         return None
#     finally:
#         if conn:
#             conn.close()
            
#     return id_ministerio # Retorna o ID ou None se a senha não bateu


@dataclass
class EscalaEntry:
    id_evento: int
    id_funcao: int
    id_voluntario: int
    funcao_instancia: int

@dataclass
class Vaga:
    id_evento: int
    data_evento_obj: object
    id_funcao: int
    funcao_instancia: int
    key: str # Uma chave única para cada vaga, ex: "evento_10-funcao_1-instancia_1"

@dataclass
class Voluntario:
    id_voluntario: int
    nome_voluntario: str
    limite_escalas_mes: int
    nivel_experiencia: str
    id_grupo: int
    funcoes: Set[int] = field(default_factory=set)
    disponibilidade: Set[int] = field(default_factory=set)
    escalas_neste_mes: int = 0
    dias_escalado: Set[object] = field(default_factory=set)

@dataclass
class Grupo:
    id_grupo: int
    limite_escalas_grupo: int
    membros: List[Voluntario] = field(default_factory=list)
    escalas_neste_mes: int = 0
    representantes: List[Voluntario] = field(default_factory=list)
    apoiadores: List[Voluntario] = field(default_factory=list)

# ----- DASHBOARD -------
def get_all_voluntarios_com_detalhes_puro(id_ministerio):
    conn = ensure_connection()
    if conn is None: return pd.DataFrame()
    try:
        query = """
            SELECT
                v.id_voluntario, v.nome_voluntario, v.limite_escalas_mes,
                v.nivel_experiencia, v.id_grupo,
                COALESCE(funcoes_agg.funcoes, '{}') AS funcoes,
                COALESCE(disp_agg.disponibilidades, '{}') AS disponibilidade
            FROM voluntarios v
            LEFT JOIN (
                SELECT id_voluntario, array_agg(id_funcao) as funcoes
                FROM voluntario_funcoes GROUP BY id_voluntario
            ) AS funcoes_agg ON v.id_voluntario = funcoes_agg.id_voluntario
            LEFT JOIN (
                SELECT id_voluntario, array_agg(id_servico) as disponibilidades
                FROM voluntario_disponibilidade GROUP BY id_voluntario
            ) AS disp_agg ON v.id_voluntario = disp_agg.id_voluntario
            WHERE v.ativo = TRUE AND v.id_ministerio = %s;
        """
        df = pd.read_sql(query, conn, params=(id_ministerio,))
        if not df.empty:
            df['funcoes'] = df['funcoes'].apply(lambda arr: [int(f) for f in arr])
            df['disponibilidade'] = df['disponibilidade'].apply(lambda arr: [int(f) for f in arr])
        return df
    except Exception as e:
        print(f"Erro ao buscar dados detalhados dos voluntários: {e}")
        return pd.DataFrame()
    finally:
        if conn: conn.close()


# --- CRUD FUNÇÕES ---

def view_all_funcoes(id_ministerio):
    """ Busca todas as funções de um ministério específico. """
    conn = ensure_connection()
    if conn is None: return pd.DataFrame()
    query = "SELECT id_funcao, nome_funcao, tipo_funcao, prioridade_alocacao FROM funcoes WHERE id_ministerio = %s ORDER BY nome_funcao ASC"
    return pd.read_sql(query, conn, params=(id_ministerio,))



def add_funcao(nome_funcao, descricao, id_ministerio, tipo_funcao, prioridade_alocacao): # 1. Novos parâmetros adicionados
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            # A lógica de verificação continua a mesma
            cur.execute("SELECT COUNT(*) FROM funcoes WHERE nome_funcao = %s AND id_ministerio = %s", (nome_funcao, id_ministerio))
            if cur.fetchone()[0] > 0:
                
                return # Alterado para retornar algo que a API possa tratar

            # 2. Comando INSERT atualizado para incluir as novas colunas
            sql = """
                INSERT INTO funcoes (nome_funcao, descricao, id_ministerio, tipo_funcao, prioridade_alocacao)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            # 3. Novos valores passados para o execute
            cur.execute(
                sql,
                (nome_funcao, descricao, id_ministerio, tipo_funcao, prioridade_alocacao)
            )
        conn.commit()

    except Exception as e:
        conn.rollback()

        raise e
    finally:
        if conn:
            conn.close()


# Função para ATUALIZAR uma função existente (CORRIGIDA)
def update_funcao(id_funcao, novo_nome, nova_descricao, novo_tipo, nova_prioridade): # 1. Novos parâmetros adicionados
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            # 2. Comando UPDATE atualizado para incluir os novos campos
            sql = """
                UPDATE funcoes
                SET nome_funcao = %s, descricao = %s, tipo_funcao = %s, prioridade_alocacao = %s
                WHERE id_funcao = %s
            """
            # 3. Novos valores passados para o execute
            cur.execute(sql, (novo_nome, nova_descricao, novo_tipo, nova_prioridade, id_funcao))
        conn.commit()
 
    except Exception as e:
        conn.rollback()

        raise e
    finally:
        if conn:
            conn.close()

def delete_funcao(id_funcao):
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM funcoes WHERE id_funcao = %s", (id_funcao,))
        conn.commit()
    except Exception as e:
        conn.rollback(); print(f"Erro ao deletar função: {e}")

# --- CRUD VOLUNTÁRIOS ---

# Versão NOVA e CORRIGIDA (sem 'telefone')



def get_voluntario_by_id(id_voluntario):
    conn = ensure_connection()
    if conn is None: return None
    # Usar SELECT * garante que a nova coluna nivel_experiencia seja incluída.
    df = pd.read_sql(f"SELECT * FROM voluntarios WHERE id_voluntario = {id_voluntario}", conn)
    return df.iloc[0] if not df.empty else None

def get_voluntario_by_name(nome_voluntario):
    conn = ensure_connection()
    if conn is None or not nome_voluntario or nome_voluntario == "**VAGO**": return None
    query = "SELECT id_voluntario FROM voluntarios WHERE nome_voluntario = %s"
    df = pd.read_sql(query, conn, params=(nome_voluntario,))
    return int(df['id_voluntario'].iloc[0]) if not df.empty else None

# Versão NOVA e CORRIGIDA (sem 'telefone')
def update_voluntario(id_voluntario, nome, limite_mes, ativo, nivel_experiencia):
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE voluntarios SET nome_voluntario = %s, limite_escalas_mes = %s, ativo = %s, nivel_experiencia = %s WHERE id_voluntario = %s",
                (nome, limite_mes, ativo, nivel_experiencia, id_voluntario)
            )
        conn.commit()
    except Exception as e:
        conn.rollback(); print(f"Erro ao atualizar voluntário: {e}")

# --- CRUD VOLUNTARIO_FUNCOES ---
def get_funcoes_of_voluntario(id_voluntario):
    conn = ensure_connection()
    if conn is None: return []
    df = pd.read_sql(f"SELECT id_funcao FROM voluntario_funcoes WHERE id_voluntario = {id_voluntario}", conn)
    return df['id_funcao'].tolist()

def update_funcoes_of_voluntario(id_voluntario, lista_ids_funcoes):
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM voluntario_funcoes WHERE id_voluntario = %s", (id_voluntario,))
            if lista_ids_funcoes:
                args = [(id_voluntario, id_funcao) for id_funcao in lista_ids_funcoes]
                cur.executemany("INSERT INTO voluntario_funcoes (id_voluntario, id_funcao) VALUES (%s, %s)", args)
        conn.commit()
    except Exception as e:
        conn.rollback(); print(f"Erro ao atualizar funções do voluntário: {e}")

def get_voluntarios_for_funcao(id_funcao):
    # Esta função agora fica mais simples e consistente
    df_completo = get_all_voluntarios_com_detalhes()
    
    # Filtra o dataframe completo para retornar apenas quem tem a função
    df_filtrado = df_completo.dropna(subset=['funcoes']) # Remove quem não tem função nenhuma
    return df_filtrado[df_filtrado['funcoes'].apply(lambda x: id_funcao in x)]

# --- CRUD SERVIÇOS_FIXOS ---
# def add_servico_fixo(nome, dia_da_semana):
#     conn = ensure_connection()
#     if conn is None: return
#     try:
#         with conn.cursor() as cur:
#             cur.execute("INSERT INTO servicos_fixos (nome_servico, dia_da_semana) VALUES (%s, %s) ON CONFLICT (nome_servico) DO NOTHING", (nome, dia_da_semana))
#         conn.commit()
#         
#     except Exception as e:
#         conn.rollback(); print(f"Erro ao adicionar serviço: {e}")

def add_servico_fixo(nome, dia_da_semana, id_ministerio):
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            # Verifica se o serviço já existe para o mesmo ministério
            cur.execute("SELECT COUNT(*) FROM servicos_fixos WHERE nome_servico = %s AND id_ministerio = %s", (nome, id_ministerio))
            if cur.fetchone()[0] > 0:
                print(f"O serviço '{nome}' já existe neste ministério.")
                return

            # Insere o novo registro com o id_ministerio
            cur.execute(
                "INSERT INTO servicos_fixos (nome_servico, dia_da_semana, id_ministerio) VALUES (%s, %s, %s)",
                (nome, dia_da_semana, id_ministerio)
            )
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        print(f"Erro ao adicionar serviço: {e}")

def view_all_servicos_fixos(id_ministerio):
    """ Busca todos os serviços fixos de um ministério específico. """
    conn = ensure_connection()
    if conn is None: return pd.DataFrame()
    query = "SELECT * FROM servicos_fixos WHERE ativo = TRUE AND id_ministerio = %s ORDER BY dia_da_semana, nome_servico ASC"
    return pd.read_sql(query, conn, params=(id_ministerio,))


def update_servico_fixo(id_servico, nome, dia_da_semana, ativo):
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE servicos_fixos SET nome_servico = %s, dia_da_semana = %s, ativo = %s WHERE id_servico = %s", (nome, dia_da_semana, ativo, id_servico))
        conn.commit()
        
    except Exception as e:
        conn.rollback(); print(f"Erro ao atualizar serviço: {e}")

def delete_servico_fixo(id_servico):
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM servicos_fixos WHERE id_servico = %s", (id_servico,))
        conn.commit()
        
    except Exception as e:
        conn.rollback(); print(f"Erro ao deletar serviço: {e}")

# --- CRUD VOLUNTARIO_DISPONIBILIDADE ---
def get_disponibilidade_of_voluntario(id_voluntario):
    conn = ensure_connection()
    if conn is None: return []
    df = pd.read_sql(f"SELECT id_servico FROM voluntario_disponibilidade WHERE id_voluntario = {id_voluntario}", conn)
    return df['id_servico'].tolist()

def update_disponibilidade_of_voluntario(id_voluntario, lista_ids_servicos):
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM voluntario_disponibilidade WHERE id_voluntario = %s", (id_voluntario,))
            if lista_ids_servicos:
                args = [(id_voluntario, id_servico) for id_servico in lista_ids_servicos]
                cur.executemany("INSERT INTO voluntario_disponibilidade (id_voluntario, id_servico) VALUES (%s, %s)", args)
        conn.commit()
    except Exception as e:
        conn.rollback(); print(f"Erro ao atualizar disponibilidade: {e}")

def update_apenas_disponibilidade(id_voluntario, lista_ids_servicos):
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM voluntario_disponibilidade WHERE id_voluntario = %s", (id_voluntario,))
            if lista_ids_servicos:
                args = [(id_voluntario, id_servico) for id_servico in lista_ids_servicos]
                cur.executemany("INSERT INTO voluntario_disponibilidade (id_voluntario, id_servico) VALUES (%s, %s)", args)
        conn.commit()
    except Exception as e:
        conn.rollback(); print(f"Erro ao atualizar disponibilidade: {e}")

# --- CRUD VOLUNTARIO_INDISPONIBILIDADE ---
def get_indisponibilidade_eventos(id_voluntario, ano, mes):
    """ Busca os IDs dos eventos específicos de indisponibilidade para um voluntário. """
    conn = ensure_connection()
    if conn is None: return []
    query = """
    SELECT vi.id_evento
    FROM voluntario_indisponibilidade_eventos vi
    JOIN eventos e ON vi.id_evento = e.id_evento
    WHERE vi.id_voluntario = %s
      AND EXTRACT(YEAR FROM e.data_evento) = %s
      AND EXTRACT(MONTH FROM e.data_evento) = %s
    """
    df = pd.read_sql(query, conn, params=(id_voluntario, ano, mes))
    return df['id_evento'].tolist()

def update_indisponibilidade_eventos(id_voluntario, ano, mes, lista_ids_eventos):
    """ Atualiza os eventos de indisponibilidade, limpando os antigos do mês e inserindo os novos. """
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            # Deleta as indisponibilidades antigas do mês/ano usando um JOIN com a tabela de eventos
            cur.execute("""
                DELETE FROM voluntario_indisponibilidade_eventos
                WHERE id_voluntario = %s AND id_evento IN (
                    SELECT id_evento FROM eventos
                    WHERE EXTRACT(YEAR FROM data_evento) = %s AND EXTRACT(MONTH FROM data_evento) = %s
                )
            """, (id_voluntario, ano, mes))

            if lista_ids_eventos:
                args = [(id_voluntario, id_evento) for id_evento in lista_ids_eventos]
                cur.executemany("""
                    INSERT INTO voluntario_indisponibilidade_eventos (id_voluntario, id_evento)
                    VALUES (%s, %s)
                """, args)
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Erro ao atualizar indisponibilidades: {e}")

# ----- MINISTERIOS ------

def get_all_ministerios():
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


# --- CRUD GRUPOS ---
def get_all_grupos_com_membros(id_ministerio, _cache_buster=None):
    """ Retorna um DataFrame com os grupos e seus membros FILTRADOS POR MINISTÉRIO. """
    conn = ensure_connection()
    if conn is None: return pd.DataFrame()
    
    try:
        query = """
        SELECT
            gv.id_grupo, gv.nome_grupo, gv.limite_escalas_grupo,
            COALESCE(membros.lista_membros, 'Nenhum membro vinculado') as membros
        FROM grupos_vinculados gv
        LEFT JOIN (
            SELECT 
                id_grupo, 
                STRING_AGG(nome_voluntario, ', ' ORDER BY nome_voluntario) as lista_membros
            FROM voluntarios
            WHERE id_grupo IS NOT NULL
            GROUP BY id_grupo
        ) as membros ON gv.id_grupo = membros.id_grupo
        WHERE gv.id_ministerio = %s
        ORDER BY gv.nome_grupo;
        """
        df = pd.read_sql(query, conn, params=(id_ministerio,))
        return df
    except Exception as e:
        print(f"Erro em get_all_grupos_com_membros: {e}")
        return pd.DataFrame()
    finally:
        # Garante que a conexão seja fechada, mesmo que ocorra um erro.
        if conn:
            conn.close()

def get_voluntarios_sem_grupo(id_ministerio):
    """ Retorna voluntários sem grupo que pertencem ao ministério especificado. """
    conn = ensure_connection()
    if conn is None: return pd.DataFrame()
    
    try:
        query = """
            SELECT id_voluntario, nome_voluntario 
            FROM voluntarios 
            WHERE ativo = TRUE 
              AND id_grupo IS NULL 
              AND id_ministerio = %s 
            ORDER BY nome_voluntario
        """
        df = pd.read_sql(query, conn, params=(id_ministerio,))
        return df
    except Exception as e:
        print(f"Erro em get_voluntarios_sem_grupo: {e}")
        return pd.DataFrame()
    finally:
        # Garante que a conexão seja fechada.
        if conn:
            conn.close()

def get_voluntarios_do_grupo(id_grupo):
    conn = ensure_connection()
    if conn is None: return pd.DataFrame()
    return pd.read_sql(f"SELECT id_voluntario, nome_voluntario FROM voluntarios WHERE ativo = TRUE AND id_grupo = {id_grupo} ORDER BY nome_voluntario", conn)

# Adicione id_ministerio como um novo parâmetro
def create_grupo(nome_grupo, ids_membros, id_ministerio, limite_grupo):
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            # SQL atualizado para inserir o limite
            sql_insert = "INSERT INTO grupos_vinculados (nome_grupo, id_ministerio, limite_escalas_grupo) VALUES (%s, %s, %s) RETURNING id_grupo"
            cur.execute(sql_insert, (nome_grupo, id_ministerio, limite_grupo))
            id_novo_grupo = cur.fetchone()[0]
            cur.execute("UPDATE voluntarios SET id_grupo = %s WHERE id_voluntario IN %s", (id_novo_grupo, tuple(ids_membros)))
        conn.commit()
    except Exception as e:
        conn.rollback(); print(f"Erro ao criar grupo: {e}")

def update_grupo(id_grupo, novo_nome, ids_membros_novos, novo_limite):
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            # SQL atualizado para o novo limite
            cur.execute("UPDATE grupos_vinculados SET nome_grupo = %s, limite_escalas_grupo = %s WHERE id_grupo = %s", (novo_nome, novo_limite, id_grupo))
            cur.execute("UPDATE voluntarios SET id_grupo = NULL WHERE id_grupo = %s", (id_grupo,))
            if ids_membros_novos:
                cur.execute("UPDATE voluntarios SET id_grupo = %s WHERE id_voluntario IN %s", (id_grupo, tuple(ids_membros_novos)))
        conn.commit()
    except Exception as e:
        conn.rollback(); print(f"Erro ao atualizar grupo: {e}")


def delete_grupo(id_grupo):
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE voluntarios SET id_grupo = NULL WHERE id_grupo = %s", (id_grupo,))
            cur.execute("DELETE FROM grupos_vinculados WHERE id_grupo = %s", (id_grupo,))
        conn.commit()
    except Exception as e:
        conn.rollback(); print(f"Erro ao deletar grupo: {e}")

# --- CRUD COTAS ---
def get_cotas_all_servicos():
    conn = ensure_connection()
    if conn is None: return pd.DataFrame()
    return pd.read_sql("SELECT * FROM servico_funcao_cotas", conn)

def get_cotas_for_servico(id_servico):
    conn = ensure_connection()
    if conn is None: return {}
    df = pd.read_sql(f"SELECT id_funcao, quantidade_necessaria FROM servico_funcao_cotas WHERE id_servico = {id_servico}", conn)
    return df.set_index('id_funcao')['quantidade_necessaria'].to_dict()

def update_cotas_servico(id_servico, cotas_dict):
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM servico_funcao_cotas WHERE id_servico = %s", (id_servico,))
            args = [(id_servico, id_f, qtd) for id_f, qtd in cotas_dict.items() if qtd > 0]
            if args:
                cur.executemany("INSERT INTO servico_funcao_cotas (id_servico, id_funcao, quantidade_necessaria) VALUES (%s, %s, %s)", args)
        conn.commit()
    except Exception as e:
        conn.rollback(); print(f"Erro ao atualizar cotas: {e}")



def add_voluntario(nome, limite_mes, nivel_experiencia, id_ministerio):
    """ Adiciona um voluntário associado a um ministério e retorna o ID. """
    conn = ensure_connection()
    if conn is None: return None
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO voluntarios (nome_voluntario, limite_escalas_mes, nivel_experiencia, id_ministerio) VALUES (%s, %s, %s, %s) RETURNING id_voluntario", 
                (nome, limite_mes, nivel_experiencia, id_ministerio)
            )
            id_novo_voluntario = cur.fetchone()[0]
            conn.commit()
            return id_novo_voluntario
    except Exception as e:
        conn.rollback()
        print(f"Erro ao adicionar voluntário: {e}")
        return None

def view_all_voluntarios(id_ministerio, include_inactive=False):
    """ Busca todos os voluntários de um ministério específico. """
    conn = ensure_connection()
    if conn is None: return pd.DataFrame()
    query = "SELECT * FROM voluntarios WHERE id_ministerio = %s"
    params = [id_ministerio]
    if not include_inactive:
        query += " AND ativo = TRUE"
    query += " ORDER BY nome_voluntario ASC"
    return pd.read_sql(query, conn, params=params)

# No seu arquivo database.py ou onde a função está definida

# No seu arquivo database.py ou onde a função está definida

# No seu arquivo database.py ou onde a função está definida



def get_all_voluntarios_com_detalhes(id_ministerio):
    """ Busca todos os detalhes dos voluntários de um ministério específico. """
    conn = ensure_connection()
    if conn is None: return pd.DataFrame()
    try:
        query = """
            SELECT
                v.id_voluntario, v.nome_voluntario, v.limite_escalas_mes,
                v.nivel_experiencia, v.id_grupo,
                COALESCE(funcoes_agg.funcoes, '{}') AS funcoes,
                COALESCE(disp_agg.disponibilidades, '{}') AS disponibilidade
            FROM voluntarios v
            LEFT JOIN (
                SELECT id_voluntario, array_agg(id_funcao) as funcoes
                FROM voluntario_funcoes GROUP BY id_voluntario
            ) AS funcoes_agg ON v.id_voluntario = funcoes_agg.id_voluntario
            LEFT JOIN (
                SELECT id_voluntario, array_agg(id_servico) as disponibilidades
                FROM voluntario_disponibilidade GROUP BY id_voluntario
            ) AS disp_agg ON v.id_voluntario = disp_agg.id_voluntario
            WHERE v.ativo = TRUE AND v.id_ministerio = %s;
        """
        df = pd.read_sql(query, conn, params=(id_ministerio,))

        # ======================================================================
        # CORREÇÃO CRÍTICA ADICIONADA AQUI
        # Garante que os itens dentro das listas sejam números inteiros.
        if not df.empty:
            df['funcoes'] = df['funcoes'].apply(lambda arr: [int(f) for f in arr])
            df['disponibilidade'] = df['disponibilidade'].apply(lambda arr: [int(f) for f in arr])
        # ======================================================================

        return df
    except Exception as e:
        print(f"Erro ao buscar dados detalhados dos voluntários: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()



def get_events_for_month(ano, mes, id_ministerio):
    """ Busca os eventos de um ministério específico. """
    conn = ensure_connection()
    if conn is None: return pd.DataFrame()
    query = """
        SELECT e.id_evento, e.id_servico_fixo, e.data_evento, sf.nome_servico 
        FROM eventos e 
        JOIN servicos_fixos sf ON e.id_servico_fixo = sf.id_servico 
        WHERE EXTRACT(YEAR FROM e.data_evento) = %s 
          AND EXTRACT(MONTH FROM e.data_evento) = %s
          AND sf.id_ministerio = %s
        ORDER BY e.data_evento ASC
    """
    return pd.read_sql(query, conn, params=(ano, mes, id_ministerio))



def update_escala_entry(id_evento, id_funcao, id_voluntario, instancia):
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM escala WHERE id_evento = %s AND id_funcao = %s AND funcao_instancia = %s", (id_evento, id_funcao, instancia))
            if id_voluntario is not None:
                cur.execute("INSERT INTO escala (id_evento, id_funcao, id_voluntario, funcao_instancia) VALUES (%s, %s, %s, %s)", (id_evento, id_funcao, id_voluntario, instancia))
        conn.commit()
    except Exception as e:
        conn.rollback(); print(f"Erro ao salvar alteração na escala: {e}")

# -------------------- INDISPONIBILIDADE DOS VOLUNTARIOS --------------------

# Adicione estas funções ao seu arquivo database.py

def get_indisponibilidade_por_mes(id_voluntario, ano, mes):
    """Busca as datas de indisponibilidade de um voluntário para um mês específico."""
    conn = ensure_connection()
    if conn is None: return []
    try:
        query = """
            SELECT data_indisponivel FROM voluntario_indisponibilidade_datas
            WHERE id_voluntario = %s 
              AND EXTRACT(YEAR FROM data_indisponivel) = %s
              AND EXTRACT(MONTH FROM data_indisponivel) = %s;
        """
        df = pd.read_sql(query, conn, params=(id_voluntario, ano, mes))
        # Retorna a lista de datas no formato 'YYYY-MM-DD'
        return [d.strftime('%Y-%m-%d') for d in df['data_indisponivel']]
    except Exception as e:
        print(f"Erro ao buscar indisponibilidades: {e}")
        return []
    finally:
        if conn: conn.close()

def update_indisponibilidade_por_mes(id_voluntario, ano, mes, lista_datas):
    """
    Atualiza as indisponibilidades de um voluntário para um mês.
    Primeiro apaga as datas antigas do mês e depois insere as novas.
    """
    conn = ensure_connection()
    if conn is None: return False
    try:
        with conn.cursor() as cur:
            # 1. Limpa as indisponibilidades antigas apenas para o mês em questão
            cur.execute("""
                DELETE FROM voluntario_indisponibilidade_datas
                WHERE id_voluntario = %s 
                  AND EXTRACT(YEAR FROM data_indisponivel) = %s 
                  AND EXTRACT(MONTH FROM data_indisponivel) = %s;
            """, (id_voluntario, ano, mes))

            # 2. Insere as novas datas, se houver alguma
            if lista_datas:
                dados_para_inserir = [(id_voluntario, data) for data in lista_datas]
                sql_insert = "INSERT INTO voluntario_indisponibilidade_datas (id_voluntario, data_indisponivel) VALUES (%s, %s)"
                cur.executemany(sql_insert, dados_para_inserir)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Erro ao atualizar indisponibilidades: {e}")
        return False
    finally:
        if conn: conn.close()


def get_indisponibilidade_datas(id_voluntario, ano, mes):
    """ Busca as datas específicas em que um voluntário está indisponível em um mês. """
    conn = ensure_connection()
    if conn is None: return []
    query = "SELECT data_indisponivel FROM voluntario_indisponibilidade_datas WHERE id_voluntario = %s AND EXTRACT(YEAR FROM data_indisponivel) = %s AND EXTRACT(MONTH FROM data_indisponivel) = %s"
    df = pd.read_sql(query, conn, params=(id_voluntario, ano, mes))
    return [d.date() for d in pd.to_datetime(df['data_indisponivel'])]

def update_indisponibilidade_datas(id_voluntario, ano, mes, datas_indisponiveis):
    """ Atualiza a lista de datas de indisponibilidade para um voluntário em um mês. """
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            # 1. Limpa as indisponibilidades antigas apenas para o mês em questão
            cur.execute("DELETE FROM voluntario_indisponibilidade_datas WHERE id_voluntario = %s AND EXTRACT(YEAR FROM data_indisponivel) = %s AND EXTRACT(MONTH FROM data_indisponivel) = %s", (id_voluntario, ano, mes))
            # 2. Insere as novas datas
            if datas_indisponiveis:
                args = [(id_voluntario, data) for data in datas_indisponiveis]
                cur.executemany("INSERT INTO voluntario_indisponibilidade_data (id_voluntario, data_indisponivel) VALUES (%s, %s)", args)
        conn.commit()
    except Exception as e:
        conn.rollback(); print(f"Erro ao atualizar indisponibilidade: {e}")

def apagar_escala_do_mes(ano, mes, id_ministerio):
    """ Apaga a escala de um mês para um ministério específico. """
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            # Query atualizada para deletar a escala APENAS de eventos
            # que pertencem a serviços do ministério correto, usando um JOIN.
            delete_query = """
                DELETE FROM escala 
                WHERE id_evento IN (
                    SELECT e.id_evento FROM eventos e
                    JOIN servicos_fixos sf ON e.id_servico_fixo = sf.id_servico
                    WHERE EXTRACT(YEAR FROM e.data_evento) = %s 
                      AND EXTRACT(MONTH FROM e.data_evento) = %s
                      AND sf.id_ministerio = %s
                )
            """
            cur.execute(delete_query, (ano, mes, id_ministerio))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Erro ao limpar escala antiga: {e}")


def alocar_grupos(vagas_df, voluntarios_df, vinculos, contagem_escalas_mes, escalados_por_data):
    """
    Tenta alocar grupos inteiros ("tudo ou nada") nas vagas disponíveis.
    Modifica 'contagem_escalas_mes' e 'escalados_por_data' diretamente.
    Retorna a escala dos grupos e os índices das vagas preenchidas.
    """
    escala_grupos = []
    vagas_preenchidas_indices = set()
    
    voluntarios_map = voluntarios_df.set_index('id_voluntario').to_dict('index')
    random.shuffle(vinculos)

    vagas_agrupadas = vagas_df.groupby(['id_evento', 'data_evento_date_obj', 'id_servico_fixo', 'id_funcao'])

    for grupo in vinculos:
        if not grupo or len(grupo) <= 1: continue
        
        grupo_tamanho = len(grupo)
        grupo_alocado = False

        if not all(membro_id in voluntarios_map for membro_id in grupo):
            continue

        primeiro_membro = voluntarios_map[grupo[0]]
        funcoes_comuns = set(primeiro_membro.get('funcoes', []))
        
        for membro_id in grupo[1:]:
            funcoes_comuns.intersection_update(voluntarios_map[membro_id].get('funcoes', []))

        if not funcoes_comuns:
            continue

        for id_funcao_alvo in funcoes_comuns:
            if grupo_alocado: break

            for (id_evento, data_evento, id_servico, id_funcao), vagas_do_grupo in vagas_agrupadas:
                if grupo_alocado: break
                
                vagas_disponiveis = vagas_do_grupo[~vagas_do_grupo.index.isin(vagas_preenchidas_indices)]

                if id_funcao == id_funcao_alvo and len(vagas_disponiveis) >= grupo_tamanho:
                    
                    todos_podem = True
                    for membro_id in grupo:
                        membro_info = voluntarios_map[membro_id]
                        if not (
                            membro_id not in escalados_por_data.get(data_evento, set()) and
                            id_servico in (membro_info.get('disponibilidade') or []) and
                            contagem_escalas_mes.get(membro_id, 0) < membro_info.get('limite_escalas_mes', 0)
                        ):
                            todos_podem = False
                            break

                    if todos_podem:
                        vagas_a_usar = vagas_disponiveis.head(grupo_tamanho)
                        
                        for i, membro_id in enumerate(grupo):
                            vaga = vagas_a_usar.iloc[i]
                            vaga_idx = vaga.name

                            escala_grupos.append({
                                'id_evento': int(vaga['id_evento']),
                                'id_funcao': int(vaga['id_funcao']),
                                'id_voluntario': int(membro_id),
                                'funcao_instancia': int(vaga['funcao_instancia'])
                            })
                            contagem_escalas_mes[membro_id] += 1
                            escalados_por_data[data_evento].add(membro_id)
                            vagas_preenchidas_indices.add(vaga_idx)
                        
                        grupo_alocado = True

    return escala_grupos, list(vagas_preenchidas_indices)


def create_events_for_month(ano, mes, id_ministerio):
    conn = ensure_connection()
    if conn is None: return False
    # Filtra os serviços fixos pelo ministério antes de criar os eventos
    servicos_fixos = view_all_servicos_fixos(id_ministerio)
    if servicos_fixos.empty:
        print("Nenhum serviço fixo cadastrado para este ministério."); return False
    try:
        with conn.cursor() as cur:
            # Apaga apenas eventos do ministério em questão
            cur.execute("""
                DELETE FROM eventos WHERE EXTRACT(YEAR FROM data_evento) = %s 
                AND EXTRACT(MONTH FROM data_evento) = %s 
                AND id_servico_fixo IN (SELECT id_servico FROM servicos_fixos WHERE id_ministerio = %s)
            """, (ano, mes, id_ministerio))
            
            _, num_dias = calendar.monthrange(ano, mes)
            for dia in range(1, num_dias + 1):
                data_atual = datetime(ano, mes, dia).date()
                dia_da_semana_ajustado = (data_atual.weekday() + 1) % 7
                for _, servico in servicos_fixos.iterrows():
                    if servico['dia_da_semana'] == dia_da_semana_ajustado:
                        cur.execute("INSERT INTO eventos (id_servico_fixo, data_evento) VALUES (%s, %s)", (int(servico['id_servico']), data_atual))
            conn.commit()
        return True
    except Exception as e:
        conn.rollback(); print(f"Erro ao criar eventos: {e}"); return False

def get_escala_completa(ano, mes, id_ministerio):
    conn = ensure_connection()
    if conn is None: return pd.DataFrame()
    # Query atualizada para garantir que apenas dados do ministério logado sejam retornados
    query = """
    SELECT 
        esc.funcao_instancia, e.id_evento, e.data_evento, sf.nome_servico,
        f.id_funcao, f.nome_funcao, v.id_voluntario, v.nome_voluntario
    FROM escala esc
    JOIN eventos e ON esc.id_evento = e.id_evento
    JOIN servicos_fixos sf ON e.id_servico_fixo = sf.id_servico
    JOIN funcoes f ON esc.id_funcao = f.id_funcao
    JOIN voluntarios v ON esc.id_voluntario = v.id_voluntario
    WHERE EXTRACT(YEAR FROM e.data_evento) = %s 
      AND EXTRACT(MONTH FROM e.data_evento) = %s
      AND sf.id_ministerio = %s
    ORDER BY e.data_evento, f.id_funcao, esc.funcao_instancia;
    """
    return pd.read_sql(query, conn, params=(ano, mes, id_ministerio))

# def gerar_escala_automatica(ano, mes, id_ministerio):
#     print(f"\n--- INICIANDO GERAÇÃO DA ESCALA PARA {mes}/{ano} ---")

#     # --- 1. SETUP INICIAL E CARGA DE DADOS ---
#     apagar_escala_do_mes(ano, mes, id_ministerio)
#     eventos = get_events_for_month(ano, mes, id_ministerio)
#     if eventos.empty:
#         
#         return
#     eventos['data_evento_obj'] = pd.to_datetime(eventos['data_evento']).dt.date
    
#     voluntarios_df = get_all_voluntarios_com_detalhes(id_ministerio)
#     cotas = get_cotas_all_servicos()
#     todas_funcoes = view_all_funcoes(id_ministerio)
#     grupos_df = get_all_grupos_com_membros(id_ministerio)

#     # Mapeamento de Funções
#     id_funcoes = {nome: id for nome, id in zip(todas_funcoes['nome_funcao'].replace('Líder de Escala', 'Líder'), todas_funcoes['id_funcao'])}
#     id_lider = id_funcoes.get('Líder')
#     id_store = id_funcoes.get('Store')
#     id_apoio = id_funcoes.get('Apoio')

#     # Limites
#     limites_grupo = {int(gid): int(lim) for gid, lim in grupos_df.set_index('id_grupo')['limite_escalas_grupo'].to_dict().items()}
    
#     # --- ESTRUTURAS DE DADOS CENTRAIS ---
#     escala_final = []
    
#     # MUDANÇA CRÍTICA: Este DataFrame será a nossa única fonte da verdade sobre vagas abertas.
#     # Ele será modificado e passado adiante a cada fase.
#     vagas_abertas_df = pd.DataFrame([
#         {
#             'id_evento': ev['id_evento'], 
#             'data_evento_obj': ev['data_evento_obj'], 
#             'id_funcao': int(cota['id_funcao']), 
#             'funcao_instancia': i
#         }
#         for _, ev in eventos.iterrows() 
#         for _, cota in cotas[cotas['id_servico'] == ev['id_servico_fixo']].iterrows()
#         for i in range(1, int(cota['quantidade_necessaria']) + 1)
#         if cota['id_funcao'] in id_funcoes.values()
#     ])
#     vagas_abertas_df.reset_index(drop=True, inplace=True) # Garante índices únicos

#     # Dicionário central para contar escalas de indivíduos e grupos
#     contagem_escalas = {
#         'individual': defaultdict(int),
#         'grupo': defaultdict(int)
#     }

#     # --- FASE 1: ALOCAÇÃO DE GRUPOS (PRIORIDADE MÁXIMA) ---
#     print("--- FASE 1: Alocando Grupos ---")
    
#     # Preparar dados dos grupos
#     candidatos_grupo_ids = list(grupos_df['id_grupo'].unique())
#     membros_por_grupo = voluntarios_df[voluntarios_df['id_grupo'].notna()].groupby('id_grupo')['id_voluntario'].apply(list).to_dict()
    
#     continuar_alocando = True
#     while continuar_alocando:
#         houve_alocacao_na_rodada = False
#         random.shuffle(candidatos_grupo_ids)

#         for id_grupo in candidatos_grupo_ids:
#             # 1. Checar limite do grupo
#             if contagem_escalas['grupo'][id_grupo] >= limites_grupo.get(id_grupo, 0):
#                 continue

#             membros_do_grupo = membros_por_grupo.get(id_grupo, [])
#             if not membros_do_grupo:
#                 continue

#             # 2. Encontrar um dia/evento adequado para o grupo inteiro
#             eventos_disponiveis = vagas_abertas_df['id_evento'].unique()
#             random.shuffle(eventos_disponiveis) # Garante variedade na escolha do evento

#             for id_evento_alvo in eventos_disponiveis:
#                 # 3. Checar se *nenhum* membro do grupo já está escalado neste dia
#                 data_evento_alvo = eventos[eventos['id_evento'] == id_evento_alvo]['data_evento_obj'].iloc[0]
#                 ids_ja_no_dia = {e['id_voluntario'] for e in escala_final if e['data_evento_obj'] == data_evento_alvo}
                
#                 if any(membro_id in ids_ja_no_dia for membro_id in membros_do_grupo):
#                     continue # Conflito, o grupo não pode neste dia. Tenta o próximo evento.

#                 # 4. LÓGICA "TUDO OU NADA": Verificar se há vagas suficientes para o grupo no evento
#                 vagas_no_evento = vagas_abertas_df[vagas_abertas_df['id_evento'] == id_evento_alvo]
                
#                 # O grupo precisa de 1 vaga principal (Líder/Store) e N-1 vagas de Apoio
#                 vaga_principal = vagas_no_evento[vagas_no_evento['id_funcao'].isin([id_lider, id_store])].head(1)
#                 vagas_apoio = vagas_no_evento[vagas_no_evento['id_funcao'] == id_apoio]

#                 if not vaga_principal.empty and len(vagas_apoio) >= (len(membros_do_grupo) - 1):
#                     # SUCESSO! Encontramos um lugar para o grupo.
#                     # 5. Alocar o grupo
                    
#                     # Aloca o primeiro membro (representante) na vaga principal
#                     lider_do_grupo = membros_do_grupo[0]
#                     vaga_lider_obj = vaga_principal.iloc[0]
#                     escala_final.append({
#                         'id_evento': int(vaga_lider_obj['id_evento']),
#                         'data_evento_obj': data_evento_alvo,
#                         'id_funcao': int(vaga_lider_obj['id_funcao']),
#                         'id_voluntario': int(lider_do_grupo),
#                         'funcao_instancia': int(vaga_lider_obj['funcao_instancia'])
#                     })
#                     vagas_abertas_df.drop(vaga_lider_obj.name, inplace=True)
#                     contagem_escalas['individual'][lider_do_grupo] += 1
                    
#                     # Aloca os outros membros nas vagas de apoio
#                     outros_membros = membros_do_grupo[1:]
#                     for i, membro_id in enumerate(outros_membros):
#                         vaga_apoio_obj = vagas_apoio.iloc[i]
#                         escala_final.append({
#                             'id_evento': int(vaga_apoio_obj['id_evento']),
#                             'data_evento_obj': data_evento_alvo,
#                             'id_funcao': int(vaga_apoio_obj['id_funcao']),
#                             'id_voluntario': int(membro_id),
#                             'funcao_instancia': int(vaga_apoio_obj['funcao_instancia'])
#                         })
#                         vagas_abertas_df.drop(vaga_apoio_obj.name, inplace=True)
#                         contagem_escalas['individual'][membro_id] += 1
                    
#                     contagem_escalas['grupo'][id_grupo] += 1
#                     houve_alocacao_na_rodada = True
#                     break # Sai do loop de eventos, pois o grupo já foi alocado nesta rodada.
            
#             if vagas_abertas_df.empty: break # Se acabaram as vagas, para tudo
#         if not houve_alocacao_na_rodada or vagas_abertas_df.empty:
#             continuar_alocando = False


#     # --- FUNÇÃO AUXILIAR PARA ALOCAÇÃO INDIVIDUAL (FASES 2, 3, 4, 5) ---
#     def alocar_individuais(candidatos_df, filtro_vagas_func, respeitar_limites=True):
#         nonlocal vagas_abertas_df, escala_final, contagem_escalas
        
#         vagas_alvo_df = vagas_abertas_df[filtro_vagas_func(vagas_abertas_df)].copy()
#         if vagas_alvo_df.empty:
#             return

#         continuar_alocando = True
#         while continuar_alocando and not vagas_alvo_df.empty:
#             houve_alocacao_na_rodada = False
#             candidatos_rodada = candidatos_df.sample(frac=1)

#             for _, candidato in candidatos_rodada.iterrows():
#                 id_cand = candidato['id_voluntario']

#                 if respeitar_limites and contagem_escalas['individual'][id_cand] >= candidato['limite_escalas_mes']:
#                     continue
                
#                 # Acha dias em que o candidato já foi escalado
#                 dias_ja_escalado = {e['data_evento_obj'] for e in escala_final if e['id_voluntario'] == id_cand}
                
#                 # Filtra vagas em dias que ele ainda não está
#                 vagas_possiveis = vagas_alvo_df[~vagas_alvo_df['data_evento_obj'].isin(dias_ja_escalado)]
#                 if vagas_possiveis.empty:
#                     continue

#                 # Prioriza o dia com menos gente (melhor balanceamento)
#                 escalados_por_data = defaultdict(int)
#                 for e in escala_final: escalados_por_data[e['data_evento_obj']] += 1
                
#                 vagas_possiveis['staff_no_dia'] = vagas_possiveis['data_evento_obj'].map(escalados_por_data)
#                 vaga_ideal = vagas_possiveis.sort_values(by='staff_no_dia').iloc[0]

#                 # Aloca o voluntário
#                 escala_final.append({
#                     'id_evento': int(vaga_ideal['id_evento']),
#                     'data_evento_obj': vaga_ideal['data_evento_obj'],
#                     'id_funcao': int(vaga_ideal['id_funcao']),
#                     'id_voluntario': int(id_cand),
#                     'funcao_instancia': int(vaga_ideal['funcao_instancia'])
#                 })
#                 contagem_escalas['individual'][id_cand] += 1
                
#                 # ATUALIZAÇÃO CRÍTICA DO ESTADO
#                 vagas_abertas_df.drop(vaga_ideal.name, inplace=True)
#                 vagas_alvo_df.drop(vaga_ideal.name, inplace=True)
                
#                 houve_alocacao_na_rodada = True
#                 break # Próximo candidato

#             if not houve_alocacao_na_rodada:
#                 continuar_alocando = False
    
#     # --- EXECUÇÃO DAS FASES INDIVIDUAIS ---
    
#     # Preparar voluntários individuais
#     voluntarios_individuais_df = voluntarios_df[voluntarios_df['id_grupo'].isnull()]

#     # Fase 2: Líderes Individuais
#     print("--- FASE 2: Alocando Líderes Individuais ---")
#     candidatos_lider_df = voluntarios_individuais_df[voluntarios_individuais_df['funcoes'].apply(lambda f: id_lider in (f or []))]
#     alocar_individuais(candidatos_lider_df, lambda df: df['id_funcao'] == id_lider)
    
#     # Fase 3: Store Individuais
#     print("--- FASE 3: Alocando Store Individuais ---")
#     candidatos_store_df = voluntarios_individuais_df[voluntarios_individuais_df['funcoes'].apply(lambda f: id_store in (f or []))]
#     alocar_individuais(candidatos_store_df, lambda df: df['id_funcao'] == id_store)

#     # Fase 4: Apoios Individuais por Nível (ORDEM CORRIGIDA)
#     print("--- FASE 4: Alocando Apoios Individuais ---")
#     filtro_apoio_func = lambda df: df['id_funcao'] == id_apoio
    
#     # 4.1: Nível Avançado
#     print("  - Sub-fase: Nível Avançado")
#     cand_avancado = voluntarios_individuais_df[
#         (voluntarios_individuais_df['funcoes'].apply(lambda f: id_apoio in (f or []))) &
#         (voluntarios_individuais_df['nivel_experiencia'] == "Avançado")
#     ]
#     if not cand_avancado.empty: alocar_individuais(cand_avancado, filtro_apoio_func)

#     # 4.2: Nível Iniciante
#     print("  - Sub-fase: Nível Iniciante")
#     cand_iniciante = voluntarios_individuais_df[
#         (voluntarios_individuais_df['funcoes'].apply(lambda f: id_apoio in (f or []))) &
#         (voluntarios_individuais_df['nivel_experiencia'] == "Iniciante")
#     ]
#     if not cand_iniciante.empty: alocar_individuais(cand_iniciante, filtro_apoio_func)

#     # 4.3: Nível Intermediário
#     print("  - Sub-fase: Nível Intermediário")
#     cand_intermediario = voluntarios_individuais_df[
#         (voluntarios_individuais_df['funcoes'].apply(lambda f: id_apoio in (f or []))) &
#         (voluntarios_individuais_df['nivel_experiencia'] == "Intermediário")
#     ]
#     if not cand_intermediario.empty: alocar_individuais(cand_intermediario, filtro_apoio_func)

#     # Fase 5: Preenchimento Forçado
#     if not vagas_abertas_df.empty:
#         print(f"--- FASE 5: {len(vagas_abertas_df)} vagas restantes. Preenchimento forçado ignorando limites. ---")
#         # Para o preenchimento forçado, qualquer voluntário pode preencher qualquer vaga restante
#         alocar_individuais(voluntarios_df, lambda df: df.index.isin(vagas_abertas_df.index), respeitar_limites=False)
    
#     print("\n--- GERAÇÃO DA ESCALA CONCLUÍDA ---\n")

#     # --- SALVAR NO BANCO ---
#     if escala_final:
#         # Remover a coluna auxiliar 'data_evento_obj' antes de salvar
#         args = [
#             (e['id_evento'], e['id_funcao'], e['id_voluntario'], e['funcao_instancia']) 
#             for e in escala_final
#         ]
        
#         conn = ensure_connection()
#         try:
#             with conn.cursor() as cur:
#                 cur.executemany("INSERT INTO escala (id_evento, id_funcao, id_voluntario, funcao_instancia) VALUES (%s, %s, %s, %s)", args)
#             conn.commit()
#             
#         except Exception as e:
#             conn.rollback()
#             print(f"Erro ao salvar escala: {e}")
#         finally:
#             if conn:
#                 conn.close()

# =========================================================================
# Nova Função de Carregamento de Dados
# Substitua sua antiga get_all_voluntarios_com_detalhes por esta
# =========================================================================
def carregar_dados_para_escala(id_ministerio):
    """
    Carrega todos os dados necessários do banco e os transforma em objetos Python,
    eliminando problemas de tipo de dado do Pandas.
    """
    conn = ensure_connection()
    if conn is None: return {}, {}

    try:
        query_vols = "SELECT * FROM voluntarios WHERE ativo = TRUE AND id_ministerio = %s"
        voluntarios_raw = pd.read_sql(query_vols, conn, params=(id_ministerio,))
        
        query_funcoes = "SELECT id_voluntario, id_funcao FROM voluntario_funcoes"
        funcoes_map_df = pd.read_sql(query_funcoes, conn)
        
        funcoes_map = funcoes_map_df.groupby('id_voluntario')['id_funcao'].apply(set).to_dict()

        voluntarios_map = {}
        for _, row in voluntarios_raw.iterrows():
            vol_id = int(row['id_voluntario'])
            voluntarios_map[vol_id] = Voluntario(
                id_voluntario=vol_id,
                nome_voluntario=str(row['nome_voluntario']),
                limite_escalas_mes=int(row['limite_escalas_mes']),
                nivel_experiencia=str(row['nivel_experiencia']),
                id_grupo=int(row['id_grupo']) if pd.notna(row['id_grupo']) else None,
                funcoes=funcoes_map.get(vol_id, set())
            )

        # Corrigido para usar o nome correto da tabela de grupos
        query_grupos = "SELECT * FROM grupos_vinculados WHERE id_ministerio = %s"
        grupos_raw = pd.read_sql(query_grupos, conn, params=(id_ministerio,))
        
        grupos_map = {}
        for _, row in grupos_raw.iterrows():
            grupo_id = int(row['id_grupo'])
            grupos_map[grupo_id] = Grupo(
                id_grupo=grupo_id,
                limite_escalas_grupo=int(row['limite_escalas_grupo'])
            )
        
        for vol in voluntarios_map.values():
            if vol.id_grupo and vol.id_grupo in grupos_map:
                grupos_map[vol.id_grupo].membros.append(vol)

        return voluntarios_map, grupos_map

    except Exception as e:
        print(f"ERRO CRÍTICO ao carregar dados: {e}")
        return {}, {}
    finally:
        if conn: conn.close()

# =========================================================================
# Função Principal de Geração de Escala (Versão Completa)
# Substitua sua função gerar_escala_automatica inteira por esta
# =========================================================================
def gerar_escala_automatica(ano, mes, id_ministerio):
    print(f"\n--- INICIANDO GERAÇÃO DA ESCALA PARA {mes}/{ano} [VERSÃO COMPLETA E CORRIGIDA] ---")

    # --- 1. SETUP E CARGA DE DADOS COM OBJETOS ---
    apagar_escala_do_mes(ano, mes, id_ministerio)
    eventos = get_events_for_month(ano, mes, id_ministerio)
    if eventos.empty: return {"status": "info", "message": "Não há eventos criados."}
    
    voluntarios_map, grupos_map = carregar_dados_para_escala(id_ministerio)
    if not voluntarios_map: return {"status": "error", "message": "Nenhum voluntário encontrado."}

    funcoes_df = view_all_funcoes(id_ministerio)
    cotas = get_cotas_all_servicos()
    
    try:
        id_apoio = funcoes_df[funcoes_df['tipo_funcao'] == 'APOIO']['id_funcao'].iloc[0]
        id_lider = funcoes_df[funcoes_df['nome_funcao'] == 'Líder']['id_funcao'].iloc[0]
        funcoes_principais = funcoes_df[funcoes_df['tipo_funcao'] == 'PRINCIPAL'].sort_values('prioridade_alocacao')
        ids_funcoes_principais = set(funcoes_principais['id_funcao'])
    except IndexError:
        return {"status": "error", "message": "Funções essenciais 'Apoio' ou 'Líder' não encontradas."}

    vagas_abertas = {}
    eventos['data_evento_obj'] = pd.to_datetime(eventos['data_evento']).dt.date
    for _, ev in eventos.iterrows():
        ev_cotas = cotas[cotas['id_servico'] == ev['id_servico_fixo']]
        for _, cota in ev_cotas.iterrows():
            id_funcao_cota = int(cota['id_funcao'])
            if id_funcao_cota in funcoes_df['id_funcao'].values:
                for i in range(1, int(cota['quantidade_necessaria']) + 1):
                    vaga_key = f"ev{ev['id_evento']}-func{id_funcao_cota}-inst{i}"
                    vagas_abertas[vaga_key] = Vaga(
                        id_evento=int(ev['id_evento']),
                        data_evento_obj=ev['data_evento_obj'],
                        id_funcao=id_funcao_cota,
                        funcao_instancia=i,
                        key=vaga_key
                    )
    
    escala_final = []

    # --- FUNÇÃO AUXILIAR GLOBAL DE ALOCAÇÃO ---
    def alocar(voluntario, vaga):
        nonlocal escala_final, vagas_abertas
        escala_final.append(EscalaEntry(
            id_evento=vaga.id_evento,
            id_funcao=vaga.id_funcao,
            id_voluntario=voluntario.id_voluntario,
            funcao_instancia=vaga.funcao_instancia
        ))
        voluntario.escalas_neste_mes += 1
        voluntario.dias_escalado.add(vaga.data_evento_obj)
        if vaga.key in vagas_abertas:
            del vagas_abertas[vaga.key]
        
        nome_funcao = funcoes_df.loc[funcoes_df['id_funcao'] == vaga.id_funcao, 'nome_funcao'].iloc[0]
        print(f"ALOCADO: '{voluntario.nome_voluntario}' na função '{nome_funcao}' no dia {vaga.data_evento_obj}")

    # --- FASE 1: GRUPOS ---
    print(f"--- FASE 1: Alocando {len(grupos_map)} Grupos ---")
    grupos_para_alocar = list(grupos_map.values())
    random.shuffle(grupos_para_alocar)
    
    eventos_unicos = list(eventos['id_evento'].unique())
    for grupo in grupos_para_alocar:
        if grupo.escalas_neste_mes >= grupo.limite_escalas_grupo: continue

        grupo.representantes = [m for m in grupo.membros if ids_funcoes_principais.intersection(m.funcoes)]
        grupo.apoiadores = [m for m in grupo.membros if m not in grupo.representantes]

        random.shuffle(eventos_unicos)
        alocado_nesta_rodada = False
        for id_evento in eventos_unicos:
            data_evento = eventos[eventos['id_evento'] == id_evento]['data_evento_obj'].iloc[0]

            ids_membros_grupo = {m.id_voluntario for m in grupo.membros}
            ids_escalados_no_dia = {e.id_voluntario for e in escala_final if e.id_evento == id_evento}
            if ids_membros_grupo.intersection(ids_escalados_no_dia): continue
            
            vagas_no_evento = [v for v in vagas_abertas.values() if v.id_evento == id_evento]

            if grupo.representantes:
                vagas_apoio_no_evento = [v for v in vagas_no_evento if v.id_funcao == id_apoio]
                if len(vagas_apoio_no_evento) < len(grupo.apoiadores): continue
                for rep in grupo.representantes:
                    vaga_principal_compativel = next((v for v in vagas_no_evento if v.id_funcao in rep.funcoes and v.id_funcao in ids_funcoes_principais), None)
                    if vaga_principal_compativel:
                        alocar(rep, vaga_principal_compativel)
                        for i, apoiador in enumerate(grupo.apoiadores):
                            alocar(apoiador, vagas_apoio_no_evento[i])
                        alocado_nesta_rodada = True
                        break
            else:
                vagas_apoio_no_evento = [v for v in vagas_no_evento if v.id_funcao == id_apoio]
                if len(vagas_apoio_no_evento) >= len(grupo.membros):
                    for i, membro in enumerate(grupo.membros):
                        alocar(membro, vagas_apoio_no_evento[i])
                    alocado_nesta_rodada = True
            
            if alocado_nesta_rodada:
                grupo.escalas_neste_mes += 1
                break
    
    # --- PREPARANDO FASES INDIVIDUAIS ---
    print("--- FASES INDIVIDUAIS ---")
    voluntarios_individuais = [v for v in voluntarios_map.values() if v.id_grupo is None]

    # --- FUNÇÃO AUXILIAR PARA FASES INDIVIDUAIS ---
    def alocar_individuais_por_fase(candidatos, vagas_filtro, respeitar_limites=True):
        nonlocal vagas_abertas, escala_final
        
        vagas_alvo = [v for v in vagas_abertas.values() if vagas_filtro(v)]
        if not vagas_alvo or not candidatos: return

        continuar_alocando = True
        while continuar_alocando and vagas_alvo:
            houve_alocacao_na_rodada = False
            random.shuffle(candidatos)
            
            staff_por_dia = defaultdict(int)
            for e in escala_final:
                evento_data = next((ev['data_evento_obj'] for _, ev in eventos.iterrows() if ev['id_evento'] == e.id_evento), None)
                if evento_data: staff_por_dia[evento_data] += 1
            vagas_alvo.sort(key=lambda v: staff_por_dia[v.data_evento_obj])
            
            for voluntario in candidatos:
                if respeitar_limites and voluntario.escalas_neste_mes >= voluntario.limite_escalas_mes: continue
                
                for vaga in vagas_alvo:
                    if vaga.key in vagas_abertas and vaga.data_evento_obj not in voluntario.dias_escalado and vaga.id_funcao in voluntario.funcoes:
                        alocar(voluntario, vaga)
                        vagas_alvo.remove(vaga)
                        houve_alocacao_na_rodada = True
                        break
                if houve_alocacao_na_rodada: break
            
            if not houve_alocacao_na_rodada:
                continuar_alocando = False

    # --- EXECUÇÃO DAS FASES INDIVIDUAIS ---
    for _, funcao in funcoes_principais.iterrows():
        id_funcao_atual, nome_funcao_atual = funcao['id_funcao'], funcao['nome_funcao']
        print(f"  - Alocando {nome_funcao_atual} (Individuais)")
        candidatos = [v for v in voluntarios_individuais if id_funcao_atual in v.funcoes]
        alocar_individuais_por_fase(candidatos, lambda v: v.id_funcao == id_funcao_atual)
        
    print("  - Alocando Apoio por Nível (Individuais)")
    candidatos_apoio = [v for v in voluntarios_individuais if id_apoio in v.funcoes]
    for nivel in ["Avançado", "Iniciante", "Intermediário"]:
        candidatos_nivel = [v for v in candidatos_apoio if v.nivel_experiencia == nivel]
        alocar_individuais_por_fase(candidatos_nivel, lambda v: v.id_funcao == id_apoio)

    print("  - Forçando preenchimento de Líderes (Individuais)")
    candidatos_lider = [v for v in voluntarios_individuais if id_lider in v.funcoes]
    alocar_individuais_por_fase(candidatos_lider, lambda v: v.id_funcao == id_lider, respeitar_limites=False)

    if vagas_abertas:
        print(f"  - Forçando preenchimento Geral para {len(vagas_abertas)} vagas (Individuais)")
        alocar_individuais_por_fase(voluntarios_individuais, lambda v: True, respeitar_limites=False)

    print("\n--- GERAÇÃO DA ESCALA CONCLUÍDA ---\n")
    if escala_final:
        print(f"Total de {len(escala_final)} alocações.")
        args = [(e.id_evento, e.id_funcao, e.id_voluntario, e.funcao_instancia) for e in escala_final]
        conn = ensure_connection()
        try:
            with conn.cursor() as cur:
                cur.executemany("INSERT INTO escala (id_evento, id_funcao, id_voluntario, funcao_instancia) VALUES (%s, %s, %s, %s)", args)
            conn.commit()
            return {"status": "success", "message": f"Escala com {len(escala_final)} alocações gerada e salva com sucesso!"}
        except Exception as e:
            conn.rollback()
            return {"status": "error", "message": f"Erro ao salvar escala: {e}"}
        finally:
            if conn: conn.close()
    else:
        return {"status": "info", "message": "Nenhuma alocação foi possível."}



def get_vinculos_para_escala():
    """
    Busca os IDs de voluntários agrupados por seu id_grupo.
    Esta função é otimizada para o gerador de escala.
    Retorna uma lista de listas, ex: [[10, 15], [21, 22, 23]]
    """
    conn = ensure_connection()
    if conn is None: 
        return []
    
    try:
        # Busca apenas voluntários ativos que pertencem a um grupo
        query = """
            SELECT id_grupo, id_voluntario
            FROM voluntarios
            WHERE id_grupo IS NOT NULL AND ativo = TRUE
            ORDER BY id_grupo;
        """
        df = pd.read_sql(query, conn)
        
        # A linha abaixo precisa estar indentada corretamente
        if df.empty:
            return []
            
        # Agrupa os IDs de voluntário pelo ID do grupo e converte para o formato de lista de listas
        vinculos = df.groupby('id_grupo')['id_voluntario'].apply(list).tolist()
        return vinculos
    except Exception as e:
        # Em uma API, é melhor imprimir o erro no console do que usar print
        print(f"Erro ao buscar vínculos para a escala: {e}")
        return []
    finally:
        if conn:
            conn.close()




def update_apenas_disponibilidade(id_voluntario, lista_ids_servicos):
    """ Atualiza apenas a disponibilidade de um voluntário. """
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM voluntario_disponibilidade WHERE id_voluntario = %s", (id_voluntario,))
            if lista_ids_servicos:
                args = [(id_voluntario, id_servico) for id_servico in lista_ids_servicos]
                cur.executemany("INSERT INTO voluntario_disponibilidade (id_voluntario, id_servico) VALUES (%s, %s)", args)
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Erro ao atualizar disponibilidade: {e}")

# Substitua a antiga 'update_escala_entry' por esta nova versão
def update_escala_entry(id_evento, id_funcao, id_voluntario, instancia):
    """
    Atualiza ou insere uma única entrada na escala, usando a 'instancia' da função.
    Se id_voluntario for None, a vaga é limpa (deletada).
    """
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            # Primeiro, deleta a entrada antiga para esta vaga específica (evento + função + instância)
            cur.execute(
                "DELETE FROM escala WHERE id_evento = %s AND id_funcao = %s AND funcao_instancia = %s",
                (id_evento, id_funcao, instancia)
            )
            # Se um novo voluntário foi selecionado (não é "Vago"), insere a nova entrada
            if id_voluntario is not None:
                cur.execute(
                    "INSERT INTO escala (id_evento, id_funcao, id_voluntario, funcao_instancia) VALUES (%s, %s, %s, %s)",
                    (id_evento, id_funcao, id_voluntario, instancia)
                )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Erro ao salvar alteração na escala: {e}")
        print(f"ERRO DETALHADO [update_escala_entry]: {e}")

def get_voluntarios_for_funcao(id_funcao):
    """
    Busca todos os voluntários ativos que estão aptos a exercer uma função específica.
    Esta função agora verifica a tabela de junção 'voluntario_funcoes'.
    """
    conn = ensure_connection()
    if conn is None:
        return pd.DataFrame()
    try:
        # Esta query junta as tabelas para encontrar todos os voluntários
        # que têm um vínculo com o id_funcao fornecido.
        query = """
            SELECT v.id_voluntario, v.nome_voluntario
            FROM voluntarios v
            JOIN voluntario_funcoes vf ON v.id_voluntario = vf.id_voluntario
            WHERE v.ativo = TRUE AND vf.id_funcao = %s
            ORDER BY v.nome_voluntario;
        """
        df = pd.read_sql(query, conn, params=(id_funcao,))
        return df
    except Exception as e:
        print(f"Erro ao buscar voluntários para a função {id_funcao}: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

def get_voluntario_by_name(nome_voluntario):
    """ Busca um voluntário pelo nome para encontrar seu ID. """
    conn = ensure_connection()
    if conn is None or not nome_voluntario: return None
    query = "SELECT id_voluntario FROM voluntarios WHERE nome_voluntario = %s"
    df = pd.read_sql(query, conn, params=(nome_voluntario,))
    return int(df['id_voluntario'].iloc[0]) if not df.empty else None

# Adicione v.nivel_experiencia ao SELECT


def atualizar_funcoes_do_voluntario(id_voluntario, nova_lista_de_ids_funcoes):
    """
    Sincroniza as funções de um voluntário usando a estratégia 'Apagar e Recriar'.
    """
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            # Passo 1: Apagar TODOS os vínculos de função antigos deste voluntário.
            cur.execute("DELETE FROM voluntario_funcoes WHERE id_voluntario = %s", (id_voluntario,))

            # Passo 2: Inserir os novos vínculos, se houver algum.
            if nova_lista_de_ids_funcoes:
                # Prepara os dados para uma inserção em massa
                dados_para_inserir = [(id_voluntario, id_funcao) for id_funcao in nova_lista_de_ids_funcoes]
                
                # Comando de inserção
                sql_insert = "INSERT INTO voluntario_funcoes (id_voluntario, id_funcao) VALUES (%s, %s)"
                cur.executemany(sql_insert, dados_para_inserir)
        
        conn.commit() # Efetiva as alterações (DELETE e INSERTs)
        
    except Exception as e:
        conn.rollback() # Desfaz tudo em caso de erro
        print(f"Erro ao atualizar as funções do voluntário: {e}")
    finally:
        if conn:
            conn.close()

            