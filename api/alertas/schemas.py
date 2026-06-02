from pydantic import BaseModel
from typing import Optional


class AlertaCriar(BaseModel):
    nome: Optional[str] = None
    cnae: Optional[str] = None
    valor_max: Optional[float] = None
    uf: Optional[str] = None
    ativo: bool = True


class AlertaResponse(BaseModel):
    id: str
    nome: Optional[str] = None
    cnae: Optional[str] = None
    valor_max: Optional[float] = None
    uf: Optional[str] = None
    criado_em: str
