# database.py - VERSÃO FINAL, COMPLETA E ESTÁVEL
import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime, date
import calendar
import random

@st.cache_resource
def get_connection():
    try:
        return psycopg2.connect(**st.secrets["postgres"])
    except Exception as e:
        st.error(f"Não foi possível conectar ao banco de dados: {e}")
        return None

def ensure_connection():
    try:
        conn = get_connection()
        if conn is None or conn.closed != 0:
            st.cache_resource.clear()
            conn = get_connection()
        return conn
    except Exception as e:
        st.error(f"Erro ao garantir a conexão com o banco de dados: {e}")
        st.cache_resource.clear()
        return None

# --- CRUD FUNÇÕES ---
def add_funcao(nome_funcao, descricao=""):
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO funcoes (nome_funcao, descricao) VALUES (%s, %s) ON CONFLICT (nome_funcao) DO NOTHING", (nome_funcao, descricao))
        conn.commit()
        st.success(f"Função '{nome_funcao}' adicionada com sucesso!")
    except Exception as e:
        conn.rollback(); st.error(f"Erro ao adicionar função: {e}")

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
def add_voluntario(nome, limite_mes, nivel_experiencia):
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO voluntarios (nome_voluntario, limite_escalas_mes, nivel_experiencia) VALUES (%s, %s, %s)", 
                (nome, limite_mes, nivel_experiencia)
            )
        conn.commit()
    except Exception as e:
        conn.rollback(); st.error(f"Erro ao adicionar voluntário: {e}")

def view_all_voluntarios(include_inactive=False):
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
    conn = ensure_connection()
    if conn is None: return pd.DataFrame()
    query = "SELECT v.id_voluntario, v.nome_voluntario FROM voluntarios v JOIN voluntario_funcoes vf ON v.id_voluntario = vf.id_voluntario WHERE v.ativo = TRUE AND vf.id_funcao = %s ORDER BY v.nome_voluntario"
    return pd.read_sql(query, conn, params=(int(id_funcao),))

# --- CRUD SERVIÇOS_FIXOS ---
def add_servico_fixo(nome, dia_da_semana):
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO servicos_fixos (nome_servico, dia_da_semana) VALUES (%s, %s) ON CONFLICT (nome_servico) DO NOTHING", (nome, dia_da_semana))
        conn.commit()
        st.success(f"Serviço '{nome}' adicionado com sucesso!")
    except Exception as e:
        conn.rollback(); st.error(f"Erro ao adicionar serviço: {e}")

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

# --- CRUD GRUPOS ---
def get_all_grupos_com_membros(_cache_buster=None):
    """ Retorna um DataFrame com todos os grupos e seus membros (VERSÃO COM QUEBRA DE CACHE). """
    conn = ensure_connection()
    if conn is None: return pd.DataFrame()
    query = """
    SELECT
        gv.id_grupo, gv.nome_grupo,
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
    ORDER BY gv.nome_grupo;
    """
    return pd.read_sql(query, conn)

def get_voluntarios_sem_grupo():
    conn = ensure_connection()
    if conn is None: return pd.DataFrame()
    return pd.read_sql("SELECT id_voluntario, nome_voluntario FROM voluntarios WHERE ativo = TRUE AND id_grupo IS NULL ORDER BY nome_voluntario", conn)

def get_voluntarios_do_grupo(id_grupo):
    conn = ensure_connection()
    if conn is None: return pd.DataFrame()
    return pd.read_sql(f"SELECT id_voluntario, nome_voluntario FROM voluntarios WHERE ativo = TRUE AND id_grupo = {id_grupo} ORDER BY nome_voluntario", conn)

def create_grupo(nome_grupo, ids_membros):
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO grupos_vinculados (nome_grupo) VALUES (%s) RETURNING id_grupo", (nome_grupo,))
            id_novo_grupo = cur.fetchone()[0]
            cur.execute("UPDATE voluntarios SET id_grupo = %s WHERE id_voluntario IN %s", (id_novo_grupo, tuple(ids_membros)))
        conn.commit()
    except Exception as e:
        conn.rollback(); st.error(f"Erro ao criar grupo: {e}")

def update_grupo(id_grupo, novo_nome, ids_membros_novos):
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE grupos_vinculados SET nome_grupo = %s WHERE id_grupo = %s", (novo_nome, id_grupo))
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

# --- LÓGICA DE ESCALA ---
def create_events_for_month(ano, mes):
    conn = ensure_connection()
    if conn is None: return False
    servicos_fixos = view_all_servicos_fixos()
    if servicos_fixos.empty:
        st.warning("Nenhum serviço fixo cadastrado."); return False
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM eventos WHERE EXTRACT(YEAR FROM data_evento) = %s AND EXTRACT(MONTH FROM data_evento) = %s", (ano, mes))
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

