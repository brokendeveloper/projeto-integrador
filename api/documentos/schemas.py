from pydantic import BaseModel
from typing import Optional


class DocumentoResponse(BaseModel):
    id: str
    nome: str
    tipo: Optional[str] = None
    categoria: str
    tamanho: int
    edital_id: str
    criado_em: Optional[str] = None
