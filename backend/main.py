from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime
import os

from database import Base, engine, SessionLocal
from models import Usuario, Veiculo
# Agora importamos hash_senha diretamente, pois o auth.py já resolveu o problema do bcrypt
from auth import hash_senha, verificar_senha, criar_token, decodificar_token

# ----------------------------
# CONFIGURAÇÃO DE SEGURANÇA
# ----------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app = FastAPI(title="AutoGest API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Garante que as tabelas existam
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_usuario_logado(token: str = Depends(oauth2_scheme)):
    email = decodificar_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão expirada. Faça login novamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return email


# ----------------------------
# ROTA DE EMERGÊNCIA: SETUP ADMIN (CORRIGIDA)
# ----------------------------
@app.get("/setup-admin")
def setup_admin(db: Session = Depends(get_db)):
    """
    Cria ou reseta o admin usando o novo algoritmo PBKDF2.
    Isso conserta logins quebrados pelo erro anterior do bcrypt.
    """
    try:
        email_admin = "admin@admin.com"
        senha_padrao = "admin123"

        # Gera o hash usando a nova função segura do auth.py
        senha_criptografada = hash_senha(senha_padrao)

        admin = db.query(Usuario).filter(Usuario.email == email_admin).first()

        if not admin:
            # Cria novo se não existir
            novo_admin = Usuario(email=email_admin, senha=senha_criptografada)
            db.add(novo_admin)
            msg = "Admin criado com sucesso (PBKDF2)!"
        else:
            # ATUALIZA a senha se já existir (para corrigir hash antigo quebrado)
            admin.senha = senha_criptografada
            msg = "Senha do Admin resetada para 'admin123' com nova criptografia!"

        db.commit()
        return {"status": "sucesso", "msg": msg}

    except Exception as e:
        db.rollback()
        return {"status": "erro", "detalhes": str(e)}


# ----------------------------
# LOGIN
# ----------------------------
@app.post("/login")
def login(dados: dict, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == dados.get("email")).first()

    # verificar_senha agora usa o auth.py compatível
    if not usuario or not verificar_senha(dados.get("senha"), usuario.senha):
        raise HTTPException(status_code=400, detail="E-mail ou senha incorretos")

    token = criar_token(usuario.email)
    return {"access_token": token, "token_type": "bearer"}


# ----------------------------
# DASHBOARD E VEÍCULOS
# ----------------------------
@app.get("/dashboard")
def dashboard(db: Session = Depends(get_db), usuario: str = Depends(get_usuario_logado)):
    total = db.query(Veiculo).count()
    estoque = db.query(Veiculo).filter(Veiculo.status == "EM_ESTOQUE").count()
    vendidos = db.query(Veiculo).filter(Veiculo.status == "VENDIDO").count()
    veiculos = db.query(Veiculo).all()
    valor_total = sum(v.valor for v in veiculos) if veiculos else 0
    return {"total_veiculos": total, "em_estoque": estoque, "vendidos": vendidos, "valor_total": valor_total}


@app.get("/veiculos")
def listar_veiculos(db: Session = Depends(get_db), usuario: str = Depends(get_usuario_logado)):
    return db.query(Veiculo).all()


@app.post("/veiculos")
def criar_veiculo(dados: dict, db: Session = Depends(get_db), usuario: str = Depends(get_usuario_logado)):
    novo = Veiculo(
        marca=dados.get("marca"), modelo=dados.get("modelo"),
        placa=dados.get("placa"), valor=dados.get("valor"), status="EM_ESTOQUE"
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@app.get("/")
def root():
    return {"status": "online", "message": "AutoGest API rodando no Render 🚀"}