"""
Módulo responsável pelo carregamento dos dados transformados no banco SQLite.
"""

import sqlite3

import pandas as pd


def create_tables(connection: sqlite3.Connection) -> None:
    """
    Cria as tabelas do banco de dados caso ainda não existam.

    Tabelas criadas:
    - universities: dados principais da universidade
    - domains: domínios de e-mail da universidade (relação 1:N)
    - web_pages: páginas web da universidade (relação 1:N)

    Args:
        connection: Conexão ativa com o banco de dados SQLite.
    """
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS universities (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT    NOT NULL,
            country         TEXT    NOT NULL,
            alpha_two_code  TEXT    NOT NULL,
            state_province  TEXT,
            UNIQUE(name, country)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS domains (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            university_id   INTEGER NOT NULL,
            domain          TEXT    NOT NULL,
            FOREIGN KEY (university_id) REFERENCES universities(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS web_pages (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            university_id   INTEGER NOT NULL,
            url             TEXT    NOT NULL,
            FOREIGN KEY (university_id) REFERENCES universities(id)
        )
    """)

    connection.commit()


def load_universities(df: pd.DataFrame, connection: sqlite3.Connection) -> None:
    """
    Carrega um DataFrame de universidades no banco SQLite usando INSERT OR IGNORE.

    A estratégia INSERT OR IGNORE garante que registros já existentes (mesmo par
    name + country) não sejam duplicados, preservando o histórico e permitindo
    execuções repetidas do pipeline sem inconsistências.

    Para cada universidade inserida com sucesso, também persiste os domínios e
    páginas web nas tabelas normalizadas correspondentes.

    Args:
        df: DataFrame transformado com dados das universidades.
        connection: Conexão ativa com o banco de dados SQLite.
    """
    cursor = connection.cursor()

    for _, row in df.iterrows():
        cursor.execute(
            """
            INSERT OR IGNORE INTO universities
                (name, country, alpha_two_code, state_province)
            VALUES (?, ?, ?, ?)
            """,
            (
                row["name"],
                row["country"],
                row["alpha_two_code"],
                row.get("state_province", ""),
            ),
        )

        if cursor.rowcount == 0:
            continue

        university_id = cursor.lastrowid

        for domain in row.get("domains", []):
            cursor.execute(
                "INSERT INTO domains (university_id, domain) VALUES (?, ?)",
                (university_id, domain),
            )

        for url in row.get("web_pages", []):
            cursor.execute(
                "INSERT INTO web_pages (university_id, url) VALUES (?, ?)",
                (university_id, url),
            )

    connection.commit()
