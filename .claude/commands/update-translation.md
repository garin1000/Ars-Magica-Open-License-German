# Bestehende Übersetzung aktualisieren

Du aktualisierst eine bestehende deutsche Übersetzung anhand von Änderungen im englischen Original. Argument: **$ARGUMENTS**

---

## Phase 0 – Vorbereitung

### 0.0 Submodul aktualisieren

Stelle sicher, dass das Submodul `original-english/` auf dem aktuellen Stand ist:

```bash
cd original-english && git fetch origin && git checkout origin/main && cd ..
```

Falls das Submodul nicht aktuell ist, informiere den Benutzer und frage, ob du fortfahren sollst.

### 0.1 Dateipaar identifizieren

**Falls kein Argument angegeben wurde (`$ARGUMENTS` ist leer):**

1. Ermittle für **jede** deutsche Übersetzungsdatei in `german-reviewed/` und `german-wip/` (außer `README.md`) das zugehörige englische Original in `original-english/reviewed/`.
2. Prüfe für jedes Dateipaar, ob das englische Original seit der letzten Bearbeitung der deutschen Datei geändert wurde (Mechanismus siehe 0.2).
3. Zeige dem Benutzer eine nummerierte Liste aller Dateien, bei denen es Änderungen gibt, im Format:
   ```
   1. [Deutscher Dateiname] ← [Englischer Dateiname]
      Quelle: german-reviewed/ | german-wip/
      Änderungen: X geänderte Zeilen seit [Datum des letzten Commits der deutschen Datei]
   ```
4. Biete zusätzlich die Option **„Alle"** an.
5. Wenn keine Änderungen gefunden werden, informiere den Benutzer und beende den Befehl.
6. Verwende `AskUserQuestion`, um die Auswahl abzufragen.
7. Fahre mit der Auswahl fort. Bei „Alle" arbeite die Dateien **sequenziell** ab (jeweils Phase 0.2 bis Phase 4).

**Falls ein Argument angegeben wurde:**

1. Suche in `original-english/reviewed/` nach einer Datei, deren Name zum Argument passt. Gibt es keine eindeutige Übereinstimmung, liste die verfügbaren Dateien auf und frage den Benutzer.
2. Suche die zugehörige deutsche Übersetzung zuerst in `german-reviewed/`, dann in `german-wip/`. Nutze dazu den Dateinamen: Die deutschen Dateien folgen dem Muster des englischen Namens, aber mit übersetzten Bestandteilen (gemäß Übersetzungstabellen) und ggf. Suffix ` Deutsch`. Wenn keine eindeutige Zuordnung möglich ist, liste die vorhandenen deutschen Dateien auf und frage den Benutzer.
3. Wenn keine deutsche Übersetzung existiert, weise den Benutzer auf den Befehl `/translate` hin und beende.

### 0.2 Änderungen seit der Übersetzung ermitteln

Für jedes Dateipaar:

1. **Referenz-Commit bestimmen (zweistufig):**

   **a) Primär — Tracking-Datei prüfen:** Lies `.translation-sync.json` (im Projektverzeichnis). Wenn ein Eintrag für die deutsche Datei existiert (prüfe sowohl den exakten Pfad als auch den alternativen Pfad in `german-reviewed/` bzw. `german-wip/`), verwende den gespeicherten `submodule_commit` als `<old-submodule-commit>`.

   **b) Fallback — Alle Commits durchsuchen:** Wenn kein Eintrag in der Tracking-Datei existiert:
   - Ermittle **alle** Commits, die die deutsche Datei verändert haben (in beiden Verzeichnissen, `german-reviewed/` und `german-wip/`):
     ```bash
     git log --format="%H" -- "<pfad-german-reviewed>" "<pfad-german-wip>"
     ```
   - Ermittle für **jeden** dieser Commits den Submodul-Stand:
     ```bash
     git ls-tree <commit> -- original-english
     ```
   - Verwende den **ältesten** (frühesten) Submodul-Commit-Hash als `<old-submodule-commit>`. Dies ist die konservativste Schätzung und zeigt alle Änderungen seit der ursprünglichen Übersetzung.
   - Gib dem Benutzer einen Hinweis, dass dies der erste Lauf ohne Tracking-Daten ist und der Referenzpunkt geschätzt wurde.
