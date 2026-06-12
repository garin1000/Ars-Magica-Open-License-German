# Formatierungsregeln: SC-, NSC- und Kreaturenbeschreibungen

**Grundlage:** Statblöcke aus ArsMagica_DE_Gesamt_work.md (Darius von Flambeau, Bjornaer-Vorlage, Der abgebrühte Veteran, Wolf, Baghl)

---

## 1. Übersicht der Beschreibungstypen

| Typ | Anwendung | Besonderheiten |
|---|---|---|
| **Magus / Maga** | SC und wichtige NSC-Magi | Künste, Bekannte Zauber, Verzerrungspunkte, Zwielichtnarben; kein Größe-Feld |
| **Mundaner SC / NSC** | Gefährten, Grogs, NSC-Sterbliche | Größe-Feld vorhanden; kein Künste-Feld; Selbstvertrauen nur bei Gefährten |
| **Kreatur ohne Machtwert** | Gewöhnliche Tiere | Klu statt Int; doppeltes Eigenschaften-Feld; Natürliche Waffen-Abschnitt |
| **Kreatur mit Machtwert** | Geister, Dämonen, Feen, magische Wesen | Machtwert als erstes Feld; Kräfte-Abschnitt; Vis wenn vorhanden |

---

## 2. Allgemeine Konventionen

### Feldbezeichnungen

- Feldbezeichnungen sind **nicht fett**, sondern schlicht als Label mit Doppelpunkt: `Eigenschaften:`, `Kampf:` usw.
- Jedes Feld beginnt in einer neuen Zeile; zwischen Feldern steht eine Leerzeile.

### Vorzeichen und Trennzeichen

- Positive Werte mit `+`: `+3`, `+1`
- Negative Werte mit einfachem Bindestrich `-`: `-2`, `-1`
- Null ohne Vorzeichen: `0`
- Wertebereiche mit einfachem Bindestrich: `1-5`, `6-10`
- Nicht zutreffend: `n/v`

### Listen (Kampf, Zauber, Fertigkeiten)

- Listeneinträge mit einfachem Bindestrich `-` als Aufzählungszeichen.
- Kampfeinträge und Bekannte Zauber als Aufzählung mit `-`.
- Fertigkeiten und Tugenden/Fehler als Fließtext (kommagetrennt), **keine** Liste.

### Kraftnamen

- Kraftnamen kursiv mit Sternchen: `*Kraftname*`
- Nach dem Kraft-Header ein `<br>` vor dem Beschreibungstext (kein einfacher Zeilenumbruch).

---

## 3. Abschnittsreihenfolge

### 3.1 Magus / Maga

| # | Feldbezeichnung | Pflicht | Hinweis |
|---|---|---|---|
| 1 | `Eigenschaften:` | ✓ | Kein Größe-Feld bei Magi |
| 2 | `Alter:` | ✓ | |
| 3 | `Gebrechlichkeit:` | ✓ | |
| 4 | `Verzerrungspunkte:` | ✓ | Nicht „Verwicklungswert" |
| 5 | `Selbstvertrauenswert:` | ✓ | |
| 6 | `Tugenden und Fehler:` | ✓ | |
| 7 | `Persönlichkeitseigenschaften:` | ✓ | |
| 8 | `Reputationen:` | ○ | Bei keinen: weglassen oder `Keine.` |
| 9 | `Kampf:` | ✓ | |
| 10 | `Absorption:` | ✓ | |
| 11 | `Erschöpfungsstufen:` | ✓ | |
| 12 | `Wundabzüge:` | ✓ | |
| 13 | `Fertigkeiten:` | ✓ | |
| 14 | `Künste:` | ✓ | |
| 15 | `Zwielichtnarben:` | ○ | Nur wenn vorhanden; sonst `Keine` |
| 16 | `Ausrüstung:` | ○ | |
| 17 | `Belastung:` | ✓ | |
| 18 | `Bekannte Zauber:` | ✓ | |
| 19 | `Erscheinungsbild:` | ○ | Fließtext |

