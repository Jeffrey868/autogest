from sqlalchemy import Column, Integer, String, Float, DateTime
from database import Base
from datetime import datetime

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    senha = Column(String)


class Veiculo(Base):
    __tablename__ = "veiculos"

    id = Column(Integer, primary_key=True, index=True)
    marca = Column(String)
    modelo = Column(String)
    placa = Column(String)
    valor = Column(Float)
    status = Column(String, default="EM_ESTOQUE")
    renave_numero = Column(String, nullable=True)
    data_saida = Column(DateTime, nullable=True)
