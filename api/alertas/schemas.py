from pydantic import BaseModel
from typing import Optional


class AlertaCriar(BaseModel):
    nome: str
    cnae: Optional[str] = None
    valor_max: Optional[float] = None
    regiao: Optional[str] = None
    ativo: bool = True


class AlertaResponse(AlertaCriar):
    id: str
    usuario_id: str
    criado_em: str
