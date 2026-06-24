#!/usr/bin/env python3
"""Sortiert alphabetisch relevante Abschnitte deutscher Ars-Magica-Regelwerke.

Unterstützt 6 Sortiertypen:
  A. link_list    — Link-Einträge [Name](link) innerhalb von Kategorieüberschriften
  B. desc_blocks  — ####-Blöcke (Tugenden, Fehler, Fertigkeiten)
  C. spells       — #####-Blöcke innerhalb #### STUFE X
  D. table        — Markdown-Tabellenzeilen
  E. bold_blocks  — **Name:**-Absatzblöcke (Qualitäten, Mängel)
  F. inline_list  — Kommaseparierte Einträge innerhalb von Tabellenzellen

Die zu sortierenden Abschnitte werden pro Datei in einer JSON-Config gespeichert
(tools/sort-entries/configs/). Beim ersten Lauf wird die Config automatisch durch
Strukturanalyse erzeugt.
"""

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_DIR = SCRIPT_DIR / "configs"


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

def _is_h1(line: str) -> bool:
    return line.startswith("# ") and not line.startswith("## ")


def find_next_h2(lines: list[str], start: int) -> int:
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("## ") or _is_h1(lines[i]):
            return i
    return len(lines)


def find_next_h3_or_above(lines: list[str], start: int) -> int:
    for i in range(start + 1, len(lines)):
        if _is_h1(lines[i]) or lines[i].startswith("## ") or lines[i].startswith("### "):
            return i
    return len(lines)


def _adjust_for_chapter_opener(lines: list[str], end: int) -> int:
    """Bewegt end rückwärts, um vorausgehende --- + Zitatblock-Muster auszuschließen."""
    i = end - 1
    while i >= 0 and lines[i].strip() == "":
        i -= 1
    if i >= 0 and lines[i].strip().startswith(">"):
        i -= 1
        while i >= 0 and lines[i].strip() == "":
            i -= 1
    if i >= 0 and lines[i].strip() == "---":
        return i
    return end


_BQ_PREFIX_RE = re.compile(r"^>\s*")


def _detect_bq_prefix(lines: list[str]) -> str:
    """Bestimmt den häufigsten Blockquote-Präfix (z.B. '>' oder '> ')."""
    from collections import Counter
    prefixes = Counter()
    for line in lines:
        m = re.match(r"^(>\s?)", line)
        if m and line.rstrip("\n") != ">":
            prefixes[m.group(1)] += 1
    if prefixes:
        return prefixes.most_common(1)[0][0]
    return ">"


def _strip_bq_line(line: str) -> str:
    """Entfernt den >-Präfix (mit beliebig vielen Leerzeichen) von einer Zeile."""
    if line.rstrip("\n").rstrip() == ">":
        return "\n"
    return _BQ_PREFIX_RE.sub("", line, count=1)


def _strip_bq_lines(lines: list[str]) -> list[str]:
    return [_strip_bq_line(line) for line in lines]


def _restore_bq_lines(lines: list[str], prefix: str) -> list[str]:
    """Fügt einen einheitlichen Blockquote-Präfix hinzu."""
    result = []
    for line in lines:
        if line.strip() == "":
            result.append(">\n")
        else:
            result.append(prefix + line)
    return result


def _is_bq_line(line: str) -> bool:
    return line.lstrip().startswith(">")


def extract_link_name(line: str) -> str:
    m = re.match(r"\[(.+?)\]", line)
    return m.group(1) if m else line


