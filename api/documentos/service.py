from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorGridFSBucket
from fastapi import UploadFile, HTTPException
from bson import ObjectId
from datetime import datetime
import hashlib


TIPOS_PERMITIDOS = {
    "application/pdf", "image/jpeg", "image/png",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
TAMANHO_MAXIMO = 10 * 1024 * 1024  # 10MB


async def fazer_upload(
    arquivo: UploadFile,
    edital_id: str,
    categoria: str,
    usuario: dict,
    db: AsyncIOMotorDatabase,
) -> dict:
    if arquivo.content_type not in TIPOS_PERMITIDOS:
        raise HTTPException(
            status_code=400,
            detail="Tipo de arquivo não aceito. Envie documentos em PDF, Word (.docx) ou imagens (JPG, PNG).",
        )

    conteudo = await arquivo.read()
    if len(conteudo) > TAMANHO_MAXIMO:
        raise HTTPException(status_code=413, detail="O arquivo é muito grande. O limite é de 10 MB por documento.")

    bucket = AsyncIOMotorGridFSBucket(db, bucket_name="documentos")
    file_id = await bucket.upload_from_stream(
        arquivo.filename,
        conteudo,
        metadata={
            "usuario_id": str(usuario["_id"]),
            "edital_id": edital_id,
            "categoria": categoria,
            "content_type": arquivo.content_type,
            "sha256": hashlib.sha256(conteudo).hexdigest(),
        },
    )
    return {
        "id": str(file_id),
        "nome": arquivo.filename,
        "tipo": arquivo.content_type,
        "categoria": categoria,
        "tamanho": len(conteudo),
        "edital_id": edital_id,
        "criado_em": datetime.utcnow().isoformat(),
    }


async def listar_documentos(edital_id: str, usuario: dict, db: AsyncIOMotorDatabase) -> list[dict]:
    bucket = AsyncIOMotorGridFSBucket(db, bucket_name="documentos")
    cursor = bucket.find({
        "metadata.usuario_id": str(usuario["_id"]),
        "metadata.edital_id": edital_id,
    })
    documentos = []
    async for doc in cursor:
        documentos.append({
            "id": str(doc._id),
            "nome": doc.filename,
            "tipo": doc.metadata.get("content_type"),
            "categoria": doc.metadata.get("categoria", "outros"),
            "tamanho": doc.length,
            "edital_id": edital_id,
            "criado_em": doc.upload_date.isoformat() if hasattr(doc, "upload_date") and doc.upload_date else None,
        })
    return documentos


async def excluir_documento(doc_id: str, usuario: dict, db: AsyncIOMotorDatabase) -> None:
    bucket = AsyncIOMotorGridFSBucket(db, bucket_name="documentos")
    try:
        obj_id = ObjectId(doc_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID inválido")

    arquivo = await bucket.open_download_stream(obj_id)
    if arquivo.metadata.get("usuario_id") != str(usuario["_id"]):
        raise HTTPException(status_code=403, detail="Você não tem permissão para remover este documento.")

    await bucket.delete(obj_id)
