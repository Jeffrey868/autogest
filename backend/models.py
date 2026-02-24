from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timedelta


class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True, index=True)
    nome_fantasia = Column(String)
    cnpj = Column(String, unique=True, index=True)
    status = Column(String, default="ATIVO")  # ATIVO, SUSPENSO, BLOQUEADO
    data_vencimento = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=30))

    # Campos para o Certificado Digital (Plug & Play)
    certificado_pfx = Column(LargeBinary, nullable=True)
    senha_certificado = Column(String, nullable=True)

    # Relacionamentos
    usuarios = relationship("Usuario", back_populates="empresa")
    veiculos = relationship("Veiculo", back_populates="empresa")


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String)
    email = Column(String, unique=True, index=True)
    senha = Column(String)
    role = Column(String, default="LOJISTA")  # "MASTER" (você) ou "LOJISTA"

    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=True)
    empresa = relationship("Empresa", back_populates="usuarios")


class Veiculo(Base):
    __tablename__ = "veiculos"

    id = Column(Integer, primary_key=True, index=True)
    marca = Column(String)
    modelo = Column(String)
    ano = Column(String)  # Adicionado para facilitar o RENAVE
    placa = Column(String, unique=True)
    valor = Column(Float)
    status = Column(String, default="EM_ESTOQUE")
    renave_numero = Column(String, nullable=True)
    data_entrada = Column(DateTime, default=datetime.utcnow)
    data_saida = Column(DateTime, nullable=True)

    # Vincula o carro a uma empresa específica
    empresa_id = Column(Integer, ForeignKey("empresas.id"))
    empresa = relationship("Empresa", back_populates="veiculos")