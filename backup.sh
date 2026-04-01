#!/usr/bin/env bash
#
# Backup script for Lernplattform (Postgres + Media)
# Backs up database, media files, and keeps last 14 days
# Run automatically via cron: 0 3 * * * /usr/local/bin/lernplattform_backup.sh
#

set -euo pipefail

# Configuration
PROJECT_DIR="/var/www/lernplattform/lernplattformne"
BACKUP_DIR="/var/backups/lernplattform"
RETENTION_DAYS=14
LOG_FILE="/var/log/lernplattform_backup.log"
TIMESTAMP=$(date +%F_%H-%M-%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1" | tee -a "${LOG_FILE}"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "${LOG_FILE}"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "${LOG_FILE}"
}

# Ensure backup directory exists
mkdir -p "${BACKUP_DIR}"
mkdir -p "$(dirname "${LOG_FILE}")"

log_info "=== Backup started at ${TIMESTAMP} ==="

# Load only required DB variables from .env without sourcing shell syntax.
# This avoids failures when other vars (e.g. SECRET_KEY) contain shell-special chars.
get_env_var() {
    local key="$1"
    local raw
    raw=$(grep -m1 "^${key}=" "${PROJECT_DIR}/.env" | cut -d'=' -f2- || true)
    raw="${raw%\"}"
    raw="${raw#\"}"
    raw="${raw%\'}"
    raw="${raw#\'}"
    printf '%s' "${raw}"
}

DB_HOST="$(get_env_var DB_HOST)"
DB_USER="$(get_env_var DB_USER)"
DB_NAME="$(get_env_var DB_NAME)"
DB_PASSWORD="$(get_env_var DB_PASSWORD)"

if [ -z "${DB_HOST}" ] || [ -z "${DB_USER}" ] || [ -z "${DB_NAME}" ] || [ -z "${DB_PASSWORD}" ]; then
    log_error "Missing DB_* values in ${PROJECT_DIR}/.env"
    exit 1
fi

export PGPASSWORD="${DB_PASSWORD}"

# Define backup file names
DB_BACKUP="${BACKUP_DIR}/db_${TIMESTAMP}.sql.gz"
MEDIA_BACKUP="${BACKUP_DIR}/media_${TIMESTAMP}.tar.gz"

# Backup PostgreSQL database
log_info "Backing up PostgreSQL database..."
if pg_dump -h "${DB_HOST}" -U "${DB_USER}" "${DB_NAME}" 2>>"${LOG_FILE}" | gzip > "${DB_BACKUP}" 2>>"${LOG_FILE}"; then
    log_info "✓ Database backed up: $(du -h "${DB_BACKUP}" | cut -f1)"
else
    log_error "✗ Database backup failed!"
    exit 1
fi
unset PGPASSWORD

# Backup media directory
log_info "Backing up media files..."
if [ -d "${PROJECT_DIR}/media" ]; then
    if tar -czf "${MEDIA_BACKUP}" -C "${PROJECT_DIR}" media 2>>"${LOG_FILE}"; then
        log_info "✓ Media backed up: $(du -h "${MEDIA_BACKUP}" | cut -f1)"
    else
        log_error "✗ Media backup failed!"
        exit 1
    fi
else
    log_warn "Media directory not found, skipping media backup"
fi

# Cleanup old backups (keep last RETENTION_DAYS days)
log_info "Cleaning up backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -type f \( -name "*.sql.gz" -o -name "*.tar.gz" \) | while read file; do
    if [ "$(find "${file}" -mtime +${RETENTION_DAYS})" ]; then
        log_warn "Removing old backup: $(basename "${file}")"
        rm -f "${file}"
    fi
done

log_info "=== Backup completed successfully ==="
log_info "You should periodically test restores. See DEPLOYMENT.md for restore instructions."
