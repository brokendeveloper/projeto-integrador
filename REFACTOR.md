# REFACTOR.md — LicitaME
## Plano completo de identidade, UX e polish

> Execute este arquivo com o Claude Code após o CLAUDE.md já ter sido aplicado.
> Siga as fases na ordem. Cada fase é independente e pode ser executada em um dia separado.
> Ao terminar cada fase, peça confirmação antes de avançar.

---

## Contexto

Este documento cobre as mudanças de identidade e qualidade do projeto — tudo que não é lógica de negócio, mas que determina se o projeto parece profissional ou gerado por IA.

**Nome escolhido:** LicitaME  
**Assistente do chatbot:** Léo  
**Tom de voz:** direto, simples, sem jargão — voltado para MEI, não para desenvolvedor

---

## Convenção de commits (igual ao CLAUDE.md)

```
<tipo>(<escopo>): <descrição em português, imperativo>
```

Escopos deste refactor: `identity`, `swagger`, `chat`, `dashboard`, `mobile`, `ux`

Exemplos:
```
refactor(identity): renomear aplicação para LicitaME em todos os módulos
feat(swagger): substituir OAuth2PasswordBearer por HTTPBearer
refactor(chat): reescrever system prompt com persona Léo
style(dashboard): aplicar fonte Sora e reorganizar cards por marco
ux(api): humanizar mensagens de erro de autenticação
```

---

---

# FASE R1 — Identidade: renomear para LicitaME

**Objetivo:** O nome LicitaME aparece de forma consistente em todos os pontos de contato — Swagger, dashboards, mobile, README e código.

**Tempo estimado:** 30–45 minutos.

**Regra:** não mude lógica de negócio. Apenas strings, títulos e metadados.

---

## R1.1 — `api/main.py` — metadados da API

Substitua o bloco de criação do `FastAPI(...)` pelo seguinte:

```python
app = FastAPI(
    title="LicitaME API",
    version="1.0.0",
    description="""
## Sobre a plataforma

**LicitaME** conecta Microempreendedores Individuais (MEIs) a oportunidades reais
de licitação pública — com base nos dados do Portal Nacional de Contratações Públicas (PNCP).

## Como usar esta API

1. Crie sua conta em `POST /auth/register`
2. Faça login em `POST /auth/login` e copie o `access_token`
3. Clique em **Authorize** (canto superior direito) e cole o token
4. Todos os demais endpoints estarão liberados

## Base legal

| Lei | Relevância |
|-----|-----------|
| Lei nº 14.133/2021 | Nova Lei de Licitações — define os requisitos de habilitação |
| LC 123/2006 | Estatuto da ME e MEI — garante preferência em licitações até R$ 80.000 |
| LGPD — Lei 13.709/2018 | Proteção de dados pessoais dos usuários |

## Projeto

Desenvolvido como projeto integrador do 5º período de ADS — CESAR School, Recife-PE.
""",
    contact={
        "name": "Equipe LicitaME — CESAR School",
        "url": "https://github.com/brokendeveloper/projeto-integrador",
    },
    license_info={
        "name": "Projeto Acadêmico — ADS 5º Período · 2025",
    },
    openapi_tags=[
        {"name": "🔐 Autenticação",  "description": "Cadastro e login de usuários MEI"},
        {"name": "📄 Editais",       "description": "Busca e filtro de contratos do PNCP com indicação de oportunidades para MEI"},
        {"name": "✅ Checklist",     "description": "Requisitos de habilitação baseados na Lei 14.133/2021, com progresso por edital"},
        {"name": "📁 Documentos",    "description": "Upload e gestão de documentos de habilitação por edital"},
        {"name": "🔔 Alertas",       "description": "Alertas personalizados de novos editais por CNAE, valor e região"},
        {"name": "📊 Histórico",     "description": "Participações em licitações e métricas de desempenho do MEI"},
        {"name": "🛡️ LGPD",         "description": "Portabilidade e exclusão de dados pessoais conforme a LGPD"},
        {"name": "📈 Analytics",     "description": "Estatísticas e análise dos contratos do PNCP"},
        {"name": "🤖 MCP",           "description": "Ferramentas do Model Context Protocol para integração com agentes IA"},
        {"name": "💬 Assistente",    "description": "Léo — assistente IA especializado em licitações para MEI"},
        {"name": "⚙️ Sistema",       "description": "Endpoints de infraestrutura"},
    ],
)
```

