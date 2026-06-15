"""Serviço MCP — mapeia nomes de ferramentas para funções de analytics."""

import json
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from api.analytics.service import (
    buscar_contratos_por_palavra,
    obter_contratos_mei,
    obter_estatisticas,
    obter_top_orgaos,
)
from .schemas import FerramentaInfo, InvocarResponse, ListaFerramentasResponse

# Definição estática das ferramentas (espelha mcp_server/server.py)
_FERRAMENTAS: list[FerramentaInfo] = [
    FerramentaInfo(
        name="buscar_contratos",
        description=(
            "Busca contratos públicos (PNCP) por palavra-chave no objeto/descrição. "
            "Retorna número de controle, objeto, valor e órgão."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "palavra_chave": {
                    "type": "string",
                    "description": "Palavra ou trecho a buscar na descrição do contrato",
                },
                "limite": {
                    "type": "integer",
                    "description": "Número máximo de resultados (padrão: 10)",
                    "default": 10,
                },
            },
            "required": ["palavra_chave"],
        },
    ),
    FerramentaInfo(
        name="estatisticas_contratos",
        description=(
            "Retorna estatísticas gerais da base: total de contratos, "
            "valor médio, máximo e mínimo."
        ),
        input_schema={"type": "object", "properties": {}},
    ),
    FerramentaInfo(
        name="top_orgaos",
        description="Retorna os órgãos públicos com maior número de contratos publicados.",
        input_schema={
            "type": "object",
            "properties": {
                "n": {
                    "type": "integer",
                    "description": "Quantidade de órgãos a retornar (padrão: 5)",
                    "default": 5,
                }
            },
        },
    ),
    FerramentaInfo(
        name="contratos_favoraveis_mei",
        description=(
            "Lista contratos com valor inicial ≤ R$ 80.000 — "
            "favoráveis à participação de microempreendedores individuais (MEI)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "limite": {
                    "type": "integer",
                    "description": "Número máximo de contratos a retornar (padrão: 10)",
                    "default": 10,
                }
            },
        },
    ),
]

_NOMES_VALIDOS = {f.name for f in _FERRAMENTAS}


def listar_ferramentas() -> ListaFerramentasResponse:
    return ListaFerramentasResponse(total=len(_FERRAMENTAS), ferramentas=_FERRAMENTAS)


async def invocar_ferramenta(
    nome: str, argumentos: dict[str, Any], db: AsyncIOMotorDatabase
) -> InvocarResponse:
    """Executa a ferramenta pelo nome e retorna o resultado serializado."""
    if nome not in _NOMES_VALIDOS:
        nomes = ", ".join(sorted(_NOMES_VALIDOS))
        return InvocarResponse(
            ferramenta=nome,
            resultado=f"Ferramenta '{nome}' não existe. Disponíveis: {nomes}",
            sucesso=False,
        )

    try:
        if nome == "buscar_contratos":
            palavra = argumentos.get("palavra_chave", "")
            if not palavra:
                return InvocarResponse(
                    ferramenta=nome,
                    resultado="Argumento 'palavra_chave' é obrigatório.",
                    sucesso=False,
                )
            limite = int(argumentos.get("limite", 10))
            docs = await buscar_contratos_por_palavra(db, palavra, limite)
            resultado = (
                f"{len(docs)} contrato(s) encontrado(s) com '{palavra}':\n"
                + json.dumps(docs, ensure_ascii=False, indent=2, default=str)
            )

        elif nome == "estatisticas_contratos":
            stats = await obter_estatisticas(db)
            resultado = json.dumps(stats.model_dump(), ensure_ascii=False, indent=2)

        elif nome == "top_orgaos":
            n = int(argumentos.get("n", 5))
            top = await obter_top_orgaos(db, n)
            resultado = json.dumps(top.model_dump(), ensure_ascii=False, indent=2)

        elif nome == "contratos_favoraveis_mei":
            limite = int(argumentos.get("limite", 10))
            mei = await obter_contratos_mei(db, limite)
            resultado = (
                f"{mei.total} contrato(s) favoráveis ao MEI (≤ R$ 80.000):\n"
                + json.dumps(mei.model_dump(), ensure_ascii=False, indent=2)
            )

        return InvocarResponse(ferramenta=nome, resultado=resultado, sucesso=True)

    except Exception as exc:
        return InvocarResponse(
            ferramenta=nome,
            resultado=f"Erro ao executar '{nome}': {exc}",
            sucesso=False,
        )
