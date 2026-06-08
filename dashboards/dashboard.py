"""Dashboard interativo para visualização dos dados do PNCP via Streamlit."""

import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

_SPARK_DIR = Path(__file__).parent.parent / "spark" / "output"


def load_spark_csvs() -> dict[str, pd.DataFrame | None]:
    """Lê os CSVs produzidos pelo pipeline PySpark (spark/output/)."""
    keys = {"completo": "contratos_completo.csv",
            "mei":      "contratos_mei.csv",
            "top":      "top_orgaos.csv"}
    result: dict[str, pd.DataFrame | None] = {}
    for k, fname in keys.items():
        path = _SPARK_DIR / fname
        result[k] = pd.read_csv(path) if path.exists() else None
    return result


def get_data() -> pd.DataFrame:
    """Carrega os dados de contratos do MongoDB Atlas.

    Returns:
        pd.DataFrame: DataFrame com todos os contratos da coleção.
    """
    client = MongoClient(os.getenv("MONGODB_URI"))
    db = client[os.getenv("MONGODB_DB", "pncp_etl")]
    collection = db[os.getenv("MONGODB_COLLECTION", "contratos")]
    data = list(collection.find({}, {"_id": 0}))
    client.close()
    return pd.DataFrame(data)


def main() -> None:
    """Ponto de entrada do dashboard Streamlit.

    Exibe:
    - KPIs gerais (total de contratos, valor total)
    - Top 10 órgãos por número de contratos (gráfico de barras)
    - Distribuição de valores iniciais (histograma)
    - Timeline de publicações por dia (linha do tempo)
    """
    st.set_page_config(page_title="LicitaME — Analytics", page_icon="📈", layout="wide")
    st.title("📈 LicitaME — Análise de Contratos PNCP")

    with st.spinner("Carregando dados do MongoDB Atlas..."):
        df = get_data()

    if df.empty:
        st.warning("Nenhum dado encontrado. Execute o pipeline ETL primeiro.")
        return

    # KPIs
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Contratos", f"{len(df):,}")

    if "valorInicial" in df.columns:
        total_valor = df["valorInicial"].sum()
        col2.metric("Valor Total (R$)", f"{total_valor:,.2f}")
        media_valor = df["valorInicial"].mean()
        col3.metric("Valor Médio (R$)", f"{media_valor:,.2f}")

    st.divider()

    # Top 10 órgãos
    if "orgaoEntidade" in df.columns:
        df["orgao_nome"] = df["orgaoEntidade"].apply(
            lambda x: x.get("razaoSocial", "Desconhecido") if isinstance(x, dict) else "Desconhecido"
        )
        top_orgaos = df["orgao_nome"].value_counts().head(10).reset_index()
        top_orgaos.columns = ["Órgão", "Quantidade"]
        fig_orgaos = px.bar(
            top_orgaos,
            x="Órgão",
            y="Quantidade",
            title="Top 10 Órgãos por Número de Contratos",
        )
        st.plotly_chart(fig_orgaos, use_container_width=True)

    # Distribuição de valores
    if "valorInicial" in df.columns:
        valores = df["valorInicial"].dropna()
        fig_hist = px.histogram(
            valores,
            nbins=50,
            title="Distribuição dos Valores Iniciais",
            labels={"value": "Valor Inicial (R$)"},
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    # Timeline
    if "dataPublicacaoPncp" in df.columns:
        df["data"] = pd.to_datetime(df["dataPublicacaoPncp"], errors="coerce")
        por_dia = df.groupby(df["data"].dt.date).size().reset_index(name="contratos")
        fig_timeline = px.line(
            por_dia,
            x="data",
            y="contratos",
            title="Contratos Publicados por Dia",
        )
        st.plotly_chart(fig_timeline, use_container_width=True)

    # ── PySpark section ────────────────────────────────────────────────────
    spark_section()


def spark_section() -> None:
    """Seção do dashboard dedicada aos resultados do pipeline PySpark."""
    spark = load_spark_csvs()
    has_data = any(v is not None for v in spark.values())

    st.markdown("---")
    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
            <span style="font-size:1.3rem;font-weight:700;">Resultados do Pipeline PySpark</span>
            <span style="background:#FF6B35;color:#fff;font-size:0.7rem;font-weight:700;
                         padding:3px 9px;border-radius:12px;letter-spacing:.5px;">⚡ BATCH</span>
        </div>
        <p style="color:#888;font-size:0.87rem;margin-top:-4px;">
            Dados processados por <strong>Apache PySpark 3.5</strong> —
            <code>spark/pyspark_transform.py</code> → <code>spark/output/</code>
        </p>
        """,
        unsafe_allow_html=True,
    )

    if not has_data:
        st.info(
            "Os arquivos CSV do PySpark ainda não foram gerados. "
            "Rode `python3 spark/pyspark_transform.py` para processar os dados."
        )
        return

    df_all = spark["completo"]
    df_mei = spark["mei"]
    df_top = spark["top"]

    # ── KPIs ──────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        total = len(df_all) if df_all is not None else "—"
        st.metric("Contratos processados", f"{total:,}" if isinstance(total, int) else total,
                  help="Linhas no contratos_completo.csv")

    with c2:
        mei_total = len(df_mei) if df_mei is not None else "—"
        st.metric("Favoráveis ao MEI (≤ R$ 80k)", f"{mei_total:,}" if isinstance(mei_total, int) else mei_total,
                  help="Contratos com valorInicial ≤ 80.000 — contratos_mei.csv")

    with c3:
        if df_top is not None and not df_top.empty:
            top1 = df_top.iloc[0]
            st.metric("Órgão com + contratos",
                      top1["orgao_nome"][:22] + "…" if len(str(top1["orgao_nome"])) > 22 else top1["orgao_nome"],
                      delta=f"{int(top1['count'])} contratos")
        else:
            st.metric("Órgão com + contratos", "—")

    with c4:
        if df_all is not None and "_etl_timestamp" in df_all.columns:
            ts = pd.to_datetime(df_all["_etl_timestamp"].iloc[0], errors="coerce")
            label = ts.strftime("%d/%m/%Y %H:%M") if pd.notna(ts) else "—"
        else:
            label = "—"
        st.metric("Último processamento", label, help="Campo _etl_timestamp do CSV")

    # ── Charts ────────────────────────────────────────────────────────────
    col_l, col_r = st.columns(2)

    with col_l:
        if df_top is not None and not df_top.empty:
            fig = px.bar(
                df_top.head(15),
                x="count",
                y="orgao_nome",
                orientation="h",
                title="Top Órgãos — saída PySpark",
                labels={"count": "Contratos", "orgao_nome": "Órgão"},
                color="count",
                color_continuous_scale="Oranges",
            )
            fig.update_layout(yaxis={"categoryorder": "total ascending"},
                              coloraxis_showscale=False,
                              height=420, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)

    with col_r:
        if df_mei is not None and "valorInicial" in df_mei.columns:
            vals = df_mei["valorInicial"].dropna()
            fig2 = px.histogram(
                vals,
                nbins=30,
                title="Distribuição de Valores — contratos MEI (PySpark)",
                labels={"value": "Valor Inicial (R$)"},
                color_discrete_sequence=["#FF6B35"],
            )
            fig2.update_layout(height=420, margin=dict(l=10, r=10, t=40, b=10),
                               bargap=0.05)
            st.plotly_chart(fig2, use_container_width=True)

    # ── Amostra da tabela MEI ─────────────────────────────────────────────
    if df_mei is not None and not df_mei.empty:
        with st.expander(f"📄 Amostra dos contratos MEI-favoráveis ({len(df_mei)} registros)", expanded=False):
            cols_show = [c for c in
                         ["orgao_nome", "objetoContrato", "valorInicial", "dataPublicacaoPncp"]
                         if c in df_mei.columns]
            display = df_mei[cols_show].head(20).copy()
            if "valorInicial" in display.columns:
                display["valorInicial"] = display["valorInicial"].apply(
                    lambda v: f"R$ {v:,.2f}" if pd.notna(v) else "—"
                )
            if "objetoContrato" in display.columns:
                display["objetoContrato"] = display["objetoContrato"].str[:70] + "…"
            st.dataframe(display, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
