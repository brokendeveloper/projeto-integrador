from pydantic import BaseModel
from typing import Optional


class EditalResumo(BaseModel):
    id: str
    numero_controle_pncp: str
    orgao: str
    objeto: str
    valor_inicial: Optional[float]
    data_publicacao: Optional[str]
    data_encerramento: Optional[str]
    favoravel_mei: bool


class EditalDetalhe(EditalResumo):
    cnpj_orgao: Optional[str]
    modalidade: Optional[str]
    url_edital: Optional[str]


class PaginacaoResponse(BaseModel):
    total: int
    pagina: int
    por_pagina: int
    dados: list[EditalResumo]
