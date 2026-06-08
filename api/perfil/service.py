import re
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from api.auth.security import hash_senha, verificar_senha


def _serializar(usuario: dict) -> dict:
    return {
        "id": str(usuario["_id"]),
        "nome": usuario["nome"],
        "email": usuario["email"],
        "cnpj": usuario["cnpj"],
        "plano": usuario.get("plano", "free"),
        "criado_em": usuario.get("criado_em"),
    }


async def obter_perfil(usuario: dict) -> dict:
    return _serializar(usuario)


async def atualizar_perfil(db: AsyncIOMotorDatabase, usuario: dict, dados: dict) -> dict:
    update: dict = {}

    if dados.get("nome"):
        update["nome"] = dados["nome"].strip()

    if dados.get("email") and dados["email"] != usuario["email"]:
        existente = await db.usuarios.find_one({"email": dados["email"]})
        if existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Esse e-mail já está em uso por outra conta.",
            )
        update["email"] = dados["email"]

    if dados.get("cnpj"):
        cnpj_digits = re.sub(r"\D", "", dados["cnpj"])
        if len(cnpj_digits) != 14:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="CNPJ deve ter 14 dígitos.",
            )
        if cnpj_digits != usuario["cnpj"]:
            existente = await db.usuarios.find_one({"cnpj": cnpj_digits})
            if existente:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Esse CNPJ já está cadastrado em outra conta.",
                )
        update["cnpj"] = cnpj_digits

    if dados.get("senha_nova"):
        if not dados.get("senha_atual"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Informe a senha atual para alterá-la.",
            )
        if not verificar_senha(dados["senha_atual"], usuario["senha_hash"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Senha atual incorreta.",
            )
        if len(dados["senha_nova"]) < 8:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="A nova senha deve ter pelo menos 8 caracteres.",
            )
        update["senha_hash"] = hash_senha(dados["senha_nova"])

    if update:
        await db.usuarios.update_one(
            {"_id": usuario["_id"]}, {"$set": update}
        )
        usuario.update(update)

    return _serializar(usuario)
