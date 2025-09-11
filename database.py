# database.py - VERSÃO FINAL, COMPLETA E ESTÁVEL
import streamlit as st
import psycopg2
import pandas as pd
from collections import defaultdict
from datetime import datetime, date
import calendar
import random
from werkzeug.security import generate_password_hash, check_password_hash

@st.cache_resource
def get_connection():
    try:
        return psycopg2.connect(**st.secrets["postgres"])
    except Exception as e:
        st.error(f"Não foi possível conectar ao banco de dados: {e}")
        return None
    
def ensure_connection():
    """
    Garante uma conexão ativa com o banco de dados. Se a conexão cacheada
    foi fechada pelo servidor (por inatividade, etc.), limpa o cache e
    cria uma nova.
    """
    conn = get_connection()
    try:
        # Tenta executar uma consulta simples e rápida para verificar se a conexão está ativa.
        # Isso é mais confiável do que apenas checar `conn.closed`.
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        # Se a consulta falhar, a conexão provavelmente foi fechada pelo servidor.
        # Limpamos o cache para remover a conexão "morta" e obtemos uma nova.
        st.cache_resource.clear()
        conn = get_connection()
    return conn


def criar_usuario(username, password, id_ministerio):
    """Cria um novo usuário com senha criptografada."""
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            password_hash = generate_password_hash(password)
            cur.execute(
                "INSERT INTO usuarios (username, password_hash, id_ministerio) VALUES (%s, %s, %s)",
                (username, password_hash, id_ministerio)
            )
        conn.commit()
        st.success(f"Usuário '{username}' criado com sucesso!")
    except Exception as e:
        conn.rollback()
        st.error(f"Erro ao criar usuário: {e}")

def verificar_login(username, password):
    """Verifica o login e retorna o id_ministerio se for válido."""
    conn = ensure_connection()
    if conn is None: return None
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT password_hash, id_ministerio FROM usuarios WHERE username = %s", (username,))
            result = cur.fetchone()
            if result:
                password_hash, id_ministerio = result
                if check_password_hash(password_hash, password):
                    return id_ministerio # Login bem-sucedido
    except Exception as e:
        st.error(f"Erro de login: {e}")
    return None # Login falhou

# --- CRUD FUNÇÕES ---

def add_funcao(nome_funcao, descricao, id_ministerio):
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            # Verifica se a função já existe para o mesmo ministério
            cur.execute("SELECT COUNT(*) FROM funcoes WHERE nome_funcao = %s AND id_ministerio = %s", (nome_funcao, id_ministerio))
            if cur.fetchone()[0] > 0:
                st.warning(f"A função '{nome_funcao}' já existe neste ministério.")
                return

            # Insere o novo registro com o id_ministerio
            cur.execute(
                "INSERT INTO funcoes (nome_funcao, descricao, id_ministerio) VALUES (%s, %s, %s)",
                (nome_funcao, descricao, id_ministerio)
            )
        conn.commit()
        st.success(f"Função '{nome_funcao}' adicionada com sucesso!")
    except Exception as e:
        conn.rollback()
        st.error(f"Erro ao adicionar função: {e}")






def view_all_funcoes(id_ministerio):
    """ Busca todas as funções de um ministério específico. """
    conn = ensure_connection()
    if conn is None: return pd.DataFrame()
    query = "SELECT * FROM funcoes WHERE id_ministerio = %s ORDER BY nome_funcao ASC"
    return pd.read_sql(query, conn, params=(id_ministerio,))


def update_funcao(id_funcao, novo_nome, nova_descricao):
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE funcoes SET nome_funcao = %s, descricao = %s WHERE id_funcao = %s", (novo_nome, nova_descricao, id_funcao))
        conn.commit()
        st.success("Função atualizada com sucesso!")
    except Exception as e:
        conn.rollback(); st.error(f"Erro ao atualizar função: {e}")

