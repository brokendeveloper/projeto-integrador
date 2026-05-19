from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException
from bson import ObjectId
from datetime import datetime


async def registrar_participacao(dados: dict, usuario: dict, db: AsyncIOMotorDatabase) -> dict:
    participacao = {
        **dados,
        "usuario_id": str(usuario["_id"]),
        "registrado_em": datetime.utcnow().isoformat(),
    }
    resultado = await db.historico.insert_one(participacao)
    return {**participacao, "id": str(resultado.inserted_id)}


async def listar_participacoes(usuario: dict, db: AsyncIOMotorDatabase) -> list[dict]:
    cursor = db.historico.find({"usuario_id": str(usuario["_id"])})
    participacoes = []
    async for p in cursor:
        participacoes.append({**p, "id": str(p["_id"]), "_id": None})
    return participacoes


async def obter_resumo(usuario: dict, db: AsyncIOMotorDatabase) -> dict:
    usuario_id = str(usuario["_id"])
    total = await db.historico.count_documents({"usuario_id": usuario_id})
    venceu = await db.historico.count_documents({"usuario_id": usuario_id, "status": "venceu"})
    em_andamento = await db.historico.count_documents({"usuario_id": usuario_id, "status": "em_andamento"})
    perdeu = await db.historico.count_documents({"usuario_id": usuario_id, "status": "perdeu"})
    desistiu = await db.historico.count_documents({"usuario_id": usuario_id, "status": "desistiu"})
    return {
        "total": total,
        "venceu": venceu,
        "em_andamento": em_andamento,
        "perdeu": perdeu,
        "desistiu": desistiu,
    }
