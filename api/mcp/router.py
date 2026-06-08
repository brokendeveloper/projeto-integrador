from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from api.dependencies import get_db, get_usuario_atual
from .schemas import InvocarRequest, InvocarResponse, ListaFerramentasResponse
from .service import invocar_ferramenta, listar_ferramentas

router = APIRouter(prefix="/mcp", tags=["🤖 MCP"])


@router.get(
    "/ferramentas",
    response_model=ListaFerramentasResponse,
    summary="Listar ferramentas MCP disponíveis",
    description=(
        "Retorna a lista completa de ferramentas expostas pelo servidor MCP deste projeto, "
        "com nome, descrição e JSON Schema dos argumentos aceitos. "
        "Estas ferramentas são idênticas às registradas em `mcp_server/server.py`."
    ),
)
async def ferramentas(
    _: dict = Depends(get_usuario_atual),
):
    return listar_ferramentas()


@router.post(
    "/invocar",
    response_model=InvocarResponse,
    summary="Invocar uma ferramenta MCP",
    description=(
        "Executa uma ferramenta MCP pelo nome, passando os argumentos necessários. "
        "Consulta o MongoDB Atlas e retorna o resultado em formato texto/JSON. "
        "\n\nFerramentas disponíveis: `buscar_contratos`, `estatisticas_contratos`, "
        "`top_orgaos`, `contratos_favoraveis_mei`."
    ),
)
async def invocar(
    body: InvocarRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    _: dict = Depends(get_usuario_atual),
):
    return await invocar_ferramenta(body.ferramenta, body.argumentos, db)
