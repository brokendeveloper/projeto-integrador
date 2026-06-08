from motor.motor_asyncio import AsyncIOMotorDatabase

_DEFAULTS = {
    "notificacoes_email": True,
    "notificacoes_push": True,
    "alertas_mei_apenas": False,
}


async def obter_config(usuario: dict) -> dict:
    salvo = usuario.get("preferencias", {})
    return {**_DEFAULTS, **salvo}


async def atualizar_config(db: AsyncIOMotorDatabase, usuario: dict, dados: dict) -> dict:
    config = {**_DEFAULTS, **usuario.get("preferencias", {})}
    for chave, valor in dados.items():
        if chave in _DEFAULTS and valor is not None:
            config[chave] = valor
    await db.usuarios.update_one(
        {"_id": usuario["_id"]}, {"$set": {"preferencias": config}}
    )
    return config
