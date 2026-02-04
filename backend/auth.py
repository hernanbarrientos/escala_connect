import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
# Importa a função nova de login (V2)
from backend.database import verificar_login_v2

# Configurações de Segurança
SECRET_KEY = os.environ.get("SECRET_KEY", "sua_chave_secreta_super_segura")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 horas

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def authenticate_user(email: str, password: str):
    # Busca o usuário no banco novo (retorna dict com dados da igreja)
    user = verificar_login_v2(email)
    if not user:
        return False
    if not verify_password(password, user['senha_hash']):
        return False
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        id_igreja: int = payload.get("id_igreja")
        role: str = payload.get("role")
        
        if email is None or id_igreja is None:
            raise credentials_exception
            
        return {
            "email": email, 
            "id_igreja": id_igreja, 
            "role": role,
            "id_usuario": payload.get("id_usuario")
        }
    except JWTError:
        raise credentials_exception