Atualize também o endpoint de health check para excluí-lo do Swagger público:

```python
@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok", "service": "LicitaME API", "version": "1.0.0"}
```

Commit:
```
refactor(identity): atualizar metadados da API para LicitaME com tags descritivas
```

---

## R1.2 — Todos os routers — atualizar o parâmetro `tags`

Em cada `router.py`, o parâmetro `tags` do `APIRouter` deve bater com as novas tags do `main.py`.

```python
# api/auth/router.py
router = APIRouter(prefix="/auth", tags=["🔐 Autenticação"])

# api/editais/router.py
router = APIRouter(prefix="/editais", tags=["📄 Editais"])

# api/checklist/router.py
router = APIRouter(prefix="/editais/{edital_id}/checklist", tags=["✅ Checklist"])

# api/documentos/router.py
router = APIRouter(prefix="/editais/{edital_id}/documentos", tags=["📁 Documentos"])

# api/alertas/router.py
router = APIRouter(prefix="/alertas", tags=["🔔 Alertas"])

# api/historico/router.py
router = APIRouter(prefix="/historico", tags=["📊 Histórico"])

# api/lgpd/router.py
router = APIRouter(prefix="/lgpd", tags=["🛡️ LGPD"])

# api/analytics/router.py
router = APIRouter(prefix="/analytics", tags=["📈 Analytics"])

# api/mcp/router.py
router = APIRouter(prefix="/mcp", tags=["🤖 MCP"])

# api/chat/router.py
router = APIRouter(prefix="/chat", tags=["💬 Assistente"])
```

Commit:
```
refactor(identity): alinhar tags dos routers com as seções do Swagger
```

---

## R1.3 — `dashboards/apresentacao.py` — trocar nome e título

Localize todas as ocorrências de `"MEI Licitações"` e `"MEI Licitacoes"` e substitua por `"LicitaME"`.

Localize o título principal e substitua:
```python
# ANTES
st.markdown("## 📋 MEI Licitações — Painel de Andamento")

# DEPOIS
st.markdown("## LicitaME — Painel de Andamento do Projeto")
```

Localize o `st.set_page_config` e atualize:
```python
st.set_page_config(
    page_title="LicitaME — Andamento do Projeto",
    page_icon="⚖️",   # ícone mais específico que 📋
    layout="wide",
)
```

Commit:
```
refactor(identity): renomear MEI Licitações para LicitaME no dashboard de apresentação
```

---

## R1.4 — `dashboards/dashboard.py` e `dashboards/chatbot.py` — título e page_config

Em `dashboard.py`:
```python
st.set_page_config(
    page_title="LicitaME — Analytics",
    page_icon="📈",
    layout="wide",
)
st.title("📈 LicitaME — Análise de Contratos PNCP")
```

Em `chatbot.py`:
```python
st.set_page_config(
    page_title="LicitaME — Léo",
    page_icon="⚖️",
    layout="centered",
)
```

Commit:
```
refactor(identity): atualizar títulos e page_config dos dashboards para LicitaME
```

---

## R1.5 — `README.md` — atualizar nome e descrição

O README deve refletir o nome LicitaME. Atualize pelo menos:

- Título principal (`# LicitaME`)
- Primeira linha de descrição
- Qualquer menção a "MEI Licitações" no corpo do texto

Não reescreva o README inteiro — apenas substitua o nome. O conteúdo técnico permanece.

Commit:
```
docs(identity): atualizar README com nome LicitaME
```

---

---

# FASE R2 — Swagger: corrigir autenticação e summaries

**Objetivo:** O Swagger para de dar erro de 422 no botão Authorize. Os endpoints têm summaries em linguagem de produto, não de documentação técnica.

**Tempo estimado:** 1–2 horas.

---

