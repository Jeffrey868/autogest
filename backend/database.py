import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Busca a URL do banco nas variáveis de ambiente (Nuvem)
# Se não encontrar (Local), usa o SQLite como padrão
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./autogest.db")

# 2. Ajuste de compatibilidade para o PostgreSQL do Render/Heroku
# Eles costumam enviar a URL começando com 'postgres://', mas o SQLAlchemy exige 'postgresql://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 3. Configuração do Engine
# O 'check_same_thread' só é necessário para o SQLite
if "sqlite" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()