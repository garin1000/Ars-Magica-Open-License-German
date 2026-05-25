#!/usr/bin/env python3
"""Sortiert alphabetisch alle relevanten Abschnitte der deutschen Basisregeln.

Sortierte Abschnitte:
  1. Liste der Tugenden — Link-Einträge innerhalb jeder Kategorie
  2. Tugenden (Beschreibungen) — ####-Blöcke
  3. Liste der Fehler — Link-Einträge innerhalb jeder Kategorie
  4. Fehler (Beschreibungen) — ####-Blöcke
  5. Fertigkeiten nach Typ — Link-Einträge innerhalb jeder Kategorie
  6. Fertigkeitsliste — ####-Blöcke
  7. Zauber (10 Formen) — #####-Blöcke innerhalb jeder STUFE
  8. Zauberindex — Tabellenzeilen
  9. Bestiariumsindex — Tabellenzeilen
 10. Traditioneller Index — Tabellenzeilen (mit Untereinträgen)
"""

import argparse
import os
import re
import sys


# ---------------------------------------------------------------------------
# Deutsche Sortierung
# ---------------------------------------------------------------------------

_UMLAUT_MAP = str.maketrans({
    "ä": "ae", "ö": "oe", "ü": "ue",
    "Ä": "Ae", "Ö": "Oe", "Ü": "Ue",
    "ß": "ss",
})

_LEADING_ARTICLES = re.compile(
    r"^(Der|Die|Das|Den|Dem|Des|Ein|Eine|Einem|Einer|Eines)\s+", re.IGNORECASE
)


def sort_key_german(text: str) -> str:
    """Erzeugt einen Sortierschlüssel für deutschen Text."""
    t = text.translate(_UMLAUT_MAP)
    t = re.sub(r"\(.*?\)", "", t)           # Klammerinhalte entfernen
    t = re.sub(r"[^A-Za-z0-9 ]", "", t)     # Sonderzeichen entfernen
    t = t.strip()
    t = _LEADING_ARTICLES.sub("", t)
    return t.casefold()


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def find_next_h2(lines: list[str], start: int) -> int:
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("## "):
            return i
    return len(lines)


def extract_link_name(line: str) -> str:
    m = re.match(r"\[(.+?)\]", line)
    return m.group(1) if m else line