## R2.1 — `api/auth/security.py` — substituir OAuth2 por HTTPBearer

Este é o ponto que causa o formulário confuso com `username/password` no Swagger.

Substitua o arquivo inteiro pelo seguinte:

```python
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTPBearer gera no Swagger um campo único "Value" onde o usuário cola o token.
# Não gera os campos username/password/client_id que causavam o erro 422.
_bearer_scheme = HTTPBearer(
    scheme_name="Bearer Token",
    description="Cole o token retornado em POST /auth/login. Formato: o token puro, sem 'Bearer '.",
)


def hash_senha(senha: str) -> str:
    return pwd_context.hash(senha)


def verificar_senha(senha: str, hash: str) -> bool:
    return pwd_context.verify(senha, hash)


def criar_token(data: dict) -> str:
    payload = data.copy()
    expira = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload["exp"] = expira
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> str:
    token = credentials.credentials
    excecao = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado. Faça login novamente.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise excecao
        return user_id
    except JWTError:
        raise excecao
```

Commit:
```
feat(swagger): substituir OAuth2PasswordBearer por HTTPBearer para corrigir erro 422 no Authorize
```

---

## R2.2 — `api/auth/router.py` — adicionar summaries e descriptions

```python
@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=201,
    summary="Criar conta",
    description="""
Cria uma nova conta de MEI na plataforma.

- O CNPJ deve ter 14 dígitos (com ou sem formatação)
- A senha deve ter no mínimo 8 caracteres
- Após o cadastro, o token de acesso é retornado imediatamente (sem precisar fazer login separado)
""",
)
async def register(...):
    ...


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Entrar na conta",
    description="""
Autentica o usuário e retorna o token de acesso JWT.

**Como usar o token no Swagger:**
1. Copie o valor do campo `access_token` da resposta
2. Clique em **Authorize** no topo da página
3. Cole o token no campo **Value** (sem digitar "Bearer")
4. Clique em Authorize — todos os endpoints autenticados estarão liberados
""",
)
async def login(...):
    ...
```

Commit:
```
docs(swagger): adicionar instruções de autenticação nos endpoints de login e registro
```

---

## R2.3 — `api/editais/router.py` — summaries em linguagem de produto

```python
@router.get(
    "",
    response_model=PaginacaoResponse,
    summary="Buscar editais",
    description="""
Retorna editais do PNCP com filtros opcionais.

O campo `favoravel_mei` indica se o edital tem valor ≤ R$ 80.000 —
limite que garante ao MEI tratamento diferenciado pela Lei 14.133/2021.

**Filtros disponíveis:**
- `cnae` — filtra pelo código de atividade do MEI
- `valor_max` — teto de valor em R$ (ex: `80000` para ver só os favoráveis)
- `regiao` — município ou estado (busca por texto)
""",
)

@router.get(
    "/{edital_id}",
    response_model=EditalDetalhe,
    summary="Ver detalhes do edital",
    description="Retorna todos os campos de um edital específico, incluindo URL do edital original no PNCP.",
)
```

Commit:
```
docs(swagger): reescrever summaries dos endpoints de editais em linguagem de produto
```

---

## R2.4 — `api/checklist/router.py` — summaries

```python
@router.get(
    "",
    summary="Ver checklist do edital",
    description="""
Retorna os requisitos de habilitação para participar deste edital,
com o progresso atual do usuário.

Os requisitos são baseados na **Lei 14.133/2021** e na **LC 123/2006**.
Usuários do plano gratuito veem os requisitos obrigatórios.
Usuários premium têm acesso ao checklist completo.
""",
)

@router.patch(
    "",
    summary="Marcar requisito como concluído",
    description="Atualiza o status de um requisito do checklist. O progresso é salvo por usuário e por edital.",
)
```

Commit:
```
docs(swagger): reescrever summaries do checklist em linguagem de produto
```

---

## R2.5 — Demais routers — summaries mínimos

Para cada router restante, adicione pelo menos o parâmetro `summary` em cada endpoint. Use linguagem direta:

