from fastapi import APIRouter, Depends, Response, status
from api.dependencies import get_db, get_usuario_atual
from .service import exportar_dados_usuario, excluir_conta_usuario

router = APIRouter(prefix="/lgpd", tags=["🛡️ LGPD"])


@router.get("/meus-dados", summary="Exportar meus dados")
async def meus_dados(
    usuario=Depends(get_usuario_atual),
    db=Depends(get_db),
):
    usuario_id = str(usuario["_id"])
    return await exportar_dados_usuario(usuario_id, db)


@router.delete("/minha-conta", status_code=status.HTTP_204_NO_CONTENT, summary="Excluir minha conta")
async def excluir_conta(
    usuario=Depends(get_usuario_atual),
    db=Depends(get_db),
):
    usuario_id = str(usuario["_id"])
    await excluir_conta_usuario(usuario_id, db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
