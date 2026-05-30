from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from api.dependencies import get_db, get_usuario_atual
from .schemas import ChatRequest, ChatResponse
from .service import processar_mensagem

router = APIRouter(prefix="/chat", tags=["💬 Assistente"])


@router.post(
    "/mensagem",
    response_model=ChatResponse,
    summary="Enviar mensagem ao assistente IA",
    description=(
        "Envia uma mensagem ao assistente baseado em Claude (Anthropic). "
        "O assistente tem acesso às ferramentas MCP do projeto e pode consultar "
        "a base de contratos PNCP para responder perguntas sobre licitações, "
        "órgãos, valores e oportunidades para MEIs. "
        "\n\n**Exemplos de perguntas:**\n"
        "- *Quantos contratos temos na base?*\n"
        "- *Quais contratos posso participar como MEI?*\n"
        "- *Busque contratos de serviços de limpeza.*\n"
        "- *Quais órgãos publicam mais contratos?*\n\n"
        "O campo `historico` é opcional e permite manter o contexto de conversas anteriores."
    ),
)
async def mensagem(
    body: ChatRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    _: dict = Depends(get_usuario_atual),
):
    return await processar_mensagem(body, db)
