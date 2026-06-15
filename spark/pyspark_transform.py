"""Pipeline de transformação PySpark sobre dados PNCP armazenados no MongoDB Atlas.

Lê os contratos do MongoDB, cria um Spark DataFrame e aplica as seguintes
transformações tabulares:
  1. Exibe schema e amostra dos dados
  2. Estatísticas descritivas dos valores monetários
  3. Top 10 órgãos por volume de contratos
  4. Contratos favoráveis ao MEI (valorInicial ≤ R$ 80.000)

Salva os resultados em spark/output/ como arquivos CSV.

Uso:
    python spark/pyspark_transform.py
"""

import os

import pandas as pd
import pymongo
from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

load_dotenv()


def _salvar_camadas_mongodb(
    df_silver: pd.DataFrame,
    df_mei: pd.DataFrame,
    df_top: pd.DataFrame,
) -> None:
    """Persiste as camadas Silver e Gold de volta ao MongoDB Atlas.

    Cria (ou recria) três coleções:
    - silver_contratos: todos os contratos com orgaoEntidade achatado
    - gold_contratos_mei: contratos favoráveis ao MEI (valorInicial <= 80.000)
    - gold_top_orgaos: top 50 órgãos por número de contratos

    Args:
        df_silver: DataFrame pandas com todos os contratos transformados.
        df_mei: DataFrame pandas com contratos filtrados para MEI.
        df_top: DataFrame pandas com ranking de órgãos.
    """
    uri = os.getenv("MONGODB_URI", "")
    db_name = os.getenv("MONGODB_DB", "pncp_etl")
    client = pymongo.MongoClient(uri)
    try:
        db = client[db_name]

        # Silver — todos os contratos com schema plano
        silver_docs = df_silver.where(pd.notnull(df_silver), None).to_dict("records")
        db["silver_contratos"].drop()
        if silver_docs:
            db["silver_contratos"].insert_many(silver_docs)
        print(f"✓ silver_contratos: {len(silver_docs)} documentos gravados.")

        # Gold — contratos favoráveis ao MEI
        mei_docs = df_mei.where(pd.notnull(df_mei), None).to_dict("records")
        db["gold_contratos_mei"].drop()
        if mei_docs:
            db["gold_contratos_mei"].insert_many(mei_docs)
        print(f"✓ gold_contratos_mei: {len(mei_docs)} documentos gravados.")

        # Gold — ranking de órgãos
        top_docs = df_top.where(pd.notnull(df_top), None).to_dict("records")
        db["gold_top_orgaos"].drop()
        if top_docs:
            db["gold_top_orgaos"].insert_many(top_docs)
        print(f"✓ gold_top_orgaos: {len(top_docs)} documentos gravados.")

    finally:
        client.close()


def _carregar_contratos_mongodb() -> pd.DataFrame:
    """Lê os contratos do MongoDB Atlas e retorna um pandas DataFrame.

    Achata o campo aninhado orgaoEntidade para colunas planas,
    facilitando a criação do Spark DataFrame.

    Returns:
        pd.DataFrame: DataFrame com todos os contratos da coleção.
    """
    uri = os.getenv("MONGODB_URI", "")
    db_name = os.getenv("MONGODB_DB", "pncp_etl")
    col_name = os.getenv("MONGODB_COLLECTION", "contratos")

    client = pymongo.MongoClient(uri)
    try:
        collection = client[db_name][col_name]
        projecao = {
            "_id": 0,
            "numeroControlePNCP": 1,
            "objetoContrato": 1,
            "valorInicial": 1,
            "valorGlobal": 1,
            "dataPublicacaoPncp": 1,
            "dataVigenciaInicio": 1,
            "dataVigenciaFim": 1,
            "orgaoEntidade": 1,
            "_etl_timestamp": 1,
        }
        docs = list(collection.find({}, projecao))
    finally:
        client.close()

    # Achatar campo aninhado orgaoEntidade
    for doc in docs:
        orgao = doc.pop("orgaoEntidade", None) or {}
        doc["orgao_cnpj"] = orgao.get("cnpj")
        doc["orgao_nome"] = orgao.get("razaoSocial")

    return pd.DataFrame(docs)


