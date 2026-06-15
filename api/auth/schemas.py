from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
import re


class UserRegister(BaseModel):
    nome: str
    email: EmailStr
    cnpj: str
    senha: str
    consentiu_termos: bool
    data_consentimento: Optional[datetime] = None

    @field_validator("cnpj")
    @classmethod
    def validar_cnpj(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v)
        if len(digits) != 14:
            raise ValueError("CNPJ deve ter 14 dígitos")
        return digits

    @field_validator("senha")
    @classmethod
    def validar_senha(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Senha deve ter pelo menos 8 caracteres")
        return v

    @field_validator("consentiu_termos")
    @classmethod
    def validar_consentimento(cls, v: bool) -> bool:
        if not v:
            raise ValueError(
                "É necessário consentir com os termos de uso para criar uma conta."
            )
        return v


class UserLogin(BaseModel):
    email: EmailStr
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserPublic(BaseModel):
    id: str
    nome: str
    email: str
    cnpj: str


class ResetSenhaRequest(BaseModel):
    email: EmailStr


class RedefinirSenhaRequest(BaseModel):
    token: str
    nova_senha: str

    @field_validator("nova_senha")
    @classmethod
    def validar_nova_senha(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("A nova senha deve ter pelo menos 8 caracteres")
        return v
