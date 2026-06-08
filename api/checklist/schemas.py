from pydantic import BaseModel
from typing import Optional


class RequisitoItem(BaseModel):
    id: str
    categoria: str
    descricao: str
    base_legal: str
    obrigatorio: bool
    plano_necessario: str = "free"
    concluido: bool = False
    documento_id: Optional[str] = None


class ChecklistResponse(BaseModel):
    edital_id: str
    progresso: float
    items: list[RequisitoItem]


class MarcarRequisito(BaseModel):
    item_id: str
    concluido: bool
    documento_id: Optional[str] = None
