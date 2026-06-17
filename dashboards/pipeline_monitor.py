"""Monitor de Pipeline — LicitaME

Exibe em tempo real o estado de cada camada da arquitetura Medallion,
métricas de execução do ETL/Spark e permite disparar execuções manuais.

Uso:
    streamlit run dashboards/pipeline_monitor.py
"""

import os
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

# ── Configuração ─────────────────────────────────────────────────────────────

API_URL = os.getenv("API_URL", "https://projeto-integrador.squareweb.app")
MONGODB_URI = os.getenv("MONGODB_URI", "")
MONGODB_DB = os.getenv("MONGODB_DB", os.getenv("MONGODB_DB_NAME", "pncp"))
SPARK_DIR = Path(__file__).parent.parent / "spark" / "output"

st.set_page_config(
    page_title="LicitaME — Monitor de Pipeline",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Helpers ───────────────────────────────────────────────────────────────────

@st.cache_resource
def get_mongo_client() -> MongoClient | None:
    if not MONGODB_URI:
        return None
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        return client
    except Exception:
        return None


def get_collection_count(db, collection: str) -> int | None:
    try:
        return db[collection].count_documents({})
    except Exception:
        return None


def get_latest_etl_timestamp(db) -> str:
    """Retorna o _etl_timestamp mais recente da coleção contratos."""
    try:
        doc = db["contratos"].find_one(
            {"_etl_timestamp": {"$exists": True}},
            sort=[("_etl_timestamp", -1)],
        )
        if doc and doc.get("_etl_timestamp"):
            ts = doc["_etl_timestamp"]
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return dt.strftime("%d/%m/%Y %H:%M UTC")
    except Exception:
        pass
    return "—"


def get_sample_contratos(db, limit: int = 200) -> pd.DataFrame:
    try:
        docs = list(db["contratos"].find(
            {"valorInicial": {"$exists": True, "$gt": 0}},
            {"valorInicial": 1, "orgaoEntidade": 1, "modalidadeNome": 1, "_id": 0},
        ).limit(limit))
        rows = []
        for d in docs:
            orgao = d.get("orgaoEntidade", {})
            rows.append({
                "valor": float(d.get("valorInicial", 0)),
                "orgao": (orgao.get("razaoSocial", "") if isinstance(orgao, dict) else "") or "—",
                "modalidade": d.get("modalidadeNome", "—") or "—",
            })
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()


def get_top_orgaos(db, n: int = 10) -> pd.DataFrame:
    try:
        docs = list(db["gold_top_orgaos"].find({}, {"_id": 0}).sort("count", -1).limit(n))
        if docs:
            return pd.DataFrame(docs)
    except Exception:
        pass
    return pd.DataFrame()


def get_gold_mei_sample(db, limit: int = 5) -> list[dict]:
    try:
        return list(db["gold_contratos_mei"].find(
            {},
            {"_id": 0, "objetoContrato": 1, "valorInicial": 1, "orgao_nome": 1},
        ).limit(limit))
    except Exception:
        return []


def check_api_health() -> tuple[bool, float]:
    try:
        t0 = time.time()
        r = requests.get(f"{API_URL}/health", timeout=5)
        latency = (time.time() - t0) * 1000
        return r.status_code == 200, latency
    except Exception:
        return False, 0.0


def trigger_spark(api_token: str) -> tuple[bool, str]:
    try:
        r = requests.post(
            f"{API_URL}/analytics/executar-spark",
            headers={"Authorization": f"Bearer {api_token}"},
            timeout=120,
        )
        if r.status_code == 200:
            return True, r.json().get("mensagem", "Spark executado com sucesso.")
        return False, f"HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return False, str(e)


# ── Layout ────────────────────────────────────────────────────────────────────

st.markdown("""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
    <span style="font-size:2rem">📊</span>
    <div>
        <h1 style="margin:0;font-size:1.6rem">LicitaME — Monitor de Pipeline</h1>
        <p style="margin:0;color:#666;font-size:.9rem">Arquitetura Medallion: Bronze → Silver → Gold · Kafka Streaming · PySpark Batch</p>
    </div>
</div>
""", unsafe_allow_html=True)
st.divider()

# ── Conexão MongoDB ───────────────────────────────────────────────────────────

client = get_mongo_client()
db = client[MONGODB_DB] if client else None

# ── Linha 1: Status da infraestrutura ────────────────────────────────────────

st.subheader("🔌 Status da Infraestrutura")
col_mongo, col_api, col_kafka, col_spark = st.columns(4)

with col_mongo:
    if db is not None:
        st.success("**MongoDB Atlas**\nConectado ✅")
    else:
        st.error("**MongoDB Atlas**\nSem conexão ❌")

with col_api:
    api_ok, latency = check_api_health()
    if api_ok:
        st.success(f"**API SquareCloud**\nOnline ✅ · {latency:.0f} ms")
    else:
        st.error("**API SquareCloud**\nOffline ❌")

with col_kafka:
    kafka_env = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "")
    if kafka_env:
        st.success(f"**Kafka**\nConfigurado ✅\n`{kafka_env[:30]}…`")
    else:
        st.warning("**Kafka**\nNão configurado ⚠️")

