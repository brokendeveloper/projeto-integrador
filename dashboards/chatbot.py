import json
import os
from typing import Any

import anthropic
import pymongo
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Configuração da página ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="LicitaME — Léo",
    page_icon="🦁",
    layout="centered",
)

# ── CSS personalizado ──────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Sora', sans-serif;
    }

    .leo-header {
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 18px 0 8px 0;
    }
    .leo-avatar {
        font-size: 2.8rem;
        line-height: 1;
    }
    .leo-title {
        font-size: 1.5rem;
        font-weight: 600;
        margin: 0;
        line-height: 1.2;
    }
    .leo-subtitle {
        font-size: 0.85rem;
        color: #888;
        margin: 0;
    }

    .suggestion-row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin: 12px 0 18px 0;
    }

    .disclaimer {
        font-size: 0.75rem;
        color: #aaa;
        text-align: center;
        margin-top: 24px;
        border-top: 1px solid #eee;
        padding-top: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Cabeçalho ─────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="leo-header">
        <div class="leo-avatar">🦁</div>
        <div>
            <p class="leo-title">Léo — LicitaME</p>
            <p class="leo-subtitle">Assistente de licitações para MEI · Dados reais do PNCP</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Ferramentas ────────────────────────────────────────────────────────────────
TOOLS: list[dict[str, Any]] = [
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
            "properties": {"n": {"type": "integer"}},
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
            "properties": {"limite": {"type": "integer"}},
        },
    },
]

