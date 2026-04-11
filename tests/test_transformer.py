"""Testes unitários para o módulo PNCPTransformer."""

import pytest

from etl.transformer import PNCPTransformer


@pytest.fixture
def transformer():
    """Retorna uma instância do PNCPTransformer para testes."""
    return PNCPTransformer()


def test_transform_adiciona_metadados(transformer):
    """Deve adicionar _etl_timestamp e _source em todos os registros."""
    records = [{"numeroControlePNCP": "abc", "valorInicial": 500.0}]
    result = transformer.transform(records)

    assert "_etl_timestamp" in result[0]
    assert result[0]["_source"] == "pncp_api"


def test_normalize_date_iso8601(transformer):
    """Deve normalizar string de data para formato ISO 8601."""
    result = transformer._normalize_date("2024-01-15T10:00:00")
    assert "2024-01-15" in result


def test_normalize_date_none(transformer):
    """Deve retornar None para valores de data nulos."""
    assert transformer._normalize_date(None) is None
    assert transformer._normalize_date("") is None


def test_normalize_monetary_float(transformer):
    """Deve converter string monetária com pontuação para float."""
    assert transformer._normalize_monetary("1.500,50") == 1500.50
    assert transformer._normalize_monetary(2000.0) == 2000.0
    assert transformer._normalize_monetary(None) is None


def test_remove_empty_fields(transformer):
    """Deve remover campos nulos e strings vazias do registro."""
    record = {"a": "valor", "b": None, "c": ""}
    result = transformer._remove_empty_fields(record)
    assert "b" not in result
    assert "c" not in result
    assert result["a"] == "valor"


def test_transform_lista_vazia(transformer):
    """Deve retornar lista vazia ao receber lista vazia."""
    assert transformer.transform([]) == []
