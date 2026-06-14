"""
Módulo de segurança da autenticação LicitaME.

Responsabilidades:
- Geração e validação de tokens JWT (HS256)
- Hash e verificação de senhas com bcrypt
- Dependência FastAPI `get_current_user` para proteção de rotas

Criptografia em repouso (AES-256):
    Todos os dados persistidos no MongoDB — incluindo hashes de senha,
    documentos GridFS e tokens de reset — são protegidos pela criptografia
    em repouso do MongoDB Atlas (AES-256 via Encrypted Storage Engine).
    O Atlas gerencia as chaves no Key Management Service configurado
    no projeto. Referência:
    https://www.mongodb.com/docs/atlas/security-encrypt-at-rest/
"""
import os
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-inseguro-troque-em-producao")
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTPBearer exibe no Swagger um campo único "Value" onde o usuário cola o token.
# Substitui OAuth2PasswordBearer que gerava formulário username/password → erro 422.
_bearer_scheme = HTTPBearer(
    scheme_name="Bearer Token",
    description="Cole o token retornado em POST /auth/login. Formato: o token puro, sem 'Bearer '.",
    auto_error=False,  # retorna None em vez de 403 quando header ausente
)


def hash_senha(senha: str) -> str:
    return pwd_context.hash(senha)


def verificar_senha(senha: str, hash: str) -> bool:
    return pwd_context.verify(senha, hash)


def criar_token(data: dict) -> str:
    payload = data.copy()
    expira = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload["exp"] = expira
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> str:
    excecao = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sua sessão expirou. Faça login novamente para continuar.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise excecao
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise excecao
        return user_id
    except JWTError:
        raise excecao