def is_link_line(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("[") and "](" in stripped


def find_heading_line(lines: list[str], heading_text: str,
                      occurrence: int = 1, start: int = 0,
                      end: int | None = None) -> int:
    if end is None:
        end = len(lines)
    count = 0
    for i in range(start, end):
        if lines[i].strip() == heading_text:
            count += 1
            if count == occurrence:
                return i
    return -1


def build_heading_index(lines: list[str]) -> list[tuple[int, int, str]]:
    """Gibt (Zeile, Ebene, Titel) für alle nicht-blockquotierten Überschriften."""
    headings = []
    for i, line in enumerate(lines):
        if line.lstrip().startswith(">"):
            continue
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue
        level = 0
        while level < len(stripped) and stripped[level] == "#":
            level += 1
        if level <= 5 and level < len(stripped) and stripped[level] == " ":
            title = stripped[level + 1:]
            headings.append((i, level, title))
    return headings


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
                for k in range(len(sorted_links)):
                    sl = sorted_links[k].rstrip('\n')
                    sl = re.sub(r'<br\s*/?\s*>\s*$', '', sl)
                    if k < len(sorted_links) - 1:
                        sl += '<br>'
                    sorted_links[k] = sl + '\n'
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

def sort_description_blocks(lines, section_start, section_end,
                            blockquote_attach=None):
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
        if (section[i].startswith("#### ") or section[i].startswith("### ")
                or section[i].startswith("## ") or _is_h1(section[i])):
            blocks.append(section[current_block_start:i])
            current_block_start = i
            if section[i].startswith("### ") or section[i].startswith("## ") or _is_h1(section[i]):
                break

    if current_block_start < len(section) and section[current_block_start].startswith("#### "):
        end_of_last = len(section)
        for j in range(current_block_start + 1, len(section)):
            if section[j].strip() == "---":
                end_of_last = j
                break
        blocks.append(section[current_block_start:end_of_last])

    if not blocks:
        return section, stats

    if blockquote_attach:
        attach_next = {k for k, v in blockquote_attach.items()
                       if v == "next"}
        if attach_next:
            _move_blockquotes_to_next(blocks, attach_next)

    blocks = [b for b in blocks if b]
    if not blocks:
        return section, stats

    stats["entries"] = len(blocks)

    def block_name(block):
        for line in block:
            if line.startswith("#### "):
                return line[5:].strip()
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


def _move_blockquotes_to_next(blocks, attach_next_names):
    """Verschiebt Blockquote-Sidebars vom Ende eines Blocks an den Anfang des nächsten."""
    for i in range(len(blocks) - 1):
        block = blocks[i]
        bq_start = None
        for j in range(len(block) - 1, 0, -1):
            line = block[j]
            stripped = line.strip()
            if stripped == "":
                continue
            if not stripped.startswith(">"):
                break
            heading_match = re.match(r">\s*####\s+(.*)", line)
            if heading_match:
                name = heading_match.group(1).strip()
                if name in attach_next_names:
                    bq_start = j
                    break
        if bq_start is not None:
            while bq_start > 0 and block[bq_start - 1].strip() == "":
                bq_start -= 1
            bq_lines = block[bq_start:]
            blocks[i] = block[:bq_start]
            blocks[i + 1] = bq_lines + blocks[i + 1]


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
# Typ E — Bold-Entry-Blöcke
# ---------------------------------------------------------------------------

_BOLD_ENTRY_RE = re.compile(r"^\*\*[^*]+\*\*")


def _bold_name(line: str) -> str:
    m = _BOLD_ENTRY_RE.match(line.strip())
    if not m:
        return line
    name = m.group(0)[2:]
    name = name[:name.index("**")]
    return name.rstrip(":")


def sort_bold_blocks(lines, section_start, section_end):
    section = lines[section_start:section_end]
    stats = {"entries": 0, "reordered": 0}

    first_bold = -1
    for i, line in enumerate(section):
        stripped = line.strip()
        if not stripped.startswith(">") and _BOLD_ENTRY_RE.match(stripped):
            first_bold = i
            break

    if first_bold == -1:
        return section, stats

    preamble = section[:first_bold]

    blocks = []
    current_start = first_bold
    postamble_start = len(section)

    for i in range(first_bold + 1, len(section)):
        stripped = section[i].strip()
        if (stripped.startswith("#### ") or stripped.startswith("### ")
                or stripped.startswith("## ") or _is_h1(stripped)):
            blocks.append(section[current_start:i])
            postamble_start = i
            break
        if not stripped.startswith(">") and _BOLD_ENTRY_RE.match(stripped):
            blocks.append(section[current_start:i])
            current_start = i
    else:
        blocks.append(section[current_start:])
        postamble_start = len(section)

    trailing = []
    if blocks and postamble_start == len(section):
        last = blocks[-1]
        bold_match = _BOLD_ENTRY_RE.match(last[0].strip())
        after_bold = last[0].strip()[bold_match.end():].strip() if bold_match else ""
        after_bold = re.sub(r'<br\s*/?\s*>', '', after_bold).strip()
        has_inline = bool(bold_match and after_bold)
        if has_inline:
            for k in range(1, len(last)):
                if last[k].strip() != "":
                    continue
                next_line = None
                for m in range(k + 1, len(last)):
                    if last[m].strip():
                        next_line = last[m]
                        break
                if next_line and not _BOLD_ENTRY_RE.match(next_line.strip()):
                    postamble_start = 0
                    blocks[-1] = last[:k + 1]
                    trailing = list(last[k + 1:])
                    break

    if len(blocks) < 2:
        return section, stats

    stats["entries"] = len(blocks)

    total_separators = 0
    for blk in blocks:
        while len(blk) > 1 and blk[-1].strip() == "":
            blk.pop()
            total_separators += 1

    sorted_blocks = sorted(blocks, key=lambda b: sort_key_german(_bold_name(b[0])))
    if sorted_blocks != blocks:
        stats["reordered"] = sum(
            1 for a, b in zip(blocks, sorted_blocks) if a[0] != b[0]
        )

    result = list(preamble)
    separators_used = 0
    for idx, block in enumerate(sorted_blocks):
        result.extend(block)
        if idx < len(sorted_blocks) - 1 and separators_used < total_separators:
            result.append("\n")
            separators_used += 1
    for _ in range(total_separators - separators_used):
        result.append("\n")
    result.extend(trailing)
    if postamble_start > 0 and postamble_start < len(section):
        result.extend(section[postamble_start:])

    return result, stats


def sort_inline_list_section(lines, section_start, section_end, sort_column=2):
    """Sortiert kommaseparierte Einträge innerhalb von Tabellenzellen."""
    section = list(lines[section_start:section_end])
    stats = {"entries": 0, "reordered": 0, "rows": 0}

    col_idx = sort_column - 1

    is_header = set()
    for i, line in enumerate(section):
        if line.strip().startswith("|") and "---" in line:
            is_header.add(i)
            if i > 0 and section[i - 1].strip().startswith("|"):
                is_header.add(i - 1)

    for i, line in enumerate(section):
        if i in is_header:
            continue
        if not line.strip().startswith("|"):
            continue

        cells = line.split("|")
        if len(cells) < col_idx + 2:
            continue

        cell = cells[col_idx + 1].strip()
        items = [item.strip() for item in cell.split(", ")]
        if len(items) < 2:
            continue

        stats["rows"] += 1
        stats["entries"] += len(items)
        sorted_items = sorted(items, key=sort_key_german)
        if sorted_items != items:
            stats["reordered"] += 1
            cells[col_idx + 1] = " " + ", ".join(sorted_items) + " "
            section[i] = "|".join(cells)

    return section, stats


# ---------------------------------------------------------------------------
# Strukturanalyse
# ---------------------------------------------------------------------------

def _detect_spells(lines, start, end, headings):
    has_stufe = False
    has_h5 = False
    for line_num, level, title in headings:
        if not (start < line_num < end):
            continue
        if level == 4 and title.startswith("STUFE"):
            has_stufe = True
        if level == 5:
            has_h5 = True
    return has_stufe and has_h5


def _detect_link_list(lines, start, end, headings):
    sub_headings = [(h[0], h[1], h[2]) for h in headings
                    if start < h[0] < end and h[1] in (3, 4)]
    if not sub_headings:
        return None

    best_level = None
    best_links = 0
    best_cats = 0

    for check_level in (3, 4):
        level_headings = [(h[0], h[2]) for h in sub_headings if h[1] == check_level]
        if not level_headings:
            continue
        total_links = 0
        cats_with_links = 0
        for idx, (h_line, _) in enumerate(level_headings):
            h_end = level_headings[idx + 1][0] if idx + 1 < len(level_headings) else end
            link_count = sum(1 for j in range(h_line, h_end) if is_link_line(lines[j]))
            if link_count > 0:
                total_links += link_count
                cats_with_links += 1
        if total_links > best_links:
            best_level = check_level
            best_links = total_links
            best_cats = cats_with_links

    if best_links < 10 or best_cats < 2:
        return None
    return {
        "cat_level": "#" * best_level + " ",
        "links": best_links,
        "categories": best_cats,
    }


def _detect_table(lines, start, end):
    table_header_line = -1
    for i in range(start, end):
        stripped = lines[i].strip()
        if stripped.startswith("|") and "---" in stripped:
            table_header_line = i - 1
            break

    if table_header_line < 0:
        return None

    data_rows = 0
    has_sub_entries = False
    text_cells = 0
    for i in range(table_header_line + 2, end):
        stripped = lines[i].strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            data_rows += 1
            cell = stripped.split("|")[1].strip() if "|" in stripped else ""
            if cell.startswith("&nbsp;") or cell.startswith("*siehe"):
                has_sub_entries = True
            if cell and not cell.replace(".", "").replace(",", "").isdigit():
                text_cells += 1
        elif stripped == "":
            break
        else:
            break

    if data_rows < 3:
        return None
    if text_cells < data_rows // 2:
        return None

    result = {"rows": data_rows}
    if has_sub_entries:
        result["keep_sub_entries"] = True
    return result


def _detect_inline_list(lines, start, end):
    """Erkennt Tabellen mit kommaseparierten nicht-numerischen Listen in Zellen.

    Nur wenn mindestens 50% der Datenzeilen Komma-Listen enthalten, wird
    inline_list erkannt. Vereinzelte Komma-Zellen in einer großen Tabelle
    werden ignoriert (das ist normaler Tabellentext, kein Listenformat).
    """
    matching_rows = 0
    total_data_rows = 0
    best_column = -1
    header_lines = set()
    for i in range(start, end):
        stripped = lines[i].strip()
        if stripped.startswith("|") and "---" in stripped:
            header_lines.add(i)
            if i > 0 and lines[i - 1].strip().startswith("|"):
                header_lines.add(i - 1)
    for i in range(start, end):
        stripped = lines[i].strip()
        if not stripped.startswith("|") or i in header_lines:
            continue
        total_data_rows += 1
        cells = stripped.split("|")
        for col_idx, cell in enumerate(cells):
            cell = cell.strip()
            items = [item.strip() for item in cell.split(", ")]
            if len(items) >= 3:
                has_text = any(not item.replace(".", "").replace(",", "").strip().isdigit()
                              for item in items if item)
                if has_text:
                    matching_rows += 1
                    if best_column < 0:
                        best_column = col_idx
                    break
    if matching_rows >= 2 and total_data_rows > 0:
        ratio = matching_rows / total_data_rows
        if ratio >= 0.5:
            return {"rows": matching_rows, "sort_column": best_column}
    return None


def _analyze_group(lines, start, end, heading, subheading, sections, headings,
                   occurrence=None):
    h4_count = sum(1 for h in headings
                   if h[1] == 4 and start < h[0] < end
                   and not h[2].startswith("STUFE"))

    bold_count = sum(1 for i in range(start, end)
                     if not lines[i].lstrip().startswith(">")
                     and _BOLD_ENTRY_RE.match(lines[i].strip()))

    if h4_count >= 3:
        entry = {"heading": heading, "type": "desc_blocks",
                 "enabled": True, "note": f"{h4_count} H4-Blöcke"}
        if subheading:
            entry["subheading"] = subheading
        if occurrence is not None:
            entry["occurrence"] = occurrence
        sections.append(entry)

    if bold_count >= 3:
        entry = {"heading": heading, "type": "bold_blocks",
                 "enabled": True, "note": f"{bold_count} Fetteinträge"}
        if subheading:
            entry["subheading"] = subheading
        if occurrence is not None:
            entry["occurrence"] = occurrence
        sections.append(entry)

    table_info = _detect_table(lines, start, end)
    if table_info:
        is_inline = _detect_inline_list(lines, start, end)
        if is_inline:
            entry = {"heading": heading, "type": "inline_list",
                     "enabled": True, "sort_column": is_inline["sort_column"],
                     "note": f"{is_inline['rows']} Zeilen mit Komma-Listen"}
        else:
            entry = {"heading": heading, "type": "table",
                     "enabled": True,
                     "note": f"{table_info['rows']} Tabellenzeilen"}
            if table_info.get("keep_sub_entries"):
                entry["keep_sub_entries"] = True
        if subheading:
            entry["subheading"] = subheading
        if occurrence is not None:
            entry["occurrence"] = occurrence
        sections.append(entry)


def analyze_file(lines: list[str]) -> list[dict]:
    headings = build_heading_index(lines)
    sections: list[dict] = []

    h2_entries = [(h[0], h[2]) for h in headings if h[1] == 2]

    h2_title_counts: dict[str, int] = {}
    for _, title in h2_entries:
        h2_title_counts[title] = h2_title_counts.get(title, 0) + 1

    h2_title_seen: dict[str, int] = {}
    for idx, (h2_line, h2_title) in enumerate(h2_entries):
        h2_title_seen[h2_title] = h2_title_seen.get(h2_title, 0) + 1
        occurrence = h2_title_seen[h2_title]
        has_dup = h2_title_counts[h2_title] > 1

        h2_end = h2_entries[idx + 1][0] if idx + 1 < len(h2_entries) else len(lines)
        heading = f"## {h2_title}"

        def make_entry(type_, extra=None):
            e = {"heading": heading, "type": type_, "enabled": True}
            if has_dup:
                e["occurrence"] = occurrence
            if extra:
                e.update(extra)
            return e

        if _detect_spells(lines, h2_line, h2_end, headings):
            sections.append(make_entry("spells", {"note": "#### STUFE + ##### Muster"}))
            continue

        link_info = _detect_link_list(lines, h2_line, h2_end, headings)
        if link_info:
            sections.append(make_entry("link_list", {
                "cat_level": link_info["cat_level"],
                "note": f"{link_info['links']} Links in {link_info['categories']} Kategorien",
            }))
            continue

        h3_in_section = [(h[0], h[2]) for h in headings
                         if h[1] == 3 and h2_line < h[0] < h2_end]

        occ = occurrence if has_dup else None
        if h3_in_section:
            for h3_idx, (h3_line, h3_title) in enumerate(h3_in_section):
                h3_end = (h3_in_section[h3_idx + 1][0]
                          if h3_idx + 1 < len(h3_in_section) else h2_end)
                sub = f"### {h3_title}"
                _analyze_group(lines, h3_line, h3_end, heading, sub,
                               sections, headings, occurrence=occ)
        else:
            _analyze_group(lines, h2_line, h2_end, heading, None,
                           sections, headings, occurrence=occ)

    _analyze_blockquote_sections(lines, sections)
    return sections


def _analyze_blockquote_sections(lines: list[str],
                                  sections: list[dict]) -> None:
    """Erkennt sortierbare Inhalte innerhalb von Blockquotes."""
    i = 0
    while i < len(lines):
        if not _is_bq_line(lines[i]):
            i += 1
            continue

        bq_start = i
        while i < len(lines) and _is_bq_line(lines[i]):
            i += 1
        bq_end = i

        stripped = _strip_bq_lines(lines[bq_start:bq_end])

        bq_headings = []
        for j, line in enumerate(stripped):
            s = line.strip()
            if s.startswith("#"):
                lvl = 0
                while lvl < len(s) and s[lvl] == "#":
                    lvl += 1
                if lvl <= 5 and lvl < len(s) and s[lvl] == " ":
                    bq_headings.append((j, lvl, s))

        for h_idx, (h_line, h_level, h_text) in enumerate(bq_headings):
            h_end = (bq_headings[h_idx + 1][0]
                     if h_idx + 1 < len(bq_headings) else len(stripped))

            bold_count = sum(1 for k in range(h_line, h_end)
                             if _BOLD_ENTRY_RE.match(stripped[k].strip()))
            if bold_count >= 3:
                sections.append({
                    "heading": h_text,
                    "type": "bold_blocks",
                    "blockquote": True,
                    "enabled": True,
                    "note": f"{bold_count} Fetteinträge (Blockquote)",
                })

            h4_count = sum(1 for k in range(h_line + 1, h_end)
                           if stripped[k].strip().startswith("#### ")
                           and not stripped[k].strip().startswith("##### "))
            if h4_count >= 3:
                sections.append({
                    "heading": h_text,
                    "type": "desc_blocks",
                    "blockquote": True,
                    "enabled": True,
                    "note": f"{h4_count} H4-Blöcke (Blockquote)",
                })


# ---------------------------------------------------------------------------
# Config-System
# ---------------------------------------------------------------------------

def _compute_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()[:16]}"