### 3.2 Mundaner SC / NSC (Gefährte, Grog, Sterblicher)

| # | Feldbezeichnung | Pflicht | Hinweis |
|---|---|---|---|
| 1 | `Eigenschaften:` | ✓ | |
| 2 | `Größe:` | ✓ | Im Gegensatz zu Magi vorhanden |
| 3 | `Alter:` | ○ | Bei wichtigen NSC angeben |
| 4 | `Gebrechlichkeit:` | ○ | Bei älteren Charakteren |
| 5 | `Verzerrungspunkte:` | ○ | Bei übernatürlich exponierten Charakteren |
| 6 | `Selbstvertrauenswert:` | ○ | Nur bei Gefährten |
| 7 | `Tugenden und Fehler:` | ✓ | |
| 8 | `Persönlichkeitseigenschaften:` | ✓ | |
| 9 | `Reputationen:` | ○ | |
| 10 | `Kampf:` | ✓ | |
| 11 | `Absorption:` | ✓ | |
| 12 | `Erschöpfungsstufen:` | ✓ | |
| 13 | `Wundabzüge:` | ✓ | |
| 14 | `Fertigkeiten:` | ✓ | |
| 15 | `Ausrüstung:` | ○ | |
| 16 | `Belastung:` | ✓ | |
| 17 | `Erscheinungsbild:` | ○ | |

### 3.3 Kreatur ohne Machtwert (gewöhnliches Tier)

| # | Feldbezeichnung | Pflicht | Hinweis |
|---|---|---|---|
| 1 | `Eigenschaften:` | ✓ | Klu statt Int |
| 2 | `Größe:` | ✓ | |
| 3 | `Selbstvertrauenswert:` | ○ | |
| 4 | `Tugenden und Fehler:` | ○ | |
| 5 | `Eigenschaften:` | ✓ | Zweites Vorkommen: Tier-Qualities (Aggressiv, Zäh usw.) |
| 6 | `Persönlichkeitseigenschaften:` | ✓ | |
| 7 | `Reputationen:` | ○ | |
| 8 | `Kampf:` | ✓ | |
| 9 | `Absorption:` | ✓ | |
| 10 | `Erschöpfungsstufen:` | ○ | |
| 11 | `Wundabzüge:` | ✓ | |
| 12 | `Fertigkeiten:` | ○ | |
| 13 | `Natürliche Waffen:` | ○ | Waffenwerte der natürlichen Angriffe |
| 14 | `Erscheinungsbild:` | ○ | |

### 3.4 Kreatur mit Machtwert (Geist, Dämon, Fee, magisches Wesen)

| # | Feldbezeichnung | Pflicht | Hinweis |
|---|---|---|---|
| 1 | `Machtwert:` | ✓ | Format: `Wert (Form)`, z. B. `15 (Terram)` |
| 2 | `Eigenschaften:` | ✓ | |
| 3 | `Größe:` | ○ | Wenn abweichend von 0 |
| 4 | `Selbstvertrauenswert:` | ○ | |
| 5 | `Tugenden und Fehler:` | ○ | |
| 6 | `Persönlichkeitseigenschaften:` | ✓ | |
| 7 | `Rufe:` | ○ | Statt `Reputationen:` |
| 8 | `Kampf:` | ✓ | |
| 9 | `Absorption:` | ✓ | |
| 10 | `Erschöpfungsstufen:` | ○ | |
| 11 | `Wundabzüge:` | ✓ | |
| 12 | `Fertigkeiten:` | ○ | |
| 13 | `Kräfte:` | ✓ | |
| 14 | `Vis:` | ○ | |
| 15 | `Ausrüstung:` | ○ | |
| 16 | `Belastung:` | ○ | |
| 17 | `Erscheinungsbild:` | ○ | |

---

## 4. Feldformat-Referenz

### 4.1 Eigenschaften (Charakteristiken)

```
Eigenschaften: Int +3, Wah +1, Stä +2, Aus 0, Prä -3, Kom -1, Ges +1, Sck +2
```

Reihenfolge: **Int, Wah, Prä, Kom, Stä, Aus, Ges, Sck**

Bei Tieren: **Klu** (Klugheit) statt Int.

Durch Alterung abgesunkene Werte: aktuellen Wert angeben, den früheren Höchstwert in Klammern dahinter: `Prä -3 (2)` (aktuell -3, ehemals +2).

### 4.2 Alter

```
Alter: 87 (64), Hermetisches Alter 62 Jahre nach der Lehrlingsprüfung.
Alter: 45 (45)
```

Bei Magi: tatsächliches Alter, scheinbares Alter in Klammern, Hermetisches Alter als Freitext. Bei Mundanen: nur eine Zahl oder `tatsächlich (scheinbar)`. Bei Kreaturen, die nicht altern: weglassen oder `n/v`.

### 4.3 Gebrechlichkeit / Verzerrungspunkte / Selbstvertrauenswert

```
Gebrechlichkeit: 0(2)
Verzerrungspunkte: 6 (19)
Selbstvertrauenswert: 1 (3)
```

Format: `Stufe(angesammelte Punkte)`. Beim Selbstvertrauenswert mit Leerzeichen vor Klammer: `1 (3)`.

### 4.4 Tugenden und Fehler

```
Tugenden und Fehler: Die Gabe; Hermetischer Magus; Begabung in (Kunst) (Perdo) (kostenlose Tugend), Makellose Magie, Affinität zu Perdo, Schneller Zauberer; Auffällige Gabe, Getrieben (Feinde des Ordens jagen), Entstellt (Brandnarben im Gesicht)
```

Reihenfolge durch Semikolon gegliedert: Kostenlose Tugenden → Große/Kleine Tugenden → Große/Kleine Fehler. Spezifizierungen in runden Klammern direkt nach dem Namen.

### 4.5 Persönlichkeitseigenschaften

```
Persönlichkeitseigenschaften: Tapfer +3, Sache verschrieben +3, Effizient +3
```

### 4.6 Reputationen

```
Reputationen: Engagierter Hoplit +3 (hermetische Magi)
Reputationen: Blutrünstig (lokal) 4
Reputationen: Keine.
```

Einheitlich `Reputationen:` für alle Charaktertypen — Reputation ist ein fester Regelbegriff. Format: `Inhalt Stufe (Typ)`. Wenn keine vorhanden: `Keine.` oder weglassen.

Hinweis: Die aktuelle Übersetzungsdatei (ArsMagica_DE_Gesamt.md) verwendet bei Kreaturen `Rufe:` — dies wird in der deutschen Ausgabe **nicht** übernommen.

### 4.7 Kampf

```
Kampf:
- Faust: Init +2, Ang +5, Vert +6, Sch +2
- Tritt: Init +1, Ang +4, Vert +4, Sch +5
- Langer Speer: Init +5, Ang +9, Vert +8, Sch +9
- Ausweichen: Init +1, Angriff n/v, Verteidigung +4, Schaden n/v
```

Jede Option in einer Zeile mit `-`. Spaltenreihenfolge: **Init, Ang, Vert, Sch**. Nicht anwendbare Werte: `n/v`. Freitext zu Kampfbesonderheiten (z. B. Hitze beim Angriff) als eigener Absatz nach der Liste, vor `Schadensabsorption`.

### 4.8 Absorption

```
Absorption: +0
Absorption: +8 (vollständige Metallschuppenrüstung)
```

Quelle in Klammern nur wenn spielrelevant.

### 4.9 Erschöpfungsstufen

```
Erschöpfungsstufen: OK, 0, 0, -2, -4, Bewusstlos
Erschöpfungsstufen: OK, 0, -1, -3, -5, Bewusstlos
Erschöpfungsstufen: OK, 0/0, -1/-1, -3, -5, Bewusstlos
```

Zusätzliche Stufen durch Schrägstrich innerhalb einer Stufe: `0/0`. Letzte Stufe `Bewusstlos`; bei Wesen die sterben statt bewusstlos werden: `Tot`.

### 4.10 Wundabzüge

```
Wundabzüge: -1 (1-5), -3 (6-10), -5 (11-15), Lähmend (16-20)
Wundabzüge: -1 (1-4), -3 (5-8), -5 (9-12), Kampfunfähig (13-16), Tot (17+)
Wundabzüge: -1 (1-7), -3 (8-14), -5 (15-21), Kampfunfähig (22-28), Tot (29+)
```

Intervallgröße skaliert mit Größe (Größe 0 = 5er-Schritte, Größe -1 = 4er-Schritte, Größe +3 = 7er-Schritte usw.). Letzte Stufe je nach Typ: Sterbliche → `Lähmend`; Kreaturen → `Kampfunfähig` + `Tot`; vertriebene Wesen → `Verbannt`.

### 4.11 Fertigkeiten

```
Fertigkeiten: Artes Liberales 4 (Grammatik), Athletik 2 (Laufen), Aufmerksamkeit 3 (Wachsamkeit), Raufen 3 (Schlagen), Magietheorie 5 (Zauber erfinden), Parma Magica 5 (Corpus)
```

Format: `Fertigkeitsname Wert (Spezialisierung)`. Kommagetrennt, kein Zeilenumbruch je Eintrag. Ortsbezogene Wissensfähigkeiten: `(Gebiets-)Kunde` oder `Gebietskunde`.

### 4.12 Künste (nur Magi)

```
Künste: Cr 10, In 6, Mu 4, Pe 18+3 (15), Re 9; An 5, Aq 6, Au 6, Co 15, He 6, Ig 6, Im 5, Me 6, Te 6 (4), Vi 8
```

Techniken zuerst (Cr In Mu Pe Re), Semikolon, dann Formen (An Aq Au Co He Ig Im Me Te Vi). Begabung in Kunst: `Pe 18+3 (15)` — aktueller Wert + Bonus (Basiswert in Klammern).

### 4.13 Zwielichtnarben

```
Zwielichtnarben: Die Schatten in Darius' Kapuze sind ungewöhnlich tief und verbergen sein Gesicht; nahegelegene, nicht-magische Gegenstände verfallen, wenn Darius Magie wirkt.
Zwielichtnarben: Keine
```

Freitext; mehrere Narben durch Semikolon trennen.

### 4.14 Ausrüstung

```
Ausrüstung: Langer Speer mit als Talisman verzaubertem Schaft, eingebettet mit dem Effekt Die Wunde, die weint (PeCo 15, Penetration 0, 50 Anwendungen pro Tag), abgestimmt auf einen +4-Bonus für Zauber, die auf Distanz zerstören, Langlebigkeitsritual: Laborsumme 35, +7 Alterungsbonus
```

Verzauberte Gegenstände mit deutschem Effektnamen, Technik-Form-Kürzel, Stufe und Nutzungsbeschränkung. Langlebigkeitsritual im Ausrüstungsfeld, kein eigener Abschnitt.

### 4.15 Belastung

```
Belastung: 0(2)
Belastung: 4 (4)
```

Format: `Wert(Last)` oder `Wert (Last)` — beide Varianten kommen vor.

### 4.16 Bekannte Zauber (nur Magi)

```
Bekannte Zauber:
- Den heulenden Wolf lähmen (PeAn 25/+27*), Meisterschaft 1 (Schnellzaubern)
- Sieben-Meilen-Schritt (ReCo 30/+25), Meisterschaft 1 (Schnellzaubern)
- Wind der weltlichen Stille (PeVi 30/+30), Meisterschaft 1 (Magieresistenz)

* Wenn Darius seinen Talisman hält, erhält er einen +4-Bonus ...
```

Format: `- Deutscher Zaubername (TechForm Stufe/+Bonus), Meisterschaft Stufe (Technik)`. Sonderboni mit `*` markieren; Erläuterung als Fußnote nach der Liste.

### 4.17 Eigenschaften: Tier-Qualities (zweites Vorkommen bei Tieren)

```
Eigenschaften: Aggressiv, Widerstandsfähig, Feiner Geruchssinn, Rudeltier/Rudelführer, Verfolgungsjäger, Scharfe Ohren, Dickes Fell, Lautstark
```

Dasselbe Feldlabel `Eigenschaften:` erscheint bei Tieren ein zweites Mal — nach `Tugenden und Fehler:` — für die Tier-Qualities (positive Tiereigenschaften). Kommagetrennte Liste.

### 4.18 Natürliche Waffen (nur Tiere)

```
Natürliche Waffen:
- Zähne: Init 0, Ang +3, Vert +1, Sch +1
```

Format wie `Kampf:`. Freitext zu Besonderheiten (z. B. Fell-Schutzbonus) als eigener Absatz darunter.

### 4.19 Kräfte (nur Kreaturen mit Machtwert)

```
Kräfte:

*Fleisch zu Stein*, 2 Punkte, Init -4, Terram:<br>
Baghl kann jeden Menschen, den er berührt, bis zum Sonnenaufgang in Stein verwandeln (Basis 20, +1 Berührung, +2 Sonne).

*Körperlos*, 0 Punkte, Init Konstant, Mentem:<br>
Baghl ist von Natur aus sowohl unsichtbar als auch nicht greifbar ...
```

Format: `*Kraftname*, X Punkte, Init Y, Form:<br>` — mit `<br>` am Ende der Header-Zeile, dann Beschreibungstext in der nächsten Zeile. Machtkosten 0 ausschreiben. Dauernde Kräfte: `Init Konstant`. Variable Kosten: `variable Punkte` mit Erläuterung in der Beschreibung. Kräfte durch Leerzeile trennen.

### 4.20 Vis

```
Vis: 2 Ignem, 1 Rego
Vis: 1 Bauer Terram-Vis kann jedes Jahr aus seinem Revier gesammelt werden, in Form eines quarzbedeckten Stalaktiten.
```

Kurze Angabe oder Freitext mit Fundort.

### 4.21 Erscheinungsbild

Fließtext. Empfohlene Reihenfolge: äußere Beschreibung → Hintergrund/Persönlichkeit → Spielleitungshinweise (optional).

---

## 5. Eigenschaften-Kürzel

| Kürzel | Deutsch | Englisch | Anwendung |
|---|---|---|---|
| Int | Intelligenz | Intelligence | Menschen, Geister, intelligente Wesen |
| Klu | Klugheit | Cunning | Tiere ohne Vernunft |
| Wah | Wahrnehmung | Perception | alle |
| Prä | Präsenz | Presence | alle |
| Kom | Kommunikation | Communication | alle |
| Stä | Stärke | Strength | alle |
| Aus | Ausdauer | Stamina | alle |
| Ges | Geschicklichkeit | Dexterity | alle |
| Sck | Schnelligkeit | Quickness | alle |

---

## 6. Meisterschaftstechniken

| Englisch (EN) | Deutsch (DE) |
|---|---|
| Fast Casting | Schnellzaubern |
| Magic Resistance | Magieresistenz |
| Multiple Casting | Mehrfachzaubern |
| Penetration | Penetration |
| Quiet Casting | Stilles Zaubern |
| Stalwart Casting | Standhaftes Zaubern |
| Still Casting | Regloses Zaubern |
| Subtle Casting | Dezentes Zaubern |
| Tethered Casting | Gefesseltes Zaubern |
| Unravelling | Auflösung |

---

## 7. Vollständige Musterblöcke

### 7.1 Muster: Magus

```
Eigenschaften: Int +3, Wah +1, Stä +2, Aus 0, Prä -3, Kom -1, Ges +1, Sck +2

Alter: 87 (64), Hermetisches Alter 62 Jahre nach der Lehrlingsprüfung.

Gebrechlichkeit: 0(2)

Verzerrungspunkte: 6 (19)

Selbstvertrauenswert: 1 (3)

Tugenden und Fehler: Die Gabe; Hermetischer Magus; Begabung in Perdo (kostenlose Tugend), Makellose Magie, Affinität zu Perdo, Schneller Zauberer; Auffällige Gabe, Getrieben (Feinde des Ordens jagen), Entstellt (Brandnarben im Gesicht)

Persönlichkeitseigenschaften: Tapfer +3, Sache verschrieben +3, Effizient +3

Reputationen: Engagierter Hoplit +3 (hermetische Magi)

Kampf:
- Faust: Init +2, Ang +5, Vert +6, Sch +2
- Langer Speer: Init +5, Ang +9, Vert +8, Sch +9

Absorption: +0

Erschöpfungsstufen: OK, 0, 0, -2, -4, Bewusstlos

Wundabzüge: -1 (1-5), -3 (6-10), -5 (11-15), Lähmend (16-20)

Fertigkeiten: Athletik 2 (Laufen), Aufmerksamkeit 3 (Wachsamkeit), Große Waffe 4 (Langer Speer), Konzentration 3 (Zauber), Magietheorie 5 (Zauber erfinden), Parma Magica 5 (Corpus), Penetration 6 (Perdo)

Künste: Cr 10, In 6, Mu 4, Pe 18+3 (15), Re 9; An 5, Aq 6, Au 6, Co 15, He 6, Ig 6, Im 5, Me 6, Te 6, Vi 8

Zwielichtnarben: Die Schatten in seiner Kapuze sind ungewöhnlich tief; nahegelegene Gegenstände verfallen, wenn er Magie wirkt.

Ausrüstung: Langer Speer (Talisman; Die Wunde, die weint, PeCo 15, Penetration 0, 50 Anwendungen pro Tag; +4-Bonus auf Distanzzerstörung). Langlebigkeitsritual: Laborsumme 35, +7 Alterungsbonus

Belastung: 0(2)

Bekannte Zauber:
- Ewige Auslöschung des Dämons (PeVi 30/+30*), Meisterschaft 1 (Schnellzaubern)
- Sieben-Meilen-Schritt (ReCo 30/+25), Meisterschaft 1 (Schnellzaubern)
- Wind der weltlichen Stille (PeVi 30/+30), Meisterschaft 1 (Magieresistenz)

* Talismanbonus +4 gilt, solange der Talisman gehalten wird.

Erscheinungsbild: [Fließtext]
```

---

### 7.2 Muster: Kreatur mit Machtwert

```
Machtwert: 15 (Terram)

Eigenschaften: Int -2, Wah +2, Prä +1, Kom -1, Stä +3, Aus +3, Ges +1, Sck -1

Selbstvertrauenswert: 1 (3 Punkte)

Tugenden und Fehler: Große Immunität: Feuer, Willensstark, Zäh, Große Verfluchung (muss eingegangene Abmachungen halten)

Persönlichkeitseigenschaften: Zurückgezogen +5, Unveränderlich +3, Stolz +2

Kampf:
- Kriegshammer: Init -1, Ang +11, Vert +3, Sch +15

Absorption: +10

Wundabzüge: -1 (1-7), -3 (8-14), -5 (15-21), Kampfunfähig (22-28), Tot (29+)

Fertigkeiten: Athletik 3 (Klettern), Große Waffe 4 (Maul), Zweites Gesicht 4 (Dschinne)

Kräfte:

*Fleisch zu Stein*, 2 Punkte, Init -4, Terram:<br>
Kann jeden Menschen, den er berührt, bis zum Sonnenaufgang in Stein verwandeln (Basis 20, +1 Berührung, +2 Sonne).

*Körperlos*, 0 Punkte, Init Konstant, Mentem:<br>
Von Natur aus unsichtbar und nicht greifbar; kann von der physischen Welt nicht beeinflusst werden.

Vis: 1 Bauer Terram-Vis jährlich aus seinem Revier; 3 Bauern Terram-Vis im erschlagenen Körper.

Erscheinungsbild: [Fließtext]
```

---

*Grundlage: ArsMagica_DE_Gesamt_work.md*
