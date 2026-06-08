from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException, status
from bson import ObjectId
from .schemas import UserRegister
from .security import hash_senha, verificar_senha, criar_token


async def registrar_usuario(dados: UserRegister, db: AsyncIOMotorDatabase) -> dict:
    existente = await db.usuarios.find_one({"email": dados.email})
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esse e-mail já tem uma conta na LicitaME. Faça login ou use outro e-mail.",
        )

    cnpj_existente = await db.usuarios.find_one({"cnpj": dados.cnpj})
    if cnpj_existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esse CNPJ já está cadastrado. Entre em contato se isso for um erro.",
        )

    usuario = {
        "nome": dados.nome,
        "email": dados.email,
        "cnpj": dados.cnpj,
        "senha_hash": hash_senha(dados.senha),
        "plano": "free",
        "criado_em": datetime.now(timezone.utc).isoformat(),
    }
    resultado = await db.usuarios.insert_one(usuario)
    token = criar_token({"sub": str(resultado.inserted_id)})
    return {"access_token": token, "token_type": "bearer"}


async def autenticar_usuario(email: str, senha: str, db: AsyncIOMotorDatabase) -> dict:
    usuario = await db.usuarios.find_one({"email": email})
    if not usuario or not verificar_senha(senha, usuario["senha_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos. Verifique e tente novamente.",
        )
    token = criar_token({"sub": str(usuario["_id"])})
    return {"access_token": token, "token_type": "bearer"}
