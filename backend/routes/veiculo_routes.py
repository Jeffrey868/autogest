from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
import models, schemas

router = APIRouter(prefix="/veiculos", tags=["Veículos"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
def criar_veiculo(veiculo: schemas.VeiculoCreate, db: Session = Depends(get_db)):
    novo = models.Veiculo(**veiculo.dict())
    db.add(novo)
    db.commit()
    return novo

@router.get("/")
def listar_veiculos(db: Session = Depends(get_db)):
    return db.query(models.Veiculo).all()
