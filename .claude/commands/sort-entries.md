# Einträge alphabetisch sortieren

Sortiere alle relevanten Abschnitte (Tugenden, Fehler, Fertigkeiten, Zauber, Indizes, Qualitäten) einer deutschen Regeldatei alphabetisch und lege das Ergebnis in `german-ordered/` ab.

**Argument:** Pfad zur Eingabedatei (aus `german-reviewed/`).

---

## Schritt 1 — Config prüfen

Prüfe, ob eine Config für die Datei existiert unter `tools/sort-entries/configs/`. Falls nicht, erzeuge sie:

```bash
python3 tools/sort-entries/sort_entries.py --analyze -i "$ARGUMENTS"
```

Zeige dem Benutzer die erkannten Abschnitte und frage, ob die Config angepasst werden soll.

## Schritt 1b — Agentenprüfung und Freigabe

Diesen Schritt nur ausführen, wenn die Config in Schritt 1 **neu erzeugt oder per `--analyze` aktualisiert** wurde.

### 1. Vorschau erzeugen

```bash
python3 tools/sort-entries/sort_entries.py --preview -i "$ARGUMENTS"
```

### 2. Englisches Original prüfen

Finde die korrespondierende englische Originaldatei in `original-english/reviewed/`. Prüfe für **jeden** erkannten Abschnitt, ob die Einträge im englischen Original **alphabetisch sortiert** sind:

| Sortiertyp | Prüfung im englischen Original |
|---|---|
| `desc_blocks` | Sind die `####`-Überschriften alphabetisch sortiert? |
| `bold_blocks` | Sind die `**Name:**`-Einträge alphabetisch sortiert? |
| `link_list` | Sind die `[Name](link)`-Zeilen pro Kategorie alphabetisch sortiert? |
| `table` | Ist die erste Datenspalte alphabetisch sortiert? |
| `spells` | Sind die `#####`-Zauber innerhalb jeder `STUFE` alphabetisch sortiert? |

### 3. Empfehlung ableiten

- **Sortiert im Original** → Empfehlung: `enabled: true` (wahrscheinlich sortierbar)
- **Nicht sortiert im Original** → Empfehlung: `enabled: false` (wahrscheinlich Referenztabelle/Fließtext)

### 4. Freigabe einholen

Lege dem Benutzer eine Tabelle zur Freigabe vor:

| Abschnitt | Typ | Einträge | Sortiert im Original? | Empfehlung |
|---|---|---|---|---|

Der Benutzer bestätigt oder ändert die Empfehlungen.

### 5. Config aktualisieren

Setze `enabled: true/false` in der Config-Datei (`tools/sort-entries/configs/`) entsprechend den Freigabe-Entscheidungen.

## Schritt 2 — Sortieren

Führe die Sortierung aus:

```bash
python3 tools/sort-entries/sort_entries.py -i "$ARGUMENTS"
```

## Schritt 3 — Ergebnis prüfen

1. Prüfe, dass die Zeilenzahl von Ein- und Ausgabe identisch ist (steht im Sortierbericht).
2. Gib dem Benutzer den Sortierbericht aus.
3. Falls die Zeilenzahl abweicht, melde dies als Fehler.

## Schritt 4 — Verifizierung

Sortiere die Datei ein zweites Mal in `tmp/sort-verify/` und vergleiche:

```bash
python3 tools/sort-entries/sort_entries.py -i "$ARGUMENTS" -o tmp/sort-verify
diff "german-ordered/$(basename "$ARGUMENTS")" "tmp/sort-verify/$(basename "$ARGUMENTS")"
rm -rf tmp/sort-verify
```

Erwartung: Kein Diff (Sortierung ist idempotent).
