import streamlit as st
import psycopg2
import pandas as pd
import calendar
from datetime import datetime

# --- NOVO GERENCIADOR DE CONEXÃO ---
# Esta função será a única responsável por fornecer uma conexão válida.
# O @st.cache_resource garante que tentaremos reutilizar a mesma conexão.
@st.cache_resource
def get_connection():
    try:
        # Tenta criar uma conexão
        conn = psycopg2.connect(**st.secrets["postgres"])
        return conn
    except Exception as e:
        st.error(f"Não foi possível conectar ao banco de dados: {e}")
        return None

# Função para verificar e reconectar se necessário
def ensure_connection():
    """Garante que a conexão está ativa, reconectando se necessário."""
    try:
        # Tenta pegar a conexão do cache
        conn = get_connection()
        # Verifica se a conexão está fechada ou com problemas
        if conn is None or conn.closed != 0:
            # Limpa o cache para forçar uma nova conexão na próxima chamada
            st.cache_resource.clear()
            # Tenta obter uma nova conexão
            conn = get_connection()
        return conn
    except Exception as e:
        st.error(f"Erro ao garantir a conexão com o banco de dados: {e}")
        st.cache_resource.clear()
        return None

# --- FUNÇÕES DAS TABELAS (AGORA MAIS ROBUSTAS) ---
# Todas as funções agora chamarão ensure_connection() no início

def add_funcao(nome_funcao, descricao=""):
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO funcoes (nome_funcao, descricao) VALUES (%s, %s) ON CONFLICT (nome_funcao) DO NOTHING", (nome_funcao, descricao))
        conn.commit()
        st.success(f"Função '{nome_funcao}' adicionada com sucesso!")
    except Exception as e:
        conn.rollback()
        st.error(f"Erro ao adicionar função: {e}")

def view_all_funcoes():
    conn = ensure_connection()
    if conn is None: return pd.DataFrame()
    return pd.read_sql("SELECT * FROM funcoes ORDER BY nome_funcao ASC", conn)

def update_funcao(id_funcao, novo_nome, nova_descricao):
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE funcoes SET nome_funcao = %s, descricao = %s WHERE id_funcao = %s", (novo_nome, nova_descricao, id_funcao))
        conn.commit()
        st.success("Função atualizada com sucesso!")
    except Exception as e:
        conn.rollback()
        st.error(f"Erro ao atualizar função: {e}")

def delete_funcao(id_funcao):
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM funcoes WHERE id_funcao = %s", (id_funcao,))
        conn.commit()
        st.success("Função deletada com sucesso!")
    except Exception as e:
        conn.rollback()
        st.error(f"Erro ao deletar função: {e}")

# --- Funções para a tabela 'voluntarios' ---

def add_voluntario(nome, telefone, limite_mes):
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO voluntarios (nome_voluntario, telefone, limite_escalas_mes) VALUES (%s, %s, %s)", (nome, telefone, limite_mes))
        conn.commit()
    except Exception as e:
        conn.rollback()
        st.error(f"Erro ao adicionar voluntário: {e}")

def view_all_voluntarios(include_inactive=False):
    """ 
    Retorna um DataFrame com os voluntários.
    Por padrão, retorna apenas os ativos. Se include_inactive for True, retorna todos.
    """
    conn = ensure_connection()
    if conn is None: return pd.DataFrame()
    
    query = "SELECT * FROM voluntarios"
    if not include_inactive:
        query += " WHERE ativo = TRUE"
    
    query += " ORDER BY nome_voluntario ASC"
    
    return pd.read_sql(query, conn)

def get_voluntario_by_id(id_voluntario):
    conn = ensure_connection()
    if conn is None: return None
    df = pd.read_sql(f"SELECT * FROM voluntarios WHERE id_voluntario = {id_voluntario}", conn)
    return df.iloc[0] if not df.empty else None

def update_voluntario(id_voluntario, nome, telefone, limite_mes, ativo):
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE voluntarios SET nome_voluntario = %s, telefone = %s, limite_escalas_mes = %s, ativo = %s WHERE id_voluntario = %s", (nome, telefone, limite_mes, ativo, id_voluntario))
        conn.commit()
    except Exception as e:
        conn.rollback()
        st.error(f"Erro ao atualizar dados básicos do voluntário.")
        print(f"ERRO DETALHADO [update_voluntario]: {e}")

# --- Funções para a tabela 'voluntario_funcoes' ---

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
        conn.rollback()
        st.error(f"Erro ao atualizar funções do voluntário.")
        print(f"ERRO DETALH-ADO [update_funcoes_of_voluntario]: {e}")

# --- Funções para a tabela 'servicos_fixos' ---

def add_servico_fixo(nome, dia_da_semana):
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO servicos_fixos (nome_servico, dia_da_semana) VALUES (%s, %s) ON CONFLICT (nome_servico) DO NOTHING", (nome, dia_da_semana))
        conn.commit()
        st.success(f"Serviço '{nome}' adicionado com sucesso!")
    except Exception as e:
        conn.rollback()
        st.error(f"Erro ao adicionar serviço: {e}")

def view_all_servicos_fixos():
    conn = ensure_connection()
    if conn is None: return pd.DataFrame()
    return pd.read_sql("SELECT * FROM servicos_fixos WHERE ativo = TRUE ORDER BY dia_da_semana, nome_servico ASC", conn)

def update_servico_fixo(id_servico, nome, dia_da_semana, ativo):
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE servicos_fixos SET nome_servico = %s, dia_da_semana = %s, ativo = %s WHERE id_servico = %s", (nome, dia_da_semana, ativo, id_servico))
        conn.commit()
        st.success("Serviço atualizado com sucesso!")
    except Exception as e:
        conn.rollback()
        st.error(f"Erro ao atualizar serviço: {e}")

def delete_servico_fixo(id_servico):
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM servicos_fixos WHERE id_servico = %s", (id_servico,))
        conn.commit()
        st.success("Serviço deletado com sucesso!")
    except Exception as e:
        conn.rollback()
        st.error(f"Erro ao deletar serviço: {e}")

# --- Funções para a tabela 'voluntario_disponibilidade' ---

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
        conn.rollback()
        st.error(f"Erro ao atualizar disponibilidade do voluntário.")
        print(f"ERRO DETALHADO [update_disponibilidade_of_voluntario]: {e}")

# --- Funções para a tabela 'voluntario_indisponibilidade' ---

def check_indisponibilidade(id_voluntario, mes_ano):
    conn = ensure_connection()
    if conn is None: return False
    df = pd.read_sql("SELECT * FROM voluntario_indisponibilidade WHERE id_voluntario = %s AND mes_ano = %s", conn, params=(id_voluntario, mes_ano))
    return not df.empty

def set_indisponibilidade(id_voluntario, mes_ano, indisponivel):
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            if indisponivel:
                cur.execute("INSERT INTO voluntario_indisponibilidade (id_voluntario, mes_ano) VALUES (%s, %s) ON CONFLICT DO NOTHING", (id_voluntario, mes_ano))
            else:
                cur.execute("DELETE FROM voluntario_indisponibilidade WHERE id_voluntario = %s AND mes_ano = %s", (id_voluntario, mes_ano))
        conn.commit()
    except Exception as e:
        conn.rollback()
        st.error(f"Erro ao definir indisponibilidade: {e}")
        print(f"ERRO DETALHADO [set_indisponibilidade]: {e}")

# --- Funções para Geração e Visualização da Escala ---

def create_events_for_month(ano, mes):
    """ Cria os registros de eventos para um determinado mês e ano. """
    conn = ensure_connection()
    if conn is None: return False
    
    # Busca todos os serviços fixos (Domingo Manhã, Quinta, etc.)
    servicos_fixos = view_all_servicos_fixos()
    if servicos_fixos.empty:
        st.warning("Nenhum serviço fixo cadastrado. Adicione serviços na página 'Gerenciar Serviços'.")
        return False

    try:
        with conn.cursor() as cur:
            # Primeiro, deleta os eventos existentes para este mês para evitar duplicatas
            cur.execute("DELETE FROM eventos WHERE EXTRACT(YEAR FROM data_evento) = %s AND EXTRACT(MONTH FROM data_evento) = %s", (ano, mes))
            
            # Pega o número de dias no mês
            _, num_dias = calendar.monthrange(ano, mes)
            
            eventos_criados = 0
            # Itera sobre cada dia do mês
            for dia in range(1, num_dias + 1):
                data_atual = datetime(ano, mes, dia).date()
                dia_da_semana_atual = data_atual.weekday() # Segunda=0, Domingo=6
                # Ajuste para nossa convenção: Domingo=0, Segunda=1...
                dia_da_semana_ajustado = (dia_da_semana_atual + 1) % 7
                
                # Verifica se há algum serviço fixo para este dia da semana
                for _, servico in servicos_fixos.iterrows():
                    if servico['dia_da_semana'] == dia_da_semana_ajustado:
                        # Insere o evento no banco de dados
                        cur.execute(
                            "INSERT INTO eventos (id_servico_fixo, data_evento) VALUES (%s, %s)",
                            (int(servico['id_servico']), data_atual)
                        )
                        eventos_criados += 1
            conn.commit()
            st.success(f"{eventos_criados} eventos criados com sucesso para {mes}/{ano}!")
            return True
    except Exception as e:
        conn.rollback()
        st.error(f"Erro ao criar eventos: {e}")
        print(f"ERRO DETALHADO [create_events_for_month]: {e}")
        return False

def get_events_for_month(ano, mes):
    """ Busca todos os eventos de um mês, juntando com o nome do serviço. """
    conn = ensure_connection()
    if conn is None: return pd.DataFrame()
    
    query = """
    SELECT e.id_evento, e.data_evento, sf.nome_servico
    FROM eventos e
    JOIN servicos_fixos sf ON e.id_servico_fixo = sf.id_servico
    WHERE EXTRACT(YEAR FROM e.data_evento) = %s AND EXTRACT(MONTH FROM e.data_evento) = %s
    ORDER BY e.data_evento ASC;
    """
    return pd.read_sql(query, conn, params=(ano, mes))

def get_escala_completa(ano, mes):
    """ Busca a escala completa de um mês com todos os nomes. """
    conn = ensure_connection()
    if conn is None: return pd.DataFrame()

    query = """
    SELECT 
        e.id_evento, 
        e.data_evento, 
        sf.nome_servico,
        f.id_funcao,
        f.nome_funcao,
        v.id_voluntario,
        v.nome_voluntario
    FROM escala esc
    JOIN eventos e ON esc.id_evento = e.id_evento
    JOIN funcoes f ON esc.id_funcao = f.id_funcao
    JOIN voluntarios v ON esc.id_voluntario = v.id_voluntario
    JOIN servicos_fixos sf ON e.id_servico_fixo = sf.id_servico
    WHERE EXTRACT(YEAR FROM e.data_evento) = %s AND EXTRACT(MONTH FROM e.data_evento) = %s
    ORDER BY e.data_evento, f.nome_funcao;
    """
    return pd.read_sql(query, conn, params=(ano, mes))

# --- Funções para a tabela 'grupos_vinculados' ---

def create_grupo_vinculado(nome_grupo, ids_voluntarios):
    """ Cria um novo grupo e vincula os voluntários a ele. """
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            # 1. Cria o grupo e obtém o ID gerado
            cur.execute("INSERT INTO grupos_vinculados (nome_grupo) VALUES (%s) RETURNING id_grupo", (nome_grupo,))
            id_novo_grupo = cur.fetchone()[0]
            
            # 2. Atualiza a tabela de voluntários com o novo ID do grupo
            # psycopg2 exige uma tupla, mesmo para um único item no IN
            cur.execute(
                "UPDATE voluntarios SET id_grupo = %s WHERE id_voluntario IN %s",
                (id_novo_grupo, tuple(ids_voluntarios))
            )
        conn.commit()
        st.success(f"Grupo '{nome_grupo}' criado com sucesso!")
    except Exception as e:
        conn.rollback()
        st.error(f"Erro ao criar grupo: {e}")
        print(f"ERRO DETALHADO [create_grupo_vinculado]: {e}")

def get_all_grupos_com_membros():
    """ Retorna um DataFrame com todos os grupos e uma lista de seus membros. """
    conn = ensure_connection()
    if conn is None: return pd.DataFrame()
    
    query = """
    SELECT 
        gv.id_grupo, 
        gv.nome_grupo, 
        STRING_AGG(v.nome_voluntario, ', ' ORDER BY v.nome_voluntario) as membros
    FROM grupos_vinculados gv
    JOIN voluntarios v ON gv.id_grupo = v.id_grupo
    GROUP BY gv.id_grupo, gv.nome_grupo
    ORDER BY gv.nome_grupo;
    """
    return pd.read_sql(query, conn)

def get_voluntarios_in_grupo(id_grupo):
    """ Retorna uma lista de IDs de voluntários que pertencem a um grupo. """
    conn = ensure_connection()
    if conn is None: return []
    df = pd.read_sql(f"SELECT id_voluntario FROM voluntarios WHERE id_grupo = {id_grupo}", conn)
    return df['id_voluntario'].tolist()

def update_grupo_vinculado(id_grupo, novo_nome, novos_ids_voluntarios):
    """ Atualiza o nome e os membros de um grupo. """
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            # 1. Atualiza o nome do grupo
            cur.execute("UPDATE grupos_vinculados SET nome_grupo = %s WHERE id_grupo = %s", (novo_nome, id_grupo))
            
            # 2. Remove o vínculo de todos os voluntários que pertenciam a este grupo (limpeza)
            cur.execute("UPDATE voluntarios SET id_grupo = NULL WHERE id_grupo = %s", (id_grupo,))
            
            # 3. Adiciona o vínculo para a nova lista de voluntários
            if novos_ids_voluntarios:
                cur.execute(
                    "UPDATE voluntarios SET id_grupo = %s WHERE id_voluntario IN %s",
                    (id_grupo, tuple(novos_ids_voluntarios))
                )
        conn.commit()
        st.success(f"Grupo '{novo_nome}' atualizado com sucesso!")
    except Exception as e:
        conn.rollback()
        st.error(f"Erro ao atualizar grupo: {e}")
        print(f"ERRO DETALHADO [update_grupo_vinculado]: {e}")

def delete_grupo_vinculado(id_grupo):
    """ Deleta um grupo (os voluntários ficam sem grupo). """
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            # O 'ON DELETE SET NULL' na tabela voluntarios já cuida de desvincular os voluntários.
            # Aqui só precisamos deletar o grupo em si.
            cur.execute("DELETE FROM grupos_vinculados WHERE id_grupo = %s", (id_grupo,))
        conn.commit()
        st.success("Grupo deletado com sucesso!")
    except Exception as e:
        conn.rollback()
        st.error(f"Erro ao deletar grupo: {e}")
        print(f"ERRO DETALHADO [delete_grupo_vinculado]: {e}")