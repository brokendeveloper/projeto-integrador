"""Testes unitários para os módulos MongoLoader e SQLiteLoader."""

import sqlite3
from unittest.mock import MagicMock, patch

import pytest

from etl.loader import SQLiteLoader


@pytest.fixture
def sqlite_loader(tmp_path):
    """Retorna um SQLiteLoader com banco em diretório temporário."""
    db_path = str(tmp_path / "test.db")
    loader = SQLiteLoader(db_path=db_path)
    yield loader
    loader.close()


def test_sqlite_loader_cria_tabela(sqlite_loader):
    """Deve criar a tabela 'contratos' ao inicializar."""
    conn = sqlite3.connect(sqlite_loader.db_path)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='contratos'"
    )
    assert cursor.fetchone() is not None
    conn.close()


def test_sqlite_loader_insere_registro(sqlite_loader):
    """Deve inserir registro com sucesso e retornar contagem correta."""
    records = [
        {
            "numeroControlePNCP": "TEST-001",
            "objetoContrato": "Objeto Teste",
            "valorInicial": 1000.0,
            "dataPublicacaoPncp": "2024-01-01T00:00:00",
            "_etl_timestamp": "2024-01-01T00:00:00+00:00",
            "_source": "pncp_api",
        }
    ]
    count = sqlite_loader.load(records)
    assert count == 1


def test_sqlite_loader_sem_duplicatas(sqlite_loader):
    """Deve ignorar registros duplicados via INSERT OR IGNORE."""
    record = [{"numeroControlePNCP": "DUP-001", "_etl_timestamp": "t", "_source": "s"}]
    sqlite_loader.load(record)
    count = sqlite_loader.load(record)
    assert count == 0


def test_sqlite_loader_lista_vazia(sqlite_loader):
    """Deve retornar 0 quando a lista de registros estiver vazia."""
    assert sqlite_loader.load([]) == 0
