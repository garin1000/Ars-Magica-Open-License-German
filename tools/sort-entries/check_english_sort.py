#!/usr/bin/env python3
"""Prüft für jeden aktivierten Sortier-Block in einer Config,
ob der entsprechende Abschnitt im englischen Original sortiert ist.

Nutzt die Zeilensynchronität zwischen deutscher und englischer Datei:
Abschnittsgrenzen werden in der deutschen Datei bestimmt und dann
an denselben Zeilenpositionen im englischen Original ausgelesen.

Ausgabe: JSON-Ergebnis nach stdout, lesbarer Bericht nach stderr.
"""

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_DIR = SCRIPT_DIR / "configs"
PROJECT_ROOT = SCRIPT_DIR.parent.parent

BOLD_RE = re.compile(r"^\*\*[^*]+\*\*")
BQ_PREFIX_RE = re.compile(r"^>\s?")


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def strip_bq(line):
    if line.rstrip().rstrip() == ">":
        return "\n"
    return BQ_PREFIX_RE.sub("", line, count=1)


def is_bq(line):
    return line.lstrip().startswith(">")


def bold_name(line):
    m = BOLD_RE.match(line.strip())
    if not m:
        return line.strip()
    name = m.group(0)[2:]
    name = name[:name.index("**")]
    return name.rstrip(":").strip()


def sort_key_en(text):
    t = re.sub(r"\(.*?\)", "", text)
    t = re.sub(r"[^A-Za-z0-9 ]", "", t)
    t = t.strip()
    t = re.sub(r"^(The|A|An)\s+", "", t, flags=re.IGNORECASE)
    return t.casefold()


def find_heading(lines, heading_text, occurrence=1, start=0, end=None):
    if end is None:
        end = len(lines)
    count = 0
    for i in range(start, end):
        if lines[i].strip() == heading_text:
            count += 1
            if count == occurrence:
                return i
    return -1


def find_next_h2(lines, start):
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("## ") or (
            lines[i].startswith("# ") and not lines[i].startswith("## ")
        ):
            return i
    return len(lines)


def find_next_h3_or_above(lines, start):
    for i in range(start + 1, len(lines)):
        s = lines[i]
        if (
            (s.startswith("# ") and not s.startswith("## "))
            or s.startswith("## ")
            or s.startswith("### ")
        ):
            return i
    return len(lines)


# ---------------------------------------------------------------------------
# Abschnittsauflösung (aus der deutschen Datei)
# ---------------------------------------------------------------------------

def resolve_range_de(de_lines, sec):
    heading = sec["heading"]
    occurrence = sec.get("occurrence", 1)
    subheading = sec.get("subheading")

    h_line = find_heading(de_lines, heading, occurrence)
    if h_line == -1:
        return -1, -1

    h2_end = find_next_h2(de_lines, h_line)

    if subheading:
        sub_line = find_heading(de_lines, subheading, 1, start=h_line, end=h2_end)
        if sub_line == -1:
            return -1, -1
        sub_end = find_next_h3_or_above(de_lines, sub_line)
        return sub_line, min(sub_end, h2_end)

    return h_line, h2_end


def resolve_bq_range_de(de_lines, sec):
    heading = sec["heading"].strip()
    occurrence = sec.get("occurrence", 1)

    level = 0
    while level < len(heading) and heading[level] == "#":
        level += 1

    count = 0
    start = -1
    for i, line in enumerate(de_lines):
        if not is_bq(line):
            continue
        content = BQ_PREFIX_RE.sub("", line.lstrip(), count=1).strip()
        if content == heading:
            count += 1
            if count == occurrence:
                start = i
                break

    if start == -1:
        return -1, -1

    for j in range(start + 1, len(de_lines)):
        stripped = de_lines[j].lstrip()
        if not stripped.startswith(">"):
            return start, j
        content = BQ_PREFIX_RE.sub("", stripped, count=1).strip()
        if content.startswith("#"):
            j_level = 0
            while j_level < len(content) and content[j_level] == "#":
                j_level += 1
            if j_level <= level and j_level < len(content) and content[j_level] == " ":
                return start, j

    return start, len(de_lines)


# ---------------------------------------------------------------------------
# Einträge extrahieren (aus dem englischen Original)
# ---------------------------------------------------------------------------

def extract_bold_names(lines):
    names = []
    for line in lines:
        s = line.strip()
        if BOLD_RE.match(s):
            names.append(bold_name(line))
    return names


def extract_h4_names(lines):
    names = []
    for line in lines:
        s = line.strip()
        if s.startswith("#### ") and not s.startswith("##### "):
            names.append(s[5:].strip())
    return names


def extract_h5_names(lines):
    names = []
    for line in lines:
        s = line.strip()
        if s.startswith("##### "):
            names.append(s[6:].strip())
    return names


def extract_table_keys(lines):
    keys = []
    in_table = False
    past_separator = False
    for line in lines:
        s = line.strip()
        if s.startswith("|") and "---" in s:
            in_table = True
            past_separator = True
            continue
        if in_table and past_separator and s.startswith("|") and s.endswith("|"):
            cell = s.split("|")[1].strip() if "|" in s else ""
            if cell.startswith("&nbsp;") or cell.startswith("*see"):
                continue
            keys.append(cell)
        elif in_table and past_separator and not s.startswith("|"):
            break
    return keys


def extract_link_names(lines):
    names = []
    for line in lines:
        s = line.strip()
        m = re.match(r"\[(.+?)\]", s)
        if m and "](" in s:
            names.append(m.group(1))
    return names


def extract_inline_list_items(lines, sort_column=2):
    col_idx = sort_column - 1
    all_items = []
    header_lines = set()
    for i, line in enumerate(lines):
        if line.strip().startswith("|") and "---" in line:
            header_lines.add(i)
            if i > 0 and lines[i - 1].strip().startswith("|"):
                header_lines.add(i - 1)
    for i, line in enumerate(lines):
        if i in header_lines or not line.strip().startswith("|"):
            continue
        cells = line.split("|")
        if len(cells) < col_idx + 2:
            continue
        cell = cells[col_idx + 1].strip()
        items = [item.strip() for item in cell.split(", ")]
        if len(items) >= 2:
            all_items.extend(items)
    return all_items


# ---------------------------------------------------------------------------
# Sortierprüfung
# ---------------------------------------------------------------------------

def is_sorted(names, key_fn=sort_key_en):
    if len(names) < 2:
        return True
    keys = [key_fn(n) for n in names]
    return all(keys[i] <= keys[i + 1] for i in range(len(keys) - 1))


def count_inversions(names, key_fn=sort_key_en):
    keys = [key_fn(n) for n in names]
    inv = 0
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            if keys[i] > keys[j]:
                inv += 1
    return inv


# ---------------------------------------------------------------------------
# Englische Originaldatei finden
# ---------------------------------------------------------------------------

# Bekannte Zuordnungen deutsch → englisch
_KNOWN_MAP = {
    "Ars Magica 5e - Häuser des Hermes - Mysterienkulte":
        "Ars Magica 5e - Houses of Hermes - Mystery Cults",
    "Ars Magica 5e - Häuser des Hermes - Societates":
        "Ars Magica 5e - Houses of Hermes - Societates",
    "Ars Magica 5e - Häuser des Hermes - Wahre Linien":
        "Ars Magica 5e - Houses of Hermes - True Lineages",
    "Ars Magica 5e - Magie - Heckenzauber (Überarbeitet)":
        "Ars Magica 5e - Magic - Hedge Magic (Revised)",
    "Ars Magica 5e - Sphären der Macht - Magie":
        "Ars Magica 5e - Realms of Power - Magic",
    "Ars Magica 5e - Wächter des Waldes - Das Rhein-Tribunal":
        "Ars Magica 5e - Guardians of the Forests - The Rhine Tribunal",
    "Ars Magica Definitive Edition Basisregeln":
        "Ars Magica - Definitive Edition (Core Rules)",
    "Ars Magica 5e - Sphären der Macht - Infernal":
        "Ars Magica 5e - Realms of Power - The Infernal",
    "Ars Magica 5e - Sphären der Macht - Das Infernale":
        "Ars Magica 5e - Realms of Power - The Infernal",
}


def find_english_original(de_stem):
    en_dir = PROJECT_ROOT / "original-english" / "reviewed"
    en_stem = _KNOWN_MAP.get(de_stem)
    if en_stem:
        path = en_dir / f"{en_stem}.md"
        if path.exists():
            return path

    for f in en_dir.glob("*.md"):
        if f.stem.casefold() == de_stem.casefold():
            return f

    return None


# ---------------------------------------------------------------------------
# Hauptprogramm
# ---------------------------------------------------------------------------

def check_file(de_path, en_path, config_path):
    config = json.loads(config_path.read_text(encoding="utf-8"))

    de_lines = de_path.read_text(encoding="utf-8").splitlines(keepends=True)
    en_lines = en_path.read_text(encoding="utf-8").splitlines(keepends=True)

    for i in range(len(de_lines)):
        if not de_lines[i].endswith("\n"):
            de_lines[i] += "\n"
    for i in range(len(en_lines)):
        if not en_lines[i].endswith("\n"):
            en_lines[i] += "\n"

    if len(de_lines) != len(en_lines):
        print(
            f"WARNUNG: Zeilenzahl unterschiedlich "
            f"(DE={len(de_lines)}, EN={len(en_lines)})",
            file=sys.stderr,
        )

    enabled = [s for s in config["sections"] if s.get("enabled")]

    results = []

    for sec in enabled:
        stype = sec["type"]
        is_bq_sec = sec.get("blockquote", False)

        if is_bq_sec:
            start, end = resolve_bq_range_de(de_lines, sec)
        else:
            start, end = resolve_range_de(de_lines, sec)

        name = sec["heading"]
        if "subheading" in sec:
            name += f" > {sec['subheading']}"
        if is_bq_sec:
            name += " [BQ]"

        if start == -1:
            results.append({
                "name": name, "type": stype,
                "status": "NOT_FOUND", "entries": [],
            })
            continue

        en_section = en_lines[start:end]
        if is_bq_sec:
            en_section = [strip_bq(l) for l in en_section]

        en_heading = en_lines[start].strip() if start < len(en_lines) else "?"

        if stype == "bold_blocks":
            names = extract_bold_names(en_section)
        elif stype == "desc_blocks":
            names = extract_h4_names(en_section)
        elif stype == "table":
            names = extract_table_keys(en_section)
        elif stype == "link_list":
            names = extract_link_names(en_section)
        elif stype == "spells":
            names = extract_h5_names(en_section)
        elif stype == "inline_list":
            sort_col = sec.get("sort_column", 2)
            names = extract_inline_list_items(en_section, sort_col)
        else:
            results.append({
                "name": name, "type": stype,
                "status": "SKIP_TYPE", "entries": [],
            })
            continue

        sorted_en = is_sorted(names)
        inversions = count_inversions(names)

        results.append({
            "name": name,
            "type": stype,
            "en_heading": en_heading,
            "entries": names,
            "count": len(names),
            "sorted": sorted_en,
            "inversions": inversions,
            "lines": f"{start + 1}-{end}",
        })

    return results


def print_report(results, file=sys.stderr):
    not_sorted = []
    sorted_blocks = []

    print("=" * 70, file=file)
    print("PRÜFBERICHT: Sortierung im englischen Original", file=file)
    print("=" * 70, file=file)
    print(file=file)

    for r in results:
        if r.get("status") in ("NOT_FOUND", "SKIP_TYPE"):
            print(f"  [{r['status']}] {r['name']} ({r['type']})", file=file)
            continue

        marker = "SORTED" if r["sorted"] else "NOT SORTED"
        print(
            f"  [{marker}] {r['name']} "
            f"({r['type']}, {r['count']} Einträge, Z.{r['lines']})",
            file=file,
        )
        print(f"           EN: {r['en_heading']}", file=file)
        if r["entries"]:
            for e in r["entries"]:
                print(f"             - {e}", file=file)
        if not r["sorted"]:
            print(f"           Inversionen: {r['inversions']}", file=file)
            not_sorted.append(r)
        else:
            sorted_blocks.append(r)
        print(file=file)

    print("=" * 70, file=file)
    print(
        f"ZUSAMMENFASSUNG: {len(sorted_blocks)} sortiert, "
        f"{len(not_sorted)} NICHT sortiert",
        file=file,
    )
    print("=" * 70, file=file)

    if not_sorted:
        print("\nNICHT SORTIERT (-> deaktivieren):", file=file)
        for r in not_sorted:
            print(
                f"  - {r['name']} ({r['count']} Einträge, "
                f"{r['inversions']} Inversionen)",
                file=file,
            )

    if sorted_blocks:
        print("\nSORTIERT (-> Zufallsprüfung nötig):", file=file)
        for r in sorted_blocks:
            print(f"  - {r['name']} ({r['count']} Einträge)", file=file)


def main():
    parser = argparse.ArgumentParser(
        description="Prüft aktivierte Sortier-Blöcke gegen das englische Original."
    )
    parser.add_argument(
        "--input", "-i", required=True,
        help="Pfad zur deutschen Eingabedatei (german-reviewed/)",
    )
    parser.add_argument(
        "--english", "-e",
        help="Pfad zum englischen Original (optional, wird automatisch gesucht)",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="JSON-Ergebnis nach stdout ausgeben",
    )
    args = parser.parse_args()

    de_path = Path(args.input).resolve()
    if not de_path.exists():
        print(f"Fehler: {de_path} existiert nicht.", file=sys.stderr)
        sys.exit(1)

    config_path = CONFIG_DIR / f"{de_path.stem}.json"
    if not config_path.exists():
        print(
            f"Fehler: Keine Config gefunden: {config_path}\n"
            f"Erzeuge zuerst eine Config mit: sort_entries.py --analyze -i ...",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.english:
        en_path = Path(args.english).resolve()
    else:
        en_path = find_english_original(de_path.stem)

    if en_path is None or not en_path.exists():
        print(
            f"Fehler: Englisches Original nicht gefunden für '{de_path.stem}'.\n"
            f"Verwende --english, um den Pfad manuell anzugeben.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"  DE: {de_path}", file=sys.stderr)
    print(f"  EN: {en_path}", file=sys.stderr)
    print(f"  Config: {config_path}", file=sys.stderr)
    print(file=sys.stderr)

    results = check_file(de_path, en_path, config_path)
    print_report(results)

    if args.json:
        json_results = [
            r for r in results
            if r.get("status") not in ("NOT_FOUND", "SKIP_TYPE")
        ]
        print(json.dumps(json_results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
