from sqlalchemy.orm import Session
import models

def criar_veiculo(db: Session, veiculo):
    db_veiculo = models.Veiculo(**veiculo.dict())
    db.add(db_veiculo)
    db.commit()
    db.refresh(db_veiculo)
    return db_veiculo


def listar_veiculos(db: Session):
    return db.query(models.Veiculo).all()


def criar_movimentacao(db: Session, mov):
    db_mov = models.Movimentacao(**mov.dict())
    db.add(db_mov)

    if mov.tipo == "SAIDA":
        veiculo = db.query(models.Veiculo).filter(models.Veiculo.id == mov.veiculo_id).first()
        veiculo.status = "VENDIDO"

    db.commit()
    db.refresh(db_mov)
    return db_mov
