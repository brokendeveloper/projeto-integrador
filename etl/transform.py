"""
Módulo responsável pela transformação e limpeza dos dados extraídos da API.
"""

import pandas as pd


def transform_universities(raw_data: list[dict]) -> pd.DataFrame:
    """
    Transforma a lista bruta de universidades em um DataFrame limpo e padronizado.

    Operações realizadas:
    - Renomeia a coluna 'state-province' para 'state_province'
    - Remove registros duplicados pelo par (name, country)
    - Preenche valores nulos em state_province com string vazia

    Args:
        raw_data: Lista de dicionários retornada pela função fetch_universities.

    Returns:
        DataFrame pandas com colunas limpas e dados prontos para carga.
    """
    df = pd.DataFrame(raw_data)
    df = df.rename(columns={"state-province": "state_province"})
    df = df.drop_duplicates(subset=["name", "country"])
    df["state_province"] = df["state_province"].fillna("")
    return df