def _config_path_for(input_path: str) -> Path:
    return CONFIG_DIR / f"{Path(input_path).stem}.json"


def _section_key(sec: dict) -> str:
    parts = [sec["heading"], sec.get("subheading", ""), sec["type"]]
    if "occurrence" in sec:
        parts.append(str(sec["occurrence"]))
    if sec.get("blockquote"):
        parts.append("bq")
    return "|".join(parts)


def _save_config(cfg_path: Path, config: dict) -> None:
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def generate_config(input_path: str, lines: list[str]) -> dict:
    return {
        "version": 1,
        "source_file": Path(input_path).name,
        "file_hash": _compute_hash(input_path),
        "sections": analyze_file(lines),
    }


def load_or_create_config(input_path: str, lines: list[str],
                          verbose: bool = False) -> dict:
    cfg_path = _config_path_for(input_path)

    if cfg_path.exists():
        config = json.loads(cfg_path.read_text(encoding="utf-8"))
        current_hash = _compute_hash(input_path)
        if config.get("file_hash") != current_hash:
            print(f"  HINWEIS: Datei hat sich seit letzter Analyse geändert.")
            print(f"  Erneute Analyse mit --analyze empfohlen.")
        return config

    print(f"  Keine Config vorhanden — erzeuge automatisch …")
    config = generate_config(input_path, lines)
    _save_config(cfg_path, config)
    enabled = [s for s in config["sections"] if s.get("enabled", True)]
    print(f"  {len(enabled)} sortierbare Abschnitte erkannt, Config gespeichert:")
    print(f"  {cfg_path}")
    return config