| Endpoint | Summary |
|---|---|
| POST /documentos | "Enviar documento" |
| GET /documentos | "Ver documentos enviados" |
| DELETE /documentos/{id} | "Remover documento" |
| POST /alertas | "Criar alerta de edital" |
| GET /alertas | "Ver meus alertas" |
| DELETE /alertas/{id} | "Remover alerta" |
| POST /historico | "Registrar participação" |
| GET /historico | "Ver histórico de participações" |
| GET /historico/resumo | "Ver resumo por resultado" |
| GET /lgpd/meus-dados | "Exportar meus dados" |
| DELETE /lgpd/minha-conta | "Excluir minha conta" |
| GET /analytics/estatisticas | "Estatísticas gerais dos contratos" |
| GET /analytics/top-orgaos | "Órgãos que mais publicam" |
| GET /analytics/contratos-mei | "Editais favoráveis ao MEI" |
| POST /analytics/executar-spark | "Rodar análise PySpark" |
| GET /mcp/ferramentas | "Listar ferramentas disponíveis" |
| POST /mcp/invocar | "Invocar ferramenta MCP" |
| POST /chat/mensagem | "Conversar com o Léo" |

Commit:
```
docs(swagger): adicionar summaries em linguagem de produto em todos os endpoints
```

---

---

# FASE R3 — Chatbot: persona Léo

**Objetivo:** O chatbot tem nome, tom de voz definido e interface que não parece demo do Streamlit.

**Tempo estimado:** 1–2 horas.

---

## R3.1 — `api/chat/service.py` — reescrever system prompt

Localize a constante ou string do system prompt. Substitua completamente pelo seguinte:

```python
SYSTEM_PROMPT = """Você é o Léo, assistente da plataforma LicitaME.

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
```

Commit:
```
refactor(chat): reescrever system prompt com persona Léo, tom e limitações definidos
```

---

## R3.2 — `api/chat/service.py` — atualizar nome do modelo

Verifique a linha que define o modelo. Certifique-se de usar:

```python
model="claude-sonnet-4-6",
max_tokens=1024,   # não precisa de mais para respostas do chatbot
```

Commit:
```
refactor(chat): ajustar parâmetros do modelo de linguagem no serviço de chat
```

---

## R3.3 — `dashboards/chatbot.py` — redesenhar interface

Substitua o conteúdo do arquivo pelo seguinte, mantendo a lógica de `executar_agente()` intacta (apenas a interface muda):