_SYSTEM_PROMPT = """Você é o Léo, assistente da plataforma LicitaME.

QUEM É O LÉO
Léo ajuda Microempreendedores Individuais (MEIs) a descobrir oportunidades de licitação pública e a entender o que precisam fazer para participar. Léo não é um chatbot genérico — ele conhece as regras do jogo: a Lei 14.133/2021, os limites de faturamento do MEI e os documentos exigidos para habilitação.

TOM
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

# ── MongoDB ────────────────────────────────────────────────────────────────────

def _get_col() -> tuple[pymongo.MongoClient, pymongo.collection.Collection]:
    uri = os.getenv("MONGODB_URI", "")
    db_name = os.getenv("MONGODB_DB", "pncp_etl")
    col_name = os.getenv("MONGODB_COLLECTION", "contratos")
    client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
    return client, client[db_name][col_name]


def _doc_resumido(doc: dict[str, Any]) -> dict[str, Any]:
    orgao = doc.get("orgaoEntidade") or {}
    return {
        "numero_controle": doc.get("numeroControlePNCP"),
        "objeto": doc.get("objetoContrato"),
        "valor_inicial": doc.get("valorInicial"),
        "orgao": orgao.get("razaoSocial"),
        "data_publicacao": doc.get("dataPublicacaoPncp"),
    }


def executar_ferramenta(name: str, arguments: dict[str, Any]) -> str:
    try:
        client, col = _get_col()
    except Exception as exc:
        return f"Erro ao conectar ao MongoDB: {exc}"

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
            return (
                f"{len(resultado)} contrato(s) encontrado(s) com '{palavra}':\n"
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
                    }
                }
            ]
            stats = list(col.aggregate(pipeline))
            dados = stats[0] if stats else {}
            dados.pop("_id", None)
            resultado = {"total_contratos": total, **dados}
            return json.dumps(resultado, ensure_ascii=False, indent=2, default=str)

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
                    "valor_total_rs": round(r.get("valor_total") or 0, 2),
                }
                for r in col.aggregate(pipeline)
            ]
            return json.dumps(resultado, ensure_ascii=False, indent=2, default=str)

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
            return (
                f"{len(resultado)} contrato(s) favorável(is) ao MEI (≤ R$ 80.000):\n"
                + json.dumps(resultado, ensure_ascii=False, indent=2, default=str)
            )

        return f"Ferramenta '{name}' não reconhecida."

    except Exception as exc:
        return f"Erro ao executar ferramenta '{name}': {exc}"
    finally:
        client.close()


# ── Agente com tool calling ────────────────────────────────────────────────────

def executar_agente(mensagens: list[dict[str, Any]]) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return "Erro: ANTHROPIC_API_KEY não definida no arquivo .env."

    cliente = anthropic.Anthropic(api_key=api_key)
    msgs = list(mensagens)

    while True:
        resposta = cliente.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=_SYSTEM_PROMPT,
            tools=TOOLS,
            messages=msgs,
        )

        if resposta.stop_reason == "end_turn":
            textos = [b.text for b in resposta.content if hasattr(b, "text")]
            return "\n".join(textos)

        if resposta.stop_reason == "tool_use":
            msgs.append({"role": "assistant", "content": resposta.content})
            resultados_tools = []
            for bloco in resposta.content:
                if bloco.type == "tool_use":
                    resultado = executar_ferramenta(bloco.name, bloco.input)
                    resultados_tools.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": bloco.id,
                            "content": resultado,
                        }
                    )
            msgs.append({"role": "user", "content": resultados_tools})
            continue

        break

    return "Não foi possível obter uma resposta."


# ── Estado da sessão ───────────────────────────────────────────────────────────

if "historico" not in st.session_state:
    st.session_state.historico: list[dict[str, str]] = []

# ── Saudação inicial ───────────────────────────────────────────────────────────

if not st.session_state.historico:
    with st.chat_message("assistant", avatar="🦁"):
        st.markdown(
            "Olá! Sou o **Léo**, seu guia em licitações públicas. "
            "Posso te ajudar a encontrar contratos compatíveis com o seu MEI, "
            "entender os documentos necessários e muito mais.\n\n"
            "Por onde quer começar?"
        )

# ── Sugestões de perguntas ─────────────────────────────────────────────────────

SUGESTOES = [
    "Quais contratos posso participar como MEI?",
    "Quantos contratos temos na base?",
    "Quais órgãos publicam mais contratos?",
    "Busque contratos de limpeza",
]

if not st.session_state.historico:
    cols = st.columns(len(SUGESTOES))
    for col, sugestao in zip(cols, SUGESTOES):
        if col.button(sugestao, use_container_width=True):
            st.session_state._sugestao_selecionada = sugestao
            st.rerun()

# ── Processar sugestão clicada ─────────────────────────────────────────────────

if "_sugestao_selecionada" in st.session_state:
    pergunta_inicial = st.session_state.pop("_sugestao_selecionada")
    st.session_state.historico.append({"role": "user", "content": pergunta_inicial})
    with st.chat_message("user"):
        st.markdown(pergunta_inicial)
    msgs_api = [{"role": m["role"], "content": m["content"]} for m in st.session_state.historico]
    with st.chat_message("assistant", avatar="🦁"):
        with st.spinner("Léo está buscando..."):
            resposta = executar_agente(msgs_api)
        st.markdown(resposta)
    st.session_state.historico.append({"role": "assistant", "content": resposta})

# ── Histórico de mensagens ─────────────────────────────────────────────────────

for msg in st.session_state.historico:
    avatar = "🦁" if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# ── Campo de entrada ───────────────────────────────────────────────────────────

pergunta = st.chat_input("Digite sua pergunta sobre licitações...")

if pergunta:
    with st.chat_message("user"):
        st.markdown(pergunta)
    st.session_state.historico.append({"role": "user", "content": pergunta})

    msgs_api = [{"role": m["role"], "content": m["content"]} for m in st.session_state.historico]

    with st.chat_message("assistant", avatar="🦁"):
        with st.spinner("Léo está buscando..."):
            resposta = executar_agente(msgs_api)
        st.markdown(resposta)

    st.session_state.historico.append({"role": "assistant", "content": resposta})

# ── Limpar conversa ────────────────────────────────────────────────────────────

if st.session_state.historico:
    if st.button("🗑️ Limpar conversa", type="secondary"):
        st.session_state.historico = []
        st.rerun()

# ── Rodapé ─────────────────────────────────────────────────────────────────────

st.markdown(
    """
    <div class="disclaimer">
        Léo é um assistente informativo e não substitui consultoria jurídica ou contábil.<br>
        Dados do <strong>PNCP</strong> · Lei 14.133/2021 · LC 123/2006, Art. 48 · LGPD
    </div>
    """,
    unsafe_allow_html=True,
)
