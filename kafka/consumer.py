"""Kafka Consumer assíncrono — processa contratos e dispara alertas MEI.

Ativação: defina KAFKA_BOOTSTRAP_SERVERS no ambiente.
O consumer roda como task asyncio no lifespan da API FastAPI.
Quando um contrato chega no tópico, verifica os critérios de cada alerta
ativo e persiste uma notificação em db.notificacoes para o usuário correspondente.

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

try:
    from confluent_kafka import Consumer as _Consumer, KafkaError, KafkaException
    _KAFKA_DISPONIVEL = bool(_BOOTSTRAP)
except ImportError:
    _Consumer = None  # type: ignore[assignment,misc]
    KafkaError = None  # type: ignore[assignment,misc]
    KafkaException = None  # type: ignore[assignment,misc]
    _KAFKA_DISPONIVEL = False


async def iniciar_consumer_alertas(db) -> "Optional[asyncio.Task]":
    """Inicia o consumer de alertas como task asyncio no lifespan da API.

    Args:
        db: AsyncIOMotorDatabase injetado pelo lifespan.

    Returns:
        asyncio.Task do loop do consumer, ou None se Kafka não estiver disponível.
    """
    if not _KAFKA_DISPONIVEL:
        logger.info(
            "Kafka não configurado (KAFKA_BOOTSTRAP_SERVERS ausente) — "
            "consumer de alertas desativado."
        )
        return None

    task = asyncio.create_task(_loop_consumer(db))
    logger.info(
        "Kafka consumer de alertas iniciado. Tópico: '%s', Group: '%s'.",
        _TOPIC,
        _GROUP_ID,
    )
    return task


async def _loop_consumer(db) -> None:
    """Loop principal do consumer — roda indefinidamente até ser cancelado."""
    loop = asyncio.get_event_loop()
    consumer = _Consumer(
        {
            "bootstrap.servers": _BOOTSTRAP,
            "group.id": _GROUP_ID,
            "auto.offset.reset": "latest",
            "enable.auto.commit": True,
        }
    )
    consumer.subscribe([_TOPIC])
    logger.debug("Consumer subscrito ao tópico '%s'.", _TOPIC)

    try:
        while True:
            # poll() é bloqueante — executa em executor para não travar o event loop
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
                await _verificar_e_notificar(contrato, db)
            except json.JSONDecodeError as exc:
                logger.warning("Mensagem Kafka ignorada (JSON inválido): %s", exc)
            except Exception as exc:
                logger.error("Erro ao processar mensagem Kafka: %s", exc, exc_info=True)

    except asyncio.CancelledError:
        logger.info("Consumer de alertas encerrado (CancelledError).")
    finally:
        consumer.close()


async def _verificar_e_notificar(contrato: dict, db) -> None:
    """Verifica se o contrato bate com algum alerta ativo e cria notificação.

    Critérios de match (todos opcionais, avaliados em AND):
      - valor_max: valorInicial do contrato <= valor_max do alerta
      - cnae: termo do alerta presente no objetoContrato (case-insensitive)
      - uf: UF do alerta igual à UF do contrato

    Args:
        contrato: dicionário do contrato recebido do tópico Kafka.
        db: AsyncIOMotorDatabase para consultar alertas e inserir notificações.
    """
    valor = float(contrato.get("valorInicial") or 0)
    objeto = (contrato.get("objetoContrato") or "").lower()
    uf_contrato = (contrato.get("uf") or "").upper()

    cursor = db.alertas.find({"ativo": True})
    async for alerta in cursor:
        # Critério valor
        if alerta.get("valor_max") and valor > float(alerta["valor_max"]):
            continue
        # Critério CNAE/palavra-chave no objeto
        if alerta.get("cnae") and alerta["cnae"].lower() not in objeto:
            continue
        # Critério UF
        if alerta.get("uf") and alerta["uf"].upper() != uf_contrato:
            continue

        # Match — persiste notificação
        notificacao = {
            "usuario_id": alerta["usuario_id"],
            "alerta_id": str(alerta["_id"]),
            "alerta_nome": alerta.get("nome", ""),
            "contrato_numero": contrato.get("numeroControlePNCP"),
            "contrato_objeto": contrato.get("objetoContrato"),
            "valor": valor,
            "lido": False,
            "criado_em": datetime.now(timezone.utc).isoformat(),
        }
        await db.notificacoes.insert_one(notificacao)
        logger.info(
            "Notificação criada — usuário: %s · contrato: %s · valor: R$ %.2f",
            alerta["usuario_id"],
            contrato.get("numeroControlePNCP"),
            valor,
        )