def analyze_and_save(input_path: str, lines: list[str]) -> dict:
    cfg_path = _config_path_for(input_path)

    new_sections = analyze_file(lines)

    if cfg_path.exists():
        old_config = json.loads(cfg_path.read_text(encoding="utf-8"))
        old_by_key = {_section_key(s): s for s in old_config.get("sections", [])}
        _PRESERVE_KEYS = {"enabled", "blockquote_attach", "sort_column"}
        for sec in new_sections:
            old = old_by_key.get(_section_key(sec))
            if old is not None:
                for key in _PRESERVE_KEYS:
                    if key in old:
                        sec[key] = old[key]

    config = {
        "version": 1,
        "source_file": Path(input_path).name,
        "file_hash": _compute_hash(input_path),
        "sections": new_sections,
    }
    _save_config(cfg_path, config)
    return config


# ---------------------------------------------------------------------------
# Hauptprogramm
# ---------------------------------------------------------------------------

def _resolve_section_range(lines: list[str], sec_cfg: dict) -> tuple[int, int]:
    heading = sec_cfg["heading"]
    occurrence = sec_cfg.get("occurrence", 1)
    subheading = sec_cfg.get("subheading")

    h_line = find_heading_line(lines, heading, occurrence)
    if h_line == -1:
        return -1, -1

    h2_end = find_next_h2(lines, h_line)
    h2_end = _adjust_for_chapter_opener(lines, h2_end)

    if subheading:
        sub_line = find_heading_line(lines, subheading, 1,
                                     start=h_line, end=h2_end)
        if sub_line == -1:
            return -1, -1
        sub_end = find_next_h3_or_above(lines, sub_line)
        adjusted = min(sub_end, h2_end)
        adjusted = _adjust_for_chapter_opener(lines, adjusted)
        return sub_line, adjusted

    return h_line, h2_end


def _resolve_blockquote_section_range(lines: list[str],
                                       sec_cfg: dict) -> tuple[int, int]:
    """Findet einen Abschnitt innerhalb eines Blockquotes."""
    heading = sec_cfg["heading"].strip()
    occurrence = sec_cfg.get("occurrence", 1)

    level = 0
    while level < len(heading) and heading[level] == "#":
        level += 1

    count = 0
    start = -1
    for i, line in enumerate(lines):
        if not _is_bq_line(line):
            continue
        content = _BQ_PREFIX_RE.sub("", line.lstrip(), count=1).strip()
        if content == heading:
            count += 1
            if count == occurrence:
                start = i
                break

    if start == -1:
        return -1, -1

    for j in range(start + 1, len(lines)):
        stripped = lines[j].lstrip()
        if not stripped.startswith(">"):
            return start, j
        content = _BQ_PREFIX_RE.sub("", stripped, count=1).strip()
        if content.startswith("#"):
            j_level = 0
            while j_level < len(content) and content[j_level] == "#":
                j_level += 1
            if j_level <= level and j_level < len(content) and content[j_level] == " ":
                return start, j

    return start, len(lines)


def process(input_path: str, output_dir: str, verbose: bool = False) -> None:
    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for i in range(len(lines)):
        if not lines[i].endswith("\n"):
            lines[i] += "\n"

    original_count = len(lines)

    config = load_or_create_config(input_path, lines, verbose)
    enabled_sections = [s for s in config.get("sections", [])
                        if s.get("enabled", True)]

    if not enabled_sections:
        print(f"  Keine aktivierten Abschnitte — Datei wird unverändert kopiert.")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, os.path.basename(input_path))
        with open(output_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return

    sections_to_process = []
    for sec_cfg in enabled_sections:
        if sec_cfg.get("blockquote"):
            start, end = _resolve_blockquote_section_range(lines, sec_cfg)
        else:
            start, end = _resolve_section_range(lines, sec_cfg)
        if start == -1:
            name = sec_cfg["heading"]
            if "subheading" in sec_cfg:
                name += f" > {sec_cfg['subheading']}"
            print(f"  WARNUNG: Abschnitt nicht gefunden: {name}")
            continue
        sections_to_process.append((sec_cfg, start, end))

    sections_to_process.sort(key=lambda s: s[1], reverse=True)

    output = list(lines)
    report = []

    for sec_cfg, start, end in sections_to_process:
        stype = sec_cfg["type"]
        name = sec_cfg["heading"]
        if "subheading" in sec_cfg:
            name += f" > {sec_cfg['subheading']}"

        is_bq = sec_cfg.get("blockquote", False)
        if is_bq:
            bq_prefix = _detect_bq_prefix(output[start:end])
            sort_input = _strip_bq_lines(output[start:end])
            sort_start, sort_end = 0, len(sort_input)
        else:
            sort_input = output
            sort_start, sort_end = start, end

        new_lines = None
        stats = None

        if stype == "link_list":
            cat_level = sec_cfg.get("cat_level", "### ")
            new_lines, stats = sort_link_list_section(
                sort_input, sort_start, sort_end, cat_level)
            report.append(
                f"  {name}: {stats['entries']} Einträge in {stats['categories']} "
                f"Kategorien, {stats['reordered']} umsortiert"
            )
        elif stype == "desc_blocks":
            bq_attach = sec_cfg.get("blockquote_attach")
            new_lines, stats = sort_description_blocks(
                sort_input, sort_start, sort_end,
                blockquote_attach=bq_attach)
            report.append(
                f"  {name}: {stats['entries']} Einträge, "
                f"{stats['reordered']} umsortiert"
            )
        elif stype == "spells":
            new_lines, stats = sort_spell_section(
                sort_input, sort_start, sort_end)
            report.append(
                f"  {name}: {stats['spells']} Zauber in {stats['levels']} Stufen, "
                f"{stats['reordered']} umsortiert"
            )
        elif stype == "table":
            keep_sub = sec_cfg.get("keep_sub_entries", False)
            new_lines, stats = sort_index_table(
                sort_input, sort_start, sort_end, keep_sub)
            report.append(
                f"  {name}: {stats['entries']} Einträge, "
                f"{stats['reordered']} umsortiert"
            )
        elif stype == "bold_blocks":
            new_lines, stats = sort_bold_blocks(
                sort_input, sort_start, sort_end)
            report.append(
                f"  {name}: {stats['entries']} Einträge, "
                f"{stats['reordered']} umsortiert"
            )
        elif stype == "inline_list":
            sort_col = sec_cfg.get("sort_column", 2)
            new_lines, stats = sort_inline_list_section(
                sort_input, sort_start, sort_end, sort_col)
            report.append(
                f"  {name}: {stats['rows']} Zeilen, {stats['entries']} Einträge, "
                f"{stats['reordered']} umsortiert"
            )

        if new_lines is not None:
            if is_bq:
                output[start:end] = _restore_bq_lines(new_lines, bq_prefix)
            else:
                output[start:end] = new_lines

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
        print("  ✓ identisch")
    print()
    print("Verarbeitete Abschnitte:")
    for line in sorted(report):
        print(line)
    print("=" * 60)


def print_analysis(config: dict) -> None:
    sections = config.get("sections", [])
    if not sections:
        print("  Keine sortierbaren Abschnitte erkannt.")
        return

    print(f"  {len(sections)} Abschnitte erkannt:\n")
    for sec in sections:
        status = "✓" if sec.get("enabled", True) else "✗"
        name = sec["heading"]
        if "subheading" in sec:
            name += f" > {sec['subheading']}"
        if sec.get("blockquote"):
            name += " [Blockquote]"
        note = sec.get("note", "")
        print(f"  {status} [{sec['type']}] {name}")
        if note:
            print(f"    {note}")


def print_preview(config: dict, lines: list[str]) -> None:
    """Gibt eine Inhaltsvorschau jedes erkannten Abschnitts aus."""
    sections = config.get("sections", [])
    if not sections:
        print("  Keine sortierbaren Abschnitte erkannt.")
        return

    for idx, sec in enumerate(sections):
        if sec.get("blockquote"):
            start, end = _resolve_blockquote_section_range(lines, sec)
        else:
            start, end = _resolve_section_range(lines, sec)
        if start == -1:
            continue

        name = sec["heading"]
        if "subheading" in sec:
            name += f" > {sec['subheading']}"
        if sec.get("blockquote"):
            name += " [Blockquote]"

        status = "✓" if sec.get("enabled", True) else "✗"
        print(f"--- [{idx}] {status} [{sec['type']}] {name} ---")
        print(f"    Zeilen {start + 1}–{end} | {sec.get('note', '')}")

        count = 0
        for i in range(start, min(end, start + 30)):
            line = lines[i].rstrip("\n")
            if line.strip():
                print(f"    {line}")
                count += 1
                if count >= 8:
                    break

        remaining = end - start
        if remaining > 30:
            print(f"    … ({remaining} Zeilen insgesamt)")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Sortiert Abschnitte deutscher Ars-Magica-Regelwerke."
    )
    parser.add_argument(
        "--input", "-i", required=True,
        help="Pfad zur Eingabedatei",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="german-ordered",
        help="Ausgabeverzeichnis (Standard: german-ordered)",
    )
    parser.add_argument(
        "--analyze", action="store_true",
        help="Nur analysieren, Config erzeugen/aktualisieren",
    )
    parser.add_argument(
        "--preview", action="store_true",
        help="Vorschau der erkannten Abschnitte mit Inhalt",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Detaillierte Ausgabe",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Fehler: Eingabedatei nicht gefunden: {args.input}", file=sys.stderr)
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for i in range(len(lines)):
        if not lines[i].endswith("\n"):
            lines[i] += "\n"

    if args.analyze:
        config = analyze_and_save(args.input, lines)
        cfg_path = _config_path_for(args.input)

        print("=" * 60)
        print("ANALYSE")
        print("=" * 60)
        print(f"  Datei:   {args.input}")
        print(f"  Config:  {cfg_path}")
        print()
        print_analysis(config)
        print("=" * 60)
    elif args.preview:
        cfg_path = _config_path_for(args.input)
        if not cfg_path.exists():
            print("Fehler: Keine Config vorhanden. Zuerst --analyze ausführen.",
                  file=sys.stderr)
            sys.exit(1)
        config = json.loads(cfg_path.read_text(encoding="utf-8"))

        print("=" * 60)
        print("VORSCHAU")
        print("=" * 60)
        print(f"  Datei:   {args.input}")
        print(f"  Config:  {cfg_path}")
        print()
        print_preview(config, lines)
        print("=" * 60)
    else:
        process(args.input, args.output_dir, args.verbose)


if __name__ == "__main__":
    main()