```python
"""Chatbot Léo — LicitaME."""

import streamlit as st
from dashboards.chatbot_agent import executar_agente  # ajuste o import conforme seu arquivo atual

st.set_page_config(
    page_title="Léo — LicitaME",
    page_icon="⚖️",
    layout="centered",
)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Sora', sans-serif;
}

.leo-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 20px 0 8px 0;
    border-bottom: 1px solid rgba(128,128,128,0.15);
    margin-bottom: 20px;
}
.leo-avatar {
    width: 44px;
    height: 44px;
    background: linear-gradient(135deg, #1F3864, #2E5DA8);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    flex-shrink: 0;
}
.leo-info { display: flex; flex-direction: column; }
.leo-nome { font-size: 1rem; font-weight: 700; color: #1F3864; }
.leo-status { font-size: 0.78rem; color: #28a745; }
.leo-disclaimer {
    font-size: 0.75rem;
    color: rgba(128,128,128,0.7);
    text-align: center;
    padding: 12px 0 0 0;
    border-top: 1px solid rgba(128,128,128,0.1);
    margin-top: 16px;
}
.sugestao-titulo {
    font-size: 0.82rem;
    color: rgba(128,128,128,0.7);
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="leo-header">
    <div class="leo-avatar">⚖️</div>
    <div class="leo-info">
        <span class="leo-nome">Léo · LicitaME</span>
        <span class="leo-status">● online</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Estado da conversa ────────────────────────────────────────────────────────
if "historico" not in st.session_state:
    st.session_state.historico = []

if "iniciado" not in st.session_state:
    st.session_state.iniciado = False

# Mensagem inicial do Léo (aparece só uma vez)
if not st.session_state.iniciado:
    with st.chat_message("assistant", avatar="⚖️"):
        st.markdown(
            "Olá! Sou o **Léo**, assistente da LicitaME. "
            "Posso te ajudar a descobrir editais para o seu perfil, "
            "entender o que você precisa para participar de uma licitação "
            "ou ver quais órgãos estão contratando mais.\n\n"
            "Como posso te ajudar hoje?"
        )
    st.session_state.iniciado = True

# ── Histórico da conversa ─────────────────────────────────────────────────────
for msg in st.session_state.historico:
    avatar = "⚖️" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# ── Sugestões de perguntas (visíveis, não dentro de expander) ─────────────────
if len(st.session_state.historico) == 0:
    st.markdown('<div class="sugestao-titulo">Perguntas frequentes:</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    sugestoes = [
        "Quais editais posso participar como MEI?",
        "Quais documentos preciso para me habilitar?",
        "Quais órgãos mais publicam contratos?",
    ]
    for col, sugestao in zip([col1, col2, col3], sugestoes):
        with col:
            if st.button(sugestao, use_container_width=True, type="secondary"):
                st.session_state._sugestao_selecionada = sugestao
                st.rerun()

# Processar sugestão clicada
if hasattr(st.session_state, "_sugestao_selecionada"):
    pergunta = st.session_state._sugestao_selecionada
    del st.session_state._sugestao_selecionada

    st.session_state.historico.append({"role": "user", "content": pergunta})
    with st.chat_message("user", avatar="👤"):
        st.markdown(pergunta)

    with st.chat_message("assistant", avatar="⚖️"):
        with st.spinner("Léo está buscando..."):
            resposta = executar_agente(pergunta, st.session_state.historico[:-1])
        st.markdown(resposta)

    st.session_state.historico.append({"role": "assistant", "content": resposta})

# ── Input do usuário ──────────────────────────────────────────────────────────
if prompt := st.chat_input("Pergunte ao Léo sobre licitações..."):
    st.session_state.historico.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="⚖️"):
        with st.spinner("Léo está buscando..."):
            try:
                resposta = executar_agente(prompt, st.session_state.historico[:-1])
            except Exception:
                resposta = (
                    "Não consegui buscar os dados agora. "
                    "Tente novamente em instantes ou verifique diretamente em pncp.gov.br."
                )
        st.markdown(resposta)

    st.session_state.historico.append({"role": "assistant", "content": resposta})

# ── Disclaimer ────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="leo-disclaimer">'
    "Léo pode cometer erros. Verifique os editais no PNCP antes de participar. "
    "Dúvidas jurídicas? Consulte um contador ou advogado."
    "</div>",
    unsafe_allow_html=True,
)
```

**Atenção:** o import de `executar_agente` deve apontar para onde essa função está definida no seu código atual. Ajuste o caminho sem mudar a lógica interna da função.

Commit:
```
feat(chat): redesenhar interface do chatbot com persona Léo e sugestões visíveis
```

---

## R3.4 — `api/chat/schemas.py` — atualizar example do Swagger

```python
class ChatRequest(BaseModel):
    mensagem: str
    historico: list[dict] = []

    model_config = {
        "json_schema_extra": {
            "example": {
                "mensagem": "Quais editais posso participar com meu CNPJ de serviços de TI?",
                "historico": []
            }
        }
    }


class ChatResponse(BaseModel):
    resposta: str
    ferramentas_usadas: list[str] = []

    model_config = {
        "json_schema_extra": {
            "example": {
                "resposta": "Encontrei 12 contratos de TI com valor até R$ 80.000. O mais recente é da Prefeitura de Caruaru, publicado em 15/05/2025, no valor de R$ 45.000. Quer ver os detalhes?",
                "ferramentas_usadas": ["contratos_favoraveis_mei"]
            }
        }
    }
```

Commit:
```
docs(swagger): adicionar exemplos reais nos schemas do chatbot
```

---

---

# FASE R4 — Mensagens de erro: linguagem humana

**Objetivo:** Nenhuma mensagem de erro da API soa como documentação técnica ou log de sistema.