def delete_funcao(id_funcao):
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM funcoes WHERE id_funcao = %s", (id_funcao,))
        conn.commit()
        st.success("Função deletada com sucesso!")
    except Exception as e:
        conn.rollback(); st.error(f"Erro ao deletar função: {e}")

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
        conn.rollback(); st.error(f"Erro ao atualizar voluntário: {e}")

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
        conn.rollback(); st.error(f"Erro ao atualizar funções do voluntário: {e}")

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
#         st.success(f"Serviço '{nome}' adicionado com sucesso!")
#     except Exception as e:
#         conn.rollback(); st.error(f"Erro ao adicionar serviço: {e}")

def add_servico_fixo(nome, dia_da_semana, id_ministerio):
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            # Verifica se o serviço já existe para o mesmo ministério
            cur.execute("SELECT COUNT(*) FROM servicos_fixos WHERE nome_servico = %s AND id_ministerio = %s", (nome, id_ministerio))
            if cur.fetchone()[0] > 0:
                st.warning(f"O serviço '{nome}' já existe neste ministério.")
                return

            # Insere o novo registro com o id_ministerio
            cur.execute(
                "INSERT INTO servicos_fixos (nome_servico, dia_da_semana, id_ministerio) VALUES (%s, %s, %s)",
                (nome, dia_da_semana, id_ministerio)
            )
        conn.commit()
        st.success(f"Serviço '{nome}' adicionado com sucesso!")
    except Exception as e:
        conn.rollback()
        st.error(f"Erro ao adicionar serviço: {e}")

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
        st.success("Serviço atualizado com sucesso!")
    except Exception as e:
        conn.rollback(); st.error(f"Erro ao atualizar serviço: {e}")

def delete_servico_fixo(id_servico):
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM servicos_fixos WHERE id_servico = %s", (id_servico,))
        conn.commit()
        st.success("Serviço deletado com sucesso!")
    except Exception as e:
        conn.rollback(); st.error(f"Erro ao deletar serviço: {e}")

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
        conn.rollback(); st.error(f"Erro ao atualizar disponibilidade: {e}")

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
        conn.rollback(); st.error(f"Erro ao atualizar disponibilidade: {e}")

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
        st.error(f"Erro ao atualizar indisponibilidades: {e}")

# ----- MINISTERIOS ------

def get_all_ministerios():
    """Busca todos os ministérios no banco de dados e retorna um DataFrame."""
    conn = ensure_connection() # << Usa sua função de conexão já existente
    if conn is None:
        return pd.DataFrame() # Retorna um DataFrame vazio se não houver conexão
    try:
        query = "SELECT id_ministerio, nome_ministerio FROM ministerios ORDER BY nome_ministerio"
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"Erro ao buscar ministérios: {e}")
        return pd.DataFrame()
    finally:
        # É uma boa prática fechar a conexão após o uso
        if conn:
            conn.close()


# --- CRUD GRUPOS ---
def get_all_grupos_com_membros(id_ministerio, _cache_buster=None):
    """ Retorna um DataFrame com os grupos e seus membros FILTRADOS POR MINISTÉRIO. """
    conn = ensure_connection()
    if conn is None: return pd.DataFrame()
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
    return pd.read_sql(query, conn, params=(id_ministerio,))

def get_voluntarios_sem_grupo(id_ministerio):
    """ Retorna voluntários sem grupo que pertencem ao ministério especificado. """
    conn = ensure_connection()
    if conn is None: return pd.DataFrame()
    
    query = """
        SELECT id_voluntario, nome_voluntario 
        FROM voluntarios 
        WHERE ativo = TRUE 
          AND id_grupo IS NULL 
          AND id_ministerio = %s 
        ORDER BY nome_voluntario
    """
    return pd.read_sql(query, conn, params=(id_ministerio,))

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
        conn.rollback(); st.error(f"Erro ao criar grupo: {e}")

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
        conn.rollback(); st.error(f"Erro ao atualizar grupo: {e}")


