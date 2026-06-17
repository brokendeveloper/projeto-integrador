import math
import re
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional
from bson import ObjectId


def _serializar_edital(doc: dict) -> dict:
    valor = doc.get("valorInicial") or doc.get("valor_inicial") or 0.0
    orgao = doc.get("orgaoEntidade", {})
    if isinstance(orgao, dict):
        nome_orgao = orgao.get("razaoSocial", orgao.get("nome", ""))
        uf = orgao.get("ufSigla", orgao.get("uf", ""))
    else:
        nome_orgao = str(orgao)
        uf = ""

    cnpj_orgao = None
    if isinstance(orgao, dict):
        cnpj_orgao = orgao.get("cnpj") or orgao.get("cnpjOrgao")

    return {
        "id": str(doc["_id"]),
        "numero_controle": doc.get("numeroControlePNCP") or "",
        "orgao": nome_orgao or "",
        "cnpj_orgao": cnpj_orgao,
        "objeto": doc.get("objetoContrato") or doc.get("objeto") or "",
        "valor_estimado": float(valor) if valor else None,
        "data_publicacao": doc.get("dataPublicacaoPncp") or doc.get("data_publicacao"),
        "data_encerramento": doc.get("dataVigenciaFim") or doc.get("data_encerramento"),
        "modalidade": doc.get("modalidadeNome") or doc.get("modalidade"),
        "uf": uf or doc.get("uf") or None,
        "favoravel_mei": float(valor) <= 80000.0 if valor else False,
        "url_edital": doc.get("linkSistemaOrigem") or doc.get("urlEdital") or None,
    }


async def buscar_editais(
    db: AsyncIOMotorDatabase,
    busca: Optional[str] = None,
    cnae: Optional[str] = None,
    valor_max: Optional[float] = None,
    regiao: Optional[str] = None,
    pagina: int = 1,
    por_pagina: int = 20,
) -> dict:
    conditions = []
    if valor_max:
        conditions.append({"$or": [
            {"valorInicial": {"$lte": valor_max}},
            {"valor_inicial": {"$lte": valor_max}},
        ]})
    if regiao:
        conditions.append({"$or": [
            {"orgaoEntidade.municipio": {"$regex": regiao, "$options": "i"}},
            {"municipio": {"$regex": regiao, "$options": "i"}},
        ]})
    if busca:
        busca_safe = re.escape(busca.strip())
        conditions.append({"$or": [
            {"objetoContrato": {"$regex": busca_safe, "$options": "i"}},
            {"objeto": {"$regex": busca_safe, "$options": "i"}},
        ]})

    filtros = {"$and": conditions} if conditions else {}
    skip = (pagina - 1) * por_pagina
    total = await db.contratos.count_documents(filtros)
    cursor = db.contratos.find(filtros).skip(skip).limit(por_pagina)
    documentos = await cursor.to_list(length=por_pagina)
    paginas = math.ceil(total / por_pagina) if total > 0 else 1

    return {
        "total": total,
        "pagina": pagina,
        "paginas": paginas,
        "items": [_serializar_edital(doc) for doc in documentos],
    }


async def buscar_edital_por_id(edital_id: str, db: AsyncIOMotorDatabase) -> dict:
    from fastapi import HTTPException, status
    try:
        doc = await db.contratos.find_one({"_id": ObjectId(edital_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="ID de edital inválido. Verifique o formato e tente novamente.")
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Edital não encontrado. Ele pode ter sido removido do PNCP.",
        )
    return _serializar_edital(doc)
