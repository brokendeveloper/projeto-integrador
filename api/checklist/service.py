from motor.motor_asyncio import AsyncIOMotorDatabase
from .rules import montar_checklist


async def obter_checklist(edital_id: str, usuario: dict, db: AsyncIOMotorDatabase) -> dict:
    plano = usuario.get("plano", "free")
    requisitos = montar_checklist(plano)

    progresso = await db.checklist_progresso.find_one({
        "usuario_id": str(usuario["_id"]),
        "edital_id": edital_id,
    })
    concluidos_ids = set()
    documentos_map = {}
    if progresso:
        for item in progresso.get("itens", []):
            if item.get("concluido"):
                concluidos_ids.add(item["requisito_id"])
            if item.get("documento_id"):
                documentos_map[item["requisito_id"]] = item["documento_id"]

    itens = [
        {**r, "concluido": r["id"] in concluidos_ids, "documento_id": documentos_map.get(r["id"])}
        for r in requisitos
    ]
    total = len(itens)
    n_concluidos = len(concluidos_ids)

    return {
        "edital_id": edital_id,
        "total": total,
        "concluidos": n_concluidos,
        "percentual": round((n_concluidos / total) * 100, 1) if total > 0 else 0.0,
        "itens": itens,
    }


async def marcar_requisito(
    edital_id: str,
    requisito_id: str,
    concluido: bool,
    documento_id: str | None,
    usuario: dict,
    db: AsyncIOMotorDatabase,
) -> dict:
    usuario_id = str(usuario["_id"])
    filtro = {"usuario_id": usuario_id, "edital_id": edital_id}
    progresso = await db.checklist_progresso.find_one(filtro)

    itens = progresso.get("itens", []) if progresso else []
    item_existente = next((i for i in itens if i["requisito_id"] == requisito_id), None)

    if item_existente:
        item_existente["concluido"] = concluido
        item_existente["documento_id"] = documento_id
    else:
        itens.append({"requisito_id": requisito_id, "concluido": concluido, "documento_id": documento_id})

    await db.checklist_progresso.update_one(
        filtro, {"$set": {"itens": itens}}, upsert=True
    )
    return await obter_checklist(edital_id, usuario, db)
