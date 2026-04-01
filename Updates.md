Voraussetzung (einmalig erledigt)

Server läuft.
Domain und HTTPS laufen.
Deploy-Skript funktioniert:
sudo /usr/local/bin/lernplattform_deploy.sh
Du hast das alles schon eingerichtet.

Update-Anleitung Für Neulinge

Lokal ändern und testen

Projekt lokal öffnen.

Änderungen machen.

Lokal kurz testen:
python manage.py runserver

Wenn ok, stoppen und committen:
git add .
git commit -m "Kurze Beschreibung der Änderung"
git push origin main

Vor dem Server-Update (empfohlen)

Auf Server einloggen:
ssh deploy@deine-domain

Manuelles Backup starten:
sudo /usr/local/bin/lernplattform_backup.sh

Server-Update ausführen

Auf dem Server diesen einen Befehl starten:
sudo /usr/local/bin/lernplattform_deploy.sh

Was der Befehl automatisch macht:

git pull

pip install

migrate

collectstatic

Dienst-Neustart

Nach dem Update kurz prüfen

Service ok?
sudo systemctl status lernplattform --no-pager -l

Login-Seite erreichbar?
curl -I https://deine-domain/accounts/login/

Admin erreichbar?
curl -I https://deine-domain/admin/

Erwartung:

Service active (running)
Login 200 oder 302
Admin 302 auf /admin/login/ ist normal
Wenn etwas schiefgeht

Logs prüfen:
sudo journalctl -u lernplattform -n 100 --no-pager
Nginx prüfen:
sudo systemctl status nginx --no-pager -l
Fehler nach Migration? Dann Deploy-Ausgabe hier posten, ich sage dir sofort den Fix.
Dein Mini-Workflow (Merkhilfe)

Lokal ändern
git push
ssh auf Server
backup
deploy
kurz testen
Wenn du willst, schreibe ich dir jetzt noch eine Super-Kurzversion mit nur 6 Befehlen zum Copy-Paste für jeden Release-Tag.

GPT-5.3-Codex • 0.9x