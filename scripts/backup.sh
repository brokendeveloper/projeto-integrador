#!/usr/bin/env bash
# backup.sh — Backup do MongoDB via mongodump
#
# Uso:
#   MONGODB_URI="<uri>" MONGODB_DB="pncp_etl" ./scripts/backup.sh
#
# Saída: backups/YYYY-MM-DD_HH-MM/
# Requer: mongodump (MongoDB Database Tools)
#   Ubuntu: https://www.mongodb.com/try/download/database-tools
#   macOS:  brew install mongodb-database-tools

set -euo pipefail

MONGODB_URI="${MONGODB_URI:?Variável MONGODB_URI não definida}"
MONGODB_DB="${MONGODB_DB:-pncp_etl}"
TIMESTAMP="$(date +%Y-%m-%d_%H-%M)"
BACKUP_DIR="backups/${TIMESTAMP}"

mkdir -p "${BACKUP_DIR}"

echo "[backup] Iniciando backup do banco '${MONGODB_DB}' em ${TIMESTAMP}..."

mongodump \
    --uri="${MONGODB_URI}" \
    --db="${MONGODB_DB}" \
    --out="${BACKUP_DIR}" \
    --gzip

echo "[backup] Backup concluído: ${BACKUP_DIR}"
echo "[backup] Conteúdo:"
ls -lh "${BACKUP_DIR}/${MONGODB_DB}/"
