from pydantic import BaseModel, EmailStr
from typing import Optional


class PerfilResponse(BaseModel):
    id: str
    nome: str
    email: str
    cnpj: str
    plano: str
    criado_em: Optional[str] = None


class PerfilUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    cnpj: Optional[str] = None
    senha_atual: Optional[str] = None
    senha_nova: Optional[str] = None
