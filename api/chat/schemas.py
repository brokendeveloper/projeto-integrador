from typing import Literal
from pydantic import BaseModel, Field


class MensagemHistorico(BaseModel):
    role: Literal["user", "assistant"] = Field(..., description="Autor da mensagem")
    content: str = Field(..., description="Conteúdo da mensagem")


class ChatRequest(BaseModel):
    mensagem: str = Field(..., description="Pergunta ou mensagem do usuário")
    historico: list[MensagemHistorico] = Field(
        default_factory=list,
        description="Histórico anterior da conversa (opcional, para manter contexto)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "mensagem": "Quais editais posso participar com meu CNPJ de serviços de TI?",
                "historico": [],
            }
        }
    }


class ChatResponse(BaseModel):
    resposta: str = Field(..., description="Resposta gerada pelo assistente IA")
    ferramentas_usadas: list[str] = Field(
        default_factory=list,
        description="Nomes das ferramentas MCP invocadas para gerar esta resposta",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "resposta": (
                    "Encontrei 12 contratos de TI com valor até R$ 80.000. "
                    "O mais recente é da Prefeitura de Caruaru, publicado em 15/05/2025, "
                    "no valor de R$ 45.000. Quer ver os detalhes?"
                ),
                "ferramentas_usadas": ["contratos_favoraveis_mei"],
            }
        }
    }