def delete_grupo(id_grupo):
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE voluntarios SET id_grupo = NULL WHERE id_grupo = %s", (id_grupo,))
            cur.execute("DELETE FROM grupos_vinculados WHERE id_grupo = %s", (id_grupo,))
        conn.commit()
    except Exception as e:
        conn.rollback(); st.error(f"Erro ao deletar grupo: {e}")

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
        conn.rollback(); st.error(f"Erro ao atualizar cotas: {e}")



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
        st.error(f"Erro ao adicionar voluntário: {e}")
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
        return df
    except Exception as e:
        st.error(f"Erro ao buscar dados detalhados dos voluntários: {e}")
        return pd.DataFrame()

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
        conn.rollback(); st.error(f"Erro ao salvar alteração na escala: {e}")

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
        conn.rollback(); st.error(f"Erro ao atualizar indisponibilidade: {e}")

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
        st.error(f"Erro ao limpar escala antiga: {e}")


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

# No arquivo: database.py

# ... (outras funções do seu arquivo) ...

def create_events_for_month(ano, mes, id_ministerio):
    conn = ensure_connection()
    if conn is None: return False
    # Filtra os serviços fixos pelo ministério antes de criar os eventos
    servicos_fixos = view_all_servicos_fixos(id_ministerio)
    if servicos_fixos.empty:
        st.warning("Nenhum serviço fixo cadastrado para este ministério."); return False
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
        st.success(f"Eventos para {mes}/{ano} criados!"); return True
    except Exception as e:
        conn.rollback(); st.error(f"Erro ao criar eventos: {e}"); return False

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