with col_spark:
    spark_csvs = any((SPARK_DIR / f).exists() for f in [
        "contratos_mei.csv", "top_orgaos.csv", "contratos_completo.csv"
    ])
    if spark_csvs:
        mtime = max(
            (SPARK_DIR / f).stat().st_mtime
            for f in ["contratos_mei.csv", "top_orgaos.csv", "contratos_completo.csv"]
            if (SPARK_DIR / f).exists()
        )
        dt = datetime.fromtimestamp(mtime).strftime("%d/%m %H:%M")
        st.success(f"**PySpark Output**\nCSVs presentes ✅\nÚltimo: {dt}")
    else:
        st.warning("**PySpark Output**\nSem CSVs ⚠️")

st.divider()

# ── Linha 2: Camadas Medallion ────────────────────────────────────────────────

st.subheader("🥇 Camadas Medallion — Contagens em Tempo Real")

col_b, col_s, col_gm, col_gt = st.columns(4)

counts = {}
if db is not None:
    for col_name in ["contratos", "silver_contratos", "gold_contratos_mei", "gold_top_orgaos"]:
        counts[col_name] = get_collection_count(db, col_name)
    ultimo_etl = get_latest_etl_timestamp(db)
else:
    counts = {k: None for k in ["contratos", "silver_contratos", "gold_contratos_mei", "gold_top_orgaos"]}
    ultimo_etl = "—"

def fmt_count(n):
    if n is None:
        return "—"
    return f"{n:,}".replace(",", ".")

with col_b:
    st.metric(
        label="🥉 Bronze — `contratos`",
        value=fmt_count(counts.get("contratos")),
        help="Dados brutos ingeridos do PNCP via ETL",
    )

with col_s:
    bronze = counts.get("contratos") or 1
    silver = counts.get("silver_contratos") or 0
    delta = f"{(silver/bronze*100):.0f}% do Bronze" if bronze else None
    st.metric(
        label="🥈 Silver — `silver_contratos`",
        value=fmt_count(counts.get("silver_contratos")),
        delta=delta,
        help="Contratos com orgaoEntidade achatado (Kafka Consumer / PySpark)",
    )

with col_gm:
    st.metric(
        label="🥇 Gold MEI — `gold_contratos_mei`",
        value=fmt_count(counts.get("gold_contratos_mei")),
        help="Contratos com valorInicial ≤ R$ 80.000 (favoráveis ao MEI)",
    )

with col_gt:
    st.metric(
        label="🥇 Gold Órgãos — `gold_top_orgaos`",
        value=fmt_count(counts.get("gold_top_orgaos")),
        help="Ranking de órgãos por volume de contratos",
    )

st.caption(f"🕐 Último ETL executado: **{ultimo_etl}** · Próxima execução automática: **03:00 UTC**")

st.divider()

# ── Linha 3: Gráficos ─────────────────────────────────────────────────────────

st.subheader("📈 Análise dos Dados — Camada Gold")

tab_orgaos, tab_valores, tab_mei = st.tabs(["Top Órgãos", "Distribuição de Valores", "Contratos MEI"])

with tab_orgaos:
    if db is not None:
        df_top = get_top_orgaos(db, 10)
        if not df_top.empty and "orgao_nome" in df_top.columns:
            fig = px.bar(
                df_top.sort_values("count"),
                x="count",
                y="orgao_nome",
                orientation="h",
                title="Top 10 Órgãos por Número de Contratos",
                labels={"count": "Nº de contratos", "orgao_nome": "Órgão"},
                color="count",
                color_continuous_scale="Blues",
            )
            fig.update_layout(showlegend=False, coloraxis_showscale=False, height=420)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Gold Top Órgãos ainda não calculado. Execute o PySpark batch abaixo.")
    else:
        st.warning("MongoDB não conectado.")

