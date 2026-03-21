"""
Ponto de entrada do pipeline ETL de universidades.

Executa sequencialmente as etapas de Extração, Transformação e Carga (ETL)
para cada país listado em COUNTRIES, persistindo os dados em SQLite.
"""

import os
import sqlite3

from etl.extract import fetch_universities
from etl.load import create_tables, load_universities
from etl.transform import transform_universities

COUNTRIES = ["Brazil", "Argentina", "Portugal", "United States"]
DB_PATH = "db/universities.db"


def run_pipeline() -> None:
    """
    Executa o pipeline ETL completo para todos os países configurados.

    Para cada país em COUNTRIES:
    1. Extrai dados da API Hipolabs
    2. Transforma e limpa os dados
    3. Carrega no banco SQLite

    Raises:
        requests.HTTPError: Se a API retornar erro HTTP em algum país.
        sqlite3.Error: Se ocorrer erro na operação com o banco de dados.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    create_tables(connection)

    for country in COUNTRIES:
        print(f"[ETL] Processando: {country}...")
        raw = fetch_universities(country)
        df = transform_universities(raw)
        load_universities(df, connection)
        print(f"      → {len(df)} registros processados.")

    connection.close()
    print("[ETL] Pipeline concluído com sucesso.")


if __name__ == "__main__":
    run_pipeline()
