from pydantic import BaseModel, Field


class FerramentaInfo(BaseModel):
    name: str = Field(..., description="Identificador único da ferramenta")
    description: str = Field(..., description="O que a ferramenta faz")
    input_schema: dict = Field(..., description="JSON Schema dos argumentos aceitos")


class ListaFerramentasResponse(BaseModel):
    total: int
    ferramentas: list[FerramentaInfo]


class InvocarRequest(BaseModel):
    ferramenta: str = Field(
        ...,
        description="Nome da ferramenta a invocar",
        examples=["top_orgaos", "buscar_contratos", "estatisticas_contratos", "contratos_favoraveis_mei"],
    )
    argumentos: dict = Field(
        default_factory=dict,
        description="Argumentos para a ferramenta (conforme input_schema)",
        examples=[{"n": 5}, {"palavra_chave": "limpeza"}, {}, {"limite": 10}],
    )


class InvocarResponse(BaseModel):
    ferramenta: str
    resultado: str = Field(..., description="Resultado em formato texto/JSON")
    sucesso: bool
