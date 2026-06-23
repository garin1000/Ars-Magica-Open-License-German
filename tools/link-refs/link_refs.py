#!/usr/bin/env python3
"""Findet und verlinkt Seitenverweise in deutschen Ars-Magica-Regelwerken.

Modi:
  --analyze        Findet unverlinkte Verweise, listet Kandidaten (JSON-Report)
  --link-toc       Verlinkt TOC-Einträge mit passenden Headern (vollautomatisch)
  --apply          Fügt Links aus resolved.json ein
  --fix-crosslinks Korrigiert bestehende Cross-File-Links (englisch → deutsch)

Pro-Datei-Configs werden unter tools/link-refs/configs/ gespeichert.
Die globale Buchtitel-Zuordnung liegt in tools/link-refs/book_aliases.json.
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
ALIASES_PATH = SCRIPT_DIR / "book_aliases.json"


# ---------------------------------------------------------------------------
# Pandoc-kompatible Anker-ID-Generierung
# ---------------------------------------------------------------------------

def pandoc_anchor_id(heading_text: str, seen: dict[str, int] | None = None) -> str:
    """Erzeugt eine Pandoc-kompatible Anker-ID aus Überschriftstext.

    Regeln (Pandoc default):
    - Zu Kleinbuchstaben
    - Leerzeichen → Bindestriche
    - Umlaute bleiben erhalten (ä, ö, ü, ß)
    - Alphanumerische Zeichen, Bindestriche, Unterstriche, Punkte bleiben
    - Alles andere (Klammern, Doppelpunkte, Anführungszeichen, etc.) wird entfernt
    - Führende Ziffern werden entfernt
    - Bei Duplikaten: -1, -2, etc.
    """
    text = heading_text.lower()
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'[^\w\-.]', '', text, flags=re.UNICODE)
    text = re.sub(r'^[\d.-]+', '', text)
    text = re.sub(r'-{2,}', '-', text)
    text = text.strip('-')
    if not text:
        text = 'section'

    if seen is not None:
        if text in seen:
            seen[text] += 1
            text = f"{text}-{seen[text]}"
        else:
            seen[text] = 0

    return text


# ---------------------------------------------------------------------------
# Header-Index
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(r'^(#{1,6})\s+(.+)$')
_BQ_HEADING_RE = re.compile(r'^(?:>\s*)+(#{1,6})\s+(.+)$')


def build_header_index(lines: list[str], include_blockquotes: bool = True) -> list[dict]:
    """Extrahiert alle Markdown-Header und ihre Pandoc-Anker-IDs."""
    seen: dict[str, int] = {}
    headers = []
    for i, line in enumerate(lines):
        stripped = line.rstrip('\n')
        m = _HEADING_RE.match(stripped)
        is_bq = False
        if not m:
            m = _BQ_HEADING_RE.match(stripped)
            is_bq = True
        if m:
            if is_bq and not include_blockquotes:
                continue
            level = len(m.group(1))
            text = m.group(2).strip()
            anchor = pandoc_anchor_id(text, seen)
            headers.append({
                'line': i + 1,
                'level': level,
                'text': text,
                'anchor': anchor,
                'blockquote': is_bq,
            })
    return headers


# ---------------------------------------------------------------------------
# Bestehende MD-Links maskieren
# ---------------------------------------------------------------------------

_MD_LINK_RE = re.compile(r'\[(?:[^\[\]]|\[(?:[^\[\]]|\[[^\]]*\])*\])*\]\([^)]*\)')


def find_link_spans(text: str) -> list[tuple[int, int]]:
    """Findet alle [text](url)-Bereiche in einer Zeile und gibt deren Positionen zurück."""
    return [(m.start(), m.end()) for m in _MD_LINK_RE.finditer(text)]


def is_inside_link(col: int, spans: list[tuple[int, int]]) -> bool:
    """Prüft ob eine Spaltenposition innerhalb eines bestehenden MD-Links liegt."""
    return any(start <= col < end for start, end in spans)


# ---------------------------------------------------------------------------
# Bestehende verlinkte Referenzen parsen → page_to_anchors
# ---------------------------------------------------------------------------

_LINKED_PAGE_RE = re.compile(
    r'\[(?:[^]]*?)(?:Seite|S\.)\s*(\d+)(?:[^]]*?)\]\(#([^)]+)\)'
)
_LINKED_CROSSFILE_RE = re.compile(
    r'\[(?:[^]]*?)(?:Seite|S\.)\s*(\d+)(?:[^]]*?)\]\(<([^>]+\.md)#([^)]+)>\)'
)


def extract_existing_mappings(lines: list[str]) -> dict[str, list[str]]:
    """Extrahiert Seite→Anker-Zuordnungen aus bereits verlinkten Referenzen."""
    page_to_anchors: dict[str, list[str]] = {}
    for line in lines:
        for m in _LINKED_PAGE_RE.finditer(line):
            page = m.group(1)
            anchor = m.group(2)
            if page not in page_to_anchors:
                page_to_anchors[page] = []
            if anchor not in page_to_anchors[page]:
                page_to_anchors[page].append(anchor)
    return page_to_anchors


def extract_crossfile_mappings(lines: list[str]) -> dict[str, dict[str, list[str]]]:
    """Extrahiert Cross-File Seite→Anker-Zuordnungen aus bestehenden Links."""
    result: dict[str, dict[str, list[str]]] = {}
    for line in lines:
        for m in _LINKED_CROSSFILE_RE.finditer(line):
            page = m.group(1)
            target_file = m.group(2)
            anchor = m.group(3)
            if target_file not in result:
                result[target_file] = {}
            if page not in result[target_file]:
                result[target_file][page] = []
            if anchor not in result[target_file][page]:
                result[target_file][page].append(anchor)
    return result


# ---------------------------------------------------------------------------
# Unverlinkte Seitenverweise finden
# ---------------------------------------------------------------------------

_PAGE_PATTERNS = [
    # "ab Seite N" / "ab S. N"
    re.compile(r'ab\s+(?:Seite|S\.)\s+(\d+)'),
    # "Seiten N, M und O"
    re.compile(r'Seiten\s+(\d+(?:\s*,\s*\d+)*)\s+und\s+(\d+)'),
    # "Seiten N und M"
    re.compile(r'Seiten\s+(\d+)\s+und\s+(\d+)'),
    # "Seite N–M" (Bereich)
    re.compile(r'(?:Seite|S\.)\s+(\d+)\s*[–-]\s*(\d+)'),
    # "Seite N" / "S. N"
    re.compile(r'(?:Seite|S\.)\s+(\d+)'),
]


def _detect_book_context(line: str, match_start: int, aliases: dict) -> str | None:
    """Erkennt einen Buchtitel vor oder um einen Seitenverweis herum."""
    prefix = line[:match_start]

    # Bold ArM5: **ArM5**,
    if re.search(r'\*\*ArM5\*\*\s*,?\s*$', prefix):
        return 'ArM5'

    # "Seite N von **ArM5**" / "Seite N von ArM5"
    suffix = line[match_start:]
    if re.search(r'^\S*\s+\d+\s+von\s+\*?\*?ArM5\*?\*?', suffix):
        return 'ArM5'

    # Kursiver Buchtitel: *Titel*,
    m = re.search(r'\*([^*]+)\*\s*[,(]?\s*$', prefix)
    if m:
        title = m.group(1).strip()
        if title in aliases:
            return title

    # Nicht-kursive bekannte Titel
    sorted_keys = sorted(aliases.keys(), key=len, reverse=True)
    for key in sorted_keys:
        if len(key) < 3:
            continue
        pattern = re.escape(key)
        km = re.search(pattern + r'\s*[,(]?\s*$', prefix)
        if km:
            return key

    # ArM5 ohne Bold
    if re.search(r'(?<!\*)ArM5\s*,?\s*$', prefix):
        return 'ArM5'

    # "von ArM5" nach dem Match
    if re.search(r'von\s+\*?\*?ArM5\*?\*?', suffix[:40]):
        return 'ArM5'

    return None


def find_unlinked_refs(lines: list[str], aliases: dict) -> list[dict]:
    """Findet alle unverlinkten Seitenverweise mit Kontext."""
    refs = []
    for line_idx, raw_line in enumerate(lines):
        line = raw_line.rstrip('\n')
        # Blockquote-Prefix entfernen für Analyse, aber Position merken
        bq_prefix = ''
        content = line
        bq_match = re.match(r'^((?:>\s*)+)', line)
        if bq_match:
            bq_prefix = bq_match.group(1)
            content = line[len(bq_prefix):]

        link_spans = find_link_spans(line)

        for pattern in _PAGE_PATTERNS:
            for m in pattern.finditer(line):
                if is_inside_link(m.start(), link_spans):
                    continue
                # URL-Kontexte ausschließen
                prefix_check = line[max(0, m.start()-30):m.start()]
                if 'atlas-games.com' in prefix_check or 'www.' in prefix_check:
                    continue

                page = m.group(1)
                book = _detect_book_context(line, m.start(), aliases)

                ctx_start = max(0, line_idx - 2)
                ctx_end = min(len(lines), line_idx + 3)
                context = ''.join(lines[ctx_start:ctx_end]).strip()

                refs.append({
                    'line': line_idx + 1,
                    'col': m.start(),
                    'match_end': m.end(),
                    'text': m.group(0),
                    'full_match': m.group(0),
                    'page': page,
                    'book': book,
                    'type': 'cross_file' if book else 'internal',
                    'context': context[:500],
                    'blockquote': bool(bq_prefix),
                })
    return refs


# ---------------------------------------------------------------------------
# Config-Verwaltung
# ---------------------------------------------------------------------------

def _config_path_for(input_path: str) -> Path:
    stem = Path(input_path).stem
    return CONFIG_DIR / f"{stem}.json"


def _file_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return f"sha256:{h.hexdigest()[:16]}"


def load_aliases() -> dict:
    if not ALIASES_PATH.exists():
        print(f"Warnung: {ALIASES_PATH} nicht gefunden.", file=sys.stderr)
        return {}
    data = json.loads(ALIASES_PATH.read_text(encoding='utf-8'))
    return data.get('aliases', {})


def load_english_to_german() -> dict:
    if not ALIASES_PATH.exists():
        return {}
    data = json.loads(ALIASES_PATH.read_text(encoding='utf-8'))
    return data.get('english_to_german_files', {})


def load_config(input_path: str) -> dict | None:
    cfg_path = _config_path_for(input_path)
    if not cfg_path.exists():
        return None
    return json.loads(cfg_path.read_text(encoding='utf-8'))


def save_config(input_path: str, config: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    cfg_path = _config_path_for(input_path)
    cfg_path.write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8'
    )
    return cfg_path


def load_target_config(target_file: str) -> dict | None:
    """Lädt die Config einer Zieldatei (für Cross-File page_to_anchors)."""
    stem = Path(target_file).stem
    cfg_path = CONFIG_DIR / f"{stem}.json"
    if not cfg_path.exists():
        return None
    return json.loads(cfg_path.read_text(encoding='utf-8'))


# ---------------------------------------------------------------------------
# TOC-Erkennung und -Verlinkung
# ---------------------------------------------------------------------------

_TOC_MARKERS = ['## Inhalt', '## Inhaltsverzeichnis', '# Inhaltsverzeichnis']
_INDENT_CHARS = ['&emsp;', '&nbsp;', '  ']

_ZAHLWORT_MAP = {
    'eins': '1', 'zwei': '2', 'drei': '3', 'vier': '4', 'fünf': '5',
    'sechs': '6', 'sieben': '7', 'acht': '8', 'neun': '9', 'zehn': '10',
    'elf': '11', 'zwölf': '12', 'dreizehn': '13', 'vierzehn': '14',
    'fünfzehn': '15', 'sechzehn': '16',
    'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
    'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10',
    'eleven': '11', 'twelve': '12', 'thirteen': '13', 'fourteen': '14',
    'fifteen': '15', 'sixteen': '16',
}


def _normalize_for_match(text: str) -> str:
    """Normalisiert Text für den TOC-Header-Vergleich."""
    t = text.strip()
    t = re.sub(r'\*\*([^*]+)\*\*', r'\1', t)
    t = re.sub(r'\*([^*]+)\*', r'\1', t)
    t = t.replace('&emsp;', '').replace('&nbsp;', '')
    t = re.sub(r'<br\s*/?>', '', t)
    t = re.sub(r'^#{1,6}\s+', '', t)
    t = re.sub(r'^-\s+', '', t)
    t = t.strip()
    return t


def _replace_zahlwort(text: str) -> str:
    """Ersetzt Zahlwörter durch Ziffern für den Vergleich."""
    t = text.lower()
    for word, digit in _ZAHLWORT_MAP.items():
        t = re.sub(r'\b' + word + r'\b', digit, t)
    return t


def find_toc_range(lines: list[str], config: dict | None = None) -> tuple[int, int] | None:
    """Findet den TOC-Bereich in der Datei."""
    markers = _TOC_MARKERS
    if config and 'toc' in config and 'start_markers' in config['toc']:
        markers = config['toc']['start_markers']

    toc_start = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        for marker in markers:
            if stripped == marker or stripped == marker + '<br>':
                toc_start = i
                break
        if toc_start is not None:
            break

    if toc_start is None:
        return None

    toc_end = toc_start + 1
    for i in range(toc_start + 1, len(lines)):
        stripped = lines[i].strip()
        if stripped.startswith('# ') and not stripped.startswith('## ') and not stripped.startswith('### '):
            if i > toc_start + 2:
                toc_end = i
                break
        if stripped.startswith('## ') and i > toc_start + 5:
            is_toc_content = False
            for j in range(i + 1, min(i + 6, len(lines))):
                nxt = lines[j].strip()
                if not nxt:
                    continue
                if nxt.startswith('- ') or nxt.startswith('&emsp;') or nxt.startswith('## '):
                    is_toc_content = True
                break
            if not is_toc_content:
                toc_end = i
                break
    else:
        toc_end = len(lines)

    return (toc_start, toc_end)


def _word_set(text: str) -> set[str]:
    """Extrahiert signifikante Wörter (>2 Zeichen) aus einem Text."""
    words = re.findall(r'[a-zäöüß]{3,}', text.lower())
    stopwords = {'und', 'oder', 'der', 'die', 'das', 'den', 'dem', 'des',
                 'ein', 'eine', 'für', 'von', 'mit', 'als', 'aus', 'auf',
                 'bei', 'nach', 'vor', 'zum', 'zur', 'über', 'unter',
                 'the', 'and', 'for', 'from', 'with'}
    return {w for w in words if w not in stopwords}


def _word_overlap_score(text_a: str, text_b: str) -> float:
    """Berechnet den Wortüberlappungs-Score zwischen zwei Texten (0.0–1.0)."""
    words_a = _word_set(text_a)
    words_b = _word_set(text_b)
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    return len(intersection) / min(len(words_a), len(words_b))


def link_toc_entries(lines: list[str], headers: list[dict],
                     config: dict | None = None) -> tuple[list[str], list[dict]]:
    """Verlinkt TOC-Einträge mit passenden Headern. Gibt modifizierte Zeilen und Report zurück."""
    toc_range = find_toc_range(lines, config)
    if toc_range is None:
        return lines, []

    toc_start, toc_end = toc_range
    result = list(lines)
    report = []

    header_lookup: dict[str, str] = {}
    header_texts: list[tuple[str, str]] = []
    anchor_to_header: dict[str, str] = {}
    for h in headers:
        norm = _normalize_for_match(h['text']).lower()
        header_lookup[norm] = h['anchor']
        header_texts.append((norm, h['anchor']))
        anchor_to_header[h['anchor']] = h['text']
        norm_z = _replace_zahlwort(norm)
        if norm_z != norm:
            header_lookup[norm_z] = h['anchor']
            header_texts.append((norm_z, h['anchor']))

    for i in range(toc_start, toc_end):
        line = result[i].rstrip('\n')

        if not line.strip() or line.strip() == '<br>':
            continue
        # Bereits verlinkte Einträge überspringen
        if re.search(r'\[.*\]\(#', line):
            continue

        # Blockquote-Einträge im TOC: > prefix entfernen
        is_bq_entry = line.lstrip().startswith('>')
        clean_line = line
        if is_bq_entry:
            clean_line = re.sub(r'^(?:>\s*)+', '', line)

        entry_text = _normalize_for_match(clean_line)
        if not entry_text:
            continue

        entry_lower = entry_text.lower()
        entry_z = _replace_zahlwort(entry_lower)

        # Stufe 1: Exakter Match
        matched_anchor = None
        for key, anchor in header_lookup.items():
            if key == entry_lower or key == entry_z:
                matched_anchor = anchor
                break

        # Stufe 2: Substring-Match
        if matched_anchor is None:
            for key, anchor in header_lookup.items():
                if entry_lower in key or key in entry_lower:
                    matched_anchor = anchor
                    break

        # Stufe 3: Zahlwort-Match
        if matched_anchor is None:
            for key, anchor in header_lookup.items():
                if _replace_zahlwort(key) == entry_z:
                    matched_anchor = anchor
                    break

        # Stufe 4: Wortüberlappung (≥70% der Wörter stimmen überein)
        if matched_anchor is None:
            best_score = 0.0
            best_anchor = None
            for h_text, h_anchor in header_texts:
                score = _word_overlap_score(entry_lower, h_text)
                if score > best_score and score >= 0.6:
                    best_score = score
                    best_anchor = h_anchor
            if best_anchor:
                matched_anchor = best_anchor

        if matched_anchor:
            # Bei Nicht-Exakt-Match den TOC-Text durch den Header-Text ersetzen
            header_text = anchor_to_header.get(matched_anchor, entry_text)
            display_text = header_text if entry_lower != header_text.lower() else entry_text
            corrected = entry_lower != display_text.lower()

            is_bold = '**' in line
            has_br = '<br>' in line
            bq_out = ''
            if is_bq_entry:
                bq_out = re.match(r'^((?:>\s*)+)', line).group(1) if re.match(r'^((?:>\s*)+)', line) else '>'

            temp = clean_line if is_bq_entry else line
            prefix_m = re.match(r'^((?:#{1,6}\s+)?(?:-\s+)?(?:(?:&emsp;|&nbsp;))*)', temp)
            prefix = prefix_m.group(1) if prefix_m else ''

            if is_bold:
                new_line = f'{bq_out}{prefix}**[{display_text}](#{matched_anchor})**'
            else:
                new_line = f'{bq_out}{prefix}[{display_text}](#{matched_anchor})'
            if has_br:
                new_line += '<br>'
            result[i] = new_line + '\n'

            report.append({
                'line': i + 1,
                'entry': entry_text,
                'header': display_text,
                'anchor': matched_anchor,
                'status': 'corrected' if corrected else 'linked',
            })
        else:
            report.append({
                'line': i + 1,
                'entry': entry_text,
                'anchor': None,
                'status': 'no_match',
            })

    return result, report


# ---------------------------------------------------------------------------
# --analyze Modus
# ---------------------------------------------------------------------------

def analyze(input_path: str, lines: list[str]) -> dict:
    """Analysiert die Datei und erzeugt einen Report mit Kandidaten."""
    aliases = load_aliases()
    headers = build_header_index(lines)
    page_to_anchors = extract_existing_mappings(lines)
    crossfile_mappings = extract_crossfile_mappings(lines)
    unlinked = find_unlinked_refs(lines, aliases)

    # Kandidaten für jeden Verweis ermitteln
    for ref in unlinked:
        if ref['type'] == 'cross_file' and ref['book']:
            target_file = aliases.get(ref['book'])
            ref['target_file'] = target_file
            if target_file is None:
                ref['type'] = 'not_translatable'
                ref['candidates'] = []
                continue
            # Kandidaten aus der Zieldatei-Config laden
            target_cfg = load_target_config(target_file)
            if target_cfg and 'page_to_anchors' in target_cfg:
                ref['candidates'] = target_cfg['page_to_anchors'].get(ref['page'], [])
            else:
                ref['candidates'] = []
        else:
            ref['target_file'] = None
            ref['candidates'] = page_to_anchors.get(ref['page'], [])

        ref['resolved_anchor'] = None
        # Auto-resolve bei genau einem Kandidaten
        if len(ref['candidates']) == 1:
            ref['resolved_anchor'] = ref['candidates'][0]

    # TOC analysieren
    toc_range = find_toc_range(lines)
    toc_info = None
    if toc_range:
        toc_info = {
            'start_line': toc_range[0] + 1,
            'end_line': toc_range[1],
            'entry_count': sum(
                1 for i in range(toc_range[0], toc_range[1])
                if lines[i].strip() and lines[i].strip() != '<br>'
                and not lines[i].strip().startswith('#')
            ),
        }

    # Statistiken
    already_linked = sum(1 for line in lines for _ in _LINKED_PAGE_RE.finditer(line))
    crossfile_linked = sum(1 for line in lines for _ in _LINKED_CROSSFILE_RE.finditer(line))

    stats = {
        'headers': len(headers),
        'already_linked_internal': already_linked,
        'already_linked_crossfile': crossfile_linked,
        'unlinked_internal': sum(1 for r in unlinked if r['type'] == 'internal'),
        'unlinked_crossfile': sum(1 for r in unlinked if r['type'] == 'cross_file'),
        'not_translatable': sum(1 for r in unlinked if r['type'] == 'not_translatable'),
        'auto_resolved': sum(1 for r in unlinked if r.get('resolved_anchor')),
        'needs_agent': sum(
            1 for r in unlinked
            if r['type'] in ('internal', 'cross_file')
            and not r.get('resolved_anchor')
            and len(r.get('candidates', [])) > 1
        ),
        'no_candidates': sum(
            1 for r in unlinked
            if r['type'] in ('internal', 'cross_file')
            and not r.get('resolved_anchor')
            and len(r.get('candidates', [])) == 0
        ),
    }

    # Unbekannte Buchtitel sammeln
    unknown_books = set()
    for ref in unlinked:
        if ref['book'] and ref['book'] not in aliases:
            unknown_books.add(ref['book'])

    # Config erzeugen/aktualisieren
    config = {
        'version': 1,
        'source_file': Path(input_path).name,
        'file_hash': _file_hash(input_path),
        'page_to_anchors': page_to_anchors,
        'toc': {
            'enabled': toc_info is not None,
            'start_markers': _TOC_MARKERS,
            'indent_chars': ['&emsp;', '&nbsp;'],
        },
        'exclude_patterns': ['www.atlas-games.com/ArM5'],
    }
    if toc_info:
        config['toc']['detected'] = toc_info

    cfg_path = save_config(input_path, config)

    report = {
        'file': input_path,
        'config_path': str(cfg_path),
        'stats': stats,
        'toc': toc_info,
        'unresolved_refs': [
            {k: v for k, v in ref.items() if k != 'match_end'}
            for ref in unlinked
            if ref['type'] in ('internal', 'cross_file')
        ],
        'not_translatable_refs': [
            {k: v for k, v in ref.items() if k != 'match_end'}
            for ref in unlinked
            if ref['type'] == 'not_translatable'
        ],
        'unknown_books': sorted(unknown_books),
    }

    return report


# ---------------------------------------------------------------------------
# --apply Modus
# ---------------------------------------------------------------------------

def apply_refs(input_path: str, lines: list[str], resolved_path: str) -> list[str]:
    """Fügt aufgelöste Referenzen als MD-Links in die Datei ein."""
    with open(resolved_path, 'r', encoding='utf-8') as f:
        resolved_data = json.load(f)

    resolved_refs = resolved_data
    if isinstance(resolved_data, dict):
        resolved_refs = resolved_data.get('unresolved_refs', [])

    # Nach Zeile und Spalte sortieren (rückwärts, um Positionen nicht zu verschieben)
    refs_by_line: dict[int, list[dict]] = {}
    for ref in resolved_refs:
        if not ref.get('resolved_anchor'):
            continue
        line_num = ref['line']
        if line_num not in refs_by_line:
            refs_by_line[line_num] = []
        refs_by_line[line_num].append(ref)

    # Refs pro Zeile nach Spalte absteigend sortieren (rückwärts ersetzen)
    for line_num in refs_by_line:
        refs_by_line[line_num].sort(key=lambda r: r['col'], reverse=True)

    result = list(lines)
    applied = 0

    for line_num, line_refs in sorted(refs_by_line.items()):
        idx = line_num - 1
        if idx < 0 or idx >= len(result):
            continue

        line = result[idx]
        link_spans = find_link_spans(line)

        for ref in line_refs:
            col = ref['col']
            if is_inside_link(col, link_spans):
                continue

            anchor = ref['resolved_anchor']
            text = ref['text']
            target_file = ref.get('target_file')

            # Suche den exakten Text an der Position
            if line[col:col+len(text)] != text:
                # Versuch Fuzzy-Match in der Nähe
                search_start = max(0, col - 10)
                search_end = min(len(line), col + len(text) + 10)
                pos = line.find(text, search_start, search_end)
                if pos == -1:
                    continue
                col = pos

            if target_file:
                replacement = f'[{text}](<{target_file}#{anchor}>)'
            else:
                replacement = f'[{text}](#{anchor})'

            line = line[:col] + replacement + line[col + len(text):]
            # Link-Spans nach Ersetzung neu berechnen
            link_spans = find_link_spans(line)
            applied += 1

        result[idx] = line

    print(f"  {applied} Links eingefügt.", file=sys.stderr)
    return result


# ---------------------------------------------------------------------------
# --fix-crosslinks Modus
# ---------------------------------------------------------------------------

_CROSSLINK_RE = re.compile(
    r'(\[[^\]]+\]\(<)([^>]+\.md)(#[^)]*>\))'
)


def fix_crosslinks(lines: list[str]) -> tuple[list[str], int]:
    """Korrigiert Cross-File-Links von englischen auf deutsche Dateinamen."""
    eng_to_ger = load_english_to_german()
    if not eng_to_ger:
        return lines, 0

    result = list(lines)
    fixed = 0

    for i, line in enumerate(result):
        new_line = line
        for m in _CROSSLINK_RE.finditer(line):
            filename = m.group(2)
            if filename in eng_to_ger:
                german_name = eng_to_ger[filename]
                if german_name is not None:
                    old = m.group(0)
                    new = m.group(1) + german_name + m.group(3)
                    new_line = new_line.replace(old, new, 1)
                    fixed += 1
        result[i] = new_line

    return result, fixed


# ---------------------------------------------------------------------------
# Hauptprogramm
# ---------------------------------------------------------------------------

def print_report(report: dict):
    """Gibt den Analyse-Report auf stderr aus."""
    stats = report['stats']
    print("=" * 60, file=sys.stderr)
    print("ANALYSE-REPORT", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"  Datei:   {report['file']}", file=sys.stderr)
    print(f"  Config:  {report['config_path']}", file=sys.stderr)
    print(file=sys.stderr)
    print(f"  Header:                    {stats['headers']}", file=sys.stderr)
    print(f"  Bereits verlinkt (intern): {stats['already_linked_internal']}", file=sys.stderr)
    print(f"  Bereits verlinkt (cross):  {stats['already_linked_crossfile']}", file=sys.stderr)
    print(f"  Unverlinkt (intern):       {stats['unlinked_internal']}", file=sys.stderr)
    print(f"  Unverlinkt (cross-file):   {stats['unlinked_crossfile']}", file=sys.stderr)
    print(f"  Nicht übersetzt:           {stats['not_translatable']}", file=sys.stderr)
    print(f"  Auto-aufgelöst:            {stats['auto_resolved']}", file=sys.stderr)
    print(f"  Braucht Agent:             {stats['needs_agent']}", file=sys.stderr)
    print(f"  Ohne Kandidaten:           {stats['no_candidates']}", file=sys.stderr)

    if report.get('toc'):
        toc = report['toc']
        print(file=sys.stderr)
        print(f"  TOC: Zeile {toc['start_line']}–{toc['end_line']}, "
              f"{toc['entry_count']} Einträge", file=sys.stderr)

    if report.get('unknown_books'):
        print(file=sys.stderr)
        print("  Unbekannte Buchtitel:", file=sys.stderr)
        for b in report['unknown_books']:
            print(f"    - {b}", file=sys.stderr)

    print("=" * 60, file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Findet und verlinkt Seitenverweise in Ars-Magica-Regelwerken."
    )
    parser.add_argument(
        "--input", "-i", required=True,
        help="Pfad zur Eingabedatei",
    )
    parser.add_argument(
        "--analyze", action="store_true",
        help="Analysieren: Unverlinkte Verweise finden, Config + JSON-Report erzeugen",
    )
    parser.add_argument(
        "--link-toc", action="store_true",
        help="TOC-Einträge mit Headern verlinken (vollautomatisch)",
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Aufgelöste Referenzen als Links einfügen",
    )
    parser.add_argument(
        "--refs", metavar="JSON",
        help="Pfad zur resolved.json (für --apply)",
    )
    parser.add_argument(
        "--fix-crosslinks", action="store_true",
        help="Bestehende Cross-File-Links korrigieren (englisch → deutsch)",
    )
    parser.add_argument(
        "--output", "-o", metavar="FILE",
        help="Report-Ausgabe in Datei (für --analyze, Standard: stdout)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Detaillierte Ausgabe",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Fehler: Eingabedatei nicht gefunden: {args.input}", file=sys.stderr)
        sys.exit(1)

    with open(args.input, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for i in range(len(lines)):
        if not lines[i].endswith('\n'):
            lines[i] += '\n'

    original_count = len(lines)

    if args.analyze:
        report = analyze(args.input, lines)
        print_report(report)

        # JSON-Report ausgeben
        report_json = json.dumps(report, ensure_ascii=False, indent=2)
        if args.output:
            Path(args.output).write_text(report_json + '\n', encoding='utf-8')
            print(f"\n  Report: {args.output}", file=sys.stderr)
        else:
            print(report_json)

    elif args.link_toc:
        config = load_config(args.input)
        headers = build_header_index(lines)
        result, toc_report = link_toc_entries(lines, headers, config)

        if len(result) != original_count:
            print("FEHLER: Zeilenzahl verändert!", file=sys.stderr)
            sys.exit(1)

        linked = sum(1 for r in toc_report if r['status'] == 'linked')
        unmatched = sum(1 for r in toc_report if r['status'] == 'no_match')
        print(f"  TOC: {linked} verlinkt, {unmatched} ohne Match", file=sys.stderr)

        if unmatched > 0:
            print("  Nicht gematchte Einträge:", file=sys.stderr)
            for r in toc_report:
                if r['status'] == 'no_match':
                    print(f"    Zeile {r['line']}: {r['entry']}", file=sys.stderr)

        with open(args.input, 'w', encoding='utf-8') as f:
            f.writelines(result)
        print(f"  Datei geschrieben: {args.input}", file=sys.stderr)

    elif args.apply:
        if not args.refs:
            print("Fehler: --refs ist erforderlich für --apply", file=sys.stderr)
            sys.exit(1)
        if not os.path.isfile(args.refs):
            print(f"Fehler: Referenzdatei nicht gefunden: {args.refs}", file=sys.stderr)
            sys.exit(1)

        result = apply_refs(args.input, lines, args.refs)

        if len(result) != original_count:
            print("FEHLER: Zeilenzahl verändert!", file=sys.stderr)
            sys.exit(1)

        with open(args.input, 'w', encoding='utf-8') as f:
            f.writelines(result)
        print(f"  Datei geschrieben: {args.input}", file=sys.stderr)

    elif args.fix_crosslinks:
        result, fixed = fix_crosslinks(lines)

        if len(result) != original_count:
            print("FEHLER: Zeilenzahl verändert!", file=sys.stderr)
            sys.exit(1)

        print(f"  {fixed} Cross-File-Links korrigiert.", file=sys.stderr)

        with open(args.input, 'w', encoding='utf-8') as f:
            f.writelines(result)
        print(f"  Datei geschrieben: {args.input}", file=sys.stderr)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
