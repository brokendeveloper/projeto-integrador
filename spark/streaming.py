"""Spark Structured Streaming — Consumer do tópico Kafka pncp.contratos.novos.

Lê contratos em tempo real do Kafka e grava na coleção silver_contratos do
MongoDB usando outputMode="append" (sem substituir o histórico).

Execução (requer spark-submit com o conector Kafka):
    spark-submit \\
        --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.2,\\
                   org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 \\
        spark/streaming.py

Variáveis de ambiente:
    KAFKA_BOOTSTRAP_SERVERS  — ex: localhost:9092
    KAFKA_TOPIC_CONTRATOS    — padrão: pncp.contratos.novos
    MONGODB_URI              — URI de conexão MongoDB
    MONGODB_DB               — nome do banco (padrão: pncp_etl)
"""

import os

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, to_timestamp
from pyspark.sql.types import (
    DoubleType,
    StringType,
    StructField,
    StructType,
)

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC = os.getenv("KAFKA_TOPIC_CONTRATOS", "pncp.contratos.novos")
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGODB_DB", "pncp_etl")
CHECKPOINT_DIR = os.getenv("KAFKA_CHECKPOINT_DIR", "/tmp/licitame_kafka_checkpoint")

# Schema esperado das mensagens Kafka (mesma estrutura do ETL transformado)
SCHEMA = StructType(
    [
        StructField("numeroControlePNCP", StringType(), nullable=True),
        StructField("objetoContrato", StringType(), nullable=True),
        StructField("valorInicial", DoubleType(), nullable=True),
        StructField("dataPublicacaoPncp", StringType(), nullable=True),
        StructField("orgao_cnpj", StringType(), nullable=True),
        StructField("orgao_nome", StringType(), nullable=True),
        StructField("uf", StringType(), nullable=True),
        StructField("_etl_timestamp", StringType(), nullable=True),
        StructField("_source", StringType(), nullable=True),
    ]
)


def main() -> None:
    spark = (
        SparkSession.builder.appName("LicitaME-KafkaStreaming")
        .config(
            "spark.mongodb.write.connection.uri",
            f"{MONGO_URI}/{MONGO_DB}",
        )
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    print(f"[streaming] Conectando ao Kafka: {BOOTSTRAP}")
    print(f"[streaming] Tópico: {TOPIC}")
    print(f"[streaming] MongoDB: {MONGO_URI}/{MONGO_DB} → silver_contratos")

    # Leitura do tópico Kafka
    df_raw = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", BOOTSTRAP)
        .option("subscribe", TOPIC)
        .option("startingOffsets", "latest")
        .load()
    )

    # Decodifica JSON e aplica schema
    df_silver = (
        df_raw.selectExpr("CAST(value AS STRING) AS json_str")
        .select(from_json(col("json_str"), SCHEMA).alias("d"))
        .select("d.*")
        .filter(col("valorInicial").isNotNull())
        .withColumn(
            "dataPublicacaoPncp",
            to_timestamp(col("dataPublicacaoPncp")),
        )
    )

    # Escrita contínua para MongoDB silver_contratos
    query = (
        df_silver.writeStream.format("mongodb")
        .option("uri", MONGO_URI)
        .option("database", MONGO_DB)
        .option("collection", "silver_contratos")
        .option("checkpointLocation", CHECKPOINT_DIR)
        .outputMode("append")
        .start()
    )

    print("[streaming] Spark Structured Streaming ativo. Aguardando mensagens...")
    query.awaitTermination()


if __name__ == "__main__":
    main()
