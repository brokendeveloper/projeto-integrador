from pydantic import BaseModel
from typing import List


class PlanoInfo(BaseModel):
    nome: str
    preco: str
    recursos: List[str]
    limite_alertas: int


class PlanoResponse(BaseModel):
    plano_atual: str
    info: PlanoInfo
    proximo_plano: PlanoInfo
