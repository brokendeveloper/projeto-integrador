"""Módulo de transformação e limpeza dos dados extraídos do PNCP."""

from datetime import datetime, timezone
from typing import Any

from utils.logger import get_logger


class PNCPTransformer:
    """Responsável pela limpeza, normalização e enriquecimento dos dados do PNCP.

    Aplica transformações padronizadas sobre os registros brutos retornados
    pela API, preparando-os para persistência no banco de dados.
    """

    _DATE_FIELDS = (
        "dataPublicacaoPncp",
        "dataVigenciaInicio",
        "dataVigenciaFim",
        "dataAssinatura",
    )
    _MONETARY_FIELDS = ("valorInicial", "valorGlobal", "valorNominal")
    _TEXT_FIELDS = ("objetoContrato", "objetoCompra", "informacaoComplementar")

    def __init__(self) -> None:
        """Inicializa o transformador com logger."""
        self.logger = get_logger(self.__class__.__name__)

    def _normalize_date(self, value: Any) -> str | None:
        """Normaliza um valor de data para o formato ISO 8601.

        Args:
            value: Valor de data bruto (string ou None).

        Returns:
            str | None: Data em formato ISO 8601 ou None se inválido.
        """
        if not value:
            return None
        try:
            if isinstance(value, str):
                return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
            return str(value)
        except (ValueError, TypeError):
            self.logger.warning("Data inválida ignorada: %s", value)
            return None

    def _normalize_monetary(self, value: Any) -> float | None:
        """Converte um valor monetário para float.

        Args:
            value: Valor monetário bruto (string com pontuação ou numérico).

        Returns:
            float | None: Valor convertido ou None se inválido.
        """
        if value is None:
            return None
        try:
            if isinstance(value, str):
                cleaned = value.replace(".", "").replace(",", ".")
                return float(cleaned)
            return float(value)
        except (ValueError, TypeError):
            self.logger.warning("Valor monetário inválido ignorado: %s", value)
            return None

    def _strip_text(self, value: Any) -> str | None:
        """Remove espaços extras e padroniza campos de texto.

        Args:
            value: Valor de texto bruto.

        Returns:
            str | None: Texto limpo ou None se vazio.
        """
        if not isinstance(value, str):
            return value
        stripped = value.strip()
        return stripped if stripped else None

    def _remove_empty_fields(self, record: dict[str, Any]) -> dict[str, Any]:
        """Remove campos nulos ou vazios desnecessários do registro.

        Args:
            record (dict): Registro bruto.

        Returns:
            dict: Registro sem campos nulos/vazios.
        """
        return {k: v for k, v in record.items() if v is not None and v != ""}

    def transform(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Aplica todas as transformações sobre a lista de registros brutos.

        Operações realizadas por registro:
        - Normalização de campos de data para ISO 8601
        - Conversão de valores monetários para float
        - Limpeza de campos de texto (strip)
        - Remoção de campos nulos/vazios
        - Adição dos campos de metadados '_etl_timestamp' e '_source'

        Args:
            records (list[dict]): Lista de registros brutos da API.

        Returns:
            list[dict]: Lista de registros transformados e enriquecidos.
        """
        etl_timestamp = datetime.now(timezone.utc).isoformat()
        transformed: list[dict[str, Any]] = []

        for record in records:
            doc = dict(record)

            for field in self._DATE_FIELDS:
                if field in doc:
                    doc[field] = self._normalize_date(doc[field])

            for field in self._MONETARY_FIELDS:
                if field in doc:
                    doc[field] = self._normalize_monetary(doc[field])

            for field in self._TEXT_FIELDS:
                if field in doc:
                    doc[field] = self._strip_text(doc[field])

            doc = self._remove_empty_fields(doc)
            doc["_etl_timestamp"] = etl_timestamp
            doc["_source"] = "pncp_api"

            transformed.append(doc)

        self.logger.info("%d registros transformados com sucesso.", len(transformed))
        return transformed
