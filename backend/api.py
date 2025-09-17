# Arquivo: api.py (Versão com Indentação Corrigida)

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
import pandas as pd
from pydantic import BaseModel
from typing import Dict, List
import numpy as np
from datetime import datetime
from collections import defaultdict
from backend.db_utils import verificar_login_puro

from backend.database import (
    add_funcao,
    add_servico_fixo,
    add_voluntario,
    atualizar_funcoes_do_voluntario,
    create_grupo,
    delete_funcao,
    delete_grupo,
    delete_servico_fixo,
    ensure_connection,
    gerar_escala_automatica,
    get_all_grupos_com_membros,
    get_all_ministerios,
    get_all_voluntarios_com_detalhes,
    get_cotas_for_servico,
    get_cotas_all_servicos, # <-- Adicionada
    get_disponibilidade_of_voluntario,
    get_events_for_month, # <-- Adicionada
    update_escala_entry,
    get_escala_completa,
    get_funcoes_of_voluntario,
    get_voluntario_by_id,
    get_voluntarios_do_grupo,
    get_voluntarios_sem_grupo,
    update_cotas_servico,
    update_disponibilidade_of_voluntario,
    update_funcao,
    update_grupo,
    update_servico_fixo,
    update_voluntario,
    verificar_login,
    # <-- Sua função de login
    view_all_funcoes,
    view_all_servicos_fixos,
    view_all_voluntarios,
    get_all_voluntarios_com_detalhes_puro
)
from backend.auth import create_access_token, get_current_user, Token
from dotenv import load_dotenv
load_dotenv()



app = FastAPI(title="API da Escala Connect")

