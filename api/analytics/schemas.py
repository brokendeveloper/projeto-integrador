from typing import Optional
from pydantic import BaseModel, Field


class EstatisticasResponse(BaseModel):
    total_contratos: int = Field(..., description="Total de contratos na base")
    media_valor: Optional[float] = Field(None, description="Valor inicial médio (R$)")
    max_valor: Optional[float] = Field(None, description="Maior valor inicial (R$)")
    min_valor: Optional[float] = Field(None, description="Menor valor inicial positivo (R$)")


class OrgaoItem(BaseModel):
    orgao: Optional[str] = Field(None, description="Razão social do órgão")
    total_contratos: int = Field(..., description="Número de contratos publicados")
    valor_total_rs: float = Field(..., description="Soma dos valores iniciais (R$)")


class TopOrgaosResponse(BaseModel):
    n: int = Field(..., description="Quantidade de órgãos retornados")
    orgaos: list[OrgaoItem]


class ContratoMEIItem(BaseModel):
    numero_controle: Optional[str] = Field(None, description="Número de controle PNCP")
    objeto: Optional[str] = Field(None, description="Descrição do objeto do contrato")
    valor_inicial: Optional[float] = Field(None, description="Valor inicial (R$)")
    orgao: Optional[str] = Field(None, description="Razão social do órgão")
    data_publicacao: Optional[str] = Field(None, description="Data de publicação (ISO 8601)")


class ContratosMEIResponse(BaseModel):
    total: int = Field(..., description="Total de contratos favoráveis ao MEI na base")
    limite: int = Field(..., description="Quantidade retornada nesta resposta")
    contratos: list[ContratoMEIItem]


class SparkJobResponse(BaseModel):
    status: str = Field(..., description="'iniciado' ou 'erro'")
    mensagem: str = Field(..., description="Detalhes sobre o job")


# ── Spark Summary (resultado dos CSVs gerados pelo pipeline) ──────────────────

class SparkOrgaoItem(BaseModel):
    orgao: str
    count: int


class SparkMEIBucket(BaseModel):
    label: str
    count: int


class SparkContratoItem(BaseModel):
    numero_controle: Optional[str] = None
    objeto: Optional[str] = None
    valor_inicial: Optional[float] = None
    orgao_nome: Optional[str] = None
    data_publicacao: Optional[str] = None


class SparkSummaryResponse(BaseModel):
    disponivel: bool = Field(..., description="True se os CSVs do PySpark já foram gerados")
    total_processado: int = Field(0, description="Linhas em contratos_completo.csv")
    total_mei: int = Field(0, description="Linhas em contratos_mei.csv")
    ultimo_processamento: Optional[str] = Field(None, description="Timestamp da última execução")
    top_orgao: Optional[str] = Field(None)
    top_orgao_count: int = Field(0)
    top_orgaos: list[SparkOrgaoItem] = Field(default_factory=list)
    mei_media_valor: Optional[float] = Field(None)
    mei_max_valor: Optional[float] = Field(None)
    mei_min_valor: Optional[float] = Field(None)
    mei_buckets: list[SparkMEIBucket] = Field(default_factory=list, description="Histograma de valores (buckets de R$ 10k)")
    mei_sample: list[SparkContratoItem] = Field(default_factory=list, description="Primeiros 20 contratos MEI-favoráveis")