with tab_valores:
    if db is not None:
        df_sample = get_sample_contratos(db, 300)
        if not df_sample.empty:
            col_hist, col_pie = st.columns(2)
            with col_hist:
                df_mei_filter = df_sample[df_sample["valor"] <= 80_000]
                fig_hist = px.histogram(
                    df_mei_filter,
                    x="valor",
                    nbins=20,
                    title="Distribuição de Valores (≤ R$ 80k)",
                    labels={"valor": "Valor Estimado (R$)"},
                    color_discrete_sequence=["#2563EB"],
                )
                fig_hist.update_layout(height=360)
                st.plotly_chart(fig_hist, use_container_width=True)

            with col_pie:
                bucket = pd.cut(
                    df_sample["valor"],
                    bins=[0, 10_000, 30_000, 80_000, float("inf")],
                    labels=["Até R$ 10k", "R$ 10k–30k", "R$ 30k–80k", "Acima R$ 80k"],
                )
                fig_pie = px.pie(
                    names=bucket.value_counts().index,
                    values=bucket.value_counts().values,
                    title="Faixas de Valor",
                    color_discrete_sequence=px.colors.sequential.Blues_r,
                )
                fig_pie.update_layout(height=360)
                st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Sem dados suficientes para análise.")
    else:
        st.warning("MongoDB não conectado.")

with tab_mei:
    if db is not None:
        amostras = get_gold_mei_sample(db, 8)
        if amostras:
            for item in amostras:
                valor = item.get("valorInicial", 0)
                orgao = item.get("orgao_nome", "—")
                objeto = item.get("objetoContrato", "—")
                st.markdown(
                    f"**R$ {valor:,.2f}** · {orgao}  \n_{objeto[:120]}{'…' if len(objeto) > 120 else ''}_"
                )
                st.divider()
        else:
            st.info("Nenhum contrato Gold MEI encontrado.")
    else:
        st.warning("MongoDB não conectado.")

st.divider()

# ── Linha 4: Fluxo da Pipeline ────────────────────────────────────────────────

st.subheader("🔄 Fluxo da Pipeline")

st.markdown("""
```
PNCP API (pull)
    │
    ▼  GitHub Actions ETL — diário 03:00 UTC
PNCPExtractor (retry 3x, paginação automática)
    │
    ▼
PNCPTransformer (ISO 8601, float, strip, remove nulos)
    │
    ├──► MongoLoader → MongoDB Bronze (contratos) ←── upsert por numeroControlePNCP
    ├──► SQLiteLoader → db/contratos.db            ←── INSERT OR IGNORE
    └──► Kafka Producer → tópico: contratos        ←── JSON, flush()
                │
                ▼  FastAPI Consumer (lifespan — 24/7 no SquareCloud)
          por mensagem:
          ├──► Silver (update_one upsert)
          ├──► Gold MEI (se valor ≤ 80k)
          ├──► Gold Top Órgãos ($inc count)
          └──► Alertas (verifica filtros MEI → notificacao)
                │
                ▼  PySpark Batch (sob demanda)
          ├──► Recalcula Silver snapshot completo
          ├──► Recalcula Gold MEI snapshot
          ├──► Recalcula Top Órgãos exato
          └──► Salva CSVs em spark/output/
```
""")

st.divider()

# ── Linha 5: Ações Manuais ────────────────────────────────────────────────────

st.subheader("⚡ Ações Manuais")

col_act1, col_act2 = st.columns(2)

with col_act1:
    st.markdown("**Executar PySpark Batch**")
    st.caption("Recalcula Silver e Gold completos, gera CSVs. Requer token JWT.")
    api_token = st.text_input("Token JWT", type="password", key="token_spark")
    if st.button("▶ Executar Spark agora", disabled=not api_token):
        with st.spinner("Executando PySpark… (pode levar até 2 minutos)"):
            ok, msg = trigger_spark(api_token)
        if ok:
            st.success(f"✅ {msg}")
            st.cache_resource.clear()
            st.rerun()
        else:
            st.error(f"❌ {msg}")

with col_act2:
    st.markdown("**Forçar ETL manual**")
    st.caption("Dispara o workflow GitHub Actions manualmente.")
    gh_token = st.text_input("GitHub Token (workflow:write)", type="password", key="token_gh")
    if st.button("▶ Disparar ETL via GitHub Actions", disabled=not gh_token):
        try:
            r = requests.post(
                "https://api.github.com/repos/brokendeveloper/projeto-integrador/actions/workflows/etl.yml/dispatches",
                headers={
                    "Authorization": f"Bearer {gh_token}",
                    "Accept": "application/vnd.github+json",
                },
                json={"ref": "main"},
                timeout=10,
            )
            if r.status_code == 204:
                st.success("✅ Workflow ETL disparado! Acompanhe em github.com/brokendeveloper/projeto-integrador/actions")
            else:
                st.error(f"❌ HTTP {r.status_code}: {r.text[:200]}")
        except Exception as e:
            st.error(f"❌ {e}")

st.divider()
st.caption(
    "LicitaME · Engenharia de Dados · "
    f"Atualizado em {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')}"
)
