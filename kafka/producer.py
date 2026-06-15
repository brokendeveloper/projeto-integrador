"""Kafka Producer — publica contratos PNCP no tópico configurado.

Ativação: defina KAFKA_BOOTSTRAP_SERVERS no ambiente.
Se a variável não estiver definida ou confluent-kafka não estiver instalado,
publicar_contratos() retorna 0 silenciosamente sem afetar o pipeline ETL.
"""

import json
import logging
import os

logger = logging.getLogger("licitame.kafka.producer")

_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "")
_TOPIC = os.getenv("KAFKA_TOPIC_CONTRATOS", "pncp.contratos.novos")
_USERNAME = os.getenv("KAFKA_USERNAME", "")
_PASSWORD = os.getenv("KAFKA_PASSWORD", "")
# Confluent Cloud → PLAIN  |  Upstash → SCRAM-SHA-256
_SASL_MECHANISM = os.getenv("KAFKA_SASL_MECHANISM", "PLAIN")


def _build_config() -> dict:
    """Constrói configuração do producer.

    Se KAFKA_USERNAME e KAFKA_PASSWORD estiverem definidos, adiciona SASL/SSL
    (necessário para Confluent Cloud, Upstash e outros serviços gerenciados).
    Sem as variáveis, usa PLAINTEXT (Docker local).
    """
    cfg: dict = {"bootstrap.servers": _BOOTSTRAP}
    if _USERNAME and _PASSWORD:
        cfg.update(
            {
                "security.protocol": "SASL_SSL",
                "sasl.mechanisms": _SASL_MECHANISM,
                "sasl.username": _USERNAME,
                "sasl.password": _PASSWORD,
            }
        )
    return cfg


try:
    from confluent_kafka import Producer as _Producer

    _producer: "_Producer | None" = _Producer(_build_config()) if _BOOTSTRAP else None
except ImportError:
    _Producer = None  # type: ignore[assignment,misc]
    _producer = None


def _delivery_report(err, msg) -> None:
    if err:
        logger.warning("Kafka entrega falhou — %s", err)


def publicar_contratos(contratos: list[dict]) -> int:
    """Publica uma lista de contratos no tópico Kafka.

    Args:
        contratos: registros já transformados pelo ETL Pipeline.

    Returns:
        Número de mensagens enfileiradas (0 se Kafka não estiver configurado).
    """
    if not _producer:
        return 0

    for doc in contratos:
        # Remove _id (ObjectId não é JSON-serializável) antes de publicar
        payload = {k: v for k, v in doc.items() if k != "_id"}
        _producer.produce(
            _TOPIC,
            value=json.dumps(payload, default=str).encode("utf-8"),
            callback=_delivery_report,
        )

    _producer.flush()
    logger.info("Kafka: %d contratos publicados em '%s'.", len(contratos), _TOPIC)
    return len(contratos)