**Tempo estimado:** 30–45 minutos.

---

## R4.1 — `api/auth/service.py`

```python
# Registro — email duplicado
raise HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Esse e-mail já tem uma conta na LicitaME. Faça login ou use outro e-mail."
)

# Registro — CNPJ duplicado
raise HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Esse CNPJ já está cadastrado. Entre em contato se isso for um erro."
)

# Login — credenciais inválidas
raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="E-mail ou senha incorretos. Verifique e tente novamente."
)
```

Commit:
```
ux(api): humanizar mensagens de erro de registro e login
```

---

## R4.2 — `api/auth/security.py`

```python
# Token inválido ou expirado
excecao = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Sua sessão expirou. Faça login novamente para continuar.",
    headers={"WWW-Authenticate": "Bearer"},
)
```

Commit:
```
ux(api): humanizar mensagem de token expirado ou inválido
```

---

## R4.3 — `api/alertas/service.py`

```python
# Limite de alertas do plano free
raise HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail=(
        "Você atingiu o limite de 3 alertas do plano gratuito. "
        "Remova um alerta existente ou faça upgrade para o plano premium."
    ),
)
```

Commit:
```
ux(api): humanizar mensagem de limite de alertas do plano gratuito
```

---

## R4.4 — `api/documentos/service.py`

```python
# Tipo de arquivo não permitido
raise HTTPException(
    status_code=400,
    detail=(
        "Tipo de arquivo não aceito. "
        "Envie documentos em PDF, Word (.docx) ou imagens (JPG, PNG)."
    ),
)

# Arquivo muito grande
raise HTTPException(
    status_code=413,
    detail="O arquivo é muito grande. O limite é de 10 MB por documento."
)

# Sem permissão para excluir
raise HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Você não tem permissão para remover este documento."
)
```

Commit:
```
ux(api): humanizar mensagens de erro de upload e permissão de documentos
```

---

## R4.5 — `api/editais/service.py`

```python
# Edital não encontrado
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Edital não encontrado. Ele pode ter sido removido do PNCP."
)

# ID inválido
raise HTTPException(
    status_code=400,
    detail="ID de edital inválido. Verifique o formato e tente novamente."
)
```

Commit:
```
ux(api): humanizar mensagens de erro de edital não encontrado
```

---

---

# FASE R5 — Dashboard: visual menos genérico

**Objetivo:** O dashboard de apresentação (`apresentacao.py`) não parece template do Streamlit.

**Tempo estimado:** 1–2 horas.

---

## R5.1 — Fonte Sora e reset visual

No início do bloco `st.markdown("""<style>...""")` do `apresentacao.py`, adicione no topo do CSS existente:

```css
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700&display=swap');

html, body, [class*="css"], .stMarkdown, .stText {
    font-family: 'Sora', sans-serif !important;
}

/* Remover o padding padrão do Streamlit no topo */
.block-container { padding-top: 2rem !important; }

/* Linha divisória mais sutil */
hr.divider {
    border: none;
    border-top: 1px solid rgba(128,128,128,0.12);
    margin: 32px 0;
}
```

Commit:
```
style(dashboard): aplicar fonte Sora e ajustar espaçamento base
```

---

## R5.2 — Agrupar fases por marco (não lista linear)

As 11 fases exibidas em grid de 2 colunas parecem lista de tarefas. Agrupe-as em 4 marcos:

```python
MARCOS = [
    {
        "titulo": "🏗️ Marco 1 — Infraestrutura",
        "descricao": "Base de dados, pipeline ETL e API REST",
        "fases": [0, 1, 2],  # índices na lista FASES
    },
    {
        "titulo": "⚙️ Marco 2 — Funcionalidades Core",
        "descricao": "Autenticação, editais, checklist, documentos e alertas",
        "fases": [3, 4, 5, 6],
    },
    {
        "titulo": "🔒 Marco 3 — Qualidade e Segurança",
        "descricao": "LGPD, rate limiting, headers HTTP e CI/CD",
        "fases": [7, 8],
    },
    {
        "titulo": "📱 Marco 4 — Produto",
        "descricao": "App mobile e integração final",
        "fases": [9, 10],
    },
]
```

