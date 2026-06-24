# Sortier-Config gegen englisches Original prüfen

Prüft alle aktivierten Sortier-Blöcke einer Config gegen das englische Original. Blöcke, die im Original nicht alphabetisch sortiert sind, werden deaktiviert. Blöcke, die nur zufällig sortiert sind, werden ebenfalls deaktiviert.

**Argument:** Pfad zur deutschen Eingabedatei (aus `german-reviewed/`).

---

## Schritt 1 — Dateien identifizieren

1. Bestimme die **deutsche Eingabedatei** aus `$ARGUMENTS`. Falls der Pfad kein Verzeichnis enthält, suche in `german-reviewed/`.
2. Prüfe, ob eine **Sort-Config** unter `tools/sort-entries/configs/<Dateiname>.json` existiert. Falls nicht, brich mit Hinweis ab: „Erzeuge zuerst eine Config mit `/sort-entries`."
3. Finde das **englische Original** in `original-english/reviewed/`. Das Skript sucht automatisch anhand bekannter Zuordnungen. Falls nicht gefunden, frage den Benutzer nach dem Pfad.
4. Prüfe, dass beide Dateien **dieselbe Zeilenzahl** haben (Zeilensynchronität).

## Schritt 2 — Sortierprüfung im englischen Original

Führe das Prüfskript aus:

```bash
python3 tools/sort-entries/check_english_sort.py -i "$ARGUMENTS" --json 2>tmp/sort_check_report.txt
```

Das Skript:
- Findet jeden aktivierten Block in der deutschen Datei (Heading + Subheading)
- Liest an denselben Zeilenpositionen das englische Original (Zeilensynchronität)
- Extrahiert die Einträge je nach Typ (`bold_blocks` → `**Name:**`, `desc_blocks` → `####`, `table` → erste Datenspalte, `link_list` → `[Name](link)`, `spells` → `#####`, `inline_list` → Kommalisten)
- Prüft, ob die Einträge alphabetisch sortiert sind
- Gibt einen lesbaren Bericht nach `tmp/sort_check_report.txt` und JSON-Ergebnisse nach stdout

Zeige dem Benutzer den Bericht aus `tmp/sort_check_report.txt`.

## Schritt 3 — Nicht sortierte Blöcke identifizieren

Aus den JSON-Ergebnissen:
- Alle Blöcke mit `"sorted": false` → **sofort zum Deaktivieren** vormerken.
- Alle Blöcke mit `"sorted": true` → weiter zu Schritt 4.

## Schritt 4 — Zufallssortierung prüfen (Agent)

Starte **einen Agenten**, der alle als sortiert erkannten Blöcke auf Zufallssortierung prüft. Übergib dem Agenten:
- Die vollständige Liste der sortierten Blöcke (Name, Typ, Anzahl Einträge, Einträge)
- Die Aufgabe, jeden Block als **INTENTIONAL** oder **COINCIDENTAL** einzustufen

**Bewertungskriterien für den Agenten:**

| Kriterium | Bewertung |
|---|---|
| Referenzliste (Tugenden, Fehler, Fertigkeiten, Kräuter, Tiere, Mineralien, Mächte, Qualitäten, Mängel, Zaubersprüche, Auren-Typen, hermetische Künste) | INTENTIONAL — **auch bei wenigen Einträgen**. Diese Listen werden im Regelwerk nachgeschlagen; alphabetische Sortierung dient dem Auffinden. Entscheidend ist der Listentyp, nicht die Länge. |
| Kategorieliste (Zauberspruchtypen, Materialgruppen) | INTENTIONAL — systematische Aufzählung, bewusst sortiert |
| ≥10 Einträge in perfekter Reihenfolge | INTENTIONAL — Zufall bei so vielen Einträgen extrem unwahrscheinlich |
| Nummerierte Einträge (1., 2., 3… oder Level 10, 15, 20…) | COINCIDENTAL — Reihenfolge folgt aus Nummerierung, nicht aus Alphabet |
| Alle Einträge identisch | COINCIDENTAL — Sortierung bedeutungslos |
| Berühmte Persönlichkeiten / historische Figuren | Prüfe, ob andere gleichartige Abschnitte im selben Buch ebenfalls sortiert sind. Falls nicht → COINCIDENTAL |
| ≤3 Einträge, die KEINE Referenzliste sind (z. B. Prozessschritte, narrative Beispiele, Regelbeschreibungen) | COINCIDENTAL — bei so wenigen Einträgen ist Zufall plausibel |
| Prozessschritte, Regelbeschreibungen, Initiationsscripts | COINCIDENTAL — logische/narrative Reihenfolge |
| Stat-Block-Felder (Characteristics, Size, Combat, Soak…) | COINCIDENTAL — feste Reihenfolge des Stat-Block-Formats, kein Alphabet |

## Schritt 5 — Ergebnis zusammenstellen

Erstelle eine Übersichtstabelle:

| Block | Typ | Einträge | Sortiert im EN? | Zufällig? | → Aktion |
|---|---|---|---|---|---|
| ... | ... | n | Nein | — | deaktivieren |
| ... | ... | n | Ja | COINCIDENTAL | deaktivieren |
| ... | ... | n | Ja | INTENTIONAL | beibehalten |

Zeige die Tabelle dem Benutzer und frage nach Freigabe.

## Schritt 6 — Config aktualisieren

Nach Freigabe durch den Benutzer:

1. Lies die Config-Datei (`tools/sort-entries/configs/<Dateiname>.json`).
2. Setze `"enabled": false` für alle Blöcke, die deaktiviert werden sollen.
3. Stelle sicher, dass die als INTENTIONAL bewerteten Blöcke `"enabled": true` haben.
4. Speichere die Config.

Gib dem Benutzer eine Zusammenfassung:
- Anzahl geprüfter Blöcke
- Davon deaktiviert (nicht sortiert im EN)
- Davon deaktiviert (nur zufällig sortiert)
- Verbleibende aktive Blöcke (mit Namen)
