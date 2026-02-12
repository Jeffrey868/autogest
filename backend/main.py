from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import os

from database import Base, engine, SessionLocal
from models import Usuario, Veiculo
from auth import hash_senha, verificar_senha, criar_token, decodificar_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
app = FastAPI(title="AutoGest API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        raise HTTPException(status_code=401, detail="Sessão expirada")
    return email

@app.get("/setup-admin")
def setup_admin(db: Session = Depends(get_db)):
    admin = db.query(Usuario).filter(Usuario.email == "admin@admin.com").first()
    senha_h = hash_senha("admin123")
    if not admin:
        db.add(Usuario(email="admin@admin.com", senha=senha_h))
        msg = "Admin criado!"
    else:
        admin.senha = senha_h
        msg = "Admin resetado!"
    db.commit()
    return {"status": "sucesso", "msg": msg}

@app.post("/login")
def login(dados: dict, db: Session = Depends(get_db)):
    u = db.query(Usuario).filter(Usuario.email == dados.get("email")).first()
    if not u or not verificar_senha(dados.get("senha"), u.senha):
        raise HTTPException(status_code=400, detail="Incorreto")
    return {"access_token": criar_token(u.email), "token_type": "bearer"}

@app.get("/dashboard")
def dashboard(db: Session = Depends(get_db), u: str = Depends(get_usuario_logado)):
    veiculos = db.query(Veiculo).all()
    return {
        "total_veiculos": len(veiculos),
        "em_estoque": len([v for v in veiculos if v.status == "EM_ESTOQUE"]),
        "valor_total": sum(v.valor for v in veiculos)
    }

@app.get("/veiculos")
def listar(db: Session = Depends(get_db), u: str = Depends(get_usuario_logado)):
    return db.query(Veiculo).all()

@app.post("/veiculos")
def criar(dados: dict, db: Session = Depends(get_db), u: str = Depends(get_usuario_logado)):
    novo = Veiculo(marca=dados['marca'], modelo=dados['modelo'], placa=dados['placa'], valor=dados['valor'], status="EM_ESTOQUE")
    db.add(novo)
    db.commit()
    return novo

@app.delete("/veiculos/{id}")
def excluir(id: int, db: Session = Depends(get_db), u: str = Depends(get_usuario_logado)):
    v = db.query(Veiculo).filter(Veiculo.id == id).first()
    if not v: raise HTTPException(status_code=404)
    db.delete(v)
    db.commit()
    return {"msg": "Excluído"}

@app.get("/")
def root(): return {"status": "online"}