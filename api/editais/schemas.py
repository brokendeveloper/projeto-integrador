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
    cnpj_orgao: Optional[str] = None
    url_edital: Optional[str] = None
    informacao_complementar: Optional[str] = None
    municipio: Optional[str] = None
    data_vigencia_inicio: Optional[str] = None
    valor_global: Optional[float] = None


class ResumoResponse(BaseModel):
    resumo: str
    cached: bool = False


class PaginacaoResponse(BaseModel):
    total: int
    pagina: int
    paginas: int
    items: list[EditalResumo]
