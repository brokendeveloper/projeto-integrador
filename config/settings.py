"""Módulo de configurações carregadas via variáveis de ambiente."""

import os

from dotenv import load_dotenv

load_dotenv()

PNCP_BASE_URL: str = os.getenv("PNCP_BASE_URL", "https://pncp.gov.br/api/consulta/v1")
PNCP_TIMEOUT: int = int(os.getenv("PNCP_TIMEOUT", "30"))
PNCP_PAGE_SIZE: int = int(os.getenv("PNCP_PAGE_SIZE", "50"))

MONGODB_URI: str = os.getenv("MONGODB_URI", "")
MONGODB_DB: str = os.getenv("MONGODB_DB", "pncp_etl")
MONGODB_COLLECTION: str = os.getenv("MONGODB_COLLECTION", "contratos")
