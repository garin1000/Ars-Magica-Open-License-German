# Begriffsreferenzen / Line References

Automatisch generierte Referenzdateien, die für jeden Fachbegriff aus den Übersetzungstabellen alle Zeilennummern auflisten, an denen der Begriff in der jeweiligen deutschen Arbeitsdatei vorkommt.

**Zweck:** Bei Änderung eines Begriffs in den Übersetzungstabellen sofort alle betroffenen Zeilen identifizieren.

## Dateien

| Referenzdatei | Quelldatei | Begriffe |
|---|---|---|
| [begriffe-basisregeln.md](begriffe-basisregeln.md) | Ars Magica Definitive Edition Basisregeln Deutsch.md | 1335 |
| [begriffe-sdm-magie.md](begriffe-sdm-magie.md) | Ars Magica 5e - Sphären der Macht - Magie.md | 724 |
| [begriffe-wdw-rhein.md](begriffe-wdw-rhein.md) | Ars Magica 5e - Wächter des Waldes - Das Rhein-Tribunal.md | 583 |
| [begriffe-heckenzauber.md](begriffe-heckenzauber.md) | Ars Magica 5e - Magie - Heckenzauber (Überarbeitet) Deutsch.md | 666 |

## Aufbau

Jede Datei enthält:
- **Kopf:** Quelldatei, Generierungsdatum, Gesamtzeilen, Anzahl erfasster Begriffe
- **Abschnitte:** Gruppiert nach Quelltabelle (grundbegriffe.md, kampf.md, tugenden-fehler.md etc.)
- **Tabelle:** DE-Begriff, EN-Entsprechung, Anzahl Vorkommen, Zeilennummern
- **Querverweise:** Begriffe, die in mehreren Tabellen definiert sind, tragen einen *(auch: ...)*-Vermerk

## Aktualisierung

Die Dateien werden mit `tmp/generate_line_references.py` generiert:

```bash
python3 tmp/generate_line_references.py
```

Nach jeder Textänderung in den german-wip-Dateien sollten die Referenzen neu generiert werden, da sich die Zeilennummern verschieben können.