3. **Aktuellen Submodul-Stand ermitteln:**
   ```bash
   cd original-english && git rev-parse HEAD
   ```
   Das ergibt `<new-submodule-commit>`.
4. **Diff erzeugen:** Prüfe, ob sich die englische Quelldatei zwischen den beiden Submodul-Commits geändert hat:
   ```bash
   cd original-english && git diff <old-submodule-commit>..<new-submodule-commit> -- "reviewed/<englische-datei>"
   ```
5. Wenn der Diff leer ist: Informiere den Benutzer, dass keine Änderungen vorliegen, und beende (für diese Datei).
6. Wenn ein Diff vorliegt: Analysiere die geänderten Stellen und erstelle eine **Zusammenfassung der Änderungen** mit:
   - Betroffene Zeilenbereiche (in der englischen Datei)
   - Art der Änderung (Korrektur, Ergänzung, Umstrukturierung, Löschung)
   - Kurzinhalt jeder Änderung
7. Zeige dem Benutzer die Zusammenfassung und den vollständigen Diff. Warte auf Bestätigung.

### 0.3 Sonderfall: Datei in `german-reviewed/`

Wenn die deutsche Datei in `german-reviewed/` liegt:
1. Informiere den Benutzer, dass die Datei schreibgeschützt ist.
2. Erstelle automatisch eine **Arbeitskopie** in `german-wip/` (mit identischem Dateinamen).
3. Alle weiteren Änderungen werden an der Arbeitskopie in `german-wip/` vorgenommen.

### 0.4 Übersetzungstabellen und Regeln laden

Lies die folgenden Dateien:
- `translation-tables/README.md` (Index der Tabellendateien)
- `translation-tables/grundbegriffe.md`
- `translation-tables/magie-regeln.md`
- `translation-tables/uebersetzungsregeln.md`

Weitere Tabellendateien bei Bedarf nachladen (z. B. `tugenden-fehler.md`, `zauber-nach-form.md`, `fertigkeiten.md` usw. – je nachdem, welche Begriffe in den geänderten Stellen vorkommen).

Lies außerdem:
- `formatting-rules/README.md`
- `formatting-rules/charakter-kreaturen-beschreibung.md` (bei Statblöcken)

---

## Phase 1 – Änderungen übertragen

Für **jede geänderte Stelle** im englischen Original:

### 1.1 Kontext laden

1. Lies den **betroffenen Zeilenbereich** aus der englischen Quelldatei (neue Version).
2. Lies den **gleichen Zeilenbereich** aus der deutschen Übersetzung.
3. Lies zusätzlich einige Zeilen Kontext davor und danach (±10 Zeilen), um den Zusammenhang zu erfassen.

### 1.2 Änderung klassifizieren und anwenden

Je nach Art der Änderung:

- **Textkorrektur (Tippfehler, Formulierung):** Übertrage die Korrektur sinngemäß in den deutschen Text. Wenn der englische Text umformuliert wurde, passe die deutsche Übersetzung an natürliches Deutsch an.
- **Inhaltliche Ergänzung (neuer Text):** Übersetze den neuen Text gemäß den Übersetzungsregeln (wie in `/translate` Phase 1). Achte auf **Zeilensynchronität** – wenn im englischen Original Zeilen hinzugekommen sind, müssen in der deutschen Datei exakt gleich viele Zeilen hinzukommen, und zwar an der korrespondierenden Position.
- **Löschung:** Entferne den entsprechenden deutschen Text. Achte auf Zeilensynchronität – wenn im Original Zeilen entfernt wurden, müssen in der deutschen Datei exakt gleich viele Zeilen entfernt werden.
- **Umstrukturierung (Absätze verschoben, Überschriftenebene geändert):** Übertrage die strukturelle Änderung in die deutsche Datei. Prüfe alle betroffenen Markdown-Links.
- **Änderung in einer sortierten Liste:** Behalte die **Reihenfolge des englischen Originals** bei (nicht alphabetisch nach deutschen Begriffen umsortieren).