Para cada marco, renderize um subtítulo e depois as fases correspondentes. Isso mostra raciocínio de produto em vez de lista mecânica.

Commit:
```
style(dashboard): reorganizar fases em marcos de entrega com contexto de produto
```

---

## R5.3 — Seção da equipe com especialização real

Substitua a lista de membros com cargo genérico "Desenvolvedor(a)" pela versão com especialização real:

```python
MEMBROS = [
    {"nome": "Luccas Fernandes",  "cargo": "ETL & Engenharia de Dados"},
    {"nome": "Gabriel Nogueira",  "cargo": "ETL & DataOps"},
    {"nome": "Nathalia Pinto",    "cargo": "Backend & API"},
    {"nome": "Eduarda Leão",      "cargo": "Produto & Documentação"},
    {"nome": "Carlos",            "cargo": "Mobile & Frontend"},
]
```

Ajuste o cargo de cada pessoa para refletir o que cada um realmente fez no projeto.

Commit:
```
style(dashboard): atualizar cargos da equipe com especialização real de cada membro
```

---

## R5.4 — Remover barra de progresso padrão do Streamlit

O `st.progress(7/11, text="...")` é imediatamente reconhecível como Streamlit padrão. Substitua por uma representação em tabela CSS:

```python
# Substitua o st.progress() por:

concluidas = 7
total = 11
pct = int((concluidas / total) * 100)
segmentos_html = ""

for i in range(total):
    cor = "#2E5DA8" if i < concluidas else "rgba(128,128,128,0.15)"
    segmentos_html += f'<div style="flex:1;height:12px;background:{cor};border-radius:3px;margin:0 2px;"></div>'

st.markdown(f"""
<div style="margin-bottom:8px;">
    <span style="font-weight:600;color:#1F3864;">{concluidas} de {total} fases concluídas</span>
    <span style="color:#888;font-size:0.85rem;margin-left:8px;">({pct}%)</span>
</div>
<div style="display:flex;gap:0;">{segmentos_html}</div>
""", unsafe_allow_html=True)
```

Commit:
```
style(dashboard): substituir barra de progresso padrão por versão CSS customizada
```

---

---

# FASE R6 — Mobile: identidade LicitaME nas telas

**Objetivo:** O app mobile exibe o nome LicitaME, o assistente se chama Léo, e as telas não parecem boilerplate de tutorial.

**Tempo estimado:** 1–2 horas.

---

## R6.1 — `mobile/constants/theme.ts` — criar ou atualizar tema

```typescript
export const COLORS = {
  primary:    "#1F3864",
  primaryMed: "#2E5DA8",
  primaryLight:"#D6E4F0",
  success:    "#1A7A4A",
  successBg:  "#E6F4ED",
  warning:    "#A07800",
  warningBg:  "#FFF8E1",
  error:      "#B00020",
  text:       "#111111",
  textSecond: "#555555",
  border:     "#E0E0E0",
  bg:         "#F8F9FC",
  white:      "#FFFFFF",
};

export const APP_NAME = "LicitaME";
export const ASSISTANT_NAME = "Léo";
export const ASSISTANT_AVATAR = "⚖️";

export const FONT = {
  regular: "System",
  bold: "System",
  sizes: { xs: 12, sm: 14, md: 16, lg: 18, xl: 22, xxl: 28 },
};
```

Commit:
```
chore(mobile): criar constantes de tema com paleta LicitaME
```

---

## R6.2 — Telas de auth — remover "MEI Licitações"

Em `mobile/app/(auth)/login.tsx` e `register.tsx`, substitua qualquer título genérico:

```typescript
// login.tsx
<Text style={styles.titulo}>LicitaME</Text>
<Text style={styles.subtitulo}>Entre na sua conta</Text>

// register.tsx  
<Text style={styles.titulo}>LicitaME</Text>
<Text style={styles.subtitulo}>Crie sua conta de MEI</Text>
```

Commit:
```
style(mobile): aplicar nome LicitaME nas telas de autenticação
```

