"""Serviço de analytics — espelha via MongoDB Aggregation as transformações do pipeline PySpark."""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger("licitame.spark")

from .schemas import (
    ContratoMEIItem,
    ContratosMEIResponse,
    EstatisticasResponse,
    OrgaoItem,
    SparkContratoItem,
    SparkJobResponse,
    SparkMEIBucket,
    SparkOrgaoItem,
    SparkSummaryResponse,
    TopOrgaosResponse,
)

_SPARK_DIR = Path(__file__).resolve().parents[2] / "spark" / "output"

# Coleção de contratos PNCP (mesmo alvo do pipeline ETL e do script PySpark)
_COLECAO = "contratos"


async def obter_estatisticas(db: AsyncIOMotorDatabase) -> EstatisticasResponse:
    """Retorna estatísticas gerais dos contratos (espelha o summary() do PySpark)."""
    col = db[_COLECAO]
    total = await col.count_documents({})

    pipeline = [
        {"$match": {"valorInicial": {"$gt": 0}}},
        {
            "$group": {
                "_id": None,
                "media_valor": {"$avg": "$valorInicial"},
                "max_valor": {"$max": "$valorInicial"},
                "min_valor": {"$min": "$valorInicial"},
            }
        },
    ]
    cursor = col.aggregate(pipeline)
    stats = await cursor.to_list(length=1)
    dados = stats[0] if stats else {}

    return EstatisticasResponse(
        total_contratos=total,
        media_valor=round(dados.get("media_valor") or 0, 2) or None,
        max_valor=dados.get("max_valor"),
        min_valor=dados.get("min_valor"),
    )


async def obter_top_orgaos(db: AsyncIOMotorDatabase, n: int = 10) -> TopOrgaosResponse:
    """Retorna os N órgãos com mais contratos (espelha o groupBy().count() do PySpark)."""
    col = db[_COLECAO]
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
    cursor = col.aggregate(pipeline)
    docs = await cursor.to_list(length=n)

    orgaos = [
        OrgaoItem(
            orgao=d.get("_id"),
            total_contratos=d["total_contratos"],
            valor_total_rs=round(d.get("valor_total") or 0, 2),
        )
        for d in docs
    ]
    return TopOrgaosResponse(n=len(orgaos), orgaos=orgaos)


async def obter_contratos_mei(
    db: AsyncIOMotorDatabase, limite: int = 20
) -> ContratosMEIResponse:
    """Retorna contratos com valorInicial ≤ R$ 80.000 (espelha o filtro MEI do PySpark)."""
    col = db[_COLECAO]
    filtro = {"valorInicial": {"$gt": 0, "$lte": 80_000}}
    total = await col.count_documents(filtro)

    cursor = col.find(
        filtro,
        {
            "_id": 0,
            "numeroControlePNCP": 1,
            "objetoContrato": 1,
            "valorInicial": 1,
            "orgaoEntidade": 1,
            "dataPublicacaoPncp": 1,
        },
    ).sort("valorInicial", 1).limit(limite)

    docs = await cursor.to_list(length=limite)

    contratos = [
        ContratoMEIItem(
            numero_controle=d.get("numeroControlePNCP"),
            objeto=d.get("objetoContrato"),
            valor_inicial=d.get("valorInicial"),
            orgao=(d.get("orgaoEntidade") or {}).get("razaoSocial"),
            data_publicacao=d.get("dataPublicacaoPncp"),
        )
        for d in docs
    ]
    return ContratosMEIResponse(total=total, limite=len(contratos), contratos=contratos)


async def executar_spark() -> SparkJobResponse:
    """Dispara spark/pyspark_transform.py como subprocesso assíncrono."""
    script = Path(__file__).resolve().parents[2] / "spark" / "pyspark_transform.py"
    if not script.exists():
        return SparkJobResponse(
            status="erro",
            mensagem=f"Script não encontrado: {script}",
        )

    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        str(script),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    # Não aguarda — retorna imediatamente para o cliente
    logger.info("[SPARK] Pipeline iniciado em background (PID %d).", proc.pid)
    asyncio.ensure_future(_aguardar_spark(proc))

    return SparkJobResponse(
        status="iniciado",
        mensagem=(
            f"Pipeline PySpark iniciado em background (PID {proc.pid}). "
            "Os CSVs serão salvos em spark/output/ ao término."
        ),
    )


