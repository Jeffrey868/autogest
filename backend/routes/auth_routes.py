from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
import models, schemas
from auth import hash_senha, verificar_senha, criar_token

router = APIRouter(prefix="/auth", tags=["Auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register")
def register(user: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    novo = models.Usuario(email=user.email, senha=hash_senha(user.senha))
    db.add(novo)
    db.commit()
    return {"msg": "Usuário criado"}

@router.post("/login")
def login(user: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.Usuario).filter(models.Usuario.email == user.email).first()
    if not db_user or not verificar_senha(user.senha, db_user.senha):
        return {"erro": "Credenciais inválidas"}
    token = criar_token(db_user.email)
    return {"access_token": token}
