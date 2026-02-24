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

# --- INICIALIZAÇÃO ---
Base.metadata.create_all(bind=engine)

def ajustar_banco_producao():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS role VARCHAR DEFAULT 'LOJISTA';"))
            conn.execute(text("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS empresa_id INTEGER;"))
            conn.execute(text("ALTER TABLE veiculos ADD COLUMN IF NOT EXISTS empresa_id INTEGER;"))
            conn.execute(text("ALTER TABLE veiculos ADD COLUMN IF NOT EXISTS ano VARCHAR;"))
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

# --- SEGURANÇA ---
def get_user_info(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    email = decodificar_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Sessão expirada")
    user = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if user.role == "LOJISTA" and user.empresa_id:
        empresa = db.query(models.Empresa).filter(models.Empresa.id == user.empresa_id).first()
        if not empresa or empresa.status != "ATIVO":
            raise HTTPException(status_code=403, detail="Conta suspensa")
    return user

# --- ROTAS DE AUTENTICAÇÃO ---
@app.post("/login")
def login(dados: dict, db: Session = Depends(get_db)):
    u = db.query(models.Usuario).filter(models.Usuario.email == dados.get("email")).first()
    if not u or not verificar_senha(dados.get("senha"), u.senha):
        raise HTTPException(status_code=400, detail="E-mail ou senha incorretos")
    return {
        "access_token": criar_token(u.email),
        "token_type": "bearer",
        "role": u.role,
        "nome": u.nome if hasattr(u, 'nome') else u.email
    }

# --- GESTÃO DE ESTOQUE ---
@app.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user: models.Usuario = Depends(get_user_info)):
    # Soma apenas veículos em estoque
    veiculos = db.query(models.Veiculo).filter(
        models.Veiculo.empresa_id == user.empresa_id,
        models.Veiculo.status == "EM_ESTOQUE"
    ).all()
    valor_total = sum(v.valor for v in veiculos) if veiculos else 0
    return {"total_veiculos": len(veiculos), "valor_total": valor_total}

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
        placa=dados['placa'].upper(), valor=dados['valor'],
        ano=dados.get('ano'), empresa_id=user.empresa_id,
        status="EM_ESTOQUE"
    )
    db.add(novo)
    db.commit()
    return novo

@app.put("/veiculos/{veiculo_id}/vender")
def vender_veiculo(veiculo_id: int, db: Session = Depends(get_db), user: models.Usuario = Depends(get_user_info)):
    veiculo = db.query(models.Veiculo).filter(
        models.Veiculo.id == veiculo_id,
        models.Veiculo.empresa_id == user.empresa_id
    ).first()
    if not veiculo: raise HTTPException(status_code=404)
    veiculo.status = "VENDIDO"
    db.commit()
    return {"status": "venda_concluida"}

@app.delete("/veiculos/{veiculo_id}")
def excluir_veiculo(veiculo_id: int, db: Session = Depends(get_db), user: models.Usuario = Depends(get_user_info)):
    veiculo = db.query(models.Veiculo).filter(
        models.Veiculo.id == veiculo_id,
        models.Veiculo.empresa_id == user.empresa_id
    ).first()
    if not veiculo: raise HTTPException(status_code=404)
    db.delete(veiculo)
    db.commit()
    return {"status": "removido"}

# --- CONFIGURAÇÕES ---
@app.post("/empresa/certificado")
async def upload_certificado(senha: str, file: UploadFile = File(...), db: Session = Depends(get_db), user: models.Usuario = Depends(get_user_info)):
    if user.role != "LOJISTA": raise HTTPException(status_code=403)
    empresa = db.query(models.Empresa).filter(models.Empresa.id == user.empresa_id).first()
    empresa.certificado_pfx = await file.read()
    empresa.senha_certificado = senha
    db.commit()
    return {"status": "sucesso"}