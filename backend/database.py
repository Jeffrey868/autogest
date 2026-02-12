import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Busca a URL do banco nas variáveis de ambiente
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./autogest.db")

# 2. Ajuste de compatibilidade para o PostgreSQL (Render exige postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 3. Configuração do Engine com suporte a SSL para a Nuvem
if "sqlite" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    # O segredo está aqui: connect_args força o SSL no driver psycopg2
    engine = create_engine(
        DATABASE_URL,
        connect_args={"sslmode": "require"},
        pool_pre_ping=True  # Verifica se a conexão está viva antes de usar
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()