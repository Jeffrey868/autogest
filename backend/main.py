from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer  # Novo: para cadeado nas rotas
from sqlalchemy.orm import Session
from datetime import datetime
import random
import os

from database import Base, engine, SessionLocal
from models import Usuario, Veiculo
from auth import hash_senha, verificar_senha, criar_token, decodificar_token  # Adicionado decodificar

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# ----------------------------
# CONFIGURAÇÃO DE SEGURANÇA
# ----------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app = FastAPI(title="AutoGest API")

# ----------------------------
# CORS (Ajustado para aceitar requisições de qualquer lugar)
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Criar banco (Garante que as tabelas existam antes do app subir)
# ----------------------------
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
    """Verifica se o token JWT é válido para liberar a rota."""
    email = decodificar_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão expirada. Faça login novamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return email


# ----------------------------
# Criar admin automático
# ----------------------------
@app.on_event("startup")
def criar_admin():
    db = SessionLocal()
    try:
        admin = db.query(Usuario).filter(Usuario.email == "admin@admin.com").first()
        if not admin:
            novo_admin = Usuario(
                email="admin@admin.com",
                senha=hash_senha("admin123")
            )
            db.add(novo_admin)
            db.commit()
            print("Admin criado automaticamente ✔")
    except Exception as e:
        print(f"Erro ao criar admin: {e}")
    finally:
        db.close()


# ----------------------------
# LOGIN (Gera o Token)
# ----------------------------
@app.post("/login")
def login(dados: dict, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == dados.get("email")).first()

    if not usuario or not verificar_senha(dados.get("senha"), usuario.senha):
        raise HTTPException(status_code=400, detail="E-mail ou senha incorretos")

    token = criar_token(usuario.email)
    return {"access_token": token, "token_type": "bearer"}


# ----------------------------
# ROTAS PROTEGIDAS (Adicionado Depends(get_usuario_logado))
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


# --- Processos RENAVE ---

@app.post("/renave/entrada/{veiculo_id}")
def registrar_renave(veiculo_id: int, db: Session = Depends(get_db), usuario: str = Depends(get_usuario_logado)):
    veiculo = db.query(Veiculo).filter(Veiculo.id == veiculo_id).first()
    if not veiculo:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")
    if veiculo.renave_numero:
        raise HTTPException(status_code=400, detail="Este veículo já possui um RENAVE ativo")

    numero = "REN" + str(random.randint(100000, 999999))
    veiculo.renave_numero = numero
    veiculo.status = "EM_ESTOQUE"
    db.commit()
    return {"msg": "RENAVE registrado com sucesso", "numero": numero}


@app.post("/renave/saida/{veiculo_id}")
def baixa_renave(veiculo_id: int, db: Session = Depends(get_db), usuario: str = Depends(get_usuario_logado)):
    veiculo = db.query(Veiculo).filter(Veiculo.id == veiculo_id).first()
    if not veiculo:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")

    veiculo.status = "VENDIDO"
    veiculo.data_saida = datetime.utcnow()
    db.commit()
    return {"msg": "Baixa de RENAVE processada (Veículo Vendido)"}


@app.get("/renave/pdf/{veiculo_id}")
def gerar_pdf_renave(veiculo_id: int, db: Session = Depends(get_db), usuario: str = Depends(get_usuario_logado)):
    veiculo = db.query(Veiculo).filter(Veiculo.id == veiculo_id).first()
    if not veiculo:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")

    file_name = f"renave_{veiculo.id}.pdf"
    doc = SimpleDocTemplate(file_name)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph(f"CERTIFICADO RENAVE - {veiculo.placa}", styles["Title"]))
    elements.append(Spacer(1, 20))

    data = [
        ["Marca", veiculo.marca],
        ["Modelo", veiculo.modelo],
        ["Placa", veiculo.placa],
        ["Valor", f"R$ {veiculo.valor:,.2f}"],
        ["Número RENAVE", veiculo.renave_numero or "Pendente"],
        ["Data de Emissão", datetime.now().strftime("%d/%m/%Y %H:%M")],
    ]

    table = Table(data)
    table.setStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke)
    ])
    elements.append(table)
    doc.build(elements)

    return FileResponse(file_name, media_type="application/pdf", filename=file_name)


@app.get("/")
def root():
    return {"status": "online", "message": "AutoGest API robusta rodando no Render 🚀"}