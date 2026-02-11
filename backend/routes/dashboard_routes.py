from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
import models

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def dashboard(db: Session = Depends(get_db)):
    total = db.query(models.Veiculo).count()
    estoque = db.query(models.Veiculo).filter(models.Veiculo.status == "EM_ESTOQUE").count()
    vendidos = db.query(models.Veiculo).filter(models.Veiculo.status == "VENDIDO").count()

    return {
        "total_veiculos": total,
        "em_estoque": estoque,
        "vendidos": vendidos
    }