def obter_dados_spark() -> SparkSummaryResponse:
    """Lê os CSVs produzidos pelo PySpark e monta o SparkSummaryResponse."""
    f_completo = _SPARK_DIR / "contratos_completo.csv"
    f_mei = _SPARK_DIR / "contratos_mei.csv"
    f_top = _SPARK_DIR / "top_orgaos.csv"

    if not any(p.exists() for p in [f_completo, f_mei, f_top]):
        return SparkSummaryResponse(disponivel=False)

    # ── Total processado ──────────────────────────────────────────────────────
    total_processado = 0
    ultimo_processamento: str | None = None
    if f_completo.exists():
        df_all = pd.read_csv(f_completo)
        total_processado = len(df_all)
        if "_etl_timestamp" in df_all.columns and not df_all.empty:
            ts = pd.to_datetime(df_all["_etl_timestamp"].iloc[0], errors="coerce")
            if pd.notna(ts):
                ultimo_processamento = ts.isoformat()

    # ── MEI stats + buckets + sample ─────────────────────────────────────────
    total_mei = 0
    mei_media: float | None = None
    mei_max: float | None = None
    mei_min: float | None = None
    mei_buckets: list[SparkMEIBucket] = []
    mei_sample: list[SparkContratoItem] = []

    if f_mei.exists():
        df_mei = pd.read_csv(f_mei)
        total_mei = len(df_mei)
        if "valorInicial" in df_mei.columns and not df_mei.empty:
            vals = df_mei["valorInicial"].dropna()
            if not vals.empty:
                mei_media = round(float(vals.mean()), 2)
                mei_max = round(float(vals.max()), 2)
                mei_min = round(float(vals.min()), 2)
                # Histograma em buckets de R$ 10k
                bins = list(range(0, 90_000, 10_000))
                labels = [f"R$ {b//1000}k–{(b+10_000)//1000}k" for b in bins]
                cut = pd.cut(vals, bins=bins + [80_000], labels=labels, right=True)
                for label, cnt in cut.value_counts().sort_index().items():
                    mei_buckets.append(SparkMEIBucket(label=str(label), count=int(cnt)))

        col_map = {
            "numeroControlePNCP": "numero_controle",
            "objetoContrato": "objeto",
            "valorInicial": "valor_inicial",
            "orgao_nome": "orgao_nome",
            "dataPublicacaoPncp": "data_publicacao",
        }
        sample_rows = df_mei.head(20)
        for _, row in sample_rows.iterrows():
            mei_sample.append(SparkContratoItem(
                numero_controle=row.get("numeroControlePNCP"),
                objeto=row.get("objetoContrato"),
                valor_inicial=row.get("valorInicial") if pd.notna(row.get("valorInicial")) else None,
                orgao_nome=row.get("orgao_nome"),
                data_publicacao=row.get("dataPublicacaoPncp"),
            ))

    # ── Top órgãos ────────────────────────────────────────────────────────────
    top_orgaos: list[SparkOrgaoItem] = []
    top_orgao: str | None = None
    top_orgao_count = 0

    if f_top.exists():
        df_top = pd.read_csv(f_top)
        for _, row in df_top.iterrows():
            top_orgaos.append(SparkOrgaoItem(
                orgao=str(row.get("orgao_nome", "")),
                count=int(row.get("count", 0)),
            ))
        if top_orgaos:
            top_orgao = top_orgaos[0].orgao
            top_orgao_count = top_orgaos[0].count

    return SparkSummaryResponse(
        disponivel=True,
        total_processado=total_processado,
        total_mei=total_mei,
        ultimo_processamento=ultimo_processamento,
        top_orgao=top_orgao,
        top_orgao_count=top_orgao_count,
        top_orgaos=top_orgaos,
        mei_media_valor=mei_media,
        mei_max_valor=mei_max,
        mei_min_valor=mei_min,
        mei_buckets=mei_buckets,
        mei_sample=mei_sample,
    )


async def _aguardar_spark(proc: asyncio.subprocess.Process) -> None:
    """Aguarda o processo PySpark em background e registra o resultado no log."""
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        logger.error(
            "[SPARK] Pipeline falhou (código %d):\n%s",
            proc.returncode,
            stderr.decode(errors="replace"),
        )
    else:
        logger.info("[SPARK] Pipeline concluído com sucesso (PID %d).", proc.pid)
        logger.debug("[SPARK] Saída final:\n%s", stdout.decode(errors="replace")[-800:])


# ── Funções utilitárias reutilizadas pelo módulo MCP ──────────────────────────

async def buscar_contratos_por_palavra(
    db: AsyncIOMotorDatabase, palavra_chave: str, limite: int = 10
) -> list[dict[str, Any]]:
    """Busca contratos por palavra-chave no objeto do contrato."""
    col = db[_COLECAO]
    cursor = col.find(
        {"objetoContrato": {"$regex": palavra_chave, "$options": "i"}},
        {
            "_id": 0,
            "numeroControlePNCP": 1,
            "objetoContrato": 1,
            "valorInicial": 1,
            "orgaoEntidade": 1,
            "dataPublicacaoPncp": 1,
        },
    ).limit(limite)
    docs = await cursor.to_list(length=limite)
    return [
        {
            "numero_controle": d.get("numeroControlePNCP"),
            "objeto": d.get("objetoContrato"),
            "valor_inicial": d.get("valorInicial"),
            "orgao": (d.get("orgaoEntidade") or {}).get("razaoSocial"),
            "data_publicacao": d.get("dataPublicacaoPncp"),
        }
        for d in docs
    ]
