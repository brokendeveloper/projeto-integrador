"""
Módulo responsável pela extração de dados da API Hipolabs de universidades.
"""

import requests


def fetch_universities(country: str) -> list[dict]:
    """
    Extrai a lista de universidades de um país via API Hipolabs.

    Args:
        country: Nome do país em inglês (ex: "Brazil", "Argentina").

    Returns:
        Lista de dicionários com os dados brutos retornados pela API.

    Raises:
        requests.HTTPError: Se a resposta da API indicar erro HTTP.
        requests.ConnectionError: Se não for possível conectar à API.
    """
    url = f"http://universities.hipolabs.com/search?country={country}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()
