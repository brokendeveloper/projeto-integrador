from pydantic import BaseModel
from typing import Optional


class EditalResumo(BaseModel):
    id: str
    numero_controle: str
    orgao: str
    objeto: str
    valor_estimado: Optional[float]
    data_publicacao: Optional[str]
    data_encerramento: Optional[str]
    modalidade: Optional[str] = None
    uf: Optional[str] = None
    favoravel_mei: bool


class EditalDetalhe(EditalResumo):
    cnpj_orgao: Optional[str]
    url_edital: Optional[str]


class PaginacaoResponse(BaseModel):
    total: int
    pagina: int
    paginas: int
    items: list[EditalResumo]
