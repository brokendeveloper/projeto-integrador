import secrets
from datetime import datetime, timedelta, timezone
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

    agora = datetime.now(timezone.utc).isoformat()
    usuario = {
        "nome": dados.nome,
        "email": dados.email,
        "cnpj": dados.cnpj,
        "senha_hash": hash_senha(dados.senha),
        "plano": "free",
        "criado_em": agora,
        "consentiu_termos": dados.consentiu_termos,
        "data_consentimento": (
            dados.data_consentimento.isoformat()
            if dados.data_consentimento
            else agora
        ),
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


async def solicitar_reset_senha(email: str, db: AsyncIOMotorDatabase) -> dict:
    """
    Gera um token de reset de senha com validade de 1 hora e persiste
    na collection 'reset_tokens'. Retorna o token diretamente pois não
    há serviço de e-mail disponível neste ambiente.

    Em produção: substituir o retorno pelo envio via e-mail transacional.
    Recomenda-se criar um índice TTL no MongoDB Atlas:
        db.reset_tokens.createIndex({ "expira_em": 1 }, { expireAfterSeconds: 0 })
    """
    usuario = await db.usuarios.find_one({"email": email})
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Se esse e-mail estiver cadastrado, um token de reset foi gerado.",
        )

    token = secrets.token_urlsafe(32)
    expira_em = datetime.now(timezone.utc) + timedelta(hours=1)

    await db.reset_tokens.delete_many({"usuario_id": str(usuario["_id"])})
    await db.reset_tokens.insert_one({
        "usuario_id": str(usuario["_id"]),
        "token": token,
        "expira_em": expira_em.isoformat(),
        "criado_em": datetime.now(timezone.utc).isoformat(),
    })

    return {"reset_token": token, "expira_em": expira_em.isoformat()}


async def redefinir_senha(token: str, nova_senha: str, db: AsyncIOMotorDatabase) -> dict:
    """
    Valida o token de reset, atualiza o hash da senha do usuário e
    remove o token da collection 'reset_tokens'.
    """
    registro = await db.reset_tokens.find_one({"token": token})
    if not registro:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido ou já utilizado.",
        )

    expira_em = datetime.fromisoformat(registro["expira_em"])
    if expira_em.tzinfo is None:
        expira_em = expira_em.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expira_em:
        await db.reset_tokens.delete_one({"token": token})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token expirado. Solicite um novo reset de senha.",
        )

    novo_hash = hash_senha(nova_senha)
    await db.usuarios.update_one(
        {"_id": ObjectId(registro["usuario_id"])},
        {"$set": {"senha_hash": novo_hash}},
    )
    await db.reset_tokens.delete_one({"token": token})

    return {"mensagem": "Senha redefinida com sucesso."}
