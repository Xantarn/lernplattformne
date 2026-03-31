#!/usr/bin/env bash
#
# Deploy script for Lernplattform
# Run this on the Hetzner server after git pull
# Usage: ./deploy.sh
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_DIR="/var/www/lernplattform"
VENV_DIR="${PROJECT_DIR}/.venv"

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
if [ ! -f "${PROJECT_DIR}/.env" ]; then
    log_error ".env file not found in ${PROJECT_DIR}"
    log_error "Please create .env file from .env.example with your production settings"
    exit 1
fi

cd "${PROJECT_DIR}"

log_info "1/5: Pulling latest code from git..."
git pull origin main

log_info "2/5: Installing/updating dependencies..."
source "${VENV_DIR}/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt

log_info "3/5: Running database migrations..."
python manage.py migrate --settings=lernplattform.settings_production

log_info "4/5: Collecting static files..."
python manage.py collectstatic --noinput --settings=lernplattform.settings_production

log_info "5/5: Restarting application service..."
sudo systemctl restart lernplattform
sudo systemctl reload nginx

# Check if service is running
if sudo systemctl is-active --quiet lernplattform; then
    log_info "✓ Deployment successful!"
    log_info "Lernplattform is running."
else
    log_error "✗ Service failed to start. Check logs with: sudo systemctl status lernplattform"
    exit 1
fi

log_info "Done! You can access the application at your domain."