def gerar_escala_automatica(ano, mes, id_ministerio):
    """
    ALGORITMO V26 (DRAFT PRIORITÁRIO):
    - A cada passo, identifica a vaga mais crítica (por prioridade de função e dia mais vazio).
    - Tenta preencher a vaga com o candidato mais descansado (grupo ou indivíduo).
    - Garante rotação e distribuição justa, respeitando a prioridade de grupos com líder.
    """
    # --- SETUP INICIAL ---
    apagar_escala_do_mes(ano, mes, id_ministerio)
    eventos = get_events_for_month(ano, mes, id_ministerio)
    if eventos.empty: st.info("Não há eventos criados para este mês."); return
    eventos['data_evento_date_obj'] = pd.to_datetime(eventos['data_evento']).dt.date
    
    voluntarios_df = get_all_voluntarios_com_detalhes(id_ministerio)
    cotas = get_cotas_all_servicos()
    todas_funcoes = view_all_funcoes(id_ministerio)
    grupos_df = get_all_grupos_com_membros(id_ministerio)

    id_funcoes = {nome: id for nome, id in zip(todas_funcoes['nome_funcao'].replace('Líder de Escala', 'Líder'), todas_funcoes['id_funcao'])}
    limites_grupo = {int(gid): int(lim) for gid, lim in grupos_df.set_index('id_grupo')['limite_escalas_grupo'].to_dict().items()}
    
    contagem_escalas_grupo = defaultdict(int)
    contagem_escalas_voluntario = defaultdict(int)
    escala_final = []
    
    vagas_df = pd.DataFrame([
        {'id_evento': ev['id_evento'], 'id_servico_fixo': ev['id_servico_fixo'], 
         'data_evento_date_obj': ev['data_evento_date_obj'], 'id_funcao': int(cota['id_funcao']), 'funcao_instancia': i}
        for _, ev in eventos.iterrows() for _, cota in cotas[cotas['id_servico'] == ev['id_servico_fixo']].iterrows() 
        for i in range(1, int(cota['quantidade_necessaria']) + 1)
        if cota['id_funcao'] in id_funcoes.values()
    ])

    # --- INÍCIO DA LÓGICA DE DRAFT ---
    id_lider = id_funcoes.get('Líder')
    id_store = id_funcoes.get('Store')
    id_apoio = id_funcoes.get('Apoio')
    prioridade_funcao = {id_lider: 1, id_store: 2, id_apoio: 3}

    # Loop principal: continua enquanto houver vagas a preencher
    while not vagas_df.empty:
        # 1. ORDENAR VAGAS POR CRITICIDADE
        escalados_por_data = defaultdict(set)
        for e in escala_final:
            evento = eventos[eventos['id_evento'] == e['id_evento']].iloc[0]
            escalados_por_data[evento['data_evento_date_obj']].add(e['id_voluntario'])

        vagas_df['staff_no_dia'] = vagas_df['data_evento_date_obj'].map(lambda d: len(escalados_por_data.get(d, set())))
        vagas_df['prioridade'] = vagas_df['id_funcao'].map(lambda f: prioridade_funcao.get(f, 99))
        vagas_df.sort_values(by=['staff_no_dia', 'prioridade'], inplace=True)
        
        if vagas_df.empty: break
        vaga_alvo = vagas_df.iloc[0]
        vaga_preenchida = False

        # 2. TENTAR PREENCHER A VAGA ALVO
        # Se for vaga de LÍDER, a prioridade é um LÍDER DE GRUPO
        if vaga_alvo['id_funcao'] == id_lider:
            candidatos_lider_grupo = voluntarios_df[(voluntarios_df['funcoes'].apply(lambda f: id_lider in (f or []))) & (voluntarios_df['id_grupo'].notna())].copy()
            candidatos_lider_grupo['contagem_grupo'] = candidatos_lider_grupo['id_grupo'].map(contagem_escalas_grupo)
            candidatos_lider_grupo = candidatos_lider_grupo.sample(frac=1).sort_values(by='contagem_grupo') # Desempate aleatório

            for _, candidato_lider in candidatos_lider_grupo.iterrows():
                id_grupo = candidato_lider['id_grupo']
                if contagem_escalas_grupo[id_grupo] >= limites_grupo.get(id_grupo, 0): continue
                
                membros_grupo = voluntarios_df[voluntarios_df['id_grupo'] == id_grupo]
                vagas_necessarias_apoio = len(membros_grupo) - 1
                vagas_apoio_disponiveis = vagas_df[(vagas_df['data_evento_date_obj'] == vaga_alvo['data_evento_date_obj']) & (vagas_df['id_funcao'] == id_apoio)]
                
                escalados_no_dia = {e['id_voluntario'] for e in escala_final if eventos[eventos['id_evento'] == e['id_evento']]['data_evento_date_obj'].iloc[0] == vaga_alvo['data_evento_date_obj']}
                todos_podem_servir = all(m['id_voluntario'] not in escalados_no_dia for _, m in membros_grupo.iterrows())

                if todos_podem_servir and len(vagas_apoio_disponiveis) >= vagas_necessarias_apoio:
                    # Aloca o grupo
                    escala_final.append({'id_evento': int(vaga_alvo['id_evento']), 'id_funcao': int(vaga_alvo['id_funcao']), 'id_voluntario': int(candidato_lider['id_voluntario']), 'funcao_instancia': int(vaga_alvo['funcao_instancia'])})
                    vagas_df.drop(vaga_alvo.name, inplace=True, errors='ignore')
                    
                    outros_membros = membros_grupo[membros_grupo['id_voluntario'] != candidato_lider['id_voluntario']]
                    vagas_para_usar = vagas_apoio_disponiveis.head(len(outros_membros))
                    for i, (_, membro) in enumerate(outros_membros.iterrows()):
                        vaga_membro = vagas_para_usar.iloc[i]
                        escala_final.append({'id_evento': int(vaga_membro['id_evento']), 'id_funcao': int(vaga_membro['id_funcao']), 'id_voluntario': int(membro['id_voluntario']), 'funcao_instancia': int(vaga_membro['funcao_instancia'])})
                        vagas_df.drop(vaga_membro.name, inplace=True, errors='ignore')

                    contagem_escalas_grupo[id_grupo] += 1
                    vaga_preenchida = True
                    break
        
        # 3. SE NÃO DEU PARA ALOCAR GRUPO, OU A VAGA NÃO É DE LÍDER, ALOCA INDIVÍDUO
        if not vaga_preenchida:
            candidatos_individuais = voluntarios_df[
                (voluntarios_df['id_grupo'].isnull()) &
                (voluntarios_df['funcoes'].apply(lambda f: vaga_alvo['id_funcao'] in (f or [])))
            ].copy()
            candidatos_individuais['contagem_pessoal'] = candidatos_individuais['id_voluntario'].map(contagem_escalas_voluntario)
            candidatos_individuais = candidatos_individuais.sample(frac=1).sort_values(by='contagem_pessoal') # Desempate aleatório

            escalados_no_dia = {e['id_voluntario'] for e in escala_final if eventos[eventos['id_evento'] == e['id_evento']]['data_evento_date_obj'].iloc[0] == vaga_alvo['data_evento_date_obj']}
            for _, candidato in candidatos_individuais.iterrows():
                cid = candidato['id_voluntario']
                if cid not in escalados_no_dia:
                    escala_final.append({'id_evento': int(vaga_alvo['id_evento']), 'id_funcao': int(vaga_alvo['id_funcao']), 'id_voluntario': int(cid), 'funcao_instancia': int(vaga_alvo['funcao_instancia'])})
                    contagem_escalas_voluntario[cid] += 1
                    vagas_df.drop(vaga_alvo.name, inplace=True, errors='ignore')
                    vaga_preenchida = True
                    break
        
        # Se mesmo após todas as tentativas a vaga não foi preenchida, remove-a para evitar loop infinito
        if not vaga_preenchida:
            vagas_df.drop(vaga_alvo.name, inplace=True, errors='ignore')

    # --- SALVAR NO BANCO ---
    if escala_final:
        conn = ensure_connection()
        try:
            with conn.cursor() as cur:
                args = [(e['id_evento'], e['id_funcao'], e['id_voluntario'], e['funcao_instancia']) for e in escala_final]
                cur.executemany("INSERT INTO escala (id_evento, id_funcao, id_voluntario, funcao_instancia) VALUES (%s, %s, %s, %s)", args)
            conn.commit()
            st.success("Escala gerada com sucesso pelo novo algoritmo de Draft!")
        except Exception as e:
            conn.rollback(); st.error(f"Erro ao salvar escala: {e}")