### 1.3 Übersetzungsregeln einhalten

Für alle übersetzten Stellen gelten dieselben Regeln wie bei `/translate`:

1. **Übersetzungstabellen** konsultieren – Abweichungen sind nicht zulässig.
2. **Natürliches Deutsch** – keine englischen Satzkonstruktionen übernehmen.
3. **Aussprachehinweise** weglassen (Leerzeile als Ersatz).
4. **Zeilensynchronität** strikt einhalten.
5. **Reihenfolge** sortierter Listen nicht ändern.
6. **Markdown-Formatierungen** beibehalten.
7. **Formatierungsregeln** für Statblöcke einhalten.

### 1.4 Neue Begriffe identifizieren

Wenn in den geänderten Stellen Fachbegriffe vorkommen, die **nicht** in den Übersetzungstabellen stehen:

1. Prüfe gründlich gegen **alle** relevanten Tabellendateien.
2. Lege dem Benutzer eine Liste der neuen Begriffe mit Übersetzungsvorschlägen und Kontext vor.
3. Warte auf Bestätigung oder Korrektur.
4. Trage freigegebene Begriffe in die passende Tabellendatei ein (Format exakt einhalten).

### 1.5 Änderungen schreiben

Verwende das **Edit-Tool** (nicht Write), um die betroffenen Stellen in der deutschen Datei in `german-wip/` zu aktualisieren. Schreibe nur die geänderten Stellen, nicht die gesamte Datei.

Melde nach jeder übertragenen Änderung den Fortschritt.

---

## Phase 2 – Konsistenzprüfung

Nach Abschluss aller Änderungen:

1. **Zeilenzahl:** Vergleiche die Gesamtzeilenzahl der aktualisierten deutschen Datei mit der englischen Quelldatei. Sie müssen identisch sein.
2. **Markdown-Links:** Prüfe **alle** internen Markdown-Links (`[Text](#anker)`). Anker müssen auf tatsächlich existierende Überschriften in der deutschen Datei verweisen. Besonders wichtig, wenn Überschriften geändert wurden.
3. **Terminologie-Stichproben:** Prüfe stichprobenartig 10 Fachbegriffe in den geänderten Stellen gegen die Übersetzungstabellen.
4. **Übergangskontext:** Lies die Übergangsstellen zu den unveränderten Bereichen und stelle sicher, dass der Text flüssig zusammenpasst (kein Stilbruch, konsistente Terminologie).
5. **Reihenfolge:** Falls sortierte Listen betroffen waren, prüfe, dass die Reihenfolge des englischen Originals beibehalten wurde.

Korrigiere gefundene Fehler direkt. Dokumentiere alle Korrekturen.

---

## Phase 3 – Lektorat

Das Lektorat wird von einem **unabhängigen Agenten** durchgeführt (Agent-Tool), der die Aktualisierung nicht selbst vorgenommen hat.

### Umfang des Lektorats

Der Lektorats-Agent prüft **nur die geänderten Stellen** (jeweils mit ±20 Zeilen Kontext), nicht die gesamte Datei. Er erhält:
- Die Zeilenbereiche der aktualisierten Stellen
- Die englische Quelldatei (gleiche Zeilenbereiche)
- Die aktualisierte deutsche Datei (gleiche Zeilenbereiche)

### Prüfkriterien

