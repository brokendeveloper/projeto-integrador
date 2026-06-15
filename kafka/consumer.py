"""Kafka Consumer assíncrono — pipeline completo Bronze → Silver → Gold + Alertas.

Ativação: defina KAFKA_BOOTSTRAP_SERVERS no ambiente.
O consumer roda como task asyncio no lifespan da API FastAPI.

Para cada mensagem recebida do tópico, executa as etapas em ordem:
  1. Silver  — flatten de orgaoEntidade + upsert em silver_contratos
  2. Gold MEI — se valorInicial ≤ 80.000, upsert em gold_contratos_mei
  3. Gold Top — incrementa contagem do órgão em gold_top_orgaos ($inc)
  4. Alertas  — verifica critérios dos alertas ativos e grava notificacoes

A diferença em relação ao pipeline batch (PySpark) é que aqui não fazemos
drop() das coleções: cada mensagem é um upsert incremental, preservando
o histórico acumulado. O batch reconstrói tudo do zero; o streaming atualiza.

Se KAFKA_BOOTSTRAP_SERVERS não estiver definido ou confluent-kafka não estiver
instalado, iniciar_consumer_alertas() retorna None sem afetar a API.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("licitame.kafka.consumer")

_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "")
_TOPIC = os.getenv("KAFKA_TOPIC_CONTRATOS", "pncp.contratos.novos")
_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "licitame-alertas")
_USERNAME = os.getenv("KAFKA_USERNAME", "")
_PASSWORD = os.getenv("KAFKA_PASSWORD", "")
_SASL_MECHANISM = os.getenv("KAFKA_SASL_MECHANISM", "PLAIN")
_LIMITE_MEI = 80_000.0

try:
    from confluent_kafka import Consumer as _Consumer, KafkaError
    _KAFKA_DISPONIVEL = bool(_BOOTSTRAP)
except ImportError:
    _Consumer = None  # type: ignore[assignment,misc]
    KafkaError = None  # type: ignore[assignment,misc]
    _KAFKA_DISPONIVEL = False


# ─── Ponto de entrada ────────────────────────────────────────────────────────

async def iniciar_consumer_alertas(db) -> "Optional[asyncio.Task]":
    """Inicia o consumer completo como task asyncio no lifespan da API.

    Returns:
        asyncio.Task do loop, ou None se Kafka não estiver disponível.
    """
    if not _KAFKA_DISPONIVEL:
        logger.info(
            "Kafka não configurado (KAFKA_BOOTSTRAP_SERVERS ausente) — consumer desativado."
        )
        return None

    # Garante índices únicos nas camadas Silver e Gold antes de iniciar o streaming
    await db.silver_contratos.create_index("numeroControlePNCP", unique=True, sparse=True)
    await db.gold_contratos_mei.create_index("numeroControlePNCP", unique=True, sparse=True)
    await db.gold_top_orgaos.create_index("orgao_nome", unique=True, sparse=True)
    logger.info("Índices únicos verificados: silver_contratos, gold_contratos_mei, gold_top_orgaos.")

    task = asyncio.create_task(_loop_consumer(db))
    logger.info(
        "Kafka consumer iniciado. Tópico: '%s', Group: '%s'. "
        "Pipeline: Silver → Gold MEI → Gold Top → Alertas.",
        _TOPIC,
        _GROUP_ID,
    )
    return task


# ─── Loop principal ───────────────────────────────────────────────────────────

async def _loop_consumer(db) -> None:
    loop = asyncio.get_event_loop()
    cfg: dict = {
        "bootstrap.servers": _BOOTSTRAP,
        "group.id": _GROUP_ID,
        "auto.offset.reset": "latest",
        "enable.auto.commit": True,
    }
    if _USERNAME and _PASSWORD:
        cfg.update(
            {
                "security.protocol": "SASL_SSL",
                "sasl.mechanisms": _SASL_MECHANISM,
                "sasl.username": _USERNAME,
                "sasl.password": _PASSWORD,
            }
        )
    consumer = _Consumer(cfg)
    consumer.subscribe([_TOPIC])
    logger.debug("Consumer subscrito ao tópico '%s'.", _TOPIC)

    try:
        while True:
            msg = await loop.run_in_executor(None, lambda: consumer.poll(timeout=1.0))
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                logger.error("Kafka consumer erro: %s", msg.error())
                continue

            try:
                contrato = json.loads(msg.value().decode("utf-8"))
                await _processar_contrato(contrato, db)
            except json.JSONDecodeError as exc:
                logger.warning("Mensagem Kafka ignorada (JSON inválido): %s", exc)
            except Exception as exc:
                logger.error("Erro ao processar mensagem Kafka: %s", exc, exc_info=True)

    except asyncio.CancelledError:
        logger.info("Consumer encerrado (CancelledError).")
    finally:
        consumer.close()


# ─── Orquestrador por mensagem ────────────────────────────────────────────────

async def _processar_contrato(contrato: dict, db) -> None:
    """Executa as 4 etapas do pipeline para um contrato recebido do Kafka."""
    numero = contrato.get("numeroControlePNCP", "desconhecido")

    doc_silver = await _gravar_silver(contrato, db)
    await _gravar_gold_mei(doc_silver, db)
    await _atualizar_gold_top_orgaos(doc_silver, db)
    await _verificar_e_notificar(contrato, db)

    logger.info("Contrato processado: %s", numero)


# ─── Etapa 1 — Silver ─────────────────────────────────────────────────────────

async def _gravar_silver(contrato: dict, db) -> dict:
    """Flatten de orgaoEntidade e upsert em silver_contratos.

    Diferença do batch: upsert incremental — não dropa a coleção.
    Chave de deduplicação: numeroControlePNCP (mesma do Bronze).
    """
    orgao = contrato.get("orgaoEntidade") or {}
    doc = {
        k: v for k, v in contrato.items()
        if k not in ("orgaoEntidade", "_id")
    }
    doc["orgao_cnpj"] = orgao.get("cnpj") or contrato.get("orgao_cnpj")
    doc["orgao_nome"] = orgao.get("razaoSocial") or contrato.get("orgao_nome")

    chave = doc.get("numeroControlePNCP")
    if chave:
        await db.silver_contratos.update_one(
            {"numeroControlePNCP": chave},
            {"$set": doc},
            upsert=True,
        )
    return doc


# ─── Etapa 2 — Gold MEI ───────────────────────────────────────────────────────

async def _gravar_gold_mei(doc_silver: dict, db) -> None:
    """Upsert em gold_contratos_mei se valorInicial ≤ R$ 80.000 (LC 123/2006).

    Diferença do batch: upsert individual — não dropa a coleção.
    """
    valor = float(doc_silver.get("valorInicial") or 0)
    if valor <= 0 or valor > _LIMITE_MEI:
        return

    chave = doc_silver.get("numeroControlePNCP")
    if chave:
        await db.gold_contratos_mei.update_one(
            {"numeroControlePNCP": chave},
            {"$set": doc_silver},
            upsert=True,
        )


# ─── Etapa 3 — Gold Top Órgãos ────────────────────────────────────────────────

async def _atualizar_gold_top_orgaos(doc_silver: dict, db) -> None:
    """Incrementa o contador do órgão em gold_top_orgaos via $inc.

    No batch, PySpark recalcula do zero com groupBy().count().
    No streaming, cada contrato incrementa atomicamente o contador do órgão.
    O resultado reflete o acumulado desde a última execução do batch.
    """
    orgao_nome = doc_silver.get("orgao_nome")
    if not orgao_nome:
        return

    valor = float(doc_silver.get("valorInicial") or 0)
    await db.gold_top_orgaos.update_one(
        {"orgao_nome": orgao_nome},
        {
            "$inc": {"count": 1, "valor_total": valor},
            "$set": {"orgao_cnpj": doc_silver.get("orgao_cnpj")},
        },
        upsert=True,
    )


# ─── Etapa 4 — Alertas ────────────────────────────────────────────────────────

async def _verificar_e_notificar(contrato: dict, db) -> None:
    """Verifica critérios dos alertas ativos e persiste notificações.

    Critérios (todos opcionais, avaliados em AND):
      - valor_max: valorInicial ≤ valor_max do alerta
      - cnae:     termo presente no objetoContrato (case-insensitive)
      - uf:       UF do alerta == UF do contrato
    """
    valor = float(contrato.get("valorInicial") or 0)
    objeto = (contrato.get("objetoContrato") or "").lower()
    uf_contrato = (contrato.get("uf") or "").upper()

    cursor = db.alertas.find({"ativo": True})
    async for alerta in cursor:
        if alerta.get("valor_max") and valor > float(alerta["valor_max"]):
            continue
        if alerta.get("cnae") and alerta["cnae"].lower() not in objeto:
            continue
        if alerta.get("uf") and alerta["uf"].upper() != uf_contrato:
            continue

        await db.notificacoes.insert_one(
            {
                "usuario_id": alerta["usuario_id"],
                "alerta_id": str(alerta["_id"]),
                "alerta_nome": alerta.get("nome", ""),
                "contrato_numero": contrato.get("numeroControlePNCP"),
                "contrato_objeto": contrato.get("objetoContrato"),
                "valor": valor,
                "lido": False,
                "criado_em": datetime.now(timezone.utc).isoformat(),
            }
        )
        logger.info(
            "Notificação criada — usuário: %s · contrato: %s · R$ %.2f",
            alerta["usuario_id"],
            contrato.get("numeroControlePNCP"),
            valor,
        )