def get_vinculos_para_escala():
    """
    Busca os IDs de voluntários agrupados por seu id_grupo.
    Esta função é otimizada para o gerador de escala.
    Retorna uma lista de listas, ex: [[10, 15], [21, 22, 23]]
    """
    conn = ensure_connection()
    if conn is None: return []
    try:
        # Busca apenas voluntários ativos que pertencem a um grupo
        query = """
            SELECT id_grupo, id_voluntario
            FROM voluntarios
            WHERE id_grupo IS NOT NULL AND ativo = TRUE
            ORDER BY id_grupo;
        """
        df = pd.read_sql(query, conn)
        
        if df.empty:
            return []
            
        # Agrupa os IDs de voluntário pelo ID do grupo e converte para o formato de lista de listas
        vinculos = df.groupby('id_grupo')['id_voluntario'].apply(list).tolist()
        return vinculos
    except Exception as e:
        st.error(f"Erro ao buscar vínculos para a escala: {e}")
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
        st.error(f"Erro ao atualizar disponibilidade: {e}")

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
        st.error(f"Erro ao salvar alteração na escala: {e}")
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
        st.error(f"Erro ao buscar voluntários para a função {id_funcao}: {e}")
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
        st.toast("Funções do voluntário atualizadas com sucesso!", icon="✅")
    except Exception as e:
        conn.rollback() # Desfaz tudo em caso de erro
        st.error(f"Erro ao atualizar as funções do voluntário: {e}")
    finally:
        if conn:
            conn.close()