def get_events_for_month(ano, mes):
    conn = ensure_connection()
    if conn is None: return pd.DataFrame()
    query = "SELECT e.id_evento, e.id_servico_fixo, e.data_evento, sf.nome_servico FROM eventos e JOIN servicos_fixos sf ON e.id_servico_fixo = sf.id_servico WHERE EXTRACT(YEAR FROM e.data_evento) = %s AND EXTRACT(MONTH FROM e.data_evento) = %s ORDER BY e.data_evento ASC"
    return pd.read_sql(query, conn, params=(ano, mes))

def get_escala_completa(ano, mes):
    conn = ensure_connection()
    if conn is None: return pd.DataFrame()
    query = """
    SELECT 
        esc.funcao_instancia, e.id_evento, e.data_evento, sf.nome_servico,
        f.id_funcao, f.nome_funcao, v.id_voluntario, v.nome_voluntario
    FROM escala esc
    LEFT JOIN eventos e ON esc.id_evento = e.id_evento
    LEFT JOIN funcoes f ON esc.id_funcao = f.id_funcao
    LEFT JOIN voluntarios v ON esc.id_voluntario = v.id_voluntario
    LEFT JOIN servicos_fixos sf ON e.id_servico_fixo = sf.id_servico
    WHERE v.nome_voluntario IS NOT NULL AND EXTRACT(YEAR FROM e.data_evento) = %s AND EXTRACT(MONTH FROM e.data_evento) = %s
    ORDER BY e.data_evento, f.id_funcao, esc.funcao_instancia;
    """
    return pd.read_sql(query, conn, params=(ano, mes))

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

def apagar_escala_do_mes(ano, mes):
    conn = ensure_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM escala WHERE id_evento IN (SELECT id_evento FROM eventos WHERE EXTRACT(YEAR FROM data_evento) = %s AND EXTRACT(MONTH FROM data_evento) = %s)", (ano, mes))
        conn.commit()
    except Exception as e:
        conn.rollback(); st.error(f"Erro ao limpar escala antiga: {e}")

