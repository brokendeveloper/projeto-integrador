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

    info_complementar = doc.get("informacaoComplementar") or doc.get("informacao_complementar")
    valor_global = doc.get("valorGlobal") or doc.get("valor_global")

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
        "informacao_complementar": info_complementar.strip() if info_complementar else None,
        "municipio": orgao.get("municipio") if isinstance(orgao, dict) else None,
        "data_vigencia_inicio": doc.get("dataVigenciaInicio") or doc.get("data_vigencia_inicio"),
        "valor_global": float(valor_global) if valor_global else None,
    }


async def buscar_editais(
    db: AsyncIOMotorDatabase,
    busca: Optional[str] = None,
    cnae: Optional[str] = None,
    valor_max: Optional[float] = None,
    regiao: Optional[str] = None,
    pagina: int = 1,
    por_pagina: int = 20,
    favoravel_mei: Optional[bool] = None,
) -> dict:
    conditions = []
    if favoravel_mei is True:
        conditions.append({"$or": [
            {"valorInicial": {"$gt": 0, "$lte": 80000}},
            {"valor_inicial": {"$gt": 0, "$lte": 80000}},
        ]})
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


async def gerar_resumo_edital(edital_id: str, db: AsyncIOMotorDatabase) -> dict:
    from fastapi import HTTPException, status
    import os
    import anthropic

    try:
        doc = await db.contratos.find_one({"_id": ObjectId(edital_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="ID de edital inválido.")
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Edital não encontrado.")

    if doc.get("_resumo_ia"):
        return {"resumo": doc["_resumo_ia"], "cached": True}

    orgao = doc.get("orgaoEntidade", {})
    nome_orgao = orgao.get("razaoSocial", orgao.get("nome", "Não informado")) if isinstance(orgao, dict) else str(orgao)
    valor = doc.get("valorInicial") or doc.get("valor_inicial") or 0
    info_comp = doc.get("informacaoComplementar") or "Não disponível"

    prompt = (
        "Você é um assistente especializado em licitações públicas brasileiras. "
        "Gere um resumo objetivo de 2 a 3 frases sobre este edital para um MEI decidir se vale a pena participar. "
        "Foque no tipo de serviço/bem, valor e acessibilidade para pequenos negócios.\n\n"
        f"Objeto: {doc.get('objetoContrato') or doc.get('objeto') or 'Não informado'}\n"
        f"Órgão: {nome_orgao}\n"
        f"Valor estimado: R$ {float(valor):,.2f}\n"
        f"Modalidade: {doc.get('modalidadeNome') or 'Não informada'}\n"
        f"Informação complementar: {info_comp}"
    )

    try:
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=250,
            messages=[{"role": "user", "content": prompt}],
        )
        resumo = message.content[0].text.strip()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Não foi possível gerar o resumo no momento. Tente novamente em instantes.",
        ) from exc

    await db.contratos.update_one(
        {"_id": ObjectId(edital_id)},
        {"$set": {"_resumo_ia": resumo}},
    )
    return {"resumo": resumo, "cached": False}


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
