from pydantic import BaseModel
from typing import Optional


class RequisitoItem(BaseModel):
    id: str
    categoria: str
    descricao: str
    base_legal: str
    obrigatorio: bool
    concluido: bool = False
    documento_id: Optional[str] = None


class ChecklistResponse(BaseModel):
    edital_id: str
    total: int
    concluidos: int
    percentual: float
    itens: list[RequisitoItem]


class MarcarRequisito(BaseModel):
    requisito_id: str
    concluido: bool
    documento_id: Optional[str] = None
