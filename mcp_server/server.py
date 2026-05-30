
import asyncio
import json
import os
from typing import Any

import pymongo
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

load_dotenv()

app = Server("mei-licitacoes")


# ── Helpers MongoDB ────────────────────────────────────────────────────────────

def _get_collection() -> tuple[pymongo.MongoClient, pymongo.collection.Collection]:
    """Abre conexão com o MongoDB e retorna (client, collection)."""
    uri = os.getenv("MONGODB_URI", "")
    db_name = os.getenv("MONGODB_DB", "pncp_etl")
    col_name = os.getenv("MONGODB_COLLECTION", "contratos")
    client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
    return client, client[db_name][col_name]


def _doc_resumido(doc: dict[str, Any]) -> dict[str, Any]:
    """Extrai os campos principais de um contrato para exibição."""
    orgao = doc.get("orgaoEntidade") or {}
    return {
        "numero_controle": doc.get("numeroControlePNCP"),
        "objeto": doc.get("objetoContrato"),
        "valor_inicial": doc.get("valorInicial"),
        "valor_global": doc.get("valorGlobal"),
        "orgao": orgao.get("razaoSocial"),
        "data_publicacao": doc.get("dataPublicacaoPncp"),
        "data_vigencia_fim": doc.get("dataVigenciaFim"),
    }


# ── Registro das ferramentas ───────────────────────────────────────────────────

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """Retorna a lista de ferramentas disponíveis no servidor MCP."""
    return [
        types.Tool(
            name="buscar_contratos",
            description=(
                "Busca contratos públicos (PNCP) por palavra-chave no objeto/descrição. "
                "Retorna uma lista com número de controle, objeto, valor e órgão."
            ),
            inputSchema={
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
        types.Tool(
            name="estatisticas_contratos",
            description=(
                "Retorna estatísticas gerais da base de contratos: total de registros, "
                "valor médio, valor máximo e valor mínimo dos contratos."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="top_orgaos",
            description="Retorna os órgãos públicos com maior número de contratos publicados.",
            inputSchema={
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
        types.Tool(
            name="contratos_favoraveis_mei",
            description=(
                "Lista contratos com valor inicial igual ou inferior a R$ 80.000 — "
                "faixa favorável à participação de microempreendedores individuais (MEI)."
            ),
            inputSchema={
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


# ── Execução das ferramentas ───────────────────────────────────────────────────

@app.call_tool()
async def call_tool(
    name: str, arguments: dict[str, Any]
) -> list[types.TextContent]:
    """Executa a ferramenta solicitada e retorna o resultado como texto JSON."""
    client, col = _get_collection()
    try:
        if name == "buscar_contratos":
            palavra = arguments["palavra_chave"]
            limite = int(arguments.get("limite", 10))
            docs = list(
                col.find(
                    {"objetoContrato": {"$regex": palavra, "$options": "i"}},
                    {"_id": 0},
                ).limit(limite)
            )
            resultado = [_doc_resumido(d) for d in docs]
            texto = (
                f"Encontrados {len(resultado)} contrato(s) com '{palavra}':\n\n"
                + json.dumps(resultado, ensure_ascii=False, indent=2, default=str)
            )

        elif name == "estatisticas_contratos":
            total = col.count_documents({})
            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "media_valor": {"$avg": "$valorInicial"},
                        "max_valor": {"$max": "$valorInicial"},
                        "min_valor": {"$min": "$valorInicial"},
                        "total_com_valor": {
                            "$sum": {
                                "$cond": [{"$gt": ["$valorInicial", None]}, 1, 0]
                            }
                        },
                    }
                }
            ]
            stats = list(col.aggregate(pipeline))
            stats_data = stats[0] if stats else {}
            stats_data.pop("_id", None)
            resultado = {"total_contratos": total, **stats_data}
            texto = (
                "Estatísticas da base de contratos PNCP:\n\n"
                + json.dumps(resultado, ensure_ascii=False, indent=2, default=str)
            )

        elif name == "top_orgaos":
            n = int(arguments.get("n", 5))
            pipeline = [
                {
                    "$group": {
                        "_id": "$orgaoEntidade.razaoSocial",
                        "total_contratos": {"$sum": 1},
                        "valor_total": {"$sum": "$valorInicial"},
                    }
                },
                {"$sort": {"total_contratos": -1}},
                {"$limit": n},
            ]
            resultado = [
                {
                    "orgao": r.get("_id", "Desconhecido"),
                    "total_contratos": r["total_contratos"],
                    "valor_total_r$": round(r.get("valor_total") or 0, 2),
                }
                for r in col.aggregate(pipeline)
            ]
            texto = (
                f"Top {n} órgãos por número de contratos:\n\n"
                + json.dumps(resultado, ensure_ascii=False, indent=2, default=str)
            )

        elif name == "contratos_favoraveis_mei":
            limite = int(arguments.get("limite", 10))
            docs = list(
                col.find(
                    {"valorInicial": {"$gt": 0, "$lte": 80_000}},
                    {"_id": 0},
                )
                .sort("valorInicial", 1)
                .limit(limite)
            )
            resultado = [_doc_resumido(d) for d in docs]
            texto = (
                f"Contratos favoráveis ao MEI (≤ R$ 80.000) — {len(resultado)} encontrado(s):\n\n"
                + json.dumps(resultado, ensure_ascii=False, indent=2, default=str)
            )

        else:
            texto = f"Ferramenta '{name}' não reconhecida."

    except pymongo.errors.ConnectionFailure as exc:
        texto = f"Erro de conexão com o MongoDB: {exc}"
    finally:
        client.close()

    return [types.TextContent(type="text", text=texto)]


# ── Ponto de entrada ───────────────────────────────────────────────────────────

async def _main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(_main())
