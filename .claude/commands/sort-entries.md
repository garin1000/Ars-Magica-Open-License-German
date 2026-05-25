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