def main() -> None:
    """Executa o pipeline PySpark completo."""
    spark = (
        SparkSession.builder.appName("LicitaME — Transformação PySpark")
        .master("local[*]")
        .config("spark.sql.repl.eagerEval.enabled", "true")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    # ── 1. Leitura do MongoDB Atlas ────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  PIPELINE PYSPARK — PNCP MEI LICITAÇÕES")
    print("=" * 60)
    print("\n[1/4] Lendo dados do MongoDB Atlas...")

    pdf = _carregar_contratos_mongodb()
    total = len(pdf)
    print(f"      → {total} registros carregados do MongoDB.")

    if pdf.empty:
        print("\nAVISO: Nenhum dado encontrado. Execute o pipeline ETL primeiro.")
        spark.stop()
        return

    # Converter para Spark DataFrame
    df = spark.createDataFrame(pdf)

    # ── 2. Schema e amostra ────────────────────────────────────────────────────
    print("\n[2/4] Schema do DataFrame:")
    df.printSchema()

    print("Amostra dos dados (5 registros):")
    df.select(
        "numeroControlePNCP",
        "objetoContrato",
        "valorInicial",
        "orgao_nome",
        "dataPublicacaoPncp",
    ).show(5, truncate=60)

    # ── 3. Estatísticas dos valores monetários ─────────────────────────────────
    print("[3/4] Estatísticas dos valores iniciais dos contratos (R$):")
    df.filter(F.col("valorInicial").isNotNull()).select("valorInicial").summary(
        "count", "mean", "stddev", "min", "25%", "75%", "max"
    ).show()

    # Top 10 órgãos por número de contratos
    print("Top 10 órgãos por número de contratos:")
    df.groupBy("orgao_nome").count().orderBy(F.desc("count")).limit(10).show(
        truncate=60
    )

    # Contratos por mês de publicação
    print("Contratos publicados por mês:")
    df.filter(F.col("dataPublicacaoPncp").isNotNull()).withColumn(
        "mes", F.substring(F.col("dataPublicacaoPncp"), 1, 7)
    ).groupBy("mes").count().orderBy("mes").show()

    # ── 4. Contratos favoráveis ao MEI ─────────────────────────────────────────
    print("[4/4] Contratos favoráveis ao MEI (valorInicial ≤ R$ 80.000):")
    df_mei = df.filter(
        F.col("valorInicial").isNotNull()
        & (F.col("valorInicial") > 0)
        & (F.col("valorInicial") <= 80_000)
    )
    total_mei = df_mei.count()
    print(f"      → {total_mei} contratos favoráveis ao MEI encontrados.\n")
    df_mei.select(
        "numeroControlePNCP", "objetoContrato", "valorInicial", "orgao_nome"
    ).orderBy("valorInicial").show(20, truncate=60)

    # ── Salvar resultados em CSV ───────────────────────────────────────────────
    os.makedirs("spark/output", exist_ok=True)

    pdf_mei = df_mei.toPandas()
    pdf_mei.to_csv("spark/output/contratos_mei.csv", index=False)
    print("✓ spark/output/contratos_mei.csv salvo.")

    pdf_top = (
        df.groupBy("orgao_nome")
        .count()
        .orderBy(F.desc("count"))
        .limit(50)
        .toPandas()
    )
    pdf_top.to_csv("spark/output/top_orgaos.csv", index=False)
    print("✓ spark/output/top_orgaos.csv salvo.")

    # Resumo tabular completo (todos os contratos, campos planos)
    pdf_completo = df.toPandas()
    pdf_completo.to_csv("spark/output/contratos_completo.csv", index=False)
    print("✓ spark/output/contratos_completo.csv salvo.")

    # ── Persistir camadas Silver e Gold no MongoDB ─────────────────────────────
    print("\n[5/5] Persistindo camadas Silver e Gold no MongoDB Atlas...")
    _salvar_camadas_mongodb(pdf_completo, pdf_mei, pdf_top)

    spark.stop()

    print("\n" + "=" * 60)
    print("  PIPELINE PYSPARK CONCLUÍDO")
    print(f"  Total de registros processados : {total}")
    print(f"  Contratos favoráveis ao MEI    : {total_mei}")
    print("  Saída CSV  : spark/output/")
    print("  Saída Mongo: silver_contratos | gold_contratos_mei | gold_top_orgaos")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