def is_link_line(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("[") and "](" in stripped


# ---------------------------------------------------------------------------
# Typ A — Link-Listen
# ---------------------------------------------------------------------------

def sort_link_list_section(lines, section_start, section_end, cat_level):
    result = list(lines[section_start:section_end])
    stats = {"categories": 0, "entries": 0, "reordered": 0}

    i = 0
    while i < len(result):
        if result[i].startswith(cat_level):
            stats["categories"] += 1
            j = i + 1
            link_positions = []
            link_lines = []
            while j < len(result) and not result[j].startswith("#"):
                if is_link_line(result[j]):
                    link_positions.append(j)
                    link_lines.append(result[j])
                j += 1

            if link_lines:
                stats["entries"] += len(link_lines)
                sorted_links = sorted(
                    link_lines,
                    key=lambda l: sort_key_german(extract_link_name(l))
                )
                if sorted_links != link_lines:
                    stats["reordered"] += sum(
                        1 for a, b in zip(link_lines, sorted_links) if a != b
                    )
                for pos, new_line in zip(link_positions, sorted_links):
                    result[pos] = new_line

            i = j
        else:
            i += 1

    return result, stats


# ---------------------------------------------------------------------------
# Typ B — Beschreibungsblöcke (####-Ebene)
# ---------------------------------------------------------------------------

def sort_description_blocks(lines, section_start, section_end):
    section = lines[section_start:section_end]
    stats = {"entries": 0, "reordered": 0}

    first_h4 = -1
    for i, line in enumerate(section):
        if line.startswith("#### "):
            first_h4 = i
            break

    if first_h4 == -1:
        return section, stats

    preamble = section[:first_h4]

    blocks = []
    current_block_start = first_h4
    for i in range(first_h4 + 1, len(section)):
        if section[i].startswith("#### ") or section[i].startswith("## ") or section[i].startswith("### "):
            blocks.append(section[current_block_start:i])
            current_block_start = i
            if section[i].startswith("## ") or section[i].startswith("### "):
                break

    if current_block_start < len(section) and section[current_block_start].startswith("#### "):
        blocks.append(section[current_block_start:])

    if not blocks:
        return section, stats

    stats["entries"] = len(blocks)

    def block_name(block):
        return block[0][5:].strip()

    sorted_blocks = sorted(blocks, key=lambda b: sort_key_german(block_name(b)))
    if sorted_blocks != blocks:
        stats["reordered"] = sum(
            1 for a, b in zip(blocks, sorted_blocks) if a[0] != b[0]
        )

    result = list(preamble)
    for block in sorted_blocks:
        result.extend(block)

    total_block_lines = sum(len(b) for b in blocks)
    last_block_end = first_h4 + total_block_lines
    if last_block_end < len(section) and not section[last_block_end].startswith("#### "):
        result.extend(section[last_block_end:])

    return result, stats


# ---------------------------------------------------------------------------
# Typ C — Zauberblöcke (#####-Ebene innerhalb #### STUFE X)
# ---------------------------------------------------------------------------

def sort_spell_section(lines, form_start, form_end):
    section = lines[form_start:form_end]
    result = []
    stats = {"levels": 0, "spells": 0, "reordered": 0}

    i = 0
    while i < len(section):
        line = section[i]

        if line.startswith("### ") and "Zauber" in line and "Leitlinien" not in line:
            result.append(line)
            i += 1
            while i < len(section) and not (section[i].startswith("### ") or section[i].startswith("## ")):
                if section[i].startswith("#### STUFE"):
                    stats["levels"] += 1
                    result.append(section[i])
                    i += 1

                    spell_blocks = []
                    current_spell_start = -1
                    pre_spell_lines = []

                    while i < len(section):
                        if section[i].startswith("##### "):
                            if current_spell_start >= 0:
                                spell_blocks.append(section[current_spell_start:i])
                            current_spell_start = i
                            i += 1
                        elif section[i].startswith("#### ") or section[i].startswith("### ") or section[i].startswith("## "):
                            break
                        else:
                            if current_spell_start == -1:
                                pre_spell_lines.append(section[i])
                            i += 1

                    if current_spell_start >= 0:
                        spell_blocks.append(section[current_spell_start:i])

                    result.extend(pre_spell_lines)

                    if spell_blocks:
                        stats["spells"] += len(spell_blocks)
                        sorted_spells = sorted(
                            spell_blocks,
                            key=lambda b: sort_key_german(b[0][6:].strip())
                        )
                        if sorted_spells != spell_blocks:
                            stats["reordered"] += sum(
                                1 for a, b in zip(spell_blocks, sorted_spells)
                                if a[0] != b[0]
                            )
                        for block in sorted_spells:
                            result.extend(block)
                else:
                    result.append(section[i])
                    i += 1
        else:
            result.append(line)
            i += 1

    return result, stats


# ---------------------------------------------------------------------------
# Typ D — Index-Tabellen
# ---------------------------------------------------------------------------

def sort_index_table(lines, section_start, section_end, keep_sub_entries=False):
    section = lines[section_start:section_end]
    stats = {"entries": 0, "reordered": 0}

    table_start = -1
    for i, line in enumerate(section):
        stripped = line.strip()
        if stripped.startswith("|") and "---" in stripped:
            table_start = i - 1
            break

    if table_start < 0:
        return section, stats

    preamble = section[:table_start]
    table_header = section[table_start]
    table_sep = section[table_start + 1]
    data_start = table_start + 2

    data_lines = []
    data_end = data_start
    for i in range(data_start, len(section)):
        stripped = section[i].strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            data_lines.append(section[i])
            data_end = i + 1
        elif stripped == "":
            data_end = i
            break
        else:
            data_end = i
            break

    if not data_lines:
        return section, stats

    if keep_sub_entries:
        groups = []
        for line in data_lines:
            cell = line.split("|")[1].strip() if "|" in line else ""
            if cell.startswith("&nbsp;") or cell.startswith("*siehe"):
                if groups:
                    groups[-1].append(line)
                else:
                    groups.append([line])
            else:
                groups.append([line])

        stats["entries"] = len(groups)

        def group_key(group):
            cell = group[0].split("|")[1].strip() if "|" in group[0] else ""
            return sort_key_german(cell)

        sorted_groups = sorted(groups, key=group_key)
        if sorted_groups != groups:
            stats["reordered"] = sum(
                1 for a, b in zip(groups, sorted_groups) if a[0] != b[0]
            )

        sorted_data = []
        for g in sorted_groups:
            sorted_data.extend(g)
    else:
        stats["entries"] = len(data_lines)

        def line_sort_key(line):
            cell = line.split("|")[1].strip() if "|" in line else ""
            return sort_key_german(cell)

        sorted_data = sorted(data_lines, key=line_sort_key)
        if sorted_data != data_lines:
            stats["reordered"] = sum(
                1 for a, b in zip(data_lines, sorted_data) if a != b
            )

    result = list(preamble)
    result.append(table_header)
    result.append(table_sep)
    result.extend(sorted_data)
    if data_end < len(section):
        result.extend(section[data_end:])

    return result, stats


# ---------------------------------------------------------------------------
# Hauptprogramm
# ---------------------------------------------------------------------------

SPELL_FORMS = [
    "Animal-Zauber", "Aquam-Zauber", "Auram-Zauber", "Corpus-Zauber",
    "Herbam-Zauber", "Ignem-Zauber", "Imaginem-Zauber", "Mentem-Zauber",
    "Terram-Zauber", "Vim-Zauber",
]


def process(input_path: str, output_dir: str) -> None:
    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for i in range(len(lines)):
        if not lines[i].endswith("\n"):
            lines[i] += "\n"

    original_count = len(lines)
    report = []

    h2_index = {}
    for i, line in enumerate(lines):
        if line.startswith("## "):
            title = line[3:].strip()
            h2_index[title] = i

    output = list(lines)

    sections_to_process = []

    if "Liste der Tugenden" in h2_index:
        start = h2_index["Liste der Tugenden"]
        end = find_next_h2(lines, start)
        sections_to_process.append(("Liste der Tugenden", "link_list", start, end, "### "))

    if "Tugenden" in h2_index:
        start = h2_index["Tugenden"]
        end = find_next_h2(lines, start)
        sections_to_process.append(("Tugenden (Beschreibungen)", "desc_blocks", start, end))

    if "Liste der Fehler" in h2_index:
        start = h2_index["Liste der Fehler"]
        end = find_next_h2(lines, start)
        sections_to_process.append(("Liste der Fehler", "link_list", start, end, "### "))

    if "Fehler" in h2_index:
        start = h2_index["Fehler"]
        end = find_next_h2(lines, start)
        sections_to_process.append(("Fehler (Beschreibungen)", "desc_blocks", start, end))

    if "Fertigkeiten nach Typ" in h2_index:
        start = h2_index["Fertigkeiten nach Typ"]
        end = find_next_h2(lines, start)
        sections_to_process.append(("Fertigkeiten nach Typ", "link_list", start, end, "#### "))

    if "Fertigkeitsliste" in h2_index:
        start = h2_index["Fertigkeitsliste"]
        end = find_next_h2(lines, start)
        sections_to_process.append(("Fertigkeitsliste (Beschreibungen)", "desc_blocks", start, end))

    for form in SPELL_FORMS:
        if form in h2_index:
            start = h2_index[form]
            end = find_next_h2(lines, start)
            sections_to_process.append((f"Zauber: {form}", "spells", start, end))

    if "Zauberindex" in h2_index:
        start = h2_index["Zauberindex"]
        end = find_next_h2(lines, start)
        sections_to_process.append(("Zauberindex", "table", start, end, False))

    if "Bestiariumsindex" in h2_index:
        start = h2_index["Bestiariumsindex"]
        end = find_next_h2(lines, start)
        sections_to_process.append(("Bestiariumsindex", "table", start, end, False))

    if "Traditioneller Index" in h2_index:
        start = h2_index["Traditioneller Index"]
        end = find_next_h2(lines, start)
        sections_to_process.append(("Traditioneller Index", "table", start, end, True))

    sections_to_process.sort(key=lambda s: s[2], reverse=True)

    for section_info in sections_to_process:
        name = section_info[0]
        stype = section_info[1]
        start = section_info[2]
        end = section_info[3]

        if stype == "link_list":
            cat_level = section_info[4]
            new_lines, stats = sort_link_list_section(output, start, end, cat_level)
            output[start:end] = new_lines
            report.append(
                f"  {name}: {stats['entries']} Einträge in {stats['categories']} "
                f"Kategorien, {stats['reordered']} umsortiert"
            )
        elif stype == "desc_blocks":
            new_lines, stats = sort_description_blocks(output, start, end)
            output[start:end] = new_lines
            report.append(
                f"  {name}: {stats['entries']} Einträge, "
                f"{stats['reordered']} umsortiert"
            )
        elif stype == "spells":
            new_lines, stats = sort_spell_section(output, start, end)
            output[start:end] = new_lines
            report.append(
                f"  {name}: {stats['spells']} Zauber in {stats['levels']} Stufen, "
                f"{stats['reordered']} umsortiert"
            )
        elif stype == "table":
            keep_sub = section_info[4]
            new_lines, stats = sort_index_table(output, start, end, keep_sub)
            output[start:end] = new_lines
            report.append(
                f"  {name}: {stats['entries']} Einträge, "
                f"{stats['reordered']} umsortiert"
            )

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, os.path.basename(input_path))
    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(output)

    output_count = len(output)

    print("=" * 60)
    print("SORTIERBERICHT")
    print("=" * 60)
    print(f"  Eingabe:  {input_path}")
    print(f"  Ausgabe:  {output_path}")
    print(f"  Zeilen:   {original_count} -> {output_count}", end="")
    if original_count != output_count:
        print(f"  ABWEICHUNG: {output_count - original_count:+d}")
    else:
        print("  identisch")
    print()
    print("Verarbeitete Abschnitte:")
    for line in sorted(report):
        print(line)
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Sortiert Abschnitte der deutschen Ars-Magica-Basisregeln."
    )
    parser.add_argument(
        "--input", "-i",
        default="german-reviewed/Ars Magica Definitive Edition Basisregeln Deutsch.md",
        help="Pfad zur Eingabedatei",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="german-ordered",
        help="Ausgabeverzeichnis",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Fehler: Eingabedatei nicht gefunden: {args.input}", file=sys.stderr)
        sys.exit(1)

    process(args.input, args.output_dir)


if __name__ == "__main__":
    main()
