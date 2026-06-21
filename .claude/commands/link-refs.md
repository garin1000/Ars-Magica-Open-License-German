# Interne und externe Verweise verlinken

Verlinke Seitenverweise, Inhaltsverzeichnisse und Querverweise in einer deutschen Regeldatei. Arbeitet auf `german-wip/`-Dateien.

**Argument:** Buchname als Freitext (z.B. "Sphären der Macht", "Basisregeln", "Heckenzauber").

---

## Schritt 0 — Datei identifizieren

1. Lies `tools/link-refs/book_aliases.json`.
2. Suche das Argument in den `aliases`-Schlüsseln (Fuzzy-Match auf Teilstring). Der zugehörige Wert ist der Dateiname.
3. Prüfe, ob die Datei in `german-wip/` existiert. Falls nicht:
   - Erstelle eine Kopie aus `german-reviewed/` nach `german-wip/`.
4. Falls kein Alias passt: Frage den Benutzer nach dem genauen Dateinamen.

**Ab hier arbeite mit der Datei in `german-wip/`.**

## Schritt 1 — Config prüfen und Analyse

Prüfe, ob eine Config unter `tools/link-refs/configs/` existiert. Falls nicht, oder wenn die Datei sich geändert hat, erzeuge sie:

```bash
python3 tools/link-refs/link_refs.py --analyze -i "german-wip/$DATEI" -o tmp/link-report.json
```

Zeige dem Benutzer die Statistiken aus dem Report (bereits verlinkt, unverlinkt, auto-aufgelöst, braucht Agent, ohne Kandidaten, nicht übersetzt).

## Schritt 2 — TOC verlinken

Falls die Datei ein Inhaltsverzeichnis hat (im Report unter `toc`):

```bash
python3 tools/link-refs/link_refs.py --link-toc -i "german-wip/$DATEI"
```

Prüfe die Ausgabe: Wie viele Einträge wurden verlinkt, wie viele blieben ohne Match? Abweichende TOC-Texte werden automatisch an den Header-Text angepasst.

Für die **nicht gematchten** TOC-Einträge:
1. Suche manuell nach dem passenden Header in der Datei.
2. Falls ein passender Header gefunden wird, dessen Text sich zu stark vom TOC-Eintrag unterscheidet: Korrigiere den TOC-Eintrag manuell (den Text an den Header-Text anpassen und den Link einfügen).
3. Falls kein passender Header existiert: Vermerk im Bericht, TOC-Eintrag unverlinkt lassen.

## Schritt 3 — Seitenverweise auflösen (Agent-gestützt)

Lies `tmp/link-report.json`. Für jeden Eintrag in `unresolved_refs`:

### 3a. Automatisch aufgelöste Verweise

Verweise mit genau einem Kandidaten haben bereits `resolved_anchor` gesetzt. Diese können direkt übernommen werden.

### 3b. Mehrdeutige Verweise (Agent-Auflösung)

Für Verweise mit **mehreren Kandidaten** (`candidates`-Liste > 1):

1. Lies den **Kontext** (5–10 Zeilen um den Verweis in der Quelldatei).
2. Lies die **Kandidaten-Header** in der Zieldatei (Überschrift + die ersten Zeilen des Abschnitts).
3. Bestimme den **korrekten Anker** basierend auf inhaltlicher Übereinstimmung.
4. Setze `resolved_anchor` im Report.

### 3c. Verweise ohne Kandidaten

Für Verweise **ohne Kandidaten** (Seitenzahl nicht im Mapping):

1. Lies den **Kontext** des Verweises.
2. Suche in der **Zieldatei** nach dem passenden Abschnitt (über Keywords aus dem Kontext).
3. Wenn gefunden: Setze `resolved_anchor` und ergänze die Seite im `page_to_anchors` der Zieldatei-Config (`tools/link-refs/configs/`).
4. Wenn nicht findbar: Vermerk im Bericht, Verweis unverlinkt lassen.

### 3d. Report speichern

Speichere den aktualisierten Report als `tmp/resolved.json`.

## Schritt 4 — Links einfügen

```bash
python3 tools/link-refs/link_refs.py --apply -i "german-wip/$DATEI" --refs tmp/resolved.json
```

## Schritt 5 — Cross-File-Links korrigieren

Falls die Datei bestehende Cross-File-Links mit **englischen Dateinamen** enthält:

```bash
python3 tools/link-refs/link_refs.py --fix-crosslinks -i "german-wip/$DATEI"
```

## Schritt 6 — Verifizierung

### 6a. Zeilenzahl

```bash
wc -l "german-wip/$DATEI"
```

Muss mit der Zeilenzahl vor der Bearbeitung übereinstimmen.

### 6b. Idempotenz

```bash
cp "german-wip/$DATEI" "tmp/idempotenz-check.md"
python3 tools/link-refs/link_refs.py --apply -i "tmp/idempotenz-check.md" --refs tmp/resolved.json 2>&1
diff "german-wip/$DATEI" "tmp/idempotenz-check.md"
rm "tmp/idempotenz-check.md"
```

Erwartung: `0 Links eingefügt` und kein Diff.

### 6c. Link-Validierung

Stichprobenartig prüfen:
- Öffne 5 der neu eingefügten Links und prüfe, ob der Anker (`#anker`) als Header in der Zieldatei existiert.
- Bei Cross-File-Links: Prüfe, ob die referenzierte `.md`-Datei in `german-reviewed/` existiert.

### 6d. Zusammenfassung

Gib dem Benutzer eine Zusammenfassung:
- TOC: N verlinkt, M korrigiert, O ohne Match
- Seitenverweise: N aufgelöst, M mehrdeutig (vom Agent aufgelöst), O ohne Kandidaten, P nicht übersetzbar
- Cross-File-Links: N korrigiert (englisch → deutsch)
- Zeilenzahl: unverändert / verändert (FEHLER)
