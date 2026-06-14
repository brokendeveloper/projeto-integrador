"""Testes para os módulos Kafka (producer e consumer).

Todos os testes rodam sem Kafka real: o Producer e o Consumer são
mockados via unittest.mock.patch para isolar a lógica de negócio.
"""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ─── Producer ───────────────────────────────────────────────────────────────

class TestKafkaProducer:
    def _make_contratos(self, n: int = 2) -> list[dict]:
        return [
            {
                "_id": f"id-{i}",
                "numeroControlePNCP": f"CNPJ-{i}-000001/2024",
                "objetoContrato": f"Material de limpeza lote {i}",
                "valorInicial": 10000.0 * i,
                "_etl_timestamp": datetime.now(timezone.utc).isoformat(),
            }
            for i in range(1, n + 1)
        ]

    def test_publicar_retorna_zero_sem_bootstrap(self):
        """Sem KAFKA_BOOTSTRAP_SERVERS, publicar_contratos() retorna 0."""
        with patch.dict("os.environ", {}, clear=False):
            # Garante que a variável não está definida
            import os
            os.environ.pop("KAFKA_BOOTSTRAP_SERVERS", None)

            # Re-importa para que o módulo releia o ambiente
            import importlib
            import kafka.producer as mod
            importlib.reload(mod)

            result = mod.publicar_contratos(self._make_contratos())
            assert result == 0

    def test_publicar_remove_campo_id(self):
        """publicar_contratos() não envia o campo _id no payload Kafka."""
        mock_producer = MagicMock()

        with patch("kafka.producer._producer", mock_producer), \
             patch("kafka.producer._BOOTSTRAP", "localhost:9092"):
            import importlib
            import kafka.producer as mod
            importlib.reload(mod)

            contratos = self._make_contratos(1)
            mod._producer = mock_producer

            # Chama diretamente com producer mockado
            mod.publicar_contratos.__globals__["_producer"] = mock_producer
            result = mod.publicar_contratos(contratos)

        # produce foi chamado uma vez e o payload não contém _id
        assert mock_producer.produce.call_count == 1
        import json
        call_kwargs = mock_producer.produce.call_args
        payload = json.loads(call_kwargs[1]["value"].decode("utf-8"))
        assert "_id" not in payload
        assert "numeroControlePNCP" in payload

    def test_publicar_varios_contratos(self):
        """publicar_contratos() chama produce() para cada contrato."""
        mock_producer = MagicMock()

        import kafka.producer as mod
        original_producer = mod._producer
        mod._producer = mock_producer
        try:
            mod.publicar_contratos(self._make_contratos(3))
        finally:
            mod._producer = original_producer

        assert mock_producer.produce.call_count == 3
        mock_producer.flush.assert_called_once()


# ─── Consumer ───────────────────────────────────────────────────────────────

class TestKafkaConsumer:
    def _make_alerta(self, **kwargs) -> dict:
        base = {
            "_id": MagicMock(__str__=lambda s: "alerta-id-001"),
            "usuario_id": "usuario-001",
            "nome": "Limpeza SP",
            "cnae": None,
            "valor_max": None,
            "uf": None,
            "ativo": True,
        }
        base.update(kwargs)
        return base

    def _make_contrato(self, **kwargs) -> dict:
        base = {
            "numeroControlePNCP": "CNPJ-001-000001/2024",
            "objetoContrato": "Serviço de limpeza predial",
            "valorInicial": 15000.0,
            "uf": "SP",
        }
        base.update(kwargs)
        return base

    def _make_mock_db(self, alertas=None):
        mock_db = MagicMock()
        mock_db.silver_contratos.update_one = AsyncMock()
        mock_db.gold_contratos_mei.update_one = AsyncMock()
        mock_db.gold_top_orgaos.update_one = AsyncMock()
        mock_db.alertas.find.return_value = _AsyncIter(alertas or [])
        mock_db.notificacoes.insert_one = AsyncMock()
        return mock_db

    # ── Pipeline completo ────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_processar_contrato_grava_silver(self):
        """_processar_contrato() upserta em silver_contratos."""
        from kafka.consumer import _processar_contrato

        contrato = self._make_contrato(
            orgaoEntidade={"cnpj": "04926214000174", "razaoSocial": "Prefeitura SP"}
        )
        mock_db = self._make_mock_db()

        await _processar_contrato(contrato, mock_db)

        mock_db.silver_contratos.update_one.assert_called_once()
        call_args = mock_db.silver_contratos.update_one.call_args
        assert call_args[1]["upsert"] is True
        doc_silver = call_args[0][1]["$set"]
        assert doc_silver["orgao_cnpj"] == "04926214000174"
        assert doc_silver["orgao_nome"] == "Prefeitura SP"
        assert "orgaoEntidade" not in doc_silver

    @pytest.mark.asyncio
    async def test_processar_contrato_grava_gold_mei_dentro_limite(self):
        """Contrato com valorInicial ≤ 80.000 deve upsert em gold_contratos_mei."""
        from kafka.consumer import _processar_contrato

        contrato = self._make_contrato(valorInicial=50000.0)
        mock_db = self._make_mock_db()

        await _processar_contrato(contrato, mock_db)

        mock_db.gold_contratos_mei.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_processar_contrato_nao_grava_gold_mei_acima_limite(self):
        """Contrato com valorInicial > 80.000 NÃO deve aparecer em gold_contratos_mei."""
        from kafka.consumer import _processar_contrato

        contrato = self._make_contrato(valorInicial=150000.0)
        mock_db = self._make_mock_db()

        await _processar_contrato(contrato, mock_db)

        mock_db.gold_contratos_mei.update_one.assert_not_called()

    @pytest.mark.asyncio
    async def test_processar_contrato_incrementa_gold_top_orgaos(self):
        """Cada contrato incrementa $inc em gold_top_orgaos para o órgão."""
        from kafka.consumer import _processar_contrato

        contrato = self._make_contrato(
            orgaoEntidade={"cnpj": "04926214000174", "razaoSocial": "Prefeitura SP"},
            valorInicial=30000.0,
        )
        mock_db = self._make_mock_db()

        await _processar_contrato(contrato, mock_db)

        mock_db.gold_top_orgaos.update_one.assert_called_once()
        call = mock_db.gold_top_orgaos.update_one.call_args
        assert call[0][0] == {"orgao_nome": "Prefeitura SP"}
        assert call[0][1]["$inc"]["count"] == 1
        assert call[0][1]["$inc"]["valor_total"] == 30000.0
        assert call[1]["upsert"] is True

    @pytest.mark.asyncio
    async def test_processar_contrato_dispara_notificacao(self):
        """Contrato que bate com alerta deve gerar notificação."""
        from kafka.consumer import _processar_contrato

        alerta = self._make_alerta(valor_max=80000.0)
        contrato = self._make_contrato(valorInicial=15000.0)
        mock_db = self._make_mock_db(alertas=[alerta])

        await _processar_contrato(contrato, mock_db)

        mock_db.notificacoes.insert_one.assert_called_once()

    # ── Inicialização ────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_iniciar_consumer_retorna_none_sem_kafka(self):
        """iniciar_consumer_alertas() retorna None se Kafka não configurado."""
        import kafka.consumer as mod
        original = mod._KAFKA_DISPONIVEL
        mod._KAFKA_DISPONIVEL = False
        try:
            result = await mod.iniciar_consumer_alertas(db=MagicMock())
            assert result is None
        finally:
            mod._KAFKA_DISPONIVEL = original

    @pytest.mark.asyncio
    async def test_verificar_alerta_sem_filtros_cria_notificacao(self):
        """Contrato qualquer bate com alerta sem filtros."""
        from kafka.consumer import _verificar_e_notificar

        alerta = self._make_alerta()
        contrato = self._make_contrato()

        mock_db = MagicMock()
        mock_db.alertas.find.return_value = _AsyncIter([alerta])
        mock_db.notificacoes.insert_one = AsyncMock()

        await _verificar_e_notificar(contrato, mock_db)

        mock_db.notificacoes.insert_one.assert_called_once()
        notif = mock_db.notificacoes.insert_one.call_args[0][0]
        assert notif["usuario_id"] == "usuario-001"
        assert notif["valor"] == 15000.0
        assert notif["lido"] is False

    @pytest.mark.asyncio
    async def test_verificar_alerta_filtro_valor_rejeita(self):
        """Contrato com valor acima do limite não gera notificação."""
        from kafka.consumer import _verificar_e_notificar

        alerta = self._make_alerta(valor_max=10000.0)
        contrato = self._make_contrato(valorInicial=50000.0)

        mock_db = MagicMock()
        mock_db.alertas.find.return_value = _AsyncIter([alerta])
        mock_db.notificacoes.insert_one = AsyncMock()

        await _verificar_e_notificar(contrato, mock_db)

        mock_db.notificacoes.insert_one.assert_not_called()

    @pytest.mark.asyncio
    async def test_verificar_alerta_filtro_valor_aceita(self):
        """Contrato dentro do valor_max gera notificação."""
        from kafka.consumer import _verificar_e_notificar

        alerta = self._make_alerta(valor_max=80000.0)
        contrato = self._make_contrato(valorInicial=40000.0)

        mock_db = MagicMock()
        mock_db.alertas.find.return_value = _AsyncIter([alerta])
        mock_db.notificacoes.insert_one = AsyncMock()

        await _verificar_e_notificar(contrato, mock_db)

        mock_db.notificacoes.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_verificar_alerta_filtro_cnae_rejeita(self):
        """Objeto do contrato sem o termo do alerta não gera notificação."""
        from kafka.consumer import _verificar_e_notificar

        alerta = self._make_alerta(cnae="informática")
        contrato = self._make_contrato(objetoContrato="Serviço de limpeza predial")

        mock_db = MagicMock()
        mock_db.alertas.find.return_value = _AsyncIter([alerta])
        mock_db.notificacoes.insert_one = AsyncMock()

        await _verificar_e_notificar(contrato, mock_db)

        mock_db.notificacoes.insert_one.assert_not_called()

    @pytest.mark.asyncio
    async def test_verificar_alerta_filtro_uf_rejeita(self):
        """UF do contrato diferente do alerta não gera notificação."""
        from kafka.consumer import _verificar_e_notificar

        alerta = self._make_alerta(uf="RJ")
        contrato = self._make_contrato(uf="SP")

        mock_db = MagicMock()
        mock_db.alertas.find.return_value = _AsyncIter([alerta])
        mock_db.notificacoes.insert_one = AsyncMock()

        await _verificar_e_notificar(contrato, mock_db)

        mock_db.notificacoes.insert_one.assert_not_called()

    @pytest.mark.asyncio
    async def test_verificar_alerta_multiplos_alertas(self):
        """Contrato que bate com 2 alertas gera 2 notificações."""
        from kafka.consumer import _verificar_e_notificar

        alertas = [
            self._make_alerta(usuario_id="u1"),
            self._make_alerta(usuario_id="u2", uf="RJ"),   # NÃO bate (UF)
            self._make_alerta(usuario_id="u3", valor_max=80000.0),
        ]
        contrato = self._make_contrato(uf="SP", valorInicial=20000.0)

        mock_db = MagicMock()
        mock_db.alertas.find.return_value = _AsyncIter(alertas)
        mock_db.notificacoes.insert_one = AsyncMock()

        await _verificar_e_notificar(contrato, mock_db)

        assert mock_db.notificacoes.insert_one.call_count == 2


# ─── Helper ─────────────────────────────────────────────────────────────────

class _AsyncIter:
    """Iterador assíncrono para mockar cursores Motor em testes."""

    def __init__(self, items):
        self._items = iter(items)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._items)
        except StopIteration:
            raise StopAsyncIteration


def aiter_from(items):
    return _AsyncIter(items)
