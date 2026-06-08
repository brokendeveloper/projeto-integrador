from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException
from bson import ObjectId
from datetime import datetime


async def criar_alerta(dados: dict, usuario: dict, db: AsyncIOMotorDatabase) -> dict:
    plano = usuario.get("plano", "free")
    if plano == "free":
        count = await db.alertas.count_documents({"usuario_id": str(usuario["_id"]), "ativo": True})
        if count >= 3:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Você atingiu o limite de 3 alertas do plano gratuito. "
                    "Remova um alerta existente ou faça upgrade para o plano premium."
                ),
            )

    if not dados.get("nome"):
        partes = []
        if dados.get("cnae"):
            partes.append(f"CNAE {dados['cnae']}")
        if dados.get("valor_max"):
            partes.append(f"até R$ {int(dados['valor_max']):,}".replace(",", "."))
        if dados.get("uf"):
            partes.append(dados["uf"])
        dados["nome"] = " · ".join(partes) if partes else "Todos os editais"

    alerta = {
        **dados,
        "usuario_id": str(usuario["_id"]),
        "criado_em": datetime.utcnow().isoformat(),
    }
    resultado = await db.alertas.insert_one(alerta)
    return {**alerta, "id": str(resultado.inserted_id)}


async def listar_alertas(usuario: dict, db: AsyncIOMotorDatabase) -> list[dict]:
    cursor = db.alertas.find({"usuario_id": str(usuario["_id"])})
    alertas = []
    async for alerta in cursor:
        alertas.append({
            "id": str(alerta["_id"]),
            "nome": alerta.get("nome"),
            "cnae": alerta.get("cnae"),
            "valor_max": alerta.get("valor_max"),
            "uf": alerta.get("uf"),
            "criado_em": alerta.get("criado_em", ""),
        })
    return alertas


async def excluir_alerta(alerta_id: str, usuario: dict, db: AsyncIOMotorDatabase) -> None:
    try:
        obj_id = ObjectId(alerta_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID inválido")
    resultado = await db.alertas.delete_one({"_id": obj_id, "usuario_id": str(usuario["_id"])})
    if resultado.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
