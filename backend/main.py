from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import text
import models
from database import Base, engine, SessionLocal
from auth import verificar_senha, criar_token, decodificar_token
from datetime import datetime

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
app = FastAPI(title="AutoGest API - SaaS Edition")

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


def get_user_info(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    email = decodificar_token(token)
    if not email: raise HTTPException(status_code=401, detail="Sessão expirada")
    user = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    return user


@app.post("/login")
def login(dados: dict, db: Session = Depends(get_db)):
    u = db.query(models.Usuario).filter(models.Usuario.email == dados.get("email")).first()
    if not u or not verificar_senha(dados.get("senha"), u.senha):
        raise HTTPException(status_code=400, detail="E-mail ou senha incorretos")
    return {"access_token": criar_token(u.email), "token_type": "bearer", "role": u.role, "nome": u.nome}


@app.get("/veiculos")
def listar(db: Session = Depends(get_db), user: models.Usuario = Depends(get_user_info)):
    return db.query(models.Veiculo).filter(
        models.Veiculo.empresa_id == user.empresa_id,
        models.Veiculo.status == "EM_ESTOQUE"
    ).all()


@app.post("/veiculos")
def criar(dados: dict, db: Session = Depends(get_db), user: models.Usuario = Depends(get_user_info)):
    novo = models.Veiculo(
        marca=dados['marca'], modelo=dados['modelo'],
        placa=dados['placa'].upper(), valor=float(dados['valor']),
        ano=dados.get('ano'), empresa_id=user.empresa_id,
        status="EM_ESTOQUE"
    )
    db.add(novo)
    db.commit()
    return novo


@app.put("/veiculos/{veiculo_id}/vender")
def vender_veiculo(veiculo_id: int, dados: dict, db: Session = Depends(get_db),
                   user: models.Usuario = Depends(get_user_info)):
    veiculo = db.query(models.Veiculo).filter(
        models.Veiculo.id == veiculo_id,
        models.Veiculo.empresa_id == user.empresa_id
    ).first()
    if not veiculo: raise HTTPException(status_code=404)

    veiculo.status = "VENDIDO"
    veiculo.comprador_nome = dados.get('nome')
    veiculo.comprador_documento = dados.get('documento')
    veiculo.comprador_endereco = dados.get('endereco')
    veiculo.valor_venda = float(dados.get('valor_venda', 0))
    veiculo.data_venda = datetime.now()

    db.commit()
    return {"status": "sucesso"}


@app.delete("/veiculos/{veiculo_id}")
def excluir(veiculo_id: int, db: Session = Depends(get_db), user: models.Usuario = Depends(get_user_info)):
    v = db.query(models.Veiculo).filter(
        models.Veiculo.id == veiculo_id,
        models.Veiculo.empresa_id == user.empresa_id
    ).first()
    if v:
        db.delete(v)
        db.commit()
    return {"status": "removido"}