from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import os

from database import Base, engine, SessionLocal
from models import Usuario, Veiculo
# Importando as funções do seu arquivo auth.py que já configuramos
from auth import hash_senha, verificar_senha, criar_token, decodificar_token

# Configuração de Segurança
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app = FastAPI(title="AutoGest API")

# Configuração de CORS para permitir que seu frontend local acesse o Render
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cria as tabelas no banco de dados se não existirem
Base.metadata.create_all(bind=engine)


# Dependência do Banco de Dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Dependência para verificar se o usuário está logado
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
# ROTAS DE AUTENTICAÇÃO
# ----------------------------

@app.get("/setup-admin")
def setup_admin(db: Session = Depends(get_db)):
    """Cria ou reseta o admin padrão."""
    try:
        admin = db.query(Usuario).filter(Usuario.email == "admin@admin.com").first()
        senha_hash = hash_senha("admin123")

        if not admin:
            novo_admin = Usuario(email="admin@admin.com", senha=senha_hash)
            db.add(novo_admin)
            msg = "Admin criado com sucesso (PBKDF2)!"
        else:
            admin.senha = senha_hash
            msg = "Senha do Admin resetada com sucesso!"

        db.commit()
        return {"status": "sucesso", "msg": msg}
    except Exception as e:
        db.rollback()
        return {"status": "erro", "detalhes": str(e)}


@app.post("/login")
def login(dados: dict, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == dados.get("email")).first()

    if not usuario or not verificar_senha(dados.get("senha"), usuario.senha):
        raise HTTPException(status_code=400, detail="E-mail ou senha incorretos")

    token = criar_token(usuario.email)
    return {"access_token": token, "token_type": "bearer"}


# ----------------------------
# ROTAS DO DASHBOARD E VEÍCULOS
# ----------------------------

@app.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db), usuario: str = Depends(get_usuario_logado)):
    """Retorna os números que alimentam os cards do frontend."""
    veiculos = db.query(Veiculo).all()
    total = len(veiculos)
    estoque = len([v for v in veiculos if v.status == "EM_ESTOQUE"])
    vendidos = len([v for v in veiculos if v.status == "VENDIDO"])
    valor_total = sum(v.valor for v in veiculos) if veiculos else 0

    return {
        "total_veiculos": total,
        "em_estoque": estoque,
        "vendidos": vendidos,
        "valor_total": valor_total
    }


@app.get("/veiculos")
def listar_veiculos(db: Session = Depends(get_db), usuario: str = Depends(get_usuario_logado)):
    """Lista todos os veículos para a tabela de estoque."""
    return db.query(Veiculo).all()


@app.post("/veiculos")
def criar_veiculo(dados: dict, db: Session = Depends(get_db), usuario: str = Depends(get_usuario_logado)):
    """Cadastra um novo veículo no sistema."""
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
def excluir_veiculo(veiculo_id: int, db: Session = Depends(get_db), usuario: str = Depends(get_usuario_logado)):
    """Remove um veículo e permite que o dashboard atualize os valores."""
    veiculo = db.query(Veiculo).filter(Veiculo.id == veiculo_id).first()

    if not veiculo:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")

    try:
        db.delete(veiculo)
        db.commit()  # Salva a remoção permanentemente para atualizar o patrimônio
        return {"status": "sucesso", "msg": "Veículo excluído com sucesso"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def root():
    return {"status": "online", "message": "AutoGest API rodando no Render 🚀"}