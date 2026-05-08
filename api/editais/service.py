from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional
from bson import ObjectId


def _serializar_edital(doc: dict) -> dict:
    valor = doc.get("valorInicial") or doc.get("valor_inicial") or 0.0
    orgao = doc.get("orgaoEntidade", {})
    if isinstance(orgao, dict):
        nome_orgao = orgao.get("razaoSocial", orgao.get("nome", ""))
    else:
        nome_orgao = str(orgao)

    return {
        "id": str(doc["_id"]),
        "numero_controle_pncp": doc.get("numeroControlePNCP", ""),
        "orgao": nome_orgao,
        "objeto": doc.get("objetoContrato", doc.get("objeto", "")),
        "valor_inicial": float(valor) if valor else None,
        "data_publicacao": doc.get("dataPublicacaoPncp", doc.get("data_publicacao")),
        "data_encerramento": doc.get("dataVigenciaFim", doc.get("data_encerramento")),
        "favoravel_mei": float(valor) <= 80000.0 if valor else False,
    }


async def buscar_editais(
    db: AsyncIOMotorDatabase,
    cnae: Optional[str] = None,
    valor_max: Optional[float] = None,
    regiao: Optional[str] = None,
    pagina: int = 1,
    por_pagina: int = 20,
) -> dict:
    filtros = {}
    if valor_max:
        filtros["$or"] = [
            {"valorInicial": {"$lte": valor_max}},
            {"valor_inicial": {"$lte": valor_max}},
        ]
    if regiao:
        filtros["$or"] = filtros.get("$or", []) + [
            {"orgaoEntidade.municipio": {"$regex": regiao, "$options": "i"}},
            {"municipio": {"$regex": regiao, "$options": "i"}},
        ]

    skip = (pagina - 1) * por_pagina
    total = await db.contratos.count_documents(filtros)
    cursor = db.contratos.find(filtros).skip(skip).limit(por_pagina)
    documentos = await cursor.to_list(length=por_pagina)

    return {
        "total": total,
        "pagina": pagina,
        "por_pagina": por_pagina,
        "dados": [_serializar_edital(doc) for doc in documentos],
    }


async def buscar_edital_por_id(edital_id: str, db: AsyncIOMotorDatabase) -> dict:
    from fastapi import HTTPException, status
    try:
        doc = await db.contratos.find_one({"_id": ObjectId(edital_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="ID inválido")
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Edital não encontrado")
    return _serializar_edital(doc)
