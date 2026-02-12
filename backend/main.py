from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import requests # Necessário para chamadas externas (SERPRO)

from database import Base, engine, SessionLocal
from models import Usuario, Veiculo
from auth import hash_senha, verificar_senha, criar_token, decodificar_token

# Configuração de segurança para proteger as rotas
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
app = FastAPI(title="AutoGest API - Produção")

# CORS: Permite que o frontend (Vercel) acesse o backend (Render)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cria as tabelas automaticamente se não existirem no banco de dados
Base.metadata.create_all(bind=engine)

# Dependência para abrir e fechar conexão com o Banco de Dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Verifica se o token do usuário é válido antes de liberar os dados
def get_usuario_logado(token: str = Depends(oauth2_scheme)):
    email = decodificar_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Sessão expirada")
    return email

# --- ROTAS DE AUTENTICAÇÃO ---
@app.post("/login")
def login(dados: dict, db: Session = Depends(get_db)):
    """Valida o usuário e devolve um token de acesso"""
    u = db.query(Usuario).filter(Usuario.email == dados.get("email")).first()
    if not u or not verificar_senha(dados.get("senha"), u.senha):
        raise HTTPException(status_code=400, detail="E-mail ou senha incorretos")
    return {"access_token": criar_token(u.email), "token_type": "bearer"}

# --- ROTAS DE GESTÃO (CRUD) ---
@app.get("/dashboard")
def dashboard(db: Session = Depends(get_db), u: str = Depends(get_usuario_logado)):
    """Calcula os números dos cards (Total e Patrimônio)"""
    veiculos = db.query(Veiculo).all()
    valor_total = sum(v.valor for v in veiculos) if veiculos else 0
    return {"total_veiculos": len(veiculos), "valor_total": valor_total}

@app.get("/veiculos")
def listar(db: Session = Depends(get_db), u: str = Depends(get_usuario_logado)):
    """Retorna a lista completa para a tabela do estoque"""
    return db.query(Veiculo).all()

@app.post("/veiculos")
def criar(dados: dict, db: Session = Depends(get_db), u: str = Depends(get_usuario_logado)):
    """Cadastra um novo veículo no banco de dados"""
    novo = Veiculo(
        marca=dados['marca'],
        modelo=dados['modelo'],
        placa=dados['placa'].upper(),
        valor=dados['valor'],
        status="EM_ESTOQUE"
    )
    db.add(novo)
    db.commit() # Salva no banco de dados
    return novo

@app.delete("/veiculos/{id}")
def excluir(id: int, db: Session = Depends(get_db), u: str = Depends(get_usuario_logado)):
    """Remove o veículo e atualiza o patrimônio"""
    v = db.query(Veiculo).filter(Veiculo.id == id).first()
    if not v: raise HTTPException(status_code=404)
    db.delete(v)
    db.commit() # Confirma a exclusão para o dashboard atualizar
    return {"status": "sucesso"}

# --- INTEGRAÇÃO RENAVE ---
@app.get("/renave/consultar/{placa}")
def consultar_serpro(placa: str, u: str = Depends(get_usuario_logado)):
    """
    Simula consulta ao SERPRO.
    Futuramente, aqui entrará o uso do certificado digital do cliente.
    """
    return {
        "marca": "VOLKSWAGEN",
        "modelo": "POLO TRACK 1.0",
        "placa": placa.upper(),
        "ano": 2024
    }