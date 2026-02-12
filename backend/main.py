from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime
import random
import os

from database import Base, engine, SessionLocal
from models import Usuario, Veiculo
# Importamos o pwd_context para garantir o hash direto e evitar falhas de biblioteca
from auth import verificar_senha, criar_token, decodificar_token, pwd_context

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
# ROTA DE EMERGÊNCIA: SETUP ADMIN
# ----------------------------
@app.get("/setup-admin")
def setup_admin(db: Session = Depends(get_db)):
    """Cria o admin forçando o hash direto para ignorar erros de encoding."""
    try:
        # Busca se já existe para não duplicar
        admin = db.query(Usuario).filter(Usuario.email == "admin@admin.com").first()

        if not admin:
            # Forçamos a senha admin123 de forma ultra-limpa
            senha_texto = "admin123"
            hash_gerado = pwd_context.hash(senha_texto)

            novo_admin = Usuario(
                email="admin@admin.com",
                senha=hash_gerado
            )
            db.add(novo_admin)
            db.commit()
            return {"status": "sucesso", "msg": "Usuário admin criado com sucesso!"}

        return {"status": "info", "msg": "O admin já existe no banco."}

    except Exception as e:
        db.rollback()
        # Retorna o erro exato para o navegador se algo der errado
        return {"status": "erro", "detalhes": str(e)}


# ----------------------------
# LOGIN
# ----------------------------
@app.post("/login")
def login(dados: dict, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == dados.get("email")).first()

    if not usuario or not verificar_senha(dados.get("senha"), usuario.senha):
        # Falha se o usuário não for encontrado (que é o que acontece sem o setup-admin)
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
        marca=dados.get("marca"),
        modelo=dados.get("modelo"),
        placa=dados.get("placa"),
        valor=dados.get("valor"),
        status="EM_ESTOQUE"
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@app.get("/")
def root():
    return {"status": "online", "message": "AutoGest API rodando no Render 🚀"}