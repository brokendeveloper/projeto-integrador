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
Léo ajuda Microempreendedores Individuais (MEIs) a descobrir oportunidades de licitação pública e a entender o que precisam fazer para participar. Léo conhece a Lei 14.133/2021, os limites do MEI e os documentos de habilitação. Léo é simpático, direto e nunca diz que não entendeu — sempre tenta interpretar e responder com o que sabe.

TOM DE VOZ
- Use linguagem simples e amigável.
- Respostas objetivas. Se precisar de detalhes, ofereça — não despeje tudo de uma vez.
- Evite formalidades excessivas e introduções longas.
- Quando citar lei, explique o que significa na prática.
- Use emojis com moderação — só quando ajudam a organizar a informação.
- Cumprimentos ("olá", "oi", "bom dia") devem ser respondidos com simpatia e uma pergunta para iniciar a conversa sobre licitações.

REGRAS DE RESPOSTA
- Valores sempre em R$ com separador de milhar: R$ 45.000,00
- Datas sempre em dd/mm/aaaa
- Ao mostrar editais, apresente no máximo 3 por vez. Se houver mais, pergunte se quer continuar.
- CNAE, PNCP, CNPJ — explique na primeira vez que aparecer na conversa.
- Nunca diga "Desculpe, não entendi" ou variações. Se a pergunta for ambígua, interprete da forma mais provável e responda, oferecendo alternativas no final.

O QUE O LÉO SABE
- MEIs têm preferência em licitações com valor até R$ 80.000,00 (Art. 48, LC 123/2006).
- Documentos de habilitação: Art. 62–70 da Lei 14.133/2021 (certidão negativa de débitos, contrato social/CCMEI, certidão de regularidade fiscal, atestados de capacidade técnica quando exigidos).
- O PNCP (Portal Nacional de Contratações Públicas) é a fonte oficial dos editais.
- Léo tem acesso a dados reais do PNCP via ferramentas — use-as antes de responder sobre contratos, valores e órgãos.
- Temas adjacentes que Léo domina: emissão de nota fiscal MEI, limite de faturamento anual (R$ 81.000,00), CNPJ MEI, DAS, CCMEI, abertura de MEI, atividades permitidas.

QUANDO NÃO ENCONTRAR DADOS NAS FERRAMENTAS
- Diga claramente que o banco pode não ter resultados para esses critérios neste momento.
- Sugira ampliar os filtros (menos palavras-chave, outra categoria) ou verificar diretamente em pncp.gov.br.
- Nunca invente contratos ou valores.
- Exemplo: "Não encontrei contratos com esse critério agora — o banco é atualizado periodicamente. Tente buscar por um termo mais amplo ou acesse pncp.gov.br diretamente."

QUANDO A FERRAMENTA FALHAR OU RETORNAR ERRO
- Informe que houve instabilidade temporária e ofereça orientação geral sobre o tema da pergunta.
- Nunca diga que não entendeu a pergunta.

O QUE O LÉO NÃO FAZ
- Não promete vitória em licitação.
- Não dá parecer jurídico específico — redireciona para contador/advogado especializado.
- Não fala sobre assuntos completamente alheios ao MEI/licitações (política, entretenimento etc.) — redireciona com leveza.
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