1. **Englischen und deutschen Text parallel lesen** (geänderte Zeilenbereiche).
2. **Zeilensynchronität prüfen.**
3. **Terminologie** gegen die Übersetzungstabellen prüfen.
4. **Natürliches Deutsch** prüfen – keine übernommenen englischen Konstruktionen.
5. **Formatierung** gegen `formatting-rules/` prüfen.
6. **Vollständigkeit** – wurde die englische Änderung vollständig und korrekt übertragen?
7. **Konsistenz** mit dem umgebenden (unveränderten) Text.

### Ergebnisdatei

Der Lektorats-Agent schreibt seine Ergebnisse in `lektorat/`, mit der Dateinamenkonvention aus `lektorat/README.md`. Die Ergebnisdatei enthält:
- **Kopfzeile:** Geprüfte Datei, englische Quelldatei, Datum, geprüfte Zeilenbereiche.
- **Terminologiefehler:** Tabelle mit Zeile, Problem und Korrektur.
- **Stilkorrekturen:** Tabelle mit Zeile, Original (EN), Übersetzung (DE), Problem und Vorschlag.
- **Formatierungsfehler:** Falls vorhanden.
- **Sonstige Befunde.**
- **Zusammenfassung.**

---

## Phase 4 – Korrekturen und Abschluss

### 4.1 Korrekturen einarbeiten

Lies das Lektoratsergebnis und arbeite die Befunde ein:
1. **Terminologiefehler** – alle korrigieren (nicht verhandelbar).
2. **Stilkorrekturen** – übernehmen, sofern sie das Deutsch verbessern.
3. **Formatierungsfehler** – alle korrigieren.
4. **Offene Fragen** – dem Benutzer vorlegen.
5. **Zeilensynchronität** – falls Abweichungen, korrigieren und erneut prüfen.

### 4.2 Finale Prüfung

- Gesamtzeilenzahl: deutsch == englisch?
- Alle Markdown-Links funktional?
- Keine Reste von englischem Text in den aktualisierten Stellen?

### 4.2a Sync-Tracking aktualisieren

Aktualisiere die Datei `.translation-sync.json` **im Projekt-Root-Verzeichnis** (NICHT in `original-english/` oder einem anderen Unterverzeichnis).

**Vorgehen:**
1. Lies die bestehende `.translation-sync.json` mit dem Read-Tool ein (falls vorhanden).
2. Parse den bestehenden JSON-Inhalt.
3. Aktualisiere den Eintrag für die bearbeitete deutsche Datei (oder füge einen neuen hinzu).
4. Schreibe die **vollständige** JSON-Datei mit **allen** Einträgen (alt + aktualisiert) zurück.

⚠️ **Niemals** die Datei mit nur dem aktualisierten Eintrag überschreiben — das löscht die Tracking-Daten aller anderen Übersetzungen.

```bash
cd original-english && git rev-parse HEAD
```
Format jedes Eintrags:
```json
{
  "<pfad-zur-deutschen-datei>": {
    "submodule_commit": "<aktueller-submodul-commit>",
    "english_file": "<pfad-zur-englischen-datei>",
    "last_sync": "<YYYY-MM-DD>"
  }
}
```

### 4.3 README aktualisieren

Aktualisiere `german-wip/README.md`: Vermerke die Aktualisierung mit Datum und einer Kurznotiz zu den übertragenen Änderungen.

### 4.4 Zusammenfassung

Gib dem Benutzer eine Zusammenfassung:
- Quelldatei und Zieldatei (mit Pfad)
- Anzahl und Art der übertragenen Änderungen
- Betroffene Zeilenbereiche
- Anzahl der vom Lektorat gefundenen und korrigierten Fehler
- **Neue Begriffe in Übersetzungstabellen:** Anzahl und Liste der neu eingetragenen Begriffe
- Offene Punkte (falls vorhanden)
- Verweis auf die Lektoratsdatei in `lektorat/`

Weise darauf hin, dass die aktualisierte Datei in `german-wip/` liegt und nach finaler Prüfung durch den Benutzer nach `german-reviewed/` verschoben werden kann.
