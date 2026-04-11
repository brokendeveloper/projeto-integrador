"""Dashboard interativo para visualização dos dados do PNCP via Streamlit."""

import os

import pandas as pd
import plotly.express as px
import streamlit as st
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()


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
    st.set_page_config(page_title="ETL PNCP — Dashboard", layout="wide")
    st.title("Dashboard — Contratos PNCP")

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


if __name__ == "__main__":
    main()
