from pydantic import BaseModel

class UsuarioCreate(BaseModel):
    email: str
    senha: str

class VeiculoCreate(BaseModel):
    marca: str
    modelo: str
    placa: str
    valor: float
