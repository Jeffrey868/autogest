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
from auth import hash_senha, verificar_senha, criar_token, decodificar_token

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# ----------------------------
# CONFIGURAÇÃO DE SEGURANÇA
# ----------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app = FastAPI(title="AutoGest API")

# CORS ajustado para permitir a conexão do seu frontend local com o Render
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cria as tabelas no banco de dados se não existirem
Base.metadata.create_all(bind=engine)


# ----------------------------
# Dependências
# ----------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_usuario_logado(token: str = Depends(oauth2_scheme)):
    """Valida o token JWT para proteger as rotas."""
    email = decodificar_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão expirada. Faça login novamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return email


# ----------------------------
# CRIAR ADMIN AUTOMÁTICO (PROTEÇÃO CONTRA ERRO DE 72 BYTES)
# ----------------------------
@app.on_event("startup")
def criar_admin():
    db = SessionLocal()
    try:
        # Verifica se o administrador já existe
        admin = db.query(Usuario).filter(Usuario.email == "admin@admin.com").first()

        if not admin:
            # Forçamos a senha limpa para evitar erro de encoding no Bcrypt
            senha_limpa = "admin123"
            novo_admin = Usuario(
                email="admin@admin.com",
                senha=hash_senha(senha_limpa)
            )
            db.add(novo_admin)
            db.commit()
            print("Admin criado automaticamente ✔")
        else:
            print("Admin já existe no banco.")

    except Exception as e:
        db.rollback()  # Crucial: limpa a transação para não travar o banco no Render
        print(f"ERRO CRÍTICO NO ADMIN: {str(e)}")
    finally:
        db.close()


# ----------------------------
# LOGIN (Rota: /login)
# ----------------------------
@app.post("/login")
def login(dados: dict, db: Session = Depends(get_db)):
    # O erro 404 foi resolvido garantindo que o fetch aponte para cá
    usuario = db.query(Usuario).filter(Usuario.email == dados.get("email")).first()

    if not usuario or not verificar_senha(dados.get("senha"), usuario.senha):
        raise HTTPException(status_code=400, detail="E-mail ou senha incorretos")

    token = criar_token(usuario.email)
    return {"access_token": token, "token_type": "bearer"}


# ----------------------------
# ROTAS DO SISTEMA (PROTEGIDAS)
# ----------------------------

@app.get("/dashboard")
def dashboard(db: Session = Depends(get_db), usuario: str = Depends(get_usuario_logado)):
    total = db.query(Veiculo).count()
    estoque = db.query(Veiculo).filter(Veiculo.status == "EM_ESTOQUE").count()
    vendidos = db.query(Veiculo).filter(Veiculo.status == "VENDIDO").count()

    veiculos = db.query(Veiculo).all()
    valor_total = sum(v.valor for v in veiculos) if veiculos else 0

    return {
        "total_veiculos": total,
        "em_estoque": estoque,
        "vendidos": vendidos,
        "valor_total": valor_total
    }


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


@app.delete("/veiculos/{veiculo_id}")
def deletar_veiculo(veiculo_id: int, db: Session = Depends(get_db), usuario: str = Depends(get_usuario_logado)):
    veiculo = db.query(Veiculo).filter(Veiculo.id == veiculo_id).first()
    if not veiculo:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")
    db.delete(veiculo)
    db.commit()
    return {"msg": "Veículo deletado com sucesso"}


@app.post("/renave/entrada/{veiculo_id}")
def registrar_renave(veiculo_id: int, db: Session = Depends(get_db), usuario: str = Depends(get_usuario_logado)):
    veiculo = db.query(Veiculo).filter(Veiculo.id == veiculo_id).first()
    if not veiculo:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")

    numero = "REN" + str(random.randint(100000, 999999))
    veiculo.renave_numero = numero
    veiculo.status = "EM_ESTOQUE"
    db.commit()
    return {"msg": "RENAVE registrado com sucesso", "numero": numero}


@app.get("/")
def root():
    return {"status": "online", "message": "AutoGest API rodando no Render 🚀"}