# HTML-Regelwerk erstellen

Konvertiere die sortierten Markdown-Dateien in `german-ordered/` zu selbstständigen HTML-Dateien mit Navigation und Fuzzy-Suche.

---

## Ablauf

1. Führe das Konvertierungsskript aus:

```bash
python3 tools/build-html/md_to_html.py
```

2. Prüfe die Ausgabe:
   - HTML-Dateien in `german-html/` vorhanden?
   - Keine externen Referenzen (self-contained)?
   - Zeilenzahl und Dateigröße plausibel?

3. Gib dem Benutzer einen kurzen Bericht mit:
   - Erzeugte Dateien und deren Größe
   - Anzahl der Navigationseinträge und Suchindex-Abschnitte
   - Hinweis, die Datei im Browser zu öffnen und Navigation + Suche zu testen

## Voraussetzungen

- `pandoc` muss installiert sein
- `tools/build-html/fuse.min.js` muss vorhanden sein
- Eingabedateien müssen in `german-ordered/` liegen (ggf. zuerst `/sort-entries` ausführen)