---

## R6.3 — Tela do chatbot mobile — identidade do Léo

Em `mobile/app/(tabs)/chat.tsx` (ou o nome que estiver no seu projeto):

```typescript
// Header da tela
<View style={styles.header}>
  <Text style={styles.headerAvatar}>⚖️</Text>
  <View>
    <Text style={styles.headerNome}>Léo</Text>
    <Text style={styles.headerStatus}>● online — LicitaME</Text>
  </View>
</View>

// Mensagem inicial (exibida quando historico está vazio)
const MENSAGEM_INICIAL = {
  role: "assistant" as const,
  content:
    "Olá! Sou o Léo, assistente da LicitaME. " +
    "Posso te ajudar a encontrar editais para o seu perfil, " +
    "entender o checklist de documentos ou ver quais órgãos estão contratando. " +
    "Como posso te ajudar?",
};

// Placeholder do input
<TextInput placeholder="Pergunte ao Léo..." ... />

// Disclaimer no rodapé
<Text style={styles.disclaimer}>
  Léo pode cometer erros. Verifique no PNCP antes de participar.
</Text>
```

Commit:
```
style(mobile): aplicar identidade do Léo na tela de chat com mensagem inicial
```

---

## R6.4 — Tab bar — ícones e labels em português

Verifique o `_layout.tsx` ou onde as tabs são definidas. Os labels devem estar em português e os ícones devem fazer sentido:

```typescript
// Tabs esperadas
{ name: "index",      title: "Editais",    icon: "file-text" }
{ name: "checklist",  title: "Checklist",  icon: "check-square" }
{ name: "documentos", title: "Documentos", icon: "folder" }
{ name: "alertas",    title: "Alertas",    icon: "bell" }
{ name: "historico",  title: "Histórico",  icon: "clock" }
```

Commit:
```
style(mobile): padronizar labels e ícones da tab bar em português
```

---

---

# Checklist de verificação final

Antes de considerar o refactor completo, verifique cada item:

### Identidade
- [ ] "MEI Licitações" não aparece mais em nenhum arquivo (use busca global: `grep -r "MEI Licitações" .`)
- [ ] "LicitaME" aparece no título do Swagger, nos dashboards e no app mobile
- [ ] O assistente se chama "Léo" no chatbot Streamlit e no mobile

### Swagger
- [ ] O botão Authorize no Swagger mostra campo único "Value" (sem username/password/client_secret)
- [ ] Fazer login via `POST /auth/login` e colar o token no Authorize funciona sem erro
- [ ] As tags aparecem com emoji e descrição (não só palavras como "auth", "editais")
- [ ] O endpoint `/health` não aparece na lista do Swagger
- [ ] Cada endpoint tem `summary` legível

### Chatbot
- [ ] O system prompt contém o nome "Léo" e as regras de tom de voz
- [ ] O chatbot abre com mensagem inicial do Léo (não tela em branco)
- [ ] As sugestões de perguntas aparecem visíveis (não dentro de expander)
- [ ] O spinner exibe "Léo está buscando..." durante a chamada
- [ ] Erros de API exibem mensagem amigável, não stack trace

### Dashboard
- [ ] A fonte Sora está sendo carregada (verifique no browser: F12 → Computed → font-family)
- [ ] As fases estão agrupadas em 4 marcos, não em lista linear
- [ ] Os cargos da equipe têm especialização real de cada membro
- [ ] A barra de progresso é CSS customizada (não `st.progress()`)

### Mensagens de erro
- [ ] Testar `POST /auth/register` com email duplicado → mensagem amigável
- [ ] Testar `POST /auth/login` com senha errada → mensagem amigável
- [ ] Testar criar 4 alertas com plano free → mensagem com instrução clara
- [ ] Testar upload de arquivo `.exe` → mensagem com tipos aceitos

### Mobile
- [ ] Telas de login/registro mostram "LicitaME" como título
- [ ] Tela de chat mostra "Léo" no header com status online
- [ ] Tab bar tem labels em português

---

*Documento criado em 30/05/2025. Aplicar após CLAUDE.md.*
