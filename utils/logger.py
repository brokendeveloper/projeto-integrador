"""Módulo de logger centralizado para o pipeline ETL."""

import logging
import os


def get_logger(name: str) -> logging.Logger:
    """Retorna um logger configurado com handler de console.

    Args:
        name (str): Nome do logger, geralmente o nome da classe.

    Returns:
        logging.Logger: Logger configurado com o nível definido em LOG_LEVEL.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        level = os.getenv("LOG_LEVEL", "INFO").upper()
        logger.setLevel(level)
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        )
        logger.addHandler(handler)
    return logger
