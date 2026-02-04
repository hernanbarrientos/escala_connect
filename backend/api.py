from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Imports internos
from backend.auth import authenticate_user, create_access_token, get_current_user, get_password_hash
from backend import database as db # O novo database.py sem pandas

app = FastAPI(title="Renovo HUB API", version="2.0.0")

# --- CONFIGURAÇÃO CORS ---
origins = [
    "http://localhost:5173",
    "https://seu-app-producao.vercel.app"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# SCHEMAS (MODELOS DE DADOS) - Validação automática
# ==============================================================================

class Token(BaseModel):
    access_token: str
    token_type: str
    user_name: str
    igreja_nome: str
    role: str

class MinisterioCreate(BaseModel):
    nome: str
    cor_hex: str = "#3b82f6"

class MinisterioResponse(BaseModel):
    id_ministerio: int
    nome: str
    cor_hex: str

class DashboardStats(BaseModel):
    total_voluntarios: int
    total_eventos: int

class VoluntarioSchema(BaseModel):
    nome: str
    email: str
    telefone: Optional[str] = None
    nivel: str = "Iniciante"
    funcoes_ids: List[int] = []

# ==============================================================================
# ROTAS DE AUTENTICAÇÃO
# ==============================================================================

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Rota oficial de login. Recebe username (email) e password.
    Retorna o JWT com os dados da Igreja embutidos.
    """
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Cria o token com os dados vitais para o frontend
    access_token = create_access_token(
        data={
            "sub": user['email'],
            "id_usuario": user['id_usuario'],
            "id_igreja": user['id_igreja'],
            "role": user['role']
        }
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_name": user['nome'],
        "igreja_nome": user['nome_igreja'], # O frontend vai amar isso
        "role": user['role']
    }

@app.get("/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """Retorna os dados do usuário logado (para teste)."""
    return current_user

# ==============================================================================
# ROTAS DA IGREJA & MINISTÉRIOS (O HUB)
# ==============================================================================

@app.get("/igreja/dashboard", response_model=DashboardStats)
def get_dashboard_igreja(current_user: dict = Depends(get_current_user)):
    """Retorna números gerais da igreja (não apenas de um ministério)."""
    stats = db.get_dashboard_stats(current_user['id_igreja'])
    return stats

@app.get("/igreja/ministerios", response_model=List[MinisterioResponse])
def listar_ministerios(current_user: dict = Depends(get_current_user)):
    """
    Lista todos os ministérios ativos da igreja do usuário logado.
    Usado para preencher o Menu Lateral ou a Tela Inicial do HUB.
    """
    ministerios = db.get_ministerios_da_igreja(current_user['id_igreja'])
    return ministerios

@app.post("/igreja/ministerios", status_code=201)
def criar_ministerio(ministerio: MinisterioCreate, current_user: dict = Depends(get_current_user)):
    """
    Cria um novo ministério na igreja.
    """
    # Verifica se é admin (opcional, por enquanto todo líder pode criar)
    # if current_user['role'] != 'ADMIN_GERAL': raise HTTPException...

    query = """
        INSERT INTO ministerios (id_igreja, nome, cor_hex)
        VALUES (%s, %s, %s)
        RETURNING id_ministerio, nome, cor_hex;
    """
    params = (current_user['id_igreja'], ministerio.nome, ministerio.cor_hex)
    
    novo_min = db.execute_modify(query, params)
    
    if not novo_min:
        raise HTTPException(status_code=500, detail="Erro ao criar ministério")
        
    return novo_min

# ==============================================================================
# ROTAS DE GESTÃO DO MINISTÉRIO (VOLUNTÁRIOS)
# ==============================================================================

@app.get("/ministerios/{id_ministerio}/voluntarios")
def listar_voluntarios(id_ministerio: int, current_user: dict = Depends(get_current_user)):
    # TODO: Verificar se current_user pertence à mesma igreja do ministério (Segurança)
    voluntarios = db.get_voluntarios_do_ministerio(id_ministerio)
    return voluntarios

@app.get("/ministerios/{id_ministerio}/funcoes")
def listar_funcoes(id_ministerio: int, current_user: dict = Depends(get_current_user)):
    return db.get_funcoes_ministerio(id_ministerio)

@app.post("/ministerios/{id_ministerio}/voluntarios", status_code=201)
def cadastrar_voluntario(
    id_ministerio: int, 
    dados: VoluntarioSchema, 
    current_user: dict = Depends(get_current_user)
):
    """
    Cadastra um voluntário novo ou vincula um existente ao ministério.
    """
    resultado = db.adicionar_voluntario_vinculo(id_ministerio, current_user['id_igreja'], dados)
    
    if not resultado:
        raise HTTPException(status_code=400, detail="Erro ao cadastrar voluntário. Talvez ele já esteja vinculado.")
        
    return {"msg": "Voluntário vinculado com sucesso!"}


@app.get("/ministerios/{id_ministerio}/servicos")
def listar_servicos(id_ministerio: int, current_user: dict = Depends(get_current_user)):
    """Rota que faltava para o frontend carregar!"""
    return db.get_servicos_ministerio(id_ministerio)