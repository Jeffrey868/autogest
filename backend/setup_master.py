from database import SessionLocal
import models
from auth import hash_senha


def setup():
    db = SessionLocal()

    # 1. Cria a sua Empresa (A dona do sistema)
    minha_empresa = models.Empresa(
        nome_fantasia="AutoGest Master",
        cnpj="00.000.000/0001-00",
        status="ATIVO"
    )
    db.add(minha_empresa)
    db.commit()
    db.refresh(minha_empresa)

    # 2. Cria o seu Usuário Master (Você)
    # AJUSTE O EMAIL E SENHA ABAIXO
    usuario_master = models.Usuario(
        nome="Administrador",
        email="admin@teste.com",
        senha=hash_senha("admin123"),  # Use a senha que desejar
        role="MASTER",
        empresa_id=minha_empresa.id
    )
    db.add(usuario_master)
    db.commit()

    print(f"Sucesso! Empresa ID {minha_empresa.id} criada e Usuário Master configurado.")
    db.close()


if __name__ == "__main__":
    setup()