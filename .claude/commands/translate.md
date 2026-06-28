# Übersetzung eines Ars-Magica-Supplements

Du übersetzt das Supplement **$ARGUMENTS** ins Deutsche. Arbeite den vollständigen Übersetzungs- und Prüfworkflow ab.

---

## Phase 0 – Vorbereitung

### 0.1 Quelldatei identifizieren

Suche in `original-english/reviewed/` nach einer Datei, deren Name zum Argument `$ARGUMENTS` passt. Gibt es keine eindeutige Übereinstimmung, liste die verfügbaren Dateien auf und frage den Benutzer, welche gemeint ist. Brich ab, wenn keine passende Datei existiert.

### 0.2 Vorhandene Arbeit prüfen

Prüfe, ob in `german-wip/` oder `german-reviewed/` bereits eine Übersetzung dieser Datei existiert:
- Falls in `german-reviewed/`: Informiere den Benutzer, dass eine freigegebene Version existiert. Frage, ob eine Arbeitskopie in `german-wip/` erstellt und überarbeitet werden soll. Bearbeite Dateien in `german-reviewed/` **niemals** direkt.
- Falls in `german-wip/`: Frage, ob die bestehende Arbeit fortgesetzt oder neu begonnen werden soll.
- Falls keine vorhanden: Fahre normal fort.

### 0.3 Umfang bestimmen

Ermittle die Gesamtzeilenzahl der englischen Quelldatei. Teile die Datei in Übersetzungsabschnitte von **maximal 800 Zeilen** ein, orientiert an inhaltlichen Grenzen (Kapitel, Abschnitte, Überschriften). Erstelle einen nummerierten Plan mit Zeilenbereichen und Abschnittstiteln und zeige ihn dem Benutzer. Warte auf Bestätigung, bevor du mit Phase 1 beginnst.

### 0.4 Deutschen Dateinamen bestimmen

Leite den deutschen Dateinamen aus dem englischen Quelldateinamen ab:

1. **Übersetzungstabellen konsultieren:** Schlage alle im Dateinamen enthaltenen Fachbegriffe in den Übersetzungstabellen nach (z. B. Tribunalnamen in `orden-tribunale.md`, Hausnamen, Sphären in `sphären-mächte.md`, allgemeine Begriffe in `grundbegriffe.md` usw.). Diese Begriffe **müssen** gemäß der Tabellen übersetzt werden.
2. **Übriger Titeltext:** Übersetze die restlichen Titelbestandteile in natürliches Deutsch.
3. **Namensschema:** Behalte das Muster des englischen Dateinamens bei (Edition, Untertitel, Ergänzung), ersetze aber alle englischen Bestandteile durch ihre deutschen Entsprechungen. **Kein ` Deutsch`-Suffix anhängen.**
4. **Bestätigung:** Zeige dem Benutzer den vorgeschlagenen Dateinamen zusammen mit dem Übersetzungsplan aus 0.3 und warte auf Bestätigung.

*Beispiel:*
- EN: `Ars Magica 5e - Guardians of the Forests - The Rhine Tribunal.md`
- → „Rhine Tribunal" → „Rheintribunal" (aus `orden-tribunale.md`)
- DE: `Ars Magica 5e - Wächter der Wälder - Das Rheintribunal.md`

### 0.5 Übersetzungstabellen und Regeln laden

Lies die folgenden Dateien – du brauchst sie durchgängig für die gesamte Übersetzung:
- `translation-tables/README.md` (Index der Tabellendateien)
- `translation-tables/grundbegriffe.md`
- `translation-tables/magie-regeln.md`
- `translation-tables/uebersetzungsregeln.md`

Weitere Tabellendateien lädst du **bei Bedarf** nach, wenn im aktuellen Abschnitt relevante Begriffe vorkommen (z. B. `tugenden-fehler.md` bei Tugenden/Fehlern, `zauber-nach-form.md` bei Zaubersprüchen, `fertigkeiten.md` bei Fertigkeitslisten, `konvent.md` bei Konventsbegriffen usw.).

Lies außerdem:
- `formatting-rules/README.md`
- `formatting-rules/charakter-kreaturen-beschreibung.md` (bei Statblöcken)

---

## Phase 1 – Abschnittweise Übersetzung

Übersetze die Quelldatei abschnittweise gemäß dem in Phase 0.3 erstellten Plan. Verwende für jeden Abschnitt **einen eigenen Übersetzungs-Agenten** (Agent-Tool mit `subagent_type: "claude"`).

### Anweisungen pro Abschnitt

Jeder Übersetzungs-Agent erhält folgende Anweisungen:

1. **Quelldatei lesen:** Lies genau den zugewiesenen Zeilenbereich aus der englischen Quelldatei.
2. **Übersetzungstabellen konsultieren:** Verwende ausschließlich die Begriffe aus den Übersetzungstabellen in `translation-tables/`. Abweichungen sind nicht zulässig.
3. **Formatierungsregeln einhalten:** Lies **vor der Übersetzung** die Datei `formatting-rules/charakter-kreaturen-beschreibung.md` und halte dich **exakt** an die dort definierten Feldbezeichnungen und Formate. Insbesondere: Feldbezeichnungen in Statblöcken sind **nicht fett** (schlicht mit Doppelpunkt), und die dort aufgeführten Label-Namen sind **zwingend** (z.B. `Verzerrungspunkte:` nicht „Verzerrungswert", `Belastung:` nicht „Behinderung", `Reputationen:` nicht „Rufe", `Erscheinungsbild:` nicht „Beschreibung", `Persönlichkeitseigenschaften:` nicht „Persönlichkeitszüge"). Verwende `n/v` statt `n/a`.
4. **Zeilensynchronität:** Die deutsche Übersetzung muss exakt dieselbe Zeilenzahl haben wie der englische Quellabschnitt. Jede Zeile muss ihrer englischen Entsprechung zugeordnet sein.
5. **Reihenfolge nicht ändern:** Sortierte Listen (z. B. Zauberindex, Tugend-/Fehlerübersichten, Bestiariumsindex, Register) behalten die **Reihenfolge des englischen Originals**. Auch wenn die deutsche alphabetische Sortierung dadurch aufgebrochen wird, darf beim Übersetzen **nicht umsortiert** werden – die Zeilenzuordnung zwischen englischer und deutscher Datei hat Vorrang.
6. **Natürliches Deutsch:** Übersetze in natürliches, flüssiges Deutsch. Übernimm keine englischen Satzkonstruktionen. Passe Satzstellung, Wortfolge und Ausdruck an die deutsche Sprache an.
7. **Aussprachehinweise:** Für englische Leser gedachte Aussprachebeispiele (z. B. „(DAH-van ALL-ath)") werden weggelassen. Um die Zeilensynchronität zu erhalten, wird die weggelassene Zeile durch eine Leerzeile in der deutschen Datei ersetzt (oder der verbleibende Text so auf die Zeilen verteilt, dass die Gesamtzahl gleich bleibt).
8. **Markdown:** Alle Markdown-Formatierungen (Überschriften, Links, Tabellen, Hervorhebungen) aus dem Original beibehalten.
9. **Ergebnis schreiben:** Schreibe den übersetzten Abschnitt in die Zieldatei in `german-wip/`. Verwende den in Phase 0.4 bestimmten und vom Benutzer bestätigten deutschen Dateinamen. Der erste Abschnitt erstellt die Datei; alle weiteren Abschnitte hängen an.
10. **Neue Begriffe identifizieren:** Sammle alle Fachbegriffe im Abschnitt, die potenziell neu sind – insbesondere Tugenden, Fehler, Fertigkeiten, Zaubersprüche, Konventsbegriffe, Kreaturen und sonstige spielmechanische Begriffe. **Prüfe jeden einzelnen Begriff mit `grep -rni` gegen die folgenden Quellen, bevor du ihn als „neu" einstufst:**
    - `grep -rni "BEGRIFF" translation-tables/` – durchsucht **alle** Tabellendateien
    - `grep -ni "BEGRIFF" german-reviewed/Ars Magica Definitive Edition Basisregeln.md` – durchsucht die **Basisregeln**
    - `grep -rni "BEGRIFF" german-reviewed/` – durchsucht **alle bereits übersetzten Dateien**
    
    Ein Begriff gilt **nur dann als neu**, wenn er in **keiner** dieser drei Quellen vorkommt. Verlasse dich nicht auf das Lesen der Tabellen allein – viele Begriffe (insbesondere Tugenden, Fehler und Fertigkeiten) sind zwar in den Basisregeln übersetzt, fehlen aber in den Übersetzungstabellen. Wenn ein Begriff in den Basisregeln gefunden wird, verwende **exakt die dort verwendete Übersetzung**. Notiere für jeden tatsächlich neuen Begriff: englischer Name, gewählte deutsche Übersetzung, Kategorie (Tugend/Fehler/Fertigkeit/Zauber/…), den Kontext, in dem der Begriff im Quelltext vorkommt (Satz oder Absatz), und ggf. Anmerkungen.

### Ablauf

- Übersetze die Abschnitte **sequenziell**, damit die Zieldatei korrekt zusammengesetzt wird.
- Melde nach jedem Abschnitt den Fortschritt: `[Abschnitt X/Y abgeschlossen – Zeilen M–N]`.
- **Neue Begriffe nach jedem Abschnitt zur Freigabe vorlegen:** Wenn ein Abschnitt Begriffe enthält, die nicht in den Übersetzungstabellen stehen:
  1. **Gründliche Gegenprüfung mit grep:** Prüfe jeden gefundenen Begriff **per `grep -rni`** gegen (a) alle Dateien in `translation-tables/`, (b) `german-reviewed/Ars Magica Definitive Edition Basisregeln.md` und (c) alle anderen Dateien in `german-reviewed/`. Erst wenn der Begriff in **keiner** dieser Quellen vorkommt, gilt er als neu. Wenn der Begriff in den Basisregeln oder einer reviewed-Datei gefunden wird, verwende **exakt die dort verwendete Übersetzung** und trage den fehlenden Begriff in die passende Tabellendatei nach.
  2. Lege dem Benutzer eine Liste der neuen Begriffe mit deinen Übersetzungsvorschlägen vor. Zeige zu jedem Begriff den **Kontext** (den Satz oder Absatz aus dem Quelltext, in dem er vorkommt), damit der Benutzer die Übersetzung beurteilen kann.
  3. **Der Benutzer kann Begriffe vor der Freigabe anpassen.** Warte auf Bestätigung oder Korrektur durch den Benutzer.
  4. Trage die vom Benutzer freigegebenen Begriffe **sofort** in die jeweils passende Tabellendatei in `translation-tables/` ein:
     - Tugenden/Fehler → `tugenden-fehler.md`
     - Fertigkeiten → `fertigkeiten.md`
     - Zaubersprüche → `zauber-nach-form.md`
     - Konventsbegriffe → `konvent.md`
     - Orden/Tribunale/Personenbezeichnungen → `orden-tribunale.md`
     - Kreaturen/Tiere → `tiere-kreaturen.md`
     - Sonstige Spielbegriffe → `grundbegriffe.md`
  5. Halte das bestehende Tabellenformat der jeweiligen Datei exakt ein (Spalten, Legende, Sortierung).
  6. Fahre erst mit dem nächsten Abschnitt fort, wenn alle neuen Begriffe eingetragen sind.

---

## Phase 2 – Konsistenzprüfung (Selbstprüfung)

Nach Abschluss aller Abschnitte prüfe die zusammengesetzte Zieldatei:

1. **Zeilenzahl:** Vergleiche die Gesamtzeilenzahl der deutschen Datei mit der englischen Quelldatei. Sie müssen identisch sein.
2. **Markdown-Links:** Prüfe alle internen Markdown-Links (`[Text](#anker)`). Anker müssen auf tatsächlich existierende Überschriften in der deutschen Datei verweisen.
3. **Abschnittsübergänge:** Lies die Übergangsstellen zwischen den Abschnitten und stelle sicher, dass keine Lücken, Überlappungen oder Brüche entstanden sind.
4. **Terminologie-Stichproben:** Prüfe stichprobenartig 20 zentrale Fachbegriffe gegen die Übersetzungstabellen.
5. **Reihenfolge:** Prüfe, dass sortierte Listen (Zauberindex, Tugend-/Fehlerübersichten, Bestiariumsindex, Register) die Reihenfolge des englischen Originals beibehalten und nicht alphabetisch nach den deutschen Begriffen umsortiert wurden.
6. **Vollständigkeit der Übersetzungstabellen:** Prüfe, ob alle im Supplement neu eingeführten Fachbegriffe (Tugenden, Fehler, Fertigkeiten, Zauber, Kreaturen usw.) in die jeweiligen Tabellendateien in `translation-tables/` eingetragen wurden. Fehlende Einträge sofort nachtragen.

Korrigiere gefundene Fehler direkt. Dokumentiere alle vorgenommenen Korrekturen kurz.

---

## Phase 3 – Unabhängiges Lektorat

Das Lektorat wird von einem **unabhängigen Agenten** durchgeführt (Agent-Tool), der die Übersetzung nicht selbst erstellt hat. Delegiere das Lektorat an einen separaten Agenten.

### Anweisungen für den Lektorats-Agenten

Der Lektorats-Agent prüft die Übersetzung abschnittweise (Abschnitte à ~800 Zeilen, können von den Übersetzungsabschnitten abweichen). Für jeden Lektoratsabschnitt:

1. **Englischen und deutschen Text parallel lesen** (jeweils denselben Zeilenbereich).
2. **Zeilensynchronität prüfen:** Stimmt die Zuordnung Zeile für Zeile?
3. **Terminologie prüfen:** Jeden Fachbegriff per `grep -rni` gegen die Übersetzungstabellen in `translation-tables/` **und** gegen die Dateien in `german-reviewed/` (insbesondere die Basisregeln) prüfen. Jede Abweichung ist ein Fehler. Begriffe, die in den Basisregeln etabliert sind aber in den Tabellen fehlen, sind ebenfalls als Fehler zu melden, wenn die Übersetzung von der Basisregel-Version abweicht.
4. **Natürliches Deutsch prüfen:** Zu direkt aus dem Englischen übernommene Satzkonstruktionen identifizieren und Alternativen vorschlagen.
5. **Formatierung prüfen:** Statblöcke, Tabellen und Markdown-Formatierung gegen die Regeln in `formatting-rules/` prüfen.
6. **Vollständigkeit prüfen:** Wurde etwas ausgelassen, hinzugefügt oder inhaltlich verändert?

### Ergebnisdatei

Der Lektorats-Agent schreibt seine Ergebnisse in `lektorat/`, mit der Dateinamenkonvention aus `lektorat/README.md`. Die Ergebnisdatei enthält:

- **Kopfzeile:** Geprüfte Datei, englische Quelldatei, Datum, geprüfter Zeilenbereich.
- **Zeilensynchronität:** Bestätigung oder Abweichungen.
- **Terminologiefehler:** Tabelle mit Zeile, Problem und Korrektur.
- **Stilkorrekturen:** Tabelle mit Zeile, Original (EN), Übersetzung (DE), Problem und Vorschlag.
- **Formatierungsfehler:** Falls vorhanden.
- **Sonstige Befunde:** Inkonsistenzen, offene Fragen.
- **Zusammenfassung:** Gesamtbewertung.

---

## Phase 4 – Korrekturen einarbeiten

Lies das Lektoratsergebnis aus `lektorat/` und arbeite die gefundenen Fehler in die Übersetzungsdatei in `german-wip/` ein:

1. **Terminologiefehler:** Alle korrigieren – diese sind nicht verhandelbar.
2. **Stilkorrekturen:** Alle übernehmen, sofern die Korrektur das natürliche Deutsch verbessert, ohne den Inhalt zu verfälschen.
3. **Formatierungsfehler:** Alle korrigieren.
4. **Offene Fragen:** Dem Benutzer vorlegen und auf Entscheidung warten.
5. **Zeilensynchronität:** Falls Abweichungen gefunden wurden, diese korrigieren und die Zeilenzahl erneut gegen das Original prüfen.

Dokumentiere kurz, welche Korrekturen du vorgenommen hast.

---

## Phase 5 – Abschluss

### 5.1 Finale Prüfung

Führe eine letzte Kontrolle durch:
- Gesamtzeilenzahl: deutsch == englisch?
- Alle Markdown-Links funktional?
- Keine Reste von englischem Text in der deutschen Datei?

### 5.1a Sync-Tracking schreiben

Aktualisiere die Datei `.translation-sync.json` **im Projekt-Root-Verzeichnis** (NICHT in `original-english/` oder einem anderen Unterverzeichnis).

**Vorgehen:**
1. Lies die bestehende `.translation-sync.json` mit dem Read-Tool ein (falls vorhanden).
2. Parse den bestehenden JSON-Inhalt.
3. Füge den neuen Eintrag hinzu (oder aktualisiere einen vorhandenen Eintrag für dieselbe deutsche Datei).
4. Schreibe die **vollständige** JSON-Datei mit **allen** Einträgen (alt + neu) zurück.

⚠️ **Niemals** die Datei mit nur dem neuen Eintrag überschreiben — das löscht die Tracking-Daten aller anderen Übersetzungen.

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

### 5.2 README aktualisieren

Aktualisiere `german-wip/README.md`: Trage die neue Übersetzungsdatei mit Titel, Quelldatei und Datum ein.

### 5.3 Zusammenfassung

Gib dem Benutzer eine Zusammenfassung:
- Quelldatei und Zieldatei (mit Pfad)
- Gesamtzeilenzahl
- Anzahl Abschnitte
- Anzahl der vom Lektorat gefundenen und korrigierten Fehler (nach Kategorie)
- **Neue Begriffe in Übersetzungstabellen:** Anzahl und Liste der neu eingetragenen Begriffe, gruppiert nach Tabellendatei
- Offene Punkte (falls vorhanden)
- Verweis auf die Lektoratsdatei in `lektorat/`

Weise darauf hin, dass die Datei in `german-wip/` liegt und nach finaler Prüfung durch den Benutzer nach `german-reviewed/` verschoben werden kann.
