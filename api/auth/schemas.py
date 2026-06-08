from pydantic import BaseModel, EmailStr, field_validator
import re


class UserRegister(BaseModel):
    nome: str
    email: EmailStr
    cnpj: str
    senha: str

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
