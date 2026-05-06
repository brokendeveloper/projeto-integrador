from fastapi import Request, Depends, HTTPException, status
from api.auth.security import get_current_user
from bson import ObjectId


async def get_db(request: Request):
    return request.app.state.db


async def get_usuario_atual(
    user_id: str = Depends(get_current_user),
    db=Depends(get_db),
):
    usuario = await db.usuarios.find_one({"_id": ObjectId(user_id)})
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    return usuario
