from fastapi import APIRouter, Depends, Query
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from .schemas import PaginacaoResponse, EditalDetalhe
from .service import buscar_editais, buscar_edital_por_id
from api.dependencies import get_db, get_usuario_atual

router = APIRouter(prefix="/editais", tags=["editais"])


@router.get("", response_model=PaginacaoResponse)
async def listar_editais(
    cnae: Optional[str] = Query(None, description="Código CNAE do MEI"),
    valor_max: Optional[float] = Query(None, description="Valor máximo do contrato em R$"),
    regiao: Optional[str] = Query(None, description="Município ou estado"),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(20, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db),
    _: dict = Depends(get_usuario_atual),
):
    return await buscar_editais(db, cnae, valor_max, regiao, pagina, por_pagina)


@router.get("/{edital_id}", response_model=EditalDetalhe)
async def detalhar_edital(
    edital_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    _: dict = Depends(get_usuario_atual),
):
    return await buscar_edital_por_id(edital_id, db)
