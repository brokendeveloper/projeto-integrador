from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import gridfs


async def exportar_dados_usuario(usuario_id: str, db: AsyncIOMotorDatabase) -> dict:
    oid = ObjectId(usuario_id)

    usuario = await db.usuarios.find_one({"_id": oid})
    if not usuario:
        return {}

    checklist = await db.checklist_progresso.find({"usuario_id": usuario_id}).to_list(None)
    alertas = await db.alertas.find({"usuario_id": usuario_id}).to_list(None)
    historico = await db.historico.find({"usuario_id": usuario_id}).to_list(None)

    def serializar(docs):
        result = []
        for doc in docs:
            doc["_id"] = str(doc["_id"])
            result.append(doc)
        return result

    return {
        "usuario": {
            "id": str(usuario["_id"]),
            "nome": usuario.get("nome"),
            "email": usuario.get("email"),
            "cnpj": usuario.get("cnpj"),
        },
        "checklist_progresso": serializar(checklist),
        "alertas": serializar(alertas),
        "historico": serializar(historico),
    }


async def excluir_conta_usuario(usuario_id: str, db: AsyncIOMotorDatabase) -> None:
    oid = ObjectId(usuario_id)

    await db.usuarios.delete_one({"_id": oid})
    await db.checklist_progresso.delete_many({"usuario_id": usuario_id})
    await db.alertas.delete_many({"usuario_id": usuario_id})
    await db.historico.delete_many({"usuario_id": usuario_id})

    # Remove arquivos do GridFS do usuário
    fs_files = db["fs.files"]
    fs_chunks = db["fs.chunks"]
    cursor = fs_files.find({"metadata.usuario_id": usuario_id})
    async for arquivo in cursor:
        await fs_chunks.delete_many({"files_id": arquivo["_id"]})
        await fs_files.delete_one({"_id": arquivo["_id"]})
