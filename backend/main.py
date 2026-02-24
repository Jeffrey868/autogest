from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import text
import models
from database import Base, engine, SessionLocal
from auth import verificar_senha, criar_token, decodificar_token

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

def ajustar_banco_producao():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS role VARCHAR DEFAULT 'LOJISTA';"))
            conn.execute(text("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS empresa_id INTEGER;"))
            conn.execute(text("ALTER TABLE veiculos ADD COLUMN IF NOT EXISTS empresa_id INTEGER;"))
            conn.execute(text("ALTER TABLE veiculos ADD COLUMN IF NOT EXISTS ano VARCHAR;"))
            conn.execute(text("ALTER TABLE veiculos ADD COLUMN IF NOT EXISTS renave_numero VARCHAR;"))
            conn.commit()
        except Exception as e:
            print(f"Aviso na migração: {e}")

ajustar_banco_producao()

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
    if not user: raise HTTPException(status_code=404)
    return user

@app.post("/login")
def login(dados: dict, db: Session = Depends(get_db)):
    u = db.query(models.Usuario).filter(models.Usuario.email == dados.get("email")).first()
    if not u or not verificar_senha(dados.get("senha"), u.senha):
        raise HTTPException(status_code=400, detail="E-mail ou senha incorretos")
    return {"access_token": criar_token(u.email), "token_type": "bearer", "role": u.role, "nome": u.nome}

@app.get("/veiculos")
def listar(db: Session = Depends(get_db), user: models.Usuario = Depends(get_user_info)):
    return db.query(models.Veiculo).filter(models.Veiculo.empresa_id == user.empresa_id, models.Veiculo.status == "EM_ESTOQUE").all()

@app.post("/veiculos")
def criar(dados: dict, db: Session = Depends(get_db), user: models.Usuario = Depends(get_user_info)):
    novo = models.Veiculo(
        marca=dados['marca'],
        modelo=dados['modelo'],
        placa=dados['placa'].upper(),
        valor=float(dados['valor']),
        ano=dados.get('ano'),
        renave_numero=dados.get('renave_numero'), # Novo Campo
        empresa_id=user.empresa_id,
        status="EM_ESTOQUE"
    )
    db.add(novo)
    db.commit()
    return novo

@app.get("/renave/consultar/{placa}")
def consultar_renave(placa: str, db: Session = Depends(get_db), user: models.Usuario = Depends(get_user_info)):
    # Simulação de consulta ao governo (futura integração SERPRO)
    return {
        "marca": "VOLKSWAGEN",
        "modelo": "GOL 1.0",
        "placa": placa.upper(),
        "ano": "2022/2023"
    }

# Mantive as outras rotas (vender, excluir, certificado) que já funcionavam...