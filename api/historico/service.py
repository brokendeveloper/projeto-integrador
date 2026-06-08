from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException
from bson import ObjectId
from datetime import datetime


async def registrar_participacao(dados: dict, usuario: dict, db: AsyncIOMotorDatabase) -> dict:
    data_participacao = datetime.utcnow().isoformat()
    participacao = {
        **dados,
        "usuario_id": str(usuario["_id"]),
        "data_participacao": data_participacao,
    }
    resultado = await db.historico.insert_one(participacao)
    return {
        "id": str(resultado.inserted_id),
        "edital_id": participacao["edital_id"],
        "status": participacao.get("status", "em_andamento"),
        "valor_proposta": participacao.get("valor_proposta"),
        "data_participacao": data_participacao,
    }


async def listar_participacoes(usuario: dict, db: AsyncIOMotorDatabase) -> list[dict]:
    cursor = db.historico.find({"usuario_id": str(usuario["_id"])})
    participacoes = []
    async for p in cursor:
        participacoes.append({
            "id": str(p["_id"]),
            "edital_id": p.get("edital_id", ""),
            "status": p.get("status", "em_andamento"),
            "valor_proposta": p.get("valor_proposta"),
            "data_participacao": p.get("data_participacao", p.get("registrado_em", "")),
        })
    return participacoes


async def obter_resumo(usuario: dict, db: AsyncIOMotorDatabase) -> dict:
    usuario_id = str(usuario["_id"])
    total = await db.historico.count_documents({"usuario_id": usuario_id})
    vencidas = await db.historico.count_documents({"usuario_id": usuario_id, "status": "vencida"})
    em_andamento = await db.historico.count_documents({"usuario_id": usuario_id, "status": "em_andamento"})
    perdidas = await db.historico.count_documents({"usuario_id": usuario_id, "status": "perdida"})
    return {
        "total": total,
        "vencidas": vencidas,
        "em_andamento": em_andamento,
        "perdidas": perdidas,
    }
