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