def gerar_escala_automatica(ano, mes):
    """
    ALGORITMO V16.1 (CORRIGIDO): Corrige o KeyError 'instancia' ao salvar a escala.
    """
    # --- 1. SETUP INICIAL E BUSCA DE DADOS ---
    apagar_escala_do_mes(ano, mes)
    
    eventos = get_events_for_month(ano, mes)
    if eventos.empty:
        st.info("Não há eventos criados para este mês.")
        return

    eventos['data_evento_date_obj'] = pd.to_datetime(eventos['data_evento']).dt.date
    voluntarios_df = get_all_voluntarios_com_detalhes()
    cotas = get_cotas_all_servicos()
    todas_funcoes = view_all_funcoes()

    id_funcoes = {
        nome: id for nome, id in zip(todas_funcoes['nome_funcao'].replace('Líder de Escala', 'Líder'), todas_funcoes['id_funcao'])
    }

    escala_final = []
    contagem_escalas_mes = {int(vol_id): 0 for vol_id in voluntarios_df['id_voluntario']}
    escalados_por_data = {data: set() for data in eventos['data_evento_date_obj'].unique()}

    # --- 2. PREPARAÇÃO DAS VAGAS E CANDIDATOS ---
    vagas_a_preencher = []
    for _, evento in eventos.iterrows():
        cotas_servico = cotas[cotas['id_servico'] == evento['id_servico_fixo']]
        for _, cota in cotas_servico.iterrows():
            for i in range(1, int(cota['quantidade_necessaria']) + 1):
                vagas_a_preencher.append({
                    'id_evento': evento['id_evento'],
                    'id_servico_fixo': evento['id_servico_fixo'],
                    'data_evento_date_obj': evento['data_evento_date_obj'],
                    'id_funcao': int(cota['id_funcao']),
                    'funcao_instancia': i
                })
    vagas_df = pd.DataFrame(vagas_a_preencher).sample(frac=1).reset_index(drop=True)

    # --- 3. FUNÇÃO AUXILIAR DE ALOCAÇÃO ---
    def alocar_por_camada(vagas_df, voluntarios_df_camada, id_funcao_alvo, nivel_experiencia_alvo=None):
        nonlocal escala_final, contagem_escalas_mes, escalados_por_data
        
        vagas_camada = vagas_df[vagas_df['id_funcao'] == id_funcao_alvo].copy()
        
        candidatos = voluntarios_df_camada[voluntarios_df_camada['funcoes'].apply(lambda x: id_funcao_alvo in (x or []))].copy()
        if nivel_experiencia_alvo:
            candidatos = candidatos[candidatos['nivel_experiencia'] == nivel_experiencia_alvo]
        
        candidatos = candidatos.sample(frac=1).reset_index(drop=True)
        vagas_preenchidas_indices = []

        for _, candidato in candidatos.iterrows():
            candidato_id = int(candidato['id_voluntario'])
            
            while contagem_escalas_mes.get(candidato_id, 0) < candidato['limite_escalas_mes']:
                vaga_encontrada = False
                for vaga_idx, vaga in vagas_camada.iterrows():
                    if vaga_idx in vagas_preenchidas_indices:
                        continue

                    if (candidato_id not in escalados_por_data.get(vaga['data_evento_date_obj'], set()) and
                        vaga['id_servico_fixo'] in (candidato.get('disponibilidade') or [])):
                        
                        escala_final.append({
                            'id_evento': vaga['id_evento'], 'id_funcao': vaga['id_funcao'],
                            'id_voluntario': candidato_id, 'funcao_instancia': vaga['funcao_instancia']
                        })
                        contagem_escalas_mes[candidato_id] += 1
                        escalados_por_data[vaga['data_evento_date_obj']].add(candidato_id)
                        vagas_preenchidas_indices.append(vaga_idx)
                        vaga_encontrada = True
                        break
                
                if not vaga_encontrada:
                    break
        
        return vagas_preenchidas_indices

    # --- 4. EXECUÇÃO DOS PASSES DE ALOCAÇÃO ---
    if 'Líder' in id_funcoes:
        indices_preenchidos = alocar_por_camada(vagas_df, voluntarios_df, id_funcoes['Líder'])
        vagas_df.drop(indices_preenchidos, inplace=True)

    if 'Store' in id_funcoes:
        indices_preenchidos = alocar_por_camada(vagas_df, voluntarios_df, id_funcoes['Store'])
        vagas_df.drop(indices_preenchidos, inplace=True)

    if 'Apoio' in id_funcoes:
        indices_preenchidos = alocar_por_camada(vagas_df, voluntarios_df, id_funcoes['Apoio'], 'Avançado')
        vagas_df.drop(indices_preenchidos, inplace=True)
        indices_preenchidos = alocar_por_camada(vagas_df, voluntarios_df, id_funcoes['Apoio'], 'Intermediário')
        vagas_df.drop(indices_preenchidos, inplace=True)
        indices_preenchidos = alocar_por_camada(vagas_df, voluntarios_df, id_funcoes['Apoio'], 'Iniciante')
        vagas_df.drop(indices_preenchidos, inplace=True)

    # --- 5. SALVAR RESULTADOS NO BANCO ---
    if escala_final:
        conn = ensure_connection()
        try:
            with conn.cursor() as cur:
                # CORREÇÃO: Alterado de e['instancia'] para e['funcao_instancia']
                args = [(e['id_evento'], e['id_funcao'], e['id_voluntario'], e['funcao_instancia']) for e in escala_final]
                cur.executemany("INSERT INTO escala (id_evento, id_funcao, id_voluntario, funcao_instancia) VALUES (%s, %s, %s, %s)", args)
            conn.commit()
            st.success("Escala preenchida com a nova lógica de distribuição!")
        except Exception as e:
            conn.rollback()
            st.error(f"Erro ao salvar escala: {e}")



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
    """ Retorna um DataFrame de voluntários que podem exercer uma função específica. """
    conn = ensure_connection()
    if conn is None: return pd.DataFrame()
    
    query = """
    SELECT v.id_voluntario, v.nome_voluntario
    FROM voluntarios v
    JOIN voluntario_funcoes vf ON v.id_voluntario = vf.id_voluntario
    WHERE v.ativo = TRUE AND vf.id_funcao = %s
    ORDER BY v.nome_voluntario;
    """
    # CORREÇÃO: Converte o id_funcao para um int padrão do Python antes de passar para a query
    return pd.read_sql(query, conn, params=(int(id_funcao),))

def get_voluntario_by_name(nome_voluntario):
    """ Busca um voluntário pelo nome para encontrar seu ID. """
    conn = ensure_connection()
    if conn is None or not nome_voluntario: return None
    query = "SELECT id_voluntario FROM voluntarios WHERE nome_voluntario = %s"
    df = pd.read_sql(query, conn, params=(nome_voluntario,))
    return int(df['id_voluntario'].iloc[0]) if not df.empty else None

# Adicione v.nivel_experiencia ao SELECT
def get_all_voluntarios_com_detalhes():
    conn = ensure_connection()
    if conn is None: return pd.DataFrame()
    query = """
    SELECT 
        v.id_voluntario, v.nome_voluntario, v.limite_escalas_mes, v.id_grupo, v.nivel_experiencia,
        ARRAY_AGG(DISTINCT vf.id_funcao) as funcoes,
        ARRAY_AGG(DISTINCT vd.id_servico) as disponibilidade
    FROM voluntarios v
    LEFT JOIN voluntario_funcoes vf ON v.id_voluntario = vf.id_voluntario
    LEFT JOIN voluntario_disponibilidade vd ON v.id_voluntario = vd.id_voluntario
    WHERE v.ativo = TRUE
    GROUP BY v.id_voluntario
    ORDER BY v.nome_voluntario;
    """
    return pd.read_sql(query, conn)
