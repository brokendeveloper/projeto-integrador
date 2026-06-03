from pydantic import BaseModel
from typing import Optional


class ConfigResponse(BaseModel):
    notificacoes_email: bool
    notificacoes_push: bool
    alertas_mei_apenas: bool


class ConfigUpdate(BaseModel):
    notificacoes_email: Optional[bool] = None
    notificacoes_push: Optional[bool] = None
    alertas_mei_apenas: Optional[bool] = None
