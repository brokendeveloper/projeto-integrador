from fastapi import APIRouter, Depends, UploadFile, File, Form
from motor.motor_asyncio import AsyncIOMotorDatabase
from .schemas import DocumentoResponse
from .service import fazer_upload, listar_documentos, excluir_documento
from api.dependencies import get_db, get_usuario_atual

router = APIRouter(prefix="/editais/{edital_id}/documentos", tags=["📁 Documentos"])


@router.post("", response_model=DocumentoResponse, status_code=201, summary="Enviar documento")
async def upload_documento(
    edital_id: str,
    arquivo: UploadFile = File(...),
    categoria: str = Form(...),
    db: AsyncIOMotorDatabase = Depends(get_db),
    usuario: dict = Depends(get_usuario_atual),
):
    return await fazer_upload(arquivo, edital_id, categoria, usuario, db)


@router.get("", response_model=list[DocumentoResponse], summary="Ver documentos enviados")
async def listar(
    edital_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    usuario: dict = Depends(get_usuario_atual),
):
    return await listar_documentos(edital_id, usuario, db)


@router.delete("/{doc_id}", status_code=204, summary="Remover documento")
async def excluir(
    edital_id: str,
    doc_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    usuario: dict = Depends(get_usuario_atual),
):
    await excluir_documento(doc_id, usuario, db)
