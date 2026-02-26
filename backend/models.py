from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class Empresa(Base):
    __tablename__ = "empresas"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String)
    cnpj = Column(String, unique=True)
    status = Column(String, default="ATIVO")
    certificado_pfx = Column(String, nullable=True)
    senha_certificado = Column(String, nullable=True)
    veiculos = relationship("Veiculo", back_populates="empresa")


class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    senha = Column(String)
    nome = Column(String)
    role = Column(String, default="LOJISTA")
    empresa_id = Column(Integer, ForeignKey("empresas.id"))


class Veiculo(Base):
    __tablename__ = "veiculos"
    id = Column(Integer, primary_key=True, index=True)
    marca = Column(String)
    modelo = Column(String)
    ano = Column(String)
    placa = Column(String, unique=True)
    valor = Column(Float)  # Valor de entrada (estoque)
    status = Column(String, default="EM_ESTOQUE")
    empresa_id = Column(Integer, ForeignKey("empresas.id"))

    # CAMPOS PARA O FORMULÁRIO RENAVE (PREENCHIDOS NA VENDA)
    comprador_nome = Column(String, nullable=True)
    comprador_documento = Column(String, nullable=True)
    comprador_endereco = Column(String, nullable=True)
    valor_venda = Column(Float, nullable=True)
    data_venda = Column(DateTime, nullable=True)

    empresa = relationship("Empresa", back_populates="veiculos")