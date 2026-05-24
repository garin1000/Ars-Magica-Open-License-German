#!/usr/bin/env python3
"""Generate line-reference files for all german-wip files.

For each german-wip file, extract all game terms from the translation tables
and record every line number where each term appears.
"""

import re
from pathlib import Path
from datetime import date

BASE = Path("/home/norbert/Rolle/arm-de-translation")
TABLES_DIR = BASE / "translation-tables"
WIP_DIR = BASE / "german-wip"
OUT_DIR = BASE / "line-references"

TABLE_FILES = [
    "grundbegriffe.md",
    "magie-regeln.md",
    "kampf.md",
    "alterung-twilight.md",
    "sphären-mächte.md",
    "tugenden-fehler.md",
    "fertigkeiten.md",
    "orden-tribunale.md",
    "konvent.md",
    "konvent-boons-hooks.md",
    "labor-fortschritt.md",
    "reputationen.md",
    "persoenlichkeitseigenschaften.md",
    "tiere-kreaturen.md",
    "magische-qualitaeten.md",
    "zauber-nach-form.md",
]

TABLE_DISPLAY_NAMES = {
    "grundbegriffe.md": "Allgemeine Spielbegriffe",
    "magie-regeln.md": "Magieregeln (Techniken, Formen, R/D/Z)",
    "kampf.md": "Kampf",
    "alterung-twilight.md": "Alterung und Zwielicht",
    "sphären-mächte.md": "Sphären und Mächte",
    "tugenden-fehler.md": "Tugenden und Fehler",
    "fertigkeiten.md": "Fertigkeiten",
    "orden-tribunale.md": "Orden, Häuser und Tribunale",
    "konvent.md": "Konvent",
    "konvent-boons-hooks.md": "Konventsvorzüge und -haken",
    "labor-fortschritt.md": "Labor und Fortschritt",
    "reputationen.md": "Reputationen",
    "persoenlichkeitseigenschaften.md": "Persönlichkeitseigenschaften",
    "tiere-kreaturen.md": "Tiere und Kreaturen",
    "magische-qualitaeten.md": "Magische Qualitäten und Mängel",
    "zauber-nach-form.md": "Zaubersprüche nach Form",
}

WIP_FILES = [
    "Ars Magica Definitive Edition Basisregeln Deutsch.md",
    "Ars Magica 5e - Sphären der Macht - Magie.md",
    "Ars Magica 5e - Wächter des Waldes - Das Rhein-Tribunal.md",
    "Ars Magica 5e - Magie - Heckenzauber (Überarbeitet) Deutsch.md",
]

SHORT_NAMES = {
    "Ars Magica Definitive Edition Basisregeln Deutsch.md": "Basisregeln",
    "Ars Magica 5e - Sphären der Macht - Magie.md": "SdM-Magie",
    "Ars Magica 5e - Wächter des Waldes - Das Rhein-Tribunal.md": "WdW-Rhein",
    "Ars Magica 5e - Magie - Heckenzauber (Überarbeitet) Deutsch.md": "Heckenzauber",
}

EXCLUDE_TERMS = {
    "–", "—", "", "n/v", "ja", "nein", "oder", "und", "der", "die", "das",
    "ein", "eine", "m.", "f.", "n.", "Sg.", "Pl.", "Typ", "Art", "Wert",
    "Name", "Rang", "Form", "Grad", "Ort", "Zahl", "Ruf",
}

MIN_TERM_LENGTH = 3


def clean_term(raw: str) -> list[str]:
    """Clean a raw cell value and return a list of usable terms."""
    raw = raw.strip()
    raw = raw.replace("**", "").replace("`", "")
    # Remove strikethrough content
    raw = re.sub(r"~~[^~]+~~", "", raw)
    # Remove (Lat.) annotations
    raw = re.sub(r"\s*\(Lat\.\)", "", raw)
    # Remove italic markers
    raw = raw.replace("*", "")

    # Split on " / " (with spaces) for genuine alternatives
    # but NOT on "/" inside parentheses or compound terms
    if " / " in raw and "(" not in raw:
        parts = [p.strip() for p in raw.split(" / ")]
    else:
        parts = [raw.strip()]

    terms = []
    for part in parts:
        # Remove gender/number annotations in parentheses at end
        part = re.sub(r"\s*\((?:Pl\.|Sg\.|m\.|f\.|n\.|=[^)]*|lat\.[^)]*)\)\s*$", "", part)
        part = part.strip(" ;,.")

        # Skip if too short, in exclude list, or starts with "("
        if len(part) < MIN_TERM_LENGTH:
            continue
        if part in EXCLUDE_TERMS:
            continue
        if part.startswith("(") and not part.endswith(")"):
            continue
        # Skip entries that are just numbers or dashes
        if re.match(r"^[\d\-−–+×\s]+$", part):
            continue

        terms.append(part)
    return terms


def find_de_column(header_cells: list[str]) -> int | None:
    """Find the column index that contains German translations."""
    for i, cell in enumerate(header_cells):
        cell_clean = cell.strip().lower()
        if "deutsch" in cell_clean or cell_clean == "de":
            return i
    return None


def find_en_column(header_cells: list[str]) -> int | None:
    """Find the column index that contains English terms."""
    for i, cell in enumerate(header_cells):
        cell_clean = cell.strip().lower()
        if "englisch" in cell_clean or cell_clean == "en":
            return i
    return None


def parse_table_cells(line: str) -> list[str]:
    """Parse a markdown table line into cells."""
    cells = [c.strip() for c in line.split("|")]
    if cells and cells[0] == "":
        cells = cells[1:]
    if cells and cells[-1] == "":
        cells = cells[:-1]
    return cells


def is_separator(cells: list[str]) -> bool:
    """Check if this is a table separator row (---|---|---)."""
    return all(re.match(r"^:?-+:?$", c.strip()) for c in cells if c.strip())


def parse_table_file(path: Path) -> list[tuple[str, str]]:
    """Parse a translation table file and return (en_term, de_term) pairs."""
    text = path.read_text(encoding="utf-8")
    lines_list = text.split("\n")

    results: list[tuple[str, str]] = []

    de_col: int | None = None
    en_col: int | None = None
    header_found = False
    after_separator = False

    for line in lines_list:
        # Skip non-table lines
        stripped = line.strip()
        if not stripped.startswith("|"):
            header_found = False
            after_separator = False
            de_col = None
            en_col = None
            continue

        cells = parse_table_cells(stripped)
        if not cells:
            continue

        # Separator row
        if is_separator(cells):
            after_separator = True
            continue

        # Before separator = header row
        if not after_separator:
            de_col = find_de_column(cells)
            en_col = find_en_column(cells)
            if de_col is not None:
                header_found = True
            continue

        # Data row (after separator, with known columns)
        if header_found and de_col is not None and de_col < len(cells):
            de_raw = cells[de_col]
            en_raw = cells[en_col] if en_col is not None and en_col < len(cells) else ""

            de_terms = clean_term(de_raw)
            en_clean = clean_term(en_raw)
            en_label = en_clean[0] if en_clean else en_raw.strip().replace("**", "").replace("*", "")

            for dt in de_terms:
                results.append((en_label, dt))

    return results


def find_lines(text_lines: list[str], term: str) -> list[int]:
    """Find all 1-based line numbers where term appears."""
    return [i + 1 for i, line in enumerate(text_lines) if term in line]


def format_line_list(lines: list[int], max_display: int = 30) -> str:
    """Format line numbers as compact string."""
    if not lines:
        return "—"
    if len(lines) <= max_display:
        return ", ".join(str(n) for n in lines)
    shown = ", ".join(str(n) for n in lines[:max_display])
    return f"{shown}, ... (+{len(lines) - max_display} weitere)"


def generate_reference(
    wip_path: Path,
    terms_by_table: dict[str, list[tuple[str, str]]],
) -> str:
    """Generate the reference content for one WIP file."""
    text = wip_path.read_text(encoding="utf-8")
    text_lines = text.split("\n")
    short_name = SHORT_NAMES.get(wip_path.name, wip_path.stem)

    # Collect all terms across tables, deduplicating by DE term.
    # Track which tables define each term.
    term_info: dict[str, tuple[str, list[str]]] = {}  # de -> (en, [table_files])

    for table_file in TABLE_FILES:
        if table_file not in terms_by_table:
            continue
        for en_label, de_term in terms_by_table[table_file]:
            if de_term not in term_info:
                term_info[de_term] = (en_label, [table_file])
            else:
                if table_file not in term_info[de_term][1]:
                    term_info[de_term][1].append(table_file)

    # Find line numbers for each term
    matched: list[tuple[str, str, list[str], list[int]]] = []
    total_refs = 0

    for de_term, (en_label, sources) in term_info.items():
        line_nums = find_lines(text_lines, de_term)
        if line_nums:
            matched.append((de_term, en_label, sources, line_nums))
            total_refs += len(line_nums)

    # Group by primary table source
    by_table: dict[str, list[tuple[str, str, list[str], list[int]]]] = {}
    for de_term, en_label, sources, line_nums in matched:
        primary = sources[0]
        if primary not in by_table:
            by_table[primary] = []
        by_table[primary].append((de_term, en_label, sources, line_nums))

    # Sort within each group
    for entries in by_table.values():
        entries.sort(key=lambda x: x[0].lower())

    # Build output
    out: list[str] = []
    out.append(f"# Begriffsreferenz: {short_name}")
    out.append("")
    out.append(f"**Quelldatei:** `german-wip/{wip_path.name}`  ")
    out.append(f"**Generiert am:** {date.today().isoformat()}  ")
    out.append(f"**Gesamtzeilen:** {len(text_lines)}")
    out.append("")
    out.append(f"**Erfasste Begriffe:** {len(matched)} (mit Vorkommen in dieser Datei)  ")
    out.append(f"**Referenzierte Zeilen insgesamt:** {total_refs}")
    out.append("")
    out.append("---")
    out.append("")

    for table_file in TABLE_FILES:
        if table_file not in by_table:
            continue

        entries = by_table[table_file]
        display_name = TABLE_DISPLAY_NAMES.get(table_file, table_file)
        out.append(f"## {display_name}")
        out.append(f"*Quelle: [{table_file}](../translation-tables/{table_file})*")
        out.append("")
        out.append("| DE-Begriff | EN | Anz. | Zeilen |")
        out.append("|---|---|---|---|")

        for de_term, en_label, sources, line_nums in entries:
            de_esc = de_term.replace("|", "\\|")
            en_esc = en_label.replace("|", "\\|")
            extra = ""
            if len(sources) > 1:
                others = [s for s in sources[1:]]
                extra = f" *(auch: {', '.join(others)})*"
            out.append(
                f"| {de_esc} | {en_esc} | {len(line_nums)} "
                f"| {format_line_list(line_nums)}{extra} |"
            )

        out.append("")

    return "\n".join(out)


def main():
    OUT_DIR.mkdir(exist_ok=True)

    # Step 1: Parse all translation tables
    print("Übersetzungstabellen einlesen...")
    terms_by_table: dict[str, list[tuple[str, str]]] = {}
    total_unique: set[str] = set()

    for tf in TABLE_FILES:
        path = TABLES_DIR / tf
        if not path.exists():
            print(f"  WARNUNG: {tf} nicht gefunden, überspringe.")
            continue
        entries = parse_table_file(path)
        terms_by_table[tf] = entries
        for _, de in entries:
            total_unique.add(de)
        print(f"  {tf}: {len(entries)} Begriffe extrahiert")

    print(f"\nGesamt: {len(total_unique)} eindeutige DE-Begriffe")
    print()

    # Step 2: Generate reference for each WIP file
    for wf in WIP_FILES:
        wip_path = WIP_DIR / wf
        if not wip_path.exists():
            print(f"WARNUNG: {wf} nicht gefunden, überspringe.")
            continue

        short = SHORT_NAMES.get(wf, Path(wf).stem)
        print(f"Verarbeite {short}...", end=" ", flush=True)

        content = generate_reference(wip_path, terms_by_table)

        out_name = f"begriffe-{short.lower()}.md"
        out_path = OUT_DIR / out_name
        out_path.write_text(content, encoding="utf-8")

        # Extract stats from content
        term_count = content.count("\n| ") - content.count("\n| DE-Begriff")
        print(f"→ {out_path.name} ({term_count} Begriffe mit Treffern)")

    print("\nFertig.")


if __name__ == "__main__":
    main()
