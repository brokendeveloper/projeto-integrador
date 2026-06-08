"""Dashboard de apresentação do andamento do projeto para público não-técnico."""

import streamlit as st

st.set_page_config(
    page_title="LicitaME — Andamento do Projeto",
    page_icon="⚖️",
    layout="wide",
)

# ── Estilos (compatível com modo claro e escuro) ──────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700&display=swap');

html, body, [class*="css"], .stMarkdown, .stText {
    font-family: 'Sora', sans-serif !important;
}

.block-container { padding-top: 2rem !important; }

    .fase-card {
        border-left: 5px solid #28a745;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 12px;
        background: rgba(40, 167, 69, 0.08);
    }
    .fase-card.pendente {
        border-left-color: #ffc107;
        background: rgba(255, 193, 7, 0.08);
    }
    .fase-titulo {
        font-size: 1.05rem;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .fase-desc {
        font-size: 0.9rem;
        opacity: 0.75;
    }
    .badge-concluido {
        background: rgba(40, 167, 69, 0.2);
        color: #28a745;
        border-radius: 12px;
        padding: 2px 10px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .badge-pendente {
        background: rgba(255, 193, 7, 0.2);
        color: #d39e00;
        border-radius: 12px;
        padding: 2px 10px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .metric-box {
        border: 1px solid rgba(128,128,128,0.2);
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        background: rgba(128,128,128,0.05);
    }
    .metric-num {
        font-size: 2.4rem;
        font-weight: 800;
        color: #0d6efd;
    }
    .metric-label {
        font-size: 0.85rem;
        opacity: 0.65;
        margin-top: 4px;
    }
    .tech-pill {
        display: inline-block;
        background: rgba(128,128,128,0.15);
        border-radius: 20px;
        padding: 4px 14px;
        margin: 4px;
        font-size: 0.82rem;
        font-weight: 500;
    }
    .section-title {
        font-size: 1.3rem;
        font-weight: 700;
        margin-bottom: 16px;
    }
    .func-card {
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        background: rgba(128,128,128,0.07);
        border: 1px solid rgba(128,128,128,0.15);
    }
    .func-titulo {
        font-weight: 700;
        margin-bottom: 8px;
    }
    .func-lista {
        margin: 0;
        padding-left: 18px;
        font-size: 0.88rem;
        opacity: 0.8;
    }
    .membro-card {
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        background: rgba(128,128,128,0.1);
        border: 1px solid rgba(128,128,128,0.15);
    }
    .membro-nome {
        font-weight: 700;
        margin-top: 8px;
    }
    .membro-cargo {
        font-size: 0.82rem;
        opacity: 0.6;
    }
    hr.divider {
        border: none;
        border-top: 1px solid rgba(128,128,128,0.2);
        margin: 28px 0;
    }
    .tech-cat {
        font-weight: 600;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)


# ── Cabeçalho ─────────────────────────────────────────────────────────────────
st.markdown("## LicitaME — Painel de Andamento do Projeto")
st.markdown(
    "**Plataforma que ajuda microempreendedores individuais (MEIs) a participar de licitações públicas "
    "de forma simples, organizada e dentro da lei.**"
)

st.markdown('<hr class="divider">', unsafe_allow_html=True)


# ── Métricas gerais ───────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Visão Geral do Projeto</div>', unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)

metricas = [
    ("11", "Fases no total"),
    ("9", "Fases concluídas"),
    ("10", "Módulos da API"),
    ("29", "Endpoints REST"),
    ("5", "Integrantes"),
]

for col, (num, label) in zip([col1, col2, col3, col4, col5], metricas):
    with col:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-num">{num}</div>
            <div class="metric-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)


# ── Progresso geral ───────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Progresso Geral</div>', unsafe_allow_html=True)
_concluidas = 9
_total = 11
_pct = int((_concluidas / _total) * 100)
_segs = "".join(
    f'<div style="flex:1;height:12px;background:{"#2E5DA8" if i < _concluidas else "rgba(128,128,128,0.15)"};border-radius:3px;margin:0 2px;"></div>'
    for i in range(_total)
)
st.markdown(
    f'<div style="margin-bottom:8px;"><span style="font-weight:600;color:#1F3864;">{_concluidas} de {_total} fases concluídas</span>'
    f'<span style="color:#888;font-size:0.85rem;margin-left:8px;">({_pct}%)</span></div>'
    f'<div style="display:flex;gap:0;">{_segs}</div>',
    unsafe_allow_html=True,
)

st.markdown('<hr class="divider">', unsafe_allow_html=True)


# ── Fases do projeto ──────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Fases do Projeto</div>', unsafe_allow_html=True)

fases = [
    {
        "num": "Fase 1",
        "titulo": "Coleta de Dados Públicos (ETL)",
        "desc": "Desenvolvemos um pipeline automático que busca editais e contratos diretamente do Portal Nacional de Contratações Públicas (PNCP), organiza as informações e as salva no banco de dados.",
        "concluida": True,
    },
    {
        "num": "Fase 2",
        "titulo": "Análise e Visualização dos Dados",
        "desc": "Criamos gráficos e relatórios interativos para explorar os dados coletados — como os órgãos que mais publicam licitações e os valores envolvidos.",
        "concluida": True,
    },
    {
        "num": "Fase 3",
        "titulo": "Estrutura da API (Base do Sistema)",
        "desc": "Montamos a espinha dorsal do sistema: a API que conecta o banco de dados a todos os outros módulos, com verificação de saúde e configuração de segurança.",
        "concluida": True,
    },
    {
        "num": "Fase 4",
        "titulo": "Cadastro e Login de Usuários",
        "desc": "Implementamos o sistema de criação de conta e acesso seguro à plataforma. As senhas são protegidas com criptografia e o acesso é controlado por token de autenticação.",
        "concluida": True,
    },
    {
        "num": "Fase 5",
        "titulo": "Consulta de Editais",
        "desc": "O MEI pode pesquisar editais disponíveis com filtros por data, modalidade e outros critérios. Os resultados são paginados e mostrados de forma organizada.",
        "concluida": True,
    },
    {
        "num": "Fase 6",
        "titulo": "Checklist de Habilitação",
        "desc": "Criamos uma lista de verificação automática baseada na Lei 14.133/2021 (Nova Lei de Licitações). O sistema indica quais documentos o MEI precisa providenciar para participar de cada edital.",
        "concluida": True,
    },
    {
        "num": "Fase 7",
        "titulo": "Documentos, Alertas e Histórico",
        "desc": "O MEI pode enviar documentos diretamente pela plataforma, configurar alertas para novos editais do seu interesse e consultar seu histórico de participações com resumo de status.",
        "concluida": True,
    },
    {
        "num": "Fase 8",
        "titulo": "Segurança e LGPD",
        "desc": "Proteção avançada da API: limite de requisições para evitar ataques, cabeçalhos de segurança HTTP e endpoints de conformidade com a LGPD (exportar e excluir dados pessoais do usuário).",
        "concluida": True,
    },
    {
        "num": "Fase 9",
        "titulo": "CI/CD e Automação",
        "desc": "Configuração do pipeline de integração contínua com GitHub Actions: execução automática dos testes a cada atualização de código, garantindo que nada quebre sem ser detectado.",
        "concluida": True,
    },
    {
        "num": "Fase 10",
        "titulo": "App Mobile (Expo + React Native)",
        "desc": "Desenvolvimento do aplicativo para celular com cinco telas principais: busca de editais, checklist, documentos, alertas e histórico — conectadas à API e com login seguro.",
        "concluida": True,
    },
    {
        "num": "Fase 11",
        "titulo": "Integração Final e Entrega",
        "desc": "Testes em dispositivo real, polimento da experiência do usuário, atualização da documentação, análise de segurança e preparação dos materiais de apresentação final.",
        "concluida": False,
    },
]

col_esq, col_dir = st.columns(2)

for i, fase in enumerate(fases):
    col = col_esq if i % 2 == 0 else col_dir
    status_class = "" if fase["concluida"] else " pendente"
    badge_class = "badge-concluido" if fase["concluida"] else "badge-pendente"
    badge_texto = "✅ Concluída" if fase["concluida"] else "⏳ Pendente"

    with col:
        st.markdown(f"""
        <div class="fase-card{status_class}">
            <div class="fase-titulo">{fase['num']} — {fase['titulo']}
                &nbsp;<span class="{badge_class}">{badge_texto}</span>
            </div>
            <div class="fase-desc">{fase['desc']}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)


# ── Funcionalidades implementadas ─────────────────────────────────────────────
st.markdown('<div class="section-title">O que o sistema já faz</div>', unsafe_allow_html=True)

funcionalidades = {
    "👤 Usuários": [
        "Cadastro de nova conta",
        "Login com proteção por senha",
        "Acesso seguro com token",
    ],
    "📄 Editais": [
        "Listagem de editais disponíveis",
        "Filtros por data e modalidade",
        "Visualização detalhada de cada edital",
    ],
    "✅ Checklist": [
        "Verificação de documentos necessários",
        "Baseado na Lei 14.133/2021",
        "Acompanhamento de progresso",
    ],
    "📁 Documentos": [
        "Upload de arquivos para cada edital",
        "Listagem dos documentos enviados",
        "Remoção de arquivos",
    ],
    "🔔 Alertas": [
        "Configuração de alertas por critério",
        "Listagem dos alertas ativos",
        "Remoção de alertas",
    ],
    "📊 Histórico": [
        "Registro de participações",
        "Consulta do histórico completo",
        "Resumo com contagem por status",
    ],
}

cols = st.columns(3)
for idx, (modulo, itens) in enumerate(funcionalidades.items()):
    with cols[idx % 3]:
        lista = "".join(f"<li>{item}</li>" for item in itens)
        st.markdown(f"""
        <div class="func-card">
            <div class="func-titulo">{modulo}</div>
            <ul class="func-lista">{lista}</ul>
        </div>
        """, unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)


# ── Tecnologias ───────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Tecnologias Utilizadas</div>', unsafe_allow_html=True)

tecnologias = {
    "🗄️ Banco de Dados": ["MongoDB Atlas", "SQLite"],
    "⚙️ Back-end": ["Python 3.12", "FastAPI", "JWT (autenticação)"],
    "📦 Coleta de Dados": ["API PNCP", "Pandas", "Tenacity (retry automático)"],
    "📊 Visualização": ["Streamlit", "Plotly"],
    "🧪 Qualidade": ["Pytest", "Testes automatizados"],
}

for categoria, techs in tecnologias.items():
    pills = "".join(f'<span class="tech-pill">{t}</span>' for t in techs)
    st.markdown(f"""
    <div style="margin-bottom:10px;">
        <span class="tech-cat">{categoria}:</span> {pills}
    </div>
    """, unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)


# ── Equipe ────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Equipe</div>', unsafe_allow_html=True)

membros = [
    {"nome": "Luccas Fernandes",  "cargo": "ETL & Engenharia de Dados"},
    {"nome": "Gabriel Nogueira",  "cargo": "ETL & DataOps"},
    {"nome": "Nathalia Pinto",    "cargo": "Backend & API"},
    {"nome": "Eduarda Leão",      "cargo": "Produto & Documentação"},
    {"nome": "Carlos",            "cargo": "Mobile & Frontend"},
]

cols_equipe = st.columns(5)
for col, membro in zip(cols_equipe, membros):
    with col:
        st.markdown(f"""
        <div class="membro-card">
            <div style="font-size:2rem;">👤</div>
            <div class="membro-nome">{membro['nome']}</div>
            <div class="membro-cargo">{membro['cargo']}</div>
        </div>
        """, unsafe_allow_html=True)
