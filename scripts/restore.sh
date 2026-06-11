#!/usr/bin/env bash
# restore.sh — Restauração do MongoDB via mongorestore
#
# Uso:
#   MONGODB_URI="<uri>" \
#   MONGODB_DB="pncp_etl" \
#   BACKUP_PATH="backups/2026-06-11_02-00" \
#   ./scripts/restore.sh
#
# Parâmetros de ambiente:
#   MONGODB_URI   — URI completa de conexão ao MongoDB (obrigatória)
#   MONGODB_DB    — Nome do banco de dados alvo (padrão: pncp_etl)
#   BACKUP_PATH   — Caminho do diretório de backup a restaurar (obrigatório)
#
# ATENÇÃO: --drop apaga as collections existentes antes de restaurar.
#          Use com cautela em produção. Remova a flag para restauração aditiva.
#
# Requer: mongorestore (MongoDB Database Tools)

set -euo pipefail

MONGODB_URI="${MONGODB_URI:?Variável MONGODB_URI não definida}"
MONGODB_DB="${MONGODB_DB:-pncp_etl}"
BACKUP_PATH="${BACKUP_PATH:?Variável BACKUP_PATH não definida (ex: backups/2026-06-11_02-00)}"

if [[ ! -d "${BACKUP_PATH}/${MONGODB_DB}" ]]; then
    echo "[restore] ERRO: Diretório '${BACKUP_PATH}/${MONGODB_DB}' não encontrado." >&2
    exit 1
fi

echo "[restore] Restaurando banco '${MONGODB_DB}' a partir de '${BACKUP_PATH}'..."

mongorestore \
    --uri="${MONGODB_URI}" \
    --db="${MONGODB_DB}" \
    --dir="${BACKUP_PATH}/${MONGODB_DB}" \
    --gzip \
    --drop

echo "[restore] Restauração concluída com sucesso."
