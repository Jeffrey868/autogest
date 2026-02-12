import os
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext

# ---------------------------------------------------------
# CORREÇÃO CRÍTICA: MUDANÇA DE ALGORITMO
# ---------------------------------------------------------
# Trocamos ["bcrypt"] por ["pbkdf2_sha256"].
# Isso resolve o erro "module 'bcrypt' has no attribute" no Render.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# 2. Configurações Gerais
SECRET_KEY = os.getenv("SECRET_KEY", "chave-secreta-temporaria-para-desenvolvimento")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 horas

def hash_senha(senha: str):
    """Transforma senha em hash seguro usando PBKDF2."""
    return pwd_context.hash(senha)

def verificar_senha(senha: str, hash_guardado: str):
    """Compara a senha digitada com o hash do banco."""
    return pwd_context.verify(senha, hash_guardado)

def criar_token(email: str):
    """Gera o JWT para o frontend."""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": email, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decodificar_token(token: str):
    """Valida o token e retorna o email."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except:
        return None