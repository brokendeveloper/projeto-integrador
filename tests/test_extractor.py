"""Testes unitários para o módulo PNCPExtractor."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from etl.extractor import PNCPExtractor


@pytest.fixture
def extractor():
    """Retorna uma instância do PNCPExtractor para testes."""
    return PNCPExtractor()


def test_fetch_contratos_retorna_lista(extractor):
    """Deve retornar lista de contratos quando a API responde com sucesso."""
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {"numeroControlePNCP": "123", "valorInicial": 1000.0}
    ]
    mock_response.raise_for_status = MagicMock()

    with patch.object(extractor.session, "get", return_value=mock_response):
        result = extractor.fetch_contratos("20240101", "20240131")

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["numeroControlePNCP"] == "123"


def test_fetch_contratos_paginacao(extractor):
    """Deve percorrer múltiplas páginas até encontrar página incompleta."""
    page1 = [{"id": i} for i in range(50)]
    page2 = [{"id": i} for i in range(10)]

    responses = [
        MagicMock(**{"json.return_value": page1, "raise_for_status": MagicMock()}),
        MagicMock(**{"json.return_value": page2, "raise_for_status": MagicMock()}),
    ]

    with patch.object(extractor.session, "get", side_effect=responses):
        result = extractor.fetch_contratos("20240101", "20240131")

    assert len(result) == 60


def test_get_levanta_http_error(extractor):
    """Deve propagar HTTPError quando a API retornar erro."""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("404")
    mock_response.status_code = 404

    with patch.object(extractor.session, "get", return_value=mock_response):
        with pytest.raises(requests.HTTPError):
            extractor._get("/contratos", {})
