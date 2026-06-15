"""Módulo de extração de dados da API do PNCP."""

import time
from typing import Any

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import PNCP_BASE_URL, PNCP_MAX_RECORDS, PNCP_PAGE_SIZE, PNCP_TIMEOUT
from utils.logger import get_logger


class PNCPExtractor:
    """Responsável por extrair dados da API pública do PNCP.

    Realiza chamadas HTTP paginadas aos endpoints do Portal Nacional de
    Contratações Públicas, com retry automático em caso de falha.
    """

    def __init__(self) -> None:
        """Inicializa o extrator com sessão HTTP e logger."""
        self.base_url = PNCP_BASE_URL
        self.timeout = PNCP_TIMEOUT
        self.page_size = PNCP_PAGE_SIZE
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        self.max_records = PNCP_MAX_RECORDS
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info("PNCPExtractor inicializado. Base URL: %s", self.base_url)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def _get(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        """Realiza uma requisição GET autenticada ao endpoint do PNCP.

        Args:
            endpoint (str): Caminho relativo do endpoint (ex: '/contratos').
            params (dict): Parâmetros de query string.

        Returns:
            dict: Resposta JSON da API.

        Raises:
            requests.HTTPError: Se a resposta indicar erro HTTP.
            requests.ConnectionError: Se não for possível conectar à API.
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as exc:
            self.logger.error("Erro HTTP %s em %s: %s", exc.response.status_code, url, exc)
            raise
        except requests.RequestException as exc:
            self.logger.error("Erro de conexão em %s: %s", url, exc)
            raise

    def _paginate(self, endpoint: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        """Percorre todas as páginas de um endpoint paginado do PNCP.

        Args:
            endpoint (str): Caminho relativo do endpoint.
            params (dict): Parâmetros base da requisição (sem 'pagina').

        Returns:
            list[dict]: Todos os registros agregados de todas as páginas.
        """
        results: list[dict[str, Any]] = []
        params = {**params, "pagina": 1, "tamanhoPagina": self.page_size}

        while True:
            self.logger.debug("Buscando página %d de %s", params["pagina"], endpoint)
            try:
                data = self._get(endpoint, params)
            except Exception as exc:
                self.logger.warning(
                    "Erro na página %d de %s — retornando %d registros parciais. Detalhe: %s",
                    params["pagina"],
                    endpoint,
                    len(results),
                    exc,
                )
                break

            records = data if isinstance(data, list) else data.get("data", [])
            results.extend(records)

            self.logger.info(
                "Página %d — %d registros obtidos (total acumulado: %d)",
                params["pagina"],
                len(records),
                len(results),
            )

            if len(records) < self.page_size:
                break

            if len(results) >= self.max_records:
                self.logger.info(
                    "Limite de %d registros atingido — parando extração.", self.max_records
                )
                break

            params["pagina"] += 1
            time.sleep(0.5)

        return results[:self.max_records]

    def fetch_contratos(self, data_inicial: str, data_final: str) -> list[dict[str, Any]]:
        """Busca contratos publicados no PNCP dentro do intervalo de datas.

        Args:
            data_inicial (str): Data de início no formato YYYYMMDD.
            data_final (str): Data de fim no formato YYYYMMDD.

        Returns:
            list[dict]: Lista de contratos retornados pela API.

        Raises:
            requests.HTTPError: Se a requisição à API falhar.
        """
        self.logger.info(
            "Extraindo contratos de %s a %s", data_inicial, data_final
        )
        params: dict[str, Any] = {
            "dataInicial": data_inicial,
            "dataFinal": data_final,
        }
        contratos = self._paginate("/contratos", params)
        self.logger.info("Total de contratos extraídos: %d", len(contratos))
        return contratos

    def fetch_atas(self, data_inicial: str, data_final: str) -> list[dict[str, Any]]:
        """Busca atas de registro de preço publicadas no PNCP.

        Args:
            data_inicial (str): Data de início no formato YYYYMMDD.
            data_final (str): Data de fim no formato YYYYMMDD.

        Returns:
            list[dict]: Lista de atas retornadas pela API.

        Raises:
            requests.HTTPError: Se a requisição à API falhar.
        """
        self.logger.info("Extraindo atas de %s a %s", data_inicial, data_final)
        params: dict[str, Any] = {
            "dataInicial": data_inicial,
            "dataFinal": data_final,
        }
        atas = self._paginate("/atas", params)
        self.logger.info("Total de atas extraídas: %d", len(atas))
        return atas
