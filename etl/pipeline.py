"""Módulo de orquestração do pipeline ETL do PNCP."""

from datetime import datetime, timedelta, timezone

from etl.extractor import PNCPExtractor
from etl.loader import MongoLoader, SQLiteLoader
from etl.transformer import PNCPTransformer
from utils.logger import get_logger


class ETLPipeline:
    """Orquestra as etapas de Extração, Transformação e Carga do pipeline PNCP.

    Coordena a execução sequencial do PNCPExtractor, PNCPTransformer e
    MongoLoader/SQLiteLoader, garantindo logging completo e tratamento de erros.
    """

    def __init__(
        self,
        data_inicial: str | None = None,
        data_final: str | None = None,
    ) -> None:
        """Inicializa o pipeline com as datas de extração e os módulos ETL.

        Se as datas não forem fornecidas, usa os últimos 7 dias por padrão.

        Args:
            data_inicial (str | None): Data de início no formato YYYYMMDD.
            data_final (str | None): Data de fim no formato YYYYMMDD.
        """
        self.logger = get_logger(self.__class__.__name__)

        hoje = datetime.now(timezone.utc)
        self.data_final = data_final or hoje.strftime("%Y%m%d")
        self.data_inicial = data_inicial or (hoje - timedelta(days=7)).strftime("%Y%m%d")

        self.extractor = PNCPExtractor()
        self.transformer = PNCPTransformer()
        self.mongo_loader = MongoLoader()
        self.sqlite_loader = SQLiteLoader()

    def run(self) -> None:
        """Executa o pipeline ETL completo.

        Etapas:
        1. Loga início da execução com timestamp.
        2. Extrai contratos e atas da API do PNCP.
        3. Transforma e normaliza os dados.
        4. Carrega no MongoDB Atlas e no SQLite local.
        5. Loga fim da execução com contagem de registros processados.

        Raises:
            Exception: Qualquer exceção é logada antes de ser re-lançada.
        """
        inicio = datetime.now(timezone.utc)
        self.logger.info(
            "=== Pipeline ETL PNCP iniciado em %s ===", inicio.isoformat()
        )
        self.logger.info(
            "Intervalo de extração: %s a %s", self.data_inicial, self.data_final
        )

        try:
            # Extração
            contratos = self.extractor.fetch_contratos(self.data_inicial, self.data_final)
            atas = self.extractor.fetch_atas(self.data_inicial, self.data_final)
            raw_records = contratos + atas
            self.logger.info("Extração concluída: %d registros brutos.", len(raw_records))

            # Transformação
            transformed = self.transformer.transform(raw_records)
            self.logger.info("Transformação concluída: %d registros.", len(transformed))

            # Carga — MongoDB Atlas
            total_mongo = self.mongo_loader.load(transformed)

            # Carga — SQLite (diferencial)
            total_sqlite = self.sqlite_loader.load(transformed)

            # Publicação no Kafka (opcional — ativo apenas se KAFKA_BOOTSTRAP_SERVERS definido)
            from kafka.producer import publicar_contratos
            total_kafka = publicar_contratos(transformed)

            fim = datetime.now(timezone.utc)
            duracao = (fim - inicio).total_seconds()
            kafka_info = f" | Kafka: {total_kafka}" if total_kafka else ""
            self.logger.info(
                "=== Pipeline concluído em %.2fs | MongoDB: %d | SQLite: %d%s ===",
                duracao,
                total_mongo,
                total_sqlite,
                kafka_info,
            )

        except Exception as exc:
            self.logger.error("Erro crítico no pipeline: %s", exc, exc_info=True)
            raise
        finally:
            self.mongo_loader.close()
            self.sqlite_loader.close()
