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

## Schritt 3 — Seitenverweise **vollständig** auflösen

**Ziel:** Alle auflösbaren Verweise in **einem** Durchgang verlinken. Nur Verweise auf nicht übersetzte Bücher (Alias = `null` in `book_aliases.json` und auch nicht in `german-wip/` vorhanden) dürfen am Ende unverlinkt bleiben.

Lies `tmp/link-report.json`. Für jeden Eintrag in `unresolved_refs`:

### Grundregel: Kontext schlägt Config

Bevor ein Kandidat aus der Config akzeptiert wird, **immer den Kontext-Text** (5–10 Zeilen um den Verweis) lesen. Häufig nennt der Text das Ziel beim Namen, z.B.:
- „siehe **Sympathetische Verbindungen**, ArM5 Seite 86"
- „wie **Bezaubernde Musik** (ArM5, Seite 65)"

Wenn der Kontext einen solchen **expliziten Zielnamen** enthält:
1. Suche diesen Namen als Header in der Zieldatei (case-insensitive, Slug-Match).
2. Falls gefunden: Dieser Header hat **Vorrang** vor den Config-Kandidaten — auch wenn er nicht in `page_to_anchors` eingetragen ist.
3. Trage den neuen Anker zusätzlich in die Config ein (Schritt 3h).

Nur wenn der Kontext **keinen** expliziten Zielnamen enthält, werden die Config-Kandidaten wie unten beschrieben verwendet.

### 3a. Automatisch aufgelöste Verweise — verifizieren

Verweise mit genau einem Kandidaten haben `resolved_anchor` gesetzt. **Prüfe für jeden Verweis**, ob die Zuordnung zum Kontext passt — lies dazu den Kontext-Text und vergleiche mit dem Kandidaten. Wende die Grundregel oben an: Nennt der Kontext einen Header-Namen, der nicht der Kandidat ist, ersetze den Kandidaten. Offensichtlich falsche Auto-Auflösungen korrigieren oder auf `null` setzen.

#### ArM5-Verweise besonders prüfen

Bei ArM5-Verweisen (Buch = `ArM5` oder `ArM`) stimmt die Seitenzahl oft **nicht** mit der ArMDE-Seitenzahl überein — dieselbe Seitennummer kann in beiden Editionen auf völlig verschiedene Kapitel verweisen. Das Tool verwendet `page_to_anchors_arm5` für ArM5-Verweise (mit Fallback auf `page_to_anchors`), aber dieses Mapping kann unvollständig oder veraltet sein.

**Pflicht:** Für jeden ArM5-Verweis den **Kontext-Text** lesen und prüfen, ob der Kandidat zum beschriebenen Thema passt. Insbesondere:

