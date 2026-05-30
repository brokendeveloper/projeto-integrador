"""Serviço de chat — integra Claude (Anthropic) com as ferramentas MCP via tool calling."""

import os
from typing import Any

import anthropic
from motor.motor_asyncio import AsyncIOMotorDatabase

from api.analytics.service import (
    buscar_contratos_por_palavra,
    obter_contratos_mei,
    obter_estatisticas,
    obter_top_orgaos,
)
from .schemas import ChatRequest, ChatResponse

# Definição das tools para o Claude (idêntica à do chatbot Streamlit)
_TOOLS: list[dict[str, Any]] = [
    {
        "name": "buscar_contratos",
        "description": (
            "Busca contratos públicos (PNCP) por palavra-chave no objeto/descrição. "
            "Retorna número de controle, objeto, valor e órgão."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "palavra_chave": {"type": "string"},
                "limite": {"type": "integer"},
            },
            "required": ["palavra_chave"],
        },
    },
    {
        "name": "estatisticas_contratos",
        "description": (
            "Retorna estatísticas gerais da base: total de contratos, "
            "valor médio, máximo e mínimo."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "top_orgaos",
        "description": "Retorna os órgãos públicos com maior número de contratos publicados.",
        "input_schema": {
            "type": "object",
            "properties": {
                "n": {"type": "integer"},
            },
        },
    },
    {
        "name": "contratos_favoraveis_mei",
        "description": (
            "Lista contratos com valor inicial ≤ R$ 80.000, "
            "favoráveis à participação de microempreendedores individuais (MEI)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limite": {"type": "integer"},
            },
        },
    },
]

_SYSTEM_PROMPT = """Você é o Léo, assistente da plataforma LicitaME.

QUEM É O LÉO
Léo ajuda Microempreendedores Individuais (MEIs) a descobrir oportunidades de licitação pública e a entender o que precisam fazer para participar. Léo não é um chatbot genérico — ele conhece as regras do jogo: a Lei 14.133/2021, os limites de faturamento do MEI e os documentos exigidos para habilitação.

TOM DE VOZ
- Use linguagem simples. O MEI não é advogado nem técnico de TI.
- Respostas curtas são melhores que longas. Se precisar de detalhes, ofereça, não despeje.
- Seja objetivo e útil. Evite introduções longas ("Claro! Com prazer vou te ajudar...").
- Quando citar artigos de lei, explique o que eles significam na prática.
- Use emojis com moderação — apenas quando ajudam a separar informações, não para enfeitar.

REGRAS DE RESPOSTA
- Valores sempre em R$ com separador de milhar: R$ 45.000,00
- Datas sempre em dd/mm/aaaa
- Ao mostrar editais, apresente no máximo 3 por vez. Se houver mais, pergunte se quer continuar.
- CNAE, PNCP, CNPJ — explique o que significa na primeira vez que aparecer na conversa.
- Nunca repita o que o usuário acabou de dizer para "confirmar que entendeu".

O QUE O LÉO SABE
- MEIs têm preferência em licitações com valor até R$ 80.000,00 (Art. 48, LC 123/2006).
- Os documentos de habilitação são definidos pela Lei 14.133/2021 (Arts. 62–70).
- O PNCP (Portal Nacional de Contratações Públicas) é a fonte oficial dos editais.
- Léo tem acesso a dados reais do PNCP via ferramentas de busca.

O QUE O LÉO NÃO FAZ
- Não promete que o MEI vai ganhar a licitação.
- Não dá parecer jurídico. Para dúvidas legais específicas: "Recomendo consultar um contador ou advogado especializado em licitações."
- Não inventa dados. Se não encontrar resultados, diz claramente.
- Não responde sobre assuntos fora do tema licitações/MEI. Redireciona educadamente.

QUANDO NÃO ENCONTRAR DADOS
Diga: "Não encontrei editais com esses critérios agora. O banco é atualizado periodicamente com dados do PNCP — tente ampliar os filtros ou verificar diretamente em pncp.gov.br."
"""


async def _executar_tool(
    nome: str, argumentos: dict[str, Any], db: AsyncIOMotorDatabase
) -> str:
    """Executa a tool invocada pelo Claude e retorna o resultado como string."""
    import json

    try:
        if nome == "buscar_contratos":
            palavra = argumentos.get("palavra_chave", "")
            limite = int(argumentos.get("limite", 10))
            docs = await buscar_contratos_por_palavra(db, palavra, limite)
            return f"{len(docs)} resultado(s):\n" + json.dumps(
                docs, ensure_ascii=False, indent=2, default=str
            )

        elif nome == "estatisticas_contratos":
            stats = await obter_estatisticas(db)
            return json.dumps(stats.model_dump(), ensure_ascii=False, indent=2)

        elif nome == "top_orgaos":
            n = int(argumentos.get("n", 5))
            top = await obter_top_orgaos(db, n)
            return json.dumps(top.model_dump(), ensure_ascii=False, indent=2)

        elif nome == "contratos_favoraveis_mei":
            limite = int(argumentos.get("limite", 10))
            mei = await obter_contratos_mei(db, limite)
            return json.dumps(mei.model_dump(), ensure_ascii=False, indent=2)

        return f"Ferramenta '{nome}' não reconhecida."

    except Exception as exc:
        return f"Erro ao executar '{nome}': {exc}"


async def processar_mensagem(
    payload: ChatRequest, db: AsyncIOMotorDatabase
) -> ChatResponse:
    """Envia a mensagem ao Claude e resolve tool calls em loop até obter resposta final."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return ChatResponse(
            resposta="Erro de configuração: ANTHROPIC_API_KEY não definida no servidor.",
            ferramentas_usadas=[],
        )

    cliente = anthropic.AsyncAnthropic(api_key=api_key)

    # Montar histórico no formato da API Anthropic
    msgs: list[dict[str, Any]] = [
        {"role": m.role, "content": m.content} for m in payload.historico
    ]
    msgs.append({"role": "user", "content": payload.mensagem})

    ferramentas_usadas: list[str] = []

    while True:
        resposta = await cliente.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=_SYSTEM_PROMPT,
            tools=_TOOLS,
            messages=msgs,
        )

        if resposta.stop_reason == "end_turn":
            textos = [b.text for b in resposta.content if hasattr(b, "text")]
            return ChatResponse(
                resposta="\n".join(textos),
                ferramentas_usadas=ferramentas_usadas,
            )

        if resposta.stop_reason == "tool_use":
            msgs.append({"role": "assistant", "content": resposta.content})

            resultados: list[dict[str, Any]] = []
            for bloco in resposta.content:
                if bloco.type == "tool_use":
                    ferramentas_usadas.append(bloco.name)
                    resultado = await _executar_tool(bloco.name, bloco.input, db)
                    resultados.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": bloco.id,
                            "content": resultado,
                        }
                    )

            msgs.append({"role": "user", "content": resultados})
            continue

        # stop_reason inesperado
        return ChatResponse(
            resposta="Não foi possível obter uma resposta do assistente.",
            ferramentas_usadas=ferramentas_usadas,
        )