# --- Configuração do CORS ---
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://escala-connect.vercel.app"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# NOVO ENDPOINT DE LOGIN
@app.post("/token", response_model=Token, tags=["Autenticação"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Altere esta linha para chamar a função pura
    id_ministerio = verificar_login_puro(form_data.username, form_data.password)
    
    if not id_ministerio:
        raise HTTPException(
            status_code=401,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": form_data.username, "id_ministerio": id_ministerio}
    )
    return {"access_token": access_token, "token_type": "bearer"}

# NOVO ENDPOINT PROTEGIDO (EXEMPLO)
@app.get("/users/me", tags=["Autenticação"])
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user

# --- Endpoints da API ---
@app.get("/")
def read_root():
    return {"Status": "API da Escala Connect está online"}

# --- Endpoints de Ministérios ---
@app.get("/ministerios", tags=["Ministérios"])
def get_todos_ministerios():
    conn = ensure_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Não foi possível conectar ao banco de dados")
    try:
        query = "SELECT id_ministerio, nome_ministerio FROM ministerios ORDER BY nome_ministerio"
        df = pd.read_sql(query, conn)
        return df.to_dict('records')
    finally:
        if conn:
            conn.close()

# NOVO ENDPOINT DE DASHBOARD
@app.get("/ministerios/{id_ministerio}/dashboard", tags=["Dashboard"])
def get_dashboard_data(id_ministerio: int, current_user: dict = Depends(get_current_user)):
    if current_user["id_ministerio"] != id_ministerio:
        raise HTTPException(status_code=403, detail="Acesso não autorizado")

    # Usa a nova função "pura"
    voluntarios_df = get_all_voluntarios_com_detalhes_puro(id_ministerio)
    grupos_df = get_all_grupos_com_membros(id_ministerio)
    funcoes_df = view_all_funcoes(id_ministerio)
    eventos_mes_atual_df = get_events_for_month(datetime.now().year, datetime.now().month, id_ministerio)
    cotas_df = get_cotas_all_servicos()
    
    todos_voluntarios_com_inativos_df = view_all_voluntarios(id_ministerio, include_inactive=True)
    voluntarios_inativos = todos_voluntarios_com_inativos_df[~todos_voluntarios_com_inativos_df['ativo']]

    # --- LÓGICA CORRIGIDA E ADICIONADA ---
    voluntarios_sem_funcao_df = voluntarios_df[voluntarios_df['funcoes'].apply(lambda x: not x)]
    lista_voluntarios_sem_funcao = voluntarios_sem_funcao_df['nome_voluntario'].tolist()
    
    total_vagas_mes = 0
    if not eventos_mes_atual_df.empty:
        for _, evento in eventos_mes_atual_df.iterrows():
            total_vagas_mes += cotas_df[cotas_df['id_servico'] == evento['id_servico_fixo']]['quantidade_necessaria'].sum()

    niveis_contagem = {}
    if not voluntarios_df.empty:
        niveis_contagem = voluntarios_df['nivel_experiencia'].value_counts().to_dict()
        
    contagem_funcoes = {}
    if not voluntarios_df.empty and not funcoes_df.empty:
        funcoes_map = funcoes_df.set_index('id_funcao')['nome_funcao'].to_dict()
        contagem = defaultdict(int)
        for funcoes_lista in voluntarios_df['funcoes']:
            if funcoes_lista:
                for id_funcao in funcoes_lista:
                    nome_funcao = funcoes_map.get(id_funcao)
                    if nome_funcao:
                        contagem[nome_funcao] += 1
        contagem_funcoes = dict(contagem)

    return {
        "kpis": {
            "voluntarios_ativos": len(voluntarios_df),
            "grupos": len(grupos_df),
            "eventos_mes": len(eventos_mes_atual_df),
            "vagas_mes": int(total_vagas_mes)
        },
        "grafico_niveis": niveis_contagem,
        "grafico_funcoes": contagem_funcoes,
        "pontos_atencao": {
            "voluntarios_inativos": voluntarios_inativos['nome_voluntario'].tolist(),
            "voluntarios_sem_funcao": lista_voluntarios_sem_funcao,
        }
    }


# --- Endpoints de Funções ---
class FuncaoBase(BaseModel):
    nome_funcao: str
    descricao: str = ""
    tipo_funcao: str
    prioridade_alocacao: int

# O modelo de criação herda todos os campos da classe base
class FuncaoCreate(FuncaoBase):
    pass

# O modelo de atualização também herda todos os campos
class FuncaoUpdate(FuncaoBase):
    pass
    

@app.get("/ministerios/{id_ministerio}/funcoes", tags=["Funções"])
def get_funcoes_por_ministerio(id_ministerio: int):
    df_funcoes = view_all_funcoes(id_ministerio)
    return df_funcoes.to_dict('records')

@app.post("/ministerios/{id_ministerio}/funcoes", tags=["Funções"])
def create_funcao_no_ministerio(id_ministerio: int, funcao: FuncaoCreate):
    # Passando os novos campos para a função add_funcao
    add_funcao(
        nome_funcao=funcao.nome_funcao,
        descricao=funcao.descricao,
        id_ministerio=id_ministerio,
        tipo_funcao=funcao.tipo_funcao,  # <-- NOVO
        prioridade_alocacao=funcao.prioridade_alocacao # <-- NOVO
    )
    return {"status": "success", "message": f"Função '{funcao.nome_funcao}' criada."}

@app.put("/funcoes/{id_funcao}", tags=["Funções"])
def update_funcao_by_id(id_funcao: int, funcao: FuncaoUpdate):
    # Passando os novos campos para a função update_funcao
    update_funcao(
        id_funcao=id_funcao,
        novo_nome=funcao.nome_funcao,
        nova_descricao=funcao.descricao,
        novo_tipo=funcao.tipo_funcao, # <-- NOVO
        nova_prioridade=funcao.prioridade_alocacao # <-- NOVO
    )
    return {"status": "success", "message": f"Função ID {id_funcao} atualizada."}

@app.delete("/funcoes/{id_funcao}", tags=["Funções"])
def delete_funcao_by_id(id_funcao: int):
    delete_funcao(id_funcao)
    return {"status": "success", "message": f"Função ID {id_funcao} excluída."}

# --- Endpoints de Serviços e Cotas ---
class ServicoCreate(BaseModel):
    nome_servico: str
    dia_da_semana: int
class ServicoUpdate(BaseModel):
    nome_servico: str
    dia_da_semana: int
    ativo: bool
class CotasUpdate(BaseModel):
    cotas: Dict[int, int]

@app.get("/ministerios/{id_ministerio}/servicos", tags=["Serviços"])
def get_servicos_por_ministerio(id_ministerio: int):
    df_servicos = view_all_servicos_fixos(id_ministerio)
    return df_servicos.to_dict('records')

@app.post("/ministerios/{id_ministerio}/servicos", tags=["Serviços"])
def create_servico_no_ministerio(id_ministerio: int, servico: ServicoCreate):
    add_servico_fixo(nome=servico.nome_servico, dia_da_semana=servico.dia_da_semana, id_ministerio=id_ministerio)
    return {"status": "success", "message": f"Serviço '{servico.nome_servico}' criado."}

@app.put("/servicos/{id_servico}", tags=["Serviços"])
def update_servico_by_id(id_servico: int, servico: ServicoUpdate):
    update_servico_fixo(id_servico=id_servico, nome=servico.nome_servico, dia_da_semana=servico.dia_da_semana, ativo=servico.ativo)
    return {"status": "success", "message": f"Serviço ID {id_servico} atualizado."}

@app.delete("/servicos/{id_servico}", tags=["Serviços"])
def delete_servico_by_id(id_servico: int):
    delete_servico_fixo(id_servico)
    return {"status": "success", "message": f"Serviço ID {id_servico} excluído."}

@app.get("/servicos/{id_servico}/cotas", tags=["Serviços"])
def get_cotas_do_servico(id_servico: int):
    cotas = get_cotas_for_servico(id_servico)
    return cotas

@app.put("/servicos/{id_servico}/cotas", tags=["Serviços"])
def update_cotas_do_servico(id_servico: int, cotas_data: CotasUpdate):
    update_cotas_servico(id_servico, cotas_data.cotas)
    return {"status": "success", "message": f"Cotas do serviço ID {id_servico} atualizadas."}

# --- Endpoints de Voluntários ---
class VoluntarioBase(BaseModel):
    nome_voluntario: str
    limite_escalas_mes: int
    nivel_experiencia: str
    ativo: bool = True
    funcoes_ids: List[int] = []
    disponibilidade_ids: List[int] = []
class VoluntarioCreate(VoluntarioBase):
    pass
class VoluntarioUpdate(VoluntarioBase):
    pass

@app.get("/ministerios/{id_ministerio}/voluntarios", tags=["Voluntários"])
def get_voluntarios_por_ministerio(id_ministerio: int, inativos: bool = False):
    df_voluntarios = view_all_voluntarios(id_ministerio, include_inactive=inativos)
    df_processado = df_voluntarios.replace({np.nan: None})
    return df_processado.to_dict('records')

@app.get("/voluntarios/{id_voluntario}/detalhes", tags=["Voluntários"])
def get_detalhes_do_voluntario(id_voluntario: int):
    dados_principais = get_voluntario_by_id(id_voluntario)
    if dados_principais is None:
        raise HTTPException(status_code=404, detail="Voluntário não encontrado")
    funcoes_ids = get_funcoes_of_voluntario(id_voluntario)
    disponibilidade_ids = get_disponibilidade_of_voluntario(id_voluntario)
    resposta = dados_principais.to_dict()
    resposta['funcoes_ids'] = funcoes_ids
    resposta['disponibilidade_ids'] = disponibilidade_ids
    return resposta

@app.post("/ministerios/{id_ministerio}/voluntarios", tags=["Voluntários"])
def create_voluntario_no_ministerio(id_ministerio: int, voluntario: VoluntarioCreate):
    id_novo_voluntario = add_voluntario(nome=voluntario.nome_voluntario, limite_mes=voluntario.limite_escalas_mes, nivel_experiencia=voluntario.nivel_experiencia, id_ministerio=id_ministerio)
    if id_novo_voluntario is None:
        raise HTTPException(status_code=500, detail="Erro ao criar o registro principal do voluntário.")
    atualizar_funcoes_do_voluntario(id_novo_voluntario, voluntario.funcoes_ids)
    update_disponibilidade_of_voluntario(id_novo_voluntario, voluntario.disponibilidade_ids)
    return {"status": "success", "message": f"Voluntário '{voluntario.nome_voluntario}' criado com sucesso.", "id_voluntario": id_novo_voluntario}

@app.put("/voluntarios/{id_voluntario}", tags=["Voluntários"])
def update_voluntario_by_id(id_voluntario: int, voluntario: VoluntarioUpdate):
    update_voluntario(id_voluntario=id_voluntario, nome=voluntario.nome_voluntario, limite_mes=voluntario.limite_escalas_mes, ativo=voluntario.ativo, nivel_experiencia=voluntario.nivel_experiencia)
    atualizar_funcoes_do_voluntario(id_voluntario, voluntario.funcoes_ids)
    update_disponibilidade_of_voluntario(id_voluntario, voluntario.disponibilidade_ids)
    return {"status": "success", "message": f"Voluntário ID {id_voluntario} atualizado."}

@app.delete("/voluntarios/{id_voluntario}", tags=["Voluntários"])
def delete_voluntario_by_id(id_voluntario: int):
    conn = ensure_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Erro de conexão com o banco de dados")
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE voluntarios SET ativo = FALSE WHERE id_voluntario = %s", (id_voluntario,))
            if cur.rowcount == 0:
                conn.rollback()
                raise HTTPException(status_code=404, detail="Voluntário não encontrado")
        conn.commit()
        return {"status": "success", "message": f"Voluntário ID {id_voluntario} inativado."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Erro no servidor: {e}")
    finally:
        if conn:
            conn.close()

# --- Endpoints de Vínculos (Grupos) ---
class GrupoBase(BaseModel):
    nome_grupo: str
    limite_escalas_grupo: int
    membros_ids: List[int]
class GrupoCreate(GrupoBase):
    pass
class GrupoUpdate(GrupoBase):
    pass

@app.get("/ministerios/{id_ministerio}/grupos", tags=["Vínculos"])
def get_grupos_por_ministerio(id_ministerio: int):
    df_grupos = get_all_grupos_com_membros(id_ministerio)
    return df_grupos.to_dict('records')

@app.get("/ministerios/{id_ministerio}/voluntarios-sem-grupo", tags=["Vínculos"])
def get_voluntarios_livres_por_ministerio(id_ministerio: int):
    df_voluntarios = get_voluntarios_sem_grupo(id_ministerio)
    return df_voluntarios.to_dict('records')

# << FUNÇÃO COM A INDENTAÇÃO CORRIGIDA >>
@app.get("/grupos/{id_grupo}/detalhes", tags=["Vínculos"])
def get_detalhes_do_grupo(id_grupo: int):
    """Retorna os dados de um grupo e os detalhes de seus membros."""
    conn = ensure_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Erro de conexão com o banco de dados")
    
    try:
        query_grupo = "SELECT * FROM grupos_vinculados WHERE id_grupo = %s"
        grupo_info_df = pd.read_sql(query_grupo, conn, params=(id_grupo,))
        
        if grupo_info_df.empty:
            raise HTTPException(status_code=404, detail="Grupo não encontrado")
            
        membros_df = get_voluntarios_do_grupo(id_grupo)
        
        resposta = grupo_info_df.to_dict('records')[0]
        resposta['membros'] = membros_df.to_dict('records')

        return resposta
    finally:
        if conn:
            conn.close()

@app.post("/ministerios/{id_ministerio}/grupos", tags=["Vínculos"])
def create_grupo_no_ministerio(id_ministerio: int, grupo: GrupoCreate):
    if len(grupo.membros_ids) < 2:
        raise HTTPException(status_code=400, detail="Um grupo precisa de pelo menos 2 membros.")
    create_grupo(nome_grupo=grupo.nome_grupo, ids_membros=grupo.membros_ids, id_ministerio=id_ministerio, limite_grupo=grupo.limite_escalas_grupo)
    return {"status": "success", "message": f"Grupo '{grupo.nome_grupo}' criado com sucesso."}

@app.put("/grupos/{id_grupo}", tags=["Vínculos"])
def update_grupo_by_id(id_grupo: int, grupo: GrupoUpdate):
    if len(grupo.membros_ids) < 2:
        raise HTTPException(status_code=400, detail="Um grupo precisa de pelo menos 2 membros.")
    update_grupo(id_grupo=id_grupo, novo_nome=grupo.nome_grupo, ids_membros_novos=grupo.membros_ids, novo_limite=grupo.limite_escalas_grupo)
    return {"status": "success", "message": f"Grupo ID {id_grupo} atualizado com sucesso."}

@app.delete("/grupos/{id_grupo}", tags=["Vínculos"])
def delete_grupo_by_id(id_grupo: int):
    delete_grupo(id_grupo)
    return {"status": "success", "message": f"Grupo ID {id_grupo} excluído com sucesso."}

# ==============================================================================
# NOVOS ENDPOINTS PARA GERAR E VISUALIZAR A ESCALA
# ==============================================================================

# --- Modelo Pydantic para a requisição ---
class EscalaRequest(BaseModel):
    ano: int
    mes: int

# --- Endpoints ---

@app.post("/ministerios/{id_ministerio}/escala/gerar", tags=["Escala"])
def endpoint_gerar_escala(id_ministerio: int, request_data: EscalaRequest):
    """
    Aciona o algoritmo para gerar a escala para um mês e ano específicos.
    """
    try:
        # Reutiliza o nosso algoritmo principal do database.py
        gerar_escala_automatica(request_data.ano, request_data.mes, id_ministerio)
        return {"status": "success", "message": "Escala gerada com sucesso!"}
    except Exception as e:
        # Em uma aplicação real, seria bom logar o erro 'e'
        raise HTTPException(status_code=500, detail="Ocorreu um erro interno ao gerar a escala.")

@app.get("/ministerios/{id_ministerio}/escala/{ano}/{mes}", tags=["Escala"])
def endpoint_get_escala(id_ministerio: int, ano: int, mes: int):
    """
    Busca a escala completa já gerada para um mês e ano específicos.
    """
    escala_df = get_escala_completa(ano, mes, id_ministerio)
    if escala_df.empty:
        return [] # Retorna lista vazia se não houver escala
    
    # Substitui valores NaN por None para compatibilidade com JSON
    df_processado = escala_df.replace({np.nan: None})
    return df_processado.to_dict('records')

# --- NOVO: Modelo Pydantic para a atualização da vaga ---
class VagaUpdate(BaseModel):
    id_evento: int
    id_funcao: int
    funcao_instancia: int
    id_voluntario: int | None # Permite que seja None para deixar a vaga "VAGA"

# ==============================================================================
# NOVOS ENDPOINTS PARA EDIÇÃO DA ESCALA
# ==============================================================================

@app.get("/funcoes/{id_funcao}/voluntarios", tags=["Voluntários"])
def get_voluntarios_por_funcao(id_funcao: int):
    """ Busca todos os voluntários aptos para exercer uma função específica. """
    conn = ensure_connection()
    if conn is None: return []
    try:
        # Precisamos de uma função no database.py para isso, vamos criá-la se não existir
        query = """
            SELECT v.id_voluntario, v.nome_voluntario
            FROM voluntarios v
            JOIN voluntario_funcoes vf ON v.id_voluntario = vf.id_voluntario
            WHERE v.ativo = TRUE AND vf.id_funcao = %s
            ORDER BY v.nome_voluntario;
        """
        df = pd.read_sql(query, conn, params=(id_funcao,))
        return df.to_dict('records')
    finally:
        if conn:
            conn.close()


@app.put("/escala/vaga", tags=["Escala"])
def update_vaga_na_escala(vaga: VagaUpdate):
    """ Atualiza uma única vaga na escala com um novo voluntário. """
    try:
        update_escala_entry(
            id_evento=vaga.id_evento,
            id_funcao=vaga.id_funcao,
            id_voluntario=vaga.id_voluntario,
            instancia=vaga.funcao_instancia
        )
        return {"status": "success", "message": "Vaga atualizada com sucesso."}
    except Exception as e:
        # <<<< MUDANÇA IMPORTANTE: Imprime o erro detalhado no console do backend >>>>
        print("\n--- ERRO DETALHADO NO ENDPOINT /escala/vaga ---")
        print(f"Tipo do Erro: {type(e)}")
        print(f"Argumentos do Erro: {e.args}")
        import traceback
        traceback.print_exc() # Imprime o traceback completo
        print("--- FIM DO ERRO DETALHADO ---\n")
        
        # Continua retornando o erro 500 para o frontend
        raise HTTPException(status_code=500, detail=f"Erro interno no servidor. Verifique o console do backend.")

# ==============================================================================
# NOVOS ENDPOINTS PARA GERAR PDF
# ==============================================================================
@app.get("/ministerios/{id_ministerio}/escala/{ano}/{mes}/pdf", tags=["Escala"])
def get_escala_pdf(id_ministerio: int, ano: int, mes: int, current_user: dict = Depends(get_current_user)):
    if current_user["id_ministerio"] != id_ministerio:
        raise HTTPException(status_code=403, detail="Acesso não autorizado")

    escala_df = get_escala_completa(ano, mes, id_ministerio)
    servicos_df = view_all_servicos_fixos(id_ministerio)
    
    meses_pt = { 1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro",10: "Outubro", 11: "Novembro", 12: "Dezembro" }
    mes_ano_str = f"{meses_pt.get(mes, '')} de {ano}"
    
    pdf_buffer = gerar_pdf_escala(escala_df, mes_ano_str, servicos_df)
    
    return StreamingResponse(pdf_buffer, media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename=escala_{ano}_{mes}.pdf"
    })


@app.get("/ministerios/{id_ministerio}/dashboard", tags=["Dashboard"])
def get_dashboard_data(id_ministerio: int, current_user: dict = Depends(get_current_user)):
    if current_user["id_ministerio"] != id_ministerio:
        raise HTTPException(status_code=403, detail="Acesso não autorizado")

    # Reutiliza suas funções existentes do database.py
    voluntarios_df = get_all_voluntarios_com_detalhes(id_ministerio)
    grupos_df = get_all_grupos_com_membros(id_ministerio)
    funcoes_df = view_all_funcoes(id_ministerio)
    eventos_mes_atual_df = get_events_for_month(datetime.now().year, datetime.now().month, id_ministerio)
    cotas_df = get_cotas_all_servicos()
    
    # Busca todos os voluntários (incluindo inativos) para a outra métrica
    todos_voluntarios_com_inativos_df = view_all_voluntarios(id_ministerio, include_inactive=True)
    voluntarios_inativos = todos_voluntarios_com_inativos_df[todos_voluntarios_com_inativos_df['ativo'] == False]

    # --- LÓGICA ADICIONADA AQUI ---
    # Encontra voluntários ativos sem nenhuma função
    voluntarios_sem_funcao_df = voluntarios_df[voluntarios_df['funcoes'].apply(lambda x: not x)]
    lista_voluntarios_sem_funcao = voluntarios_sem_funcao_df['nome_voluntario'].tolist()
    
    # Encontra voluntários ativos sem disponibilidade
    voluntarios_sem_disponibilidade_df = voluntarios_df[voluntarios_df['disponibilidade'].apply(lambda x: not x)]
    lista_voluntarios_sem_disponibilidade = voluntarios_sem_disponibilidade_df['nome_voluntario'].tolist()


    total_vagas_mes = 0
    if not eventos_mes_atual_df.empty:
        for _, evento in eventos_mes_atual_df.iterrows():
            total_vagas_mes += cotas_df[cotas_df['id_servico'] == evento['id_servico_fixo']]['quantidade_necessaria'].sum()

    niveis_contagem = {}
    if not voluntarios_df.empty:
        niveis_contagem = voluntarios_df['nivel_experiencia'].value_counts().to_dict()
        
    contagem_funcoes = {}
    if not voluntarios_df.empty and not funcoes_df.empty:
        funcoes_map = funcoes_df.set_index('id_funcao')['nome_funcao'].to_dict()
        contagem = defaultdict(int)
        for funcoes_lista in voluntarios_df['funcoes']:
            if funcoes_lista:
                for id_funcao in funcoes_lista:
                    nome_funcao = funcoes_map.get(id_funcao)
                    if nome_funcao:
                        contagem[nome_funcao] += 1
        contagem_funcoes = dict(contagem)


    return {
        "kpis": {
            "voluntarios_ativos": len(voluntarios_df),
            "grupos": len(grupos_df),
            "eventos_mes": len(eventos_mes_atual_df),
            "vagas_mes": int(total_vagas_mes)
        },
        "grafico_niveis": niveis_contagem,
        "grafico_funcoes": contagem_funcoes,
        "pontos_atencao": {
            "voluntarios_inativos": voluntarios_inativos['nome_voluntario'].tolist(),
            "voluntarios_sem_funcao": lista_voluntarios_sem_funcao,
            "voluntarios_sem_disponibilidade": lista_voluntarios_sem_disponibilidade
        }
    }