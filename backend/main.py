from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime
import random
import os

from database import Base, engine, SessionLocal
from models import Usuario, Veiculo
from auth import hash_senha, verificar_senha, criar_token

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

app = FastAPI(title="AutoGest API")

# ----------------------------
# CORS
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Criar banco
# ----------------------------
Base.metadata.create_all(bind=engine)

# ----------------------------
# Dependência DB
# ----------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------------------------
# Criar admin automático
# ----------------------------
@app.on_event("startup")
def criar_admin():
    db = SessionLocal()
    admin = db.query(Usuario).filter(Usuario.email == "admin@admin.com").first()

    if not admin:
        novo_admin = Usuario(
            email="admin@admin.com",
            senha=hash_senha("admin123")
        )
        db.add(novo_admin)
        db.commit()
        print("Admin criado automaticamente ✔")

    db.close()

# ----------------------------
# LOGIN
# ----------------------------
@app.post("/login")
def login(dados: dict, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(
        Usuario.email == dados.get("email")
    ).first()

    if not usuario:
        raise HTTPException(status_code=400, detail="Usuário não encontrado")

    if not verificar_senha(dados.get("senha"), usuario.senha):
        raise HTTPException(status_code=400, detail="Senha incorreta")

    token = criar_token(usuario.email)

    return {"access_token": token}

# ----------------------------
# DASHBOARD
# ----------------------------
@app.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    total = db.query(Veiculo).count()
    estoque = db.query(Veiculo).filter(Veiculo.status == "EM_ESTOQUE").count()
    vendidos = db.query(Veiculo).filter(Veiculo.status == "VENDIDO").count()
    valor_total = sum(v.valor for v in db.query(Veiculo).all())

    return {
        "total_veiculos": total,
        "em_estoque": estoque,
        "vendidos": vendidos,
        "valor_total": valor_total
    }

# ----------------------------
# CRUD VEÍCULOS
# ----------------------------

@app.post("/veiculos")
def criar_veiculo(dados: dict, db: Session = Depends(get_db)):
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


@app.get("/veiculos")
def listar_veiculos(db: Session = Depends(get_db)):
    return db.query(Veiculo).all()


@app.delete("/veiculos/{veiculo_id}")
def deletar_veiculo(veiculo_id: int, db: Session = Depends(get_db)):
    veiculo = db.query(Veiculo).filter(Veiculo.id == veiculo_id).first()

    if not veiculo:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")

    db.delete(veiculo)
    db.commit()

    return {"msg": "Veículo deletado com sucesso"}


# ----------------------------
# RENAVE ENTRADA
# ----------------------------
@app.post("/renave/entrada/{veiculo_id}")
def registrar_renave(veiculo_id: int, db: Session = Depends(get_db)):
    veiculo = db.query(Veiculo).filter(Veiculo.id == veiculo_id).first()

    if not veiculo:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")

    if veiculo.renave_numero:
        raise HTTPException(status_code=400, detail="Já possui RENAVE")

    numero = "REN" + str(random.randint(100000, 999999))

    veiculo.renave_numero = numero
    veiculo.status = "EM_ESTOQUE"

    db.commit()

    return {"msg": "RENAVE registrado com sucesso", "numero": numero}


# ----------------------------
# RENAVE SAÍDA (VENDA)
# ----------------------------
@app.post("/renave/saida/{veiculo_id}")
def baixa_renave(veiculo_id: int, db: Session = Depends(get_db)):
    veiculo = db.query(Veiculo).filter(Veiculo.id == veiculo_id).first()

    if not veiculo:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")

    veiculo.status = "VENDIDO"
    veiculo.data_saida = datetime.utcnow()

    db.commit()

    return {"msg": "Veículo vendido com sucesso"}


# ----------------------------
# GERAR PDF RENAVE
# ----------------------------
@app.get("/renave/pdf/{veiculo_id}")
def gerar_pdf_renave(veiculo_id: int, db: Session = Depends(get_db)):
    veiculo = db.query(Veiculo).filter(Veiculo.id == veiculo_id).first()

    if not veiculo:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")

    file_name = f"renave_{veiculo.id}.pdf"

    doc = SimpleDocTemplate(file_name)
    elements = []

    styles = getSampleStyleSheet()

    elements.append(Paragraph("DOCUMENTO RENAVE - AutoGest", styles["Title"]))
    elements.append(Spacer(1, 20))

    data = [
        ["Marca", veiculo.marca],
        ["Modelo", veiculo.modelo],
        ["Placa", veiculo.placa],
        ["Valor", f"R$ {veiculo.valor}"],
        ["RENAVE", veiculo.renave_numero or "Não registrado"],
        ["Status", veiculo.status],
    ]

    table = Table(data)
    table.setStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey)
    ])

    elements.append(table)
    doc.build(elements)

    return FileResponse(
        file_name,
        media_type="application/pdf",
        filename=file_name
    )


# ----------------------------
# ROOT
# ----------------------------
@app.get("/")
def root():
    return {"msg": "AutoGest API rodando 🚀"}
