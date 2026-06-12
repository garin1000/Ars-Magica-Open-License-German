# HTML-Regelwerk erstellen

Konvertiere Markdown-Dateien aus `german-ordered/` zu selbstständigen HTML-Dateien mit Navigation und Fuzzy-Suche.

**Argument (optional):** Pfad zu einer oder mehreren Markdown-Dateien. Ohne Argument werden alle `.md`-Dateien in `german-ordered/` konvertiert.

---

## Ablauf

1. Prüfe, ob das Argument der vollständige Dateiname ist. Ergänze, wenn nicht.

2. Führe das Konvertierungsskript aus:

```bash
python3 tools/build-html/md_to_html.py $ARGUMENTS
```

3. Prüfe die Ausgabe:
   - HTML-Dateien in `german-html/` vorhanden?
   - Keine externen Referenzen (self-contained)?
   - Zeilenzahl und Dateigröße plausibel?

4. Gib dem Benutzer einen kurzen Bericht mit:
   - Erzeugte Dateien und deren Größe
   - Anzahl der Navigationseinträge und Suchindex-Abschnitte
   - Hinweis, die Datei im Browser zu öffnen und Navigation + Suche zu testen

## Voraussetzungen

- `pandoc` muss installiert sein
- `tools/build-html/fuse.min.js` muss vorhanden sein
- Eingabedateien müssen in `german-ordered/` liegen (ggf. zuerst `/sort-entries` ausführen)
