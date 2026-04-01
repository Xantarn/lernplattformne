# Updates.md

Einfache Schritt-fuer-Schritt-Anleitung fuer Updates auf dem Server.

## 1) Standard-Workflow (immer gleich)

### A. Lokal (dein Rechner)

```bash
cd C:\Users\xanta\Documents\PPlatform\lernplattform
git add .
git commit -m "Kurze Beschreibung der Aenderung"
git push origin main
```

### B. Server

```bash
ssh deploy@lernlattformne.de
cd /var/www/lernplattform/lernplattformne
sudo /usr/local/bin/lernplattform_backup.sh
/usr/local/bin/lernplattform_deploy.sh
```

Wichtig: Deploy immer ohne sudo starten.

```bash
/usr/local/bin/lernplattform_deploy.sh
```

Nicht verwenden:

```bash
sudo /usr/local/bin/lernplattform_deploy.sh
```

## 2) Schnelltest nach jedem Update

```bash
curl -I https://lernlattformne.de/accounts/login/
curl -I https://lernlattformne.de/admin/
sudo systemctl status lernplattform --no-pager -l
```

Erwartung:
- Login: 200 oder 302
- Admin: 302 auf /admin/login/ ist normal
- Service: active (running)

## 3) Wenn git pull blockiert (lokale Datei geaendert)

Fehler-Beispiel: local changes would be overwritten by merge.

```bash
cd /var/www/lernplattform/lernplattformne
git stash push -m "server-local-change" -- deploy.sh
git pull origin main
chmod +x deploy.sh
sudo cp deploy.sh /usr/local/bin/lernplattform_deploy.sh
sudo chmod +x /usr/local/bin/lernplattform_deploy.sh
/usr/local/bin/lernplattform_deploy.sh
git stash list
git stash drop
```

## 4) Wenn Rechte kaputt sind (permission denied in .git)

Fehler-Beispiel: insufficient permission for adding an object to repository database.

```bash
cd /var/www/lernplattform/lernplattformne
sudo chown -R deploy:deploy /var/www/lernplattform/lernplattformne
git status
```

Danach normal weiter mit Pull + Deploy.

## 5) Backup kurz pruefen

```bash
sudo ls -lh /var/backups/lernplattform
sudo tail -n 40 /var/log/lernplattform_backup.log
sudo crontab -l
```

## 6) Mini-Checkliste fuer Release-Tag

1. Lokal: commit + push
2. Server: backup
3. Server: deploy (ohne sudo)
4. Login/Admin testen
5. Service-Status checken

Wenn ein Schritt fehlschlaegt: Fehlermeldung komplett kopieren und dann gezielt fixen.























Klar, wir machen es ganz einfach, Schritt für Schritt zum Nachmachen.

Auf deinem PC (lokal) ins Projekt gehen
In PowerShell:
cd C:\Users\xanta\Documents\PPlatform\lernplattform

Änderung speichern und hochladen
Nacheinander ausführen:
git add base.html
git commit -m "Add graphite theme palette"
git push origin main

Wenn bei commit steht nothing to commit, ist das okay, dann einfach mit push weitermachen.

Auf den Server verbinden
In PowerShell:
ssh deploy@lernlattformne.de

Auf dem Server ins Projekt gehen
cd /var/www/lernplattform/lernplattformne

Sicherheits-Backup machen (empfohlen)
sudo /usr/local/bin/lernplattform_backup.sh

Deployment ausführen
sudo /usr/local/bin/lernplattform_deploy.sh

Kurz prüfen, ob alles läuft
curl -I https://lernlattformne.de/accounts/login/
curl -I https://lernlattformne.de/admin/

Erwartung:

Login: 200 oder 302

Admin: 302 auf /admin/login/ ist normal

Im Browser testen
Seite neu laden und oben auf Theme klicken, bis Graphite angezeigt wird.

Wenn du willst, schick mir einfach die Ausgabe von Schritt 6 und 7, dann bestätige ich dir sofort, ob alles sauber deployed ist.

