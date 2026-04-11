"""Módulo de carregamento dos dados transformados nos bancos de destino."""

from typing import Any

from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError, ConnectionFailure

from config.settings import MONGODB_COLLECTION, MONGODB_DB, MONGODB_URI
from utils.logger import get_logger


class MongoLoader:
    """Responsável pela persistência dos dados no MongoDB Atlas.

    Realiza upsert em lotes usando 'numeroControlePNCP' como chave única,
    garantindo idempotência e ausência de duplicatas na coleção.
    """

    def __init__(self, batch_size: int = 500) -> None:
        """Inicializa o loader e verifica a conexão com o MongoDB Atlas.

        Args:
            batch_size (int): Número máximo de documentos por lote de inserção.

        Raises:
            ConnectionFailure: Se não for possível conectar ao MongoDB Atlas.
            ValueError: Se MONGODB_URI não estiver definida.
        """
        if not MONGODB_URI:
            raise ValueError(
                "MONGODB_URI não definida. Configure a variável de ambiente."
            )

        self.batch_size = batch_size
        self.logger = get_logger(self.__class__.__name__)

        self.client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        try:
            self.client.admin.command("ping")
            self.logger.info("Conexão com MongoDB Atlas estabelecida.")
        except ConnectionFailure as exc:
            self.logger.error("Falha ao conectar ao MongoDB Atlas: %s", exc)
            raise

        self.db = self.client[MONGODB_DB]
        self.collection = self.db[MONGODB_COLLECTION]
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        """Cria índices na coleção para garantir unicidade e performance.

        Índices criados:
        - Único em 'numeroControlePNCP' (evita duplicatas)
        - Em 'dataPublicacaoPncp' (facilita queries por data)
        """
        self.collection.create_index("numeroControlePNCP", unique=True, sparse=True)
        self.collection.create_index("dataPublicacaoPncp")
        self.logger.info("Índices verificados/criados na coleção '%s'.", MONGODB_COLLECTION)

    def load(self, records: list[dict[str, Any]]) -> int:
        """Persiste os registros no MongoDB Atlas via upsert em lotes.

        Usa bulk_write com UpdateOne/upsert para garantir idempotência.
        Documentos são agrupados em lotes de tamanho 'batch_size'.

        Args:
            records (list[dict]): Lista de documentos transformados.

        Returns:
            int: Número total de documentos inseridos ou atualizados.

        Raises:
            BulkWriteError: Se ocorrer erro durante a escrita em lote.
        """
        if not records:
            self.logger.warning("Nenhum registro para carregar no MongoDB.")
            return 0

        total_upserted = 0

        for i in range(0, len(records), self.batch_size):
            batch = records[i : i + self.batch_size]
            operations = [
                UpdateOne(
                    {"numeroControlePNCP": doc.get("numeroControlePNCP")},
                    {"$set": doc},
                    upsert=True,
                )
                for doc in batch
            ]
            try:
                result = self.collection.bulk_write(operations, ordered=False)
                upserted = result.upserted_count + result.modified_count
                total_upserted += upserted
                self.logger.info(
                    "Lote %d/%d — %d documentos upserted.",
                    i // self.batch_size + 1,
                    -(-len(records) // self.batch_size),
                    upserted,
                )
            except BulkWriteError as exc:
                self.logger.error("Erro no bulk_write: %s", exc.details)
                raise

        self.logger.info("Carga concluída. Total upserted: %d.", total_upserted)
        return total_upserted

    def close(self) -> None:
        """Fecha a conexão com o MongoDB Atlas."""
        self.client.close()
        self.logger.info("Conexão com MongoDB Atlas encerrada.")


import sqlite3


class SQLiteLoader:
    """Persistência adicional dos dados de contratos em banco SQLite local.

    Implementado como diferencial para permitir análise offline dos dados
    sem dependência de conectividade com o MongoDB Atlas.
    """

    def __init__(self, db_path: str = "db/contratos.db") -> None:
        """Inicializa o loader e cria as tabelas necessárias.

        Args:
            db_path (str): Caminho para o arquivo SQLite.
        """
        import os

        self.db_path = db_path
        self.logger = get_logger(self.__class__.__name__)
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.connection = sqlite3.connect(db_path)
        self._create_tables()
        self.logger.info("SQLiteLoader inicializado em '%s'.", db_path)

    def _create_tables(self) -> None:
        """Cria as tabelas do banco SQLite caso não existam.

        Tabelas criadas:
        - contratos: campos principais de cada contrato PNCP.
        """
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS contratos (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_controle_pncp  TEXT    UNIQUE,
                objeto_contrato       TEXT,
                valor_inicial         REAL,
                data_publicacao_pncp  TEXT,
                data_vigencia_inicio  TEXT,
                data_vigencia_fim     TEXT,
                orgao_cnpj            TEXT,
                orgao_razao_social    TEXT,
                etl_timestamp         TEXT,
                source                TEXT
            )
        """)
        self.connection.commit()

    def load(self, records: list[dict[str, Any]]) -> int:
        """Persiste os registros no SQLite via INSERT OR IGNORE.

        Args:
            records (list[dict]): Lista de documentos transformados.

        Returns:
            int: Número de registros inseridos com sucesso.
        """
        if not records:
            self.logger.warning("Nenhum registro para carregar no SQLite.")
            return 0

        cursor = self.connection.cursor()
        inserted = 0

        for doc in records:
            orgao = doc.get("orgaoEntidade") or {}
            cursor.execute(
                """
                INSERT OR IGNORE INTO contratos (
                    numero_controle_pncp, objeto_contrato, valor_inicial,
                    data_publicacao_pncp, data_vigencia_inicio, data_vigencia_fim,
                    orgao_cnpj, orgao_razao_social, etl_timestamp, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doc.get("numeroControlePNCP"),
                    doc.get("objetoContrato"),
                    doc.get("valorInicial"),
                    doc.get("dataPublicacaoPncp"),
                    doc.get("dataVigenciaInicio"),
                    doc.get("dataVigenciaFim"),
                    orgao.get("cnpj"),
                    orgao.get("razaoSocial"),
                    doc.get("_etl_timestamp"),
                    doc.get("_source"),
                ),
            )
            if cursor.rowcount:
                inserted += 1

        self.connection.commit()
        self.logger.info("SQLite: %d registros inseridos.", inserted)
        return inserted

    def close(self) -> None:
        """Fecha a conexão com o banco SQLite."""
        self.connection.close()
        self.logger.info("Conexão SQLite encerrada.")
