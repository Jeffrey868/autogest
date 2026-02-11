from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
import models
from renave import gerar_pdf

router = APIRouter(prefix="/renave", tags=["RENAVE"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/{veiculo_id}")
def gerar(veiculo_id: int, db: Session = Depends(get_db)):
    veiculo = db.query(models.Veiculo).filter(models.Veiculo.id == veiculo_id).first()
    return {"arquivo": gerar_pdf(veiculo)}