1. **Kapitelzugehörigkeit prüfen:** Verweist der Kontext z.B. auf Zauberregeln (Hermetic Magic), aber der Kandidat ist eine Tugend/Fehler-Beschreibung? → Falsche Edition, Kandidat verwerfen und korrekten Anchor suchen.
2. **Namentlich genannte Regelelemente direkt verlinken:** Nennt der Kontext einen Zauber, eine Tugend, einen Fehler oder einen Regelabschnitt beim Namen (z.B. „*Grube der klaffenden Erde*", „Glück", „Tabelle außergewöhnlicher Ergebnisse"), dann den **exakten Header** dieses Elements in der Zieldatei suchen und direkt darauf verlinken — nicht auf eine Nachbar-Überschrift auf derselben Seite. Seitenzahlen sind in Markdown bedeutungslos; nur der Anchor zählt.
3. **Bekannte Problemseiten:** Die Seiten 65, 82, 83, 100, 103, 107, 158, 166 haben unterschiedliche Inhalte in ArM5 und ArMDE. Kandidaten aus `page_to_anchors` für diese Seiten sind bei ArM5-Verweisen mit hoher Wahrscheinlichkeit falsch.

### 3b. Mehrdeutige Verweise (Agent-Auflösung)

Für Verweise mit **mehreren Kandidaten** (`candidates`-Liste > 1):

1. Lies den **Kontext** (5–10 Zeilen um den Verweis in der Quelldatei).
2. Wende die **Grundregel** an: Nennt der Kontext das Ziel beim Namen, suche den Header direkt in der Zieldatei.
3. Andernfalls: Lies die **Kandidaten-Header** in der Zieldatei (Überschrift + die ersten Zeilen des Abschnitts) und bestimme den korrekten Anker basierend auf inhaltlicher Übereinstimmung.
4. Setze `resolved_anchor` im Report.

### 3c. Verweise ohne Kandidaten — aktiv auflösen

Für **alle** Verweise ohne Kandidaten (Seitenzahl nicht im Mapping):

1. **Gruppiere** die fehlenden Seitenzahlen nach Ziel-Buch.
2. Nutze einen **Agenten**, um die Zuordnungen für alle fehlenden Seiten eines Buchs auf einmal zu finden: Agent liest den Kontext jedes Verweises (und wendet die Grundregel an), sucht den passenden Header in der Zieldatei und liefert den Anchor-Slug zurück.
3. **Parallele Agenten** pro Ziel-Buch einsetzen, um Zeit zu sparen.
4. Setze `resolved_anchor` und `target_file` im Report.

### 3d. Falsch klassifizierte Verweise korrigieren

Das Analyse-Tool erkennt manchmal Buch-Aliase nicht korrekt:
- Verweise mit `type: "internal"` und `book: null/self`, die im Kontext explizit ein anderes Buch nennen (z.B. „Seite 29 von *Häuser des Hermes: Mysterienkulte*"), müssen **umklassifiziert** werden: `target_file` und `type` auf das korrekte Buch setzen.
- Ungewöhnliche Aliase wie „ArM" (statt „ArM5"), „Ars Magica Fünfte Edition", „Grundregelwerk" erkennen und auf die richtige Zieldatei mappen.
- Auch `german-wip/`-Dateien als gültige Zieldateien berücksichtigen (z.B. wenn SdM:I in wip vorliegt, aber `book_aliases.json` noch `null` hat).

### 3e. Zieldateien in german-wip prüfen

Vor dem Aufgeben eines Verweises: Prüfe, ob die Zieldatei in `german-wip/` existiert, auch wenn `book_aliases.json` den Eintrag als `null` führt. Falls ja, aktualisiere `book_aliases.json` und löse den Verweis auf.

### 3f. Anchor-Format validieren

Alle Anchors müssen dem Format von `pandoc_anchor_id()` entsprechen:
- Kleinbuchstaben, Bindestriche statt Leerzeichen, Umlaute erhalten
- **Doppel-Hyphens** (`--`) sind korrekt und dürfen **nicht** zu `-` zusammengefasst werden. Sie entstehen, wenn Sonderzeichen wie Gedankenstriche (–, —), Schrägstriche (/) oder Kaufmanns-Und (&) in Überschriften entfernt werden und zwei Bindestriche aufeinanderfolgen. Beispiel: Header `Merinita – Feenmagie` → Anchor `merinita--feenmagie`.

### 3f-2. Duplikat-Header und Seitenzahl-Zuordnung

In der Zieldatei können **mehrere Header mit identischem Text** existieren (z.B. „Selbstvertrauen" in verschiedenen Kapiteln). Pandoc/GFM nummeriert diese: `#selbstvertrauen`, `#selbstvertrauen-1`, `#selbstvertrauen-2`.

**Wenn eine Seitenzahl auf einen Header verweist, der mehrfach vorkommt:**
1. Prüfe im **englischen Original** (gleiche Zeilennummer), welcher Anchor-Suffix dort verwendet wird (z.B. `#confidence` vs. `#confidence-1`).
2. Verwende den **entsprechenden DE-Suffix** (z.B. `#selbstvertrauen` vs. `#selbstvertrauen-1`).
3. Zwei Seitenzahlen auf derselben Zeile, die zum **selben Anchor** zeigen, dürfen **nur dann zu einem Link zusammengefasst** werden, wenn es tatsächlich nur **einen** Header gibt und beide Seiten denselben Abschnitt meinen. In diesem Fall einen `<!-- link-arm5: ... -->` Kommentar anhängen.
4. Wenn zwei Seitenzahlen auf **verschiedene Abschnitte** verweisen (auch wenn der Header-Text gleich ist), müssen sie **getrennte Links** mit den korrekten Suffixen sein.

**Verweise auf nicht übersetzte Bücher:** Seitenzahlen, die auf nicht übersetzte Quellenbücher verweisen (z.B. *Kunst & Gelehrsamkeit*, *Art & Academe*), werden **entlinkt** (reiner Text). Der interne Verweis bleibt als Link bestehen.

### 3f-3. ArM5-Seitenverweise in den Basisregeln (link-arm5 Kommentare)

Die Basisregeln-Referenzsektion enthält Seitenpaare aus ArM5 (5th Edition) und ArMDE (Definitive Edition), die auf denselben Abschnitt verweisen. Diese werden in **einem** Link zusammengefasst und mit einem Kommentar versehen:

```
[S. 89/S. 229](#wirkungen-des-zwielichts)<!-- link-arm5: "S. 89" → gleiche Stelle wie "S. 229" -->
```

Prüfe auf bestehende `<!-- link-arm5: ... -->` Kommentare, bevor ein Seitenpaar getrennt wird. Falls vorhanden: **Nicht trennen**.

### 3g. Abweichende Verweistexte (Redirect-Kommentare)

Die Definitive Edition (DE) hat gegenüber der 5th Edition Regelelemente umbenannt, zusammengefasst oder ersetzt (z.B. „Enchanting Music" → „Enchanting (Ability)"). Da die Quellenbände auf der 5th Edition basieren, referenzieren sie noch die alten Namen, die in der DE nicht mehr als Header existieren.

**Vorgehen:**

1. **Prüfe auf bestehenden Kommentar.** Suche in der Quelldatei nach einem HTML-Kommentar direkt **am Link** im Format:
   ```
   [...](<...>)<!-- link-redirect: "Quelltext" → "Zieltext" -->
   ```
   Falls vorhanden: Verwende den im Kommentar angegebenen Anker als `resolved_anchor`. **Nicht erneut nachfragen.**

2. **Kein Kommentar vorhanden:** Wenn ein Verweis aufgelöst wird und der Verweistext (z.B. „Bezaubernde Musik") **nicht** als Header in der Zieldatei existiert, aber der `resolved_anchor` auf einen **anderen** Header zeigt (z.B. „Bezaubernde (Fertigkeit)"):
   - **Frage den Benutzer**, ob der Link auf den gefundenen Anker zeigen soll, und nenne dabei den Verweistext, den Ziel-Header und die Zieldatei.
   - Falls **ja**: Setze `resolved_anchor` und markiere den Verweis als `redirect: true` im Report.
   - Falls **nein** oder der Benutzer ein anderes Ziel nennt: Entsprechend anpassen.

3. **Kommentar einfügen.** Für jeden bestätigten Redirect wird der HTML-Kommentar **direkt an die Linkdefinition** angehängt, ohne Zeilenumbruch:
   ```
   [Seite 65](<Basisregeln.md#bezaubernde-fertigkeit>)<!-- link-redirect: "Bezaubernde Musik" → "Bezaubernde (Fertigkeit)" -->
   ```
   So bleibt die **Zeilenzahl** unverändert und der Kommentar ist eindeutig dem Link zugeordnet.

### 3h. Report speichern

Speichere den aktualisierten Report als `tmp/resolved.json`.

### 3i. Aufgelöste Seitenzuordnungen in Configs zurückschreiben

Alle in Schritt 3 neu aufgelösten Seite→Anker-Zuordnungen müssen in die Config-Dateien unter `tools/link-refs/configs/` eingetragen werden, damit sie bei künftigen Durchläufen automatisch aufgelöst werden.

**Getrennte Mappings für ArM5 und ArMDE:** Die Definitive Edition hat gegenüber der 5th Edition Seitenzahlen verschoben — dieselbe Seitenzahl kann in ArM5 und ArMDE auf unterschiedliche Abschnitte verweisen. Daher werden die Zuordnungen in **zwei getrennten** Mappings verwaltet:
- `page_to_anchors_arm5` — für Verweise mit Buch-Kontext `ArM5` / `ArM`
- `page_to_anchors_armde` — für Verweise mit Buch-Kontext `ArMDE` und für interne Verweise

Das alte `page_to_anchors` wird als **Legacy-Fallback** noch gelesen, aber neue Einträge werden immer in das passende editionsspezifische Mapping geschrieben.

**Migration bestehender Configs:** Wenn eine Config nur das alte `page_to_anchors` enthält, muss es **nicht** sofort migriert werden — das Tool fällt automatisch darauf zurück. Bei Gelegenheit (oder wenn ein Seitenzahl-Konflikt zwischen ArM5 und ArMDE auftritt) sollten die Einträge aufgeteilt werden.

1. **Sammle** alle aufgelösten Verweise aus `tmp/resolved.json`, die einen `resolved_anchor` haben.
2. **Gruppiere** sie nach Zieldatei:
   - Interne Verweise (`type: "internal"`) → Config der bearbeiteten Datei (`page_to_anchors_armde`).
   - Cross-File-Verweise (`type: "cross_file"`) → Config der jeweiligen `target_file` (`page_to_anchors_arm5` oder `page_to_anchors_armde`, je nach `book`-Feld).
3. **Für jede Zieldatei:**
   - Falls keine Config existiert: Erstelle eine mit `version`, `source_file` und leeren editionsspezifischen Mappings.
   - Trage jede neue Seite→Anker-Zuordnung in das **passende** Mapping ein (nur wenn die Seite noch nicht enthalten ist, oder der Anker noch nicht in der Liste der Seite steht).
4. **Überspringe** Verweise, die bewusst auf `null` gesetzt wurden (nicht übersetzbar, Substring-Überlappung, Seitenzahlen ohne DE-Entsprechung).

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
- Redirects: N abweichende Verweistexte (davon M neu bestätigt, O aus bestehendem Kommentar)
- Cross-File-Links: N korrigiert (englisch → deutsch)
- Zeilenzahl: unverändert / verändert (FEHLER)
