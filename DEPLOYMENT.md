# Lernplattform Deployment Guide

Komplette Schritt-für-Schritt-Anleitung zum Deployment der Lernplattform auf Hetzner Cloud.

---

## 1. Hetzner Cloud Server Erstellen und Konfigurieren

### 1.1 Server kaufen/mieten

1. **Hetzner Cloud** (https://console.hetzner.cloud) öffnen
2. **Projekt erstellen** oder vorhandenes nutzen
3. **Create Server** klicken
   - **Image**: Ubuntu 24.04 (LTS)
   - **Type**: CPX22 (2 vCPU x86 AMD, 4GB RAM, 80 GB NVMe) – beste Wahl für Lernplattform
   - **Datacenter**: Falkenstein (schnell zu DE) oder deine Nähe
   - **SSH Key**: Neue erstellen oder existierende Select >  KEY HINZUFÜGEN
   - **Server Name**: `lernplattform`
   - **Create & Buy Now**

4. **Nach dem Start**: Server IP notieren (z.B. `123.45.67.89`)

### 1.2 Domain vorbereiten

1. Domain-Provider (z.B. Ionos, Namecheap) öffnen
2. **A-Record** auf Server-IP setzen:
   - Host: `@` (oder leer lassen)
   - Typ: `A`
   - Wert: `123.45.67.89`
   - Optional: `www` auch auf gleiche IP

3. **CNAME** für www (falls nicht gemacht):
   - Host: `www`
   - Typ: `CNAME`
   - Wert: `deine-domain.de.`

Nach ~1-5 Min: `ping deine-domain.de` sollte Server-IP zurückgeben

---

## 2. Server-Grundkonfiguration

SSH zum Server:
```bash
ssh root@123.45.67.89
```

### 2.1 System Update und Basis-Tools

```bash
apt update
apt upgrade -y
apt install -y \
    build-essential \
    python3-venv \
    python3-dev \
    python3-pip \
    git \
    nginx \
    postgresql \
    postgresql-contrib \
    ufw \
    fail2ban \
    curl \
    wget \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils
```

> **Hinweis**: CPX22 hat x86-AMD-Architektur mit 80 GB Speicher – ideal für dein Projekt mit Uploads und OCR. Tesseract und Poppler sind auf Ubuntu standardmäßig verfügbar.

### 2.2 Firewall konfigurieren

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

Bestätigung: `y`

### 2.3 Deploy-User anlegen

```bash
adduser deploy
# Passwort setzen (oder leer lassen für SSH-Key-only)
```

Ihm Sudo-Rechte geben:
```bash
usermod -aG sudo deploy
```

SSH-Zugang von lokal einrichten (optional, aber empfohlen):
```bash
su - deploy
mkdir -p ~/.ssh
# Deine lokale public key einfügen:
echo "ssh-rsa AAAA... your-key" >> ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

Danach als `deploy` anmelden:
```bash
ssh deploy@deine-domain.de
```

---

## 3. Django-Projekt klonen und Umgebung einrichten

Weiterhin als `deploy` User:

```bash
mkdir -p /var/www
cd /var/www
git clone https://github.com/DEIN_ACCOUNT/lernplattform.git
cd lernplattform
```

### 3.1 Python Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.2 Environment-Variablen einrichten

Kopiere `.env.example` zu `.env`:
```bash
cp .env.example .env
nano .env
```

Wichtige Felder ausfüllen:

```env
SECRET_KEY=generate_this_with_django_shell  # siehe weiter unten
DEBUG=False
ALLOWED_HOSTS=deine-domain.de,www.deine-domain.de
CSRF_TRUSTED_ORIGINS=https://deine-domain.de,https://www.deine-domain.de

DB_NAME=lernplattform_db
DB_USER=lernplattform_user
DB_PASSWORD=very-strong-password-minimum-20-chars
DB_HOST=localhost
DB_PORT=5432
```

**SECRET_KEY generieren**:
```bash
source .venv/bin/activate
python manage.py shell
# In der Python Shell:
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
# Output kopieren und in .env SECRET_KEY einfügen
exit()
```

---

## 4. PostgreSQL Datenbank einrichten

```bash
sudo -u postgres psql
```

In der Postgres-Shell:
```sql
CREATE DATABASE lernplattform_db;
CREATE USER lernplattform_user WITH PASSWORD 'your-password-from-env';
ALTER ROLE lernplattform_user SET client_encoding TO 'utf8';
ALTER ROLE lernplattform_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE lernplattform_user SET default_transaction_deferrable TO on;
GRANT ALL PRIVILEGES ON DATABASE lernplattform_db TO lernplattform_user;
\q
```

**Test-Verbindung**:
```bash
psql -h localhost -U lernplattform_user -d lernplattform_db -c "SELECT 1"
```

---

## 5. Django Initialisierung

```bash
cd /var/www/lernplattform
source .venv/bin/activate
```

Migrationen ausführen:
```bash
python manage.py migrate --settings=lernplattform.settings_production
```

Static Files sammeln:
```bash
python manage.py collectstatic --noinput --settings=lernplattform.settings_production
```

Admin-User (Superuser) anlegen:
```bash
python manage.py createsuperuser --settings=lernplattform.settings_production
# Django fragt nach: Username, Email, Password (zweimal eingeben)
```

---

## 6. Gunicorn als Systemd Service

Erstelle Datei: `/etc/systemd/system/lernplattform.service`

```bash
sudo nano /etc/systemd/system/lernplattform.service
```

Einfügen (passt Datei-Pfade ggf. an):
```ini
[Unit]
Description=Lernplattform Gunicorn Application
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=notify
User=deploy
Group=www-data
WorkingDirectory=/var/www/lernplattform
Environment="PATH=/var/www/lernplattform/.venv/bin"
ExecStart=/var/www/lernplattform/.venv/bin/gunicorn \
    --workers 4 \
    --worker-class sync \
    --bind 127.0.0.1:8000 \
    --timeout 60 \
    --access-logfile /var/log/lernplattform/gunicorn_access.log \
    --error-logfile /var/log/lernplattform/gunicorn_error.log \
    lernplattform.wsgi:application

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Log-Verzeichnis vorbereiten:
```bash
sudo mkdir -p /var/log/lernplattform
sudo chown deploy:www-data /var/log/lernplattform
```

Service aktivieren und starten:
```bash
sudo systemctl daemon-reload
sudo systemctl enable lernplattform
sudo systemctl start lernplattform
sudo systemctl status lernplattform
```

Status sollte **active (running)** sein. Wenn nicht:
```bash
sudo journalctl -u lernplattform -n 50  # letzte 50 Zeilen
```

---

## 7. Nginx Reverse Proxy

Erstelle Datei: `/etc/nginx/sites-available/lernplattform`

```bash
sudo nano /etc/nginx/sites-available/lernplattform
```

Einfügen:
```nginx
server {
    listen 80;
    server_name deine-domain.de www.deine-domain.de;

    client_max_body_size 100M;

    # Redirect Static Files
    location /static/ {
        alias /var/www/lernplattform/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Redirect Media Files
    location /media/ {
        alias /var/www/lernplattform/media/;
        expires 7d;
    }

    # Proxy zu Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

Enable:
```bash
sudo ln -s /etc/nginx/sites-available/lernplattform /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default 2>/dev/null || true
sudo nginx -t  # Syntax Check
sudo systemctl reload nginx
```

Test: `curl http://deine-domain.de` – sollte Seite zurückgeben

---

## 8. HTTPS mit Let's Encrypt (Certbot)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d deine-domain.de -d www.deine-domain.de
```

Certbot fragt:
- Email: deine-email@beispiel.de
- Terms: `y`
- Newsletter: `n` (oder `y`)

Auto-Renewal aktivieren:
```bash
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

Test: `https://deine-domain.de` sollte funktionieren

---

## 9. Automatische Backups einrichten

Skript-Datei vorbereiten:
```bash
sudo cp /var/www/lernplattform/backup.sh /usr/local/bin/lernplattform_backup.sh
sudo chmod +x /usr/local/bin/lernplattform_backup.sh
```

Cron-Job für tägliche Backups um 03:00 Uhr:
```bash
sudo crontab -e
```

Einfügen:
```cron
0 3 * * * /usr/local/bin/lernplattform_backup.sh >> /var/log/lernplattform_backup.log 2>&1
```

Speichern (Ctrl+O, Enter, Ctrl+X)

Testen:
```bash
sudo /usr/local/bin/lernplattform_backup.sh
sudo ls -lh /var/backups/lernplattform/
```

---

## 10. Deploy-Skript einrichten

```bash
sudo cp /var/www/lernplattform/deploy.sh /usr/local/bin/lernplattform_deploy.sh
sudo chmod +x /usr/local/bin/lernplattform_deploy.sh
```

Danach reicht zum Deployment:
```bash
cd /var/www/lernplattform
lernplattform_deploy.sh
```

---

## Workflow: Lokal entwickeln → Server deployen

### Lokal (deinen Computer)

```bash
# Änderungen tätigen, lokal testen
python manage.py test  # optional
git add .
git commit -m "Feature XYZ hinzugefügt"
git push origin main
```

### Server (automatisches Deployment)

```bash
ssh deploy@deine-domain.de
/usr/local/bin/lernplattform_deploy.sh
```

Fertig! Seite ist aktualisiert. Status prüfen:
```bash
sudo systemctl status lernplattform
tail -f /var/log/lernplattform/*
```

---

## Backup & Restore

### Manuell ein Backup machen

```bash
sudo /usr/local/bin/lernplattform_backup.sh
ls -lh /var/backups/lernplattform/
```

### Restore Test (WICHTIG!)

Führe regelmäßig durch, um sicherzustellen, dass Backups funktionieren.

1. **Klon-Datenbasis erstellen**
```bash
sudo -u postgres psql
CREATE DATABASE lernplattform_test;
\q
```

2. **Backup einspielen**
```bash
sudo -u postgres psql lernplattform_test < <(zcat /var/backups/lernplattform/db_LATEST.sql.gz)
```

3. **Media entpacken (optional für vollen Test)**
```bash
cd /tmp
tar -xzf /var/backups/lernplattform/media_LATEST.tar.gz
ls media/
```

4. **Test-DB löschen**
```bash
sudo -u postgres psql
DROP DATABASE lernplattform_test;
\q
```

Wenn alles klappt: prima! Backups sind sicher.

---

## Monitoring & Troubleshooting

### Logs anschauen

Django Logs:
```bash
tail -f /var/log/lernplattform/django.log
```

Gunicorn Logs:
```bash
sudo tail -f /var/log/lernplattform/gunicorn_*.log
```

Nginx Logs:
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

Service-Status:
```bash
sudo systemctl status lernplattform
sudo systemctl status nginx
sudo systemctl status postgresql
```

### Service neu starten

Wenn etwas hängt:
```bash
sudo systemctl restart lernplattform
sudo systemctl restart nginx
sudo systemctl restart postgresql
```

### Speicher überprüfen

```bash
df -h              # Disk usage
free -h            # RAM
ps aux | grep python  # Running processes
```

---

## Security Best Practices

1. **SSH hardening**: Passwort-Login deaktivieren
   ```bash
   sudo nano /etc/ssh/sshd_config
   # PasswordAuthentication no setzen
   sudo systemctl restart ssh
   ```

2. **Fail2Ban**: Bruteforce-Schutz (bereits aktiv)
   ```bash
   sudo fail2ban-client status
   ```

3. **Firewall Logs**:
   ```bash
   sudo ufw status verbose
   ```

4. **Regelmäßige Updates**:
   ```bash
   sudo unattended-upgrade
   ```

---

   - CPX21 → CPX31 (4 vCPU, 8 GB RAM) für mehr Last
   - CPX41 (8 vCPU, 16 GB RAM) für sehr viele gleichzeitige Nutzer

2. **Gunicorn Worker erhöhen**: `/etc/systemd/system/lernplattform.service`
   - Aktuelle Einstellung: `--workers 4`
   - Bei CPX31: auf `--workers 6` erhöhen
   - Dann `sudo systemctl restart lernplattform`

3. **Postgres optimieren**: je nach Load (gerne später machen)


1. **CPU/RAM upgraden**: Hetzner Cloud UI > Server > Resize (mit downtime)
2. **Gunicorn Worker erhöhen**: `/etc/systemd/system/lernplattform.service`
   - `--workers 5` statt 3
3. **Postgres optimieren**: je nach Load (gerne später machen)
4. **CDN hinzufügen**: für Static Files, falls viele Nutzer weltweit

---

## Checkliste vor Go-Live

- [ ] Domain zeigt auf Server IP
- [ ] HTTPS/SSL funktioniert
- [ ] Admin-Login funktioniert
- [ ] Backup läuft, Restore getestet
- [ ] Firewall korrekt konfiguriert
- [ ] Logs überprüft, keine Fehler
- [ ] Performance getestet mit mehreren gleichzeitigen Nutzern
- [ ] OCR auf Linux getestet (ggf. Pfade anpassen)
- [ ] CODE_EXECUTION: überprüft, ob Security-Sandboxing reicht

---

## Support & Weitere Infos

- **Django Doku**: https://docs.djangoproject.com/
- **Gunicorn**: https://docs.gunicorn.org/
- **Let's Encrypt Cert**: Auto-Renew prüfen: `sudo certbot renew --dry-run`
- **Hetzner**: https://docs.hetzner.cloud/

Bei Fragen oder Problemen: Logs prüfen, dann im Projekt-Git Issue öffnen oder Support kontaktieren.
