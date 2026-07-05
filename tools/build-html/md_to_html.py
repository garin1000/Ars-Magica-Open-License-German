#!/usr/bin/env python3
"""Konvertiert Markdown-Dateien aus german-ordered/ in self-contained HTML.

Jede HTML-Datei enthält:
  - Einklappbare Navigation (links, H1-H3)
  - Volltextsuche (rechts)
  - Volltext-Suchindex
  - Bildschirmoptimiertes CSS
"""

import argparse
import base64
import html
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent


def _fix_internal_links(html_out: str) -> str:
    """Gleicht href-Targets an tatsächliche IDs an.

    Pandoc erzeugt IDs inkonsistent: Bei Headern mit echtem Hyphen
    (z.B. „Zivil- und") bleibt „--" erhalten, bei entfernten
    Sonderzeichen (–, /, &) wird zu „-" kollabiert.  Die MD-Links
    verwenden durchgehend „--".  Dieser Post-Processing-Schritt
    passt die hrefs an die tatsächlich erzeugten IDs an.
    """
    id_re = re.compile(r'<h[1-6]\s+id="([^"]*)"')
    ids = set(id_re.findall(html_out))
    if not ids:
        return html_out

    def fix_href(m):
        anchor = m.group(1)
        if anchor in ids:
            return m.group(0)
        collapsed = re.sub(r'-{2,}', '-', anchor)
        if collapsed in ids:
            return f'href="#{collapsed}"'
        return m.group(0)

    return re.compile(r'href="#([^"]*)"').sub(fix_href, html_out)


def pandoc_to_html(md_path: str) -> str:
    result = subprocess.run(
        ["pandoc", "--from", "markdown+lists_without_preceding_blankline", "--to", "html5",
         "--wrap=none", str(md_path)],
        capture_output=True, text=True, check=True,
    )
    html_out = re.sub(r'<colgroup>.*?</colgroup>\n?', '', result.stdout, flags=re.DOTALL)
    html_out = re.sub(r'<!--.*?-->\n?', '', html_out, flags=re.DOTALL)
    html_out = re.sub(r'(href="[^"]+)\.md((?:#[^"]*)?")', r'\1.html\2', html_out)
    html_out = _fix_internal_links(html_out)
    return html_out


def extract_nav_and_index(body_html: str) -> tuple[list[dict], list[dict]]:
    """Extrahiert Navigationsbaum (H1-H3) und Suchindex (H2-H4) aus HTML."""
    heading_re = re.compile(
        r'<h([1-6])\s+id="([^"]*)"[^>]*>(.*?)</h\1>', re.DOTALL
    )
    tag_strip_re = re.compile(r'<[^>]+>')

    nav_tree = []
    search_index = []

    headings_with_pos = []
    for m in heading_re.finditer(body_html):
        level = int(m.group(1))
        hid = m.group(2)
        raw_title = m.group(3)
        title = tag_strip_re.sub('', raw_title).strip()
        headings_with_pos.append((m.start(), m.end(), level, hid, title))

    for i, (start, end, level, hid, title) in enumerate(headings_with_pos):
        if level <= 3:
            nav_tree.append({"level": level, "id": hid, "title": title})

        if level >= 2:
            if i + 1 < len(headings_with_pos):
                section_end = headings_with_pos[i + 1][0]
            else:
                section_end = len(body_html)

            section_html = body_html[end:section_end]
            section_text = tag_strip_re.sub(' ', section_html)
            section_text = re.sub(r'\s+', ' ', section_text).strip()

            search_index.append({
                "id": hid,
                "title": title,
                "text": section_text,
            })

    return nav_tree, search_index


def build_nav_html(nav_tree: list[dict], logo_b64: str) -> str:
    """Baut verschachtelte HTML-Navigation aus dem Heading-Baum."""
    lines = ['<nav id="sidebar">\n']
    lines.append(f'  <div class="nav-logo"><img src="data:image/png;base64,{logo_b64}" alt="Ars Magica Open License"></div>\n')
    lines.append('  <div class="nav-header">Navigation</div>\n')
    lines.append('  <div class="nav-content">\n')

    prev_level = 0

    for i, item in enumerate(nav_tree):
        level = item["level"]
        has_children = (i + 1 < len(nav_tree) and nav_tree[i + 1]["level"] > level)

        if level > prev_level:
            for _ in range(level - prev_level):
                collapsed = ' collapsed' if prev_level > 0 else ''
                lines.append(f'  <ul class="nav-level-{level}{collapsed}">\n')
        elif level < prev_level:
            for _ in range(prev_level - level):
                lines.append('  </li>\n  </ul>\n')
            lines.append('  </li>\n')
        else:
            lines.append('  </li>\n')

        esc_title = html.escape(item["title"])
        toggle = ' class="has-children"' if has_children else ''
        arrow = '<span class="nav-toggle-arrow">&#9654;</span>' if has_children else ''
        lines.append(
            f'    <li{toggle}>'
            f'{arrow}<a href="#{item["id"]}">{esc_title}</a>\n'
        )

        prev_level = level

    for _ in range(prev_level):
        lines.append('  </li>\n  </ul>\n')

    lines.append('  </div>\n')
    lines.append('</nav>\n')
    return ''.join(lines)


def get_css() -> str:
    return """\
:root {
  --nav-width: 280px;
  --search-width: 320px;
  --bg: #fafaf8;
  --bg-nav: #f0eeea;
  --bg-search: #f5f4f0;
  --text: #2c2c2c;
  --text-muted: #666;
  --accent: #8b4513;
  --accent-light: #d4a574;
  --border: #ddd;
  --highlight: #fff3cd;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

html { scroll-padding-top: 1rem; }

body {
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  font-size: 16px;
  line-height: 1.65;
  color: var(--text);
  background: var(--bg);
}

/* --- Layout ------------------------------------------------------------ */

#sidebar {
  position: fixed; top: 0; left: 0; bottom: 30px;
  width: var(--nav-width);
  min-width: 180px;
  max-width: 50vw;
  background: var(--bg-nav);
  border-right: none;
  overflow-y: auto;
  z-index: 100;
  font-size: 0.85rem;
  transition: transform 0.25s;
}


#nav-resize {
  position: fixed; top: 0; bottom: 30px;
  left: var(--nav-width);
  width: 8px;
  cursor: col-resize;
  z-index: 101;
  background: var(--bg-nav);
  border-left: 1px solid var(--border);
  border-right: 1px solid var(--border);
  transition: background 0.15s;
}
#nav-resize:hover, #nav-resize.active { background: var(--accent-light); }

#search-resize {
  position: fixed; top: 0; bottom: 30px;
  right: var(--search-width);
  width: 8px;
  cursor: col-resize;
  z-index: 101;
  background: var(--bg-search);
  border-left: 1px solid var(--border);
  border-right: 1px solid var(--border);
  transition: background 0.15s;
  display: none;
}
body.search-open #search-resize { display: block; }
#search-resize:hover, #search-resize.active { background: var(--accent-light); }

#main-content {
  margin-left: calc(var(--nav-width) + 8px);
  margin-right: 0;
  padding: 2rem 3rem 3rem;
  margin-bottom: 30px;
  max-width: none;
  transition: margin 0.15s;
}

body.search-open #main-content {
  margin-right: calc(var(--search-width) + 8px);
}

#search-panel {
  position: fixed; top: 0; right: 0; bottom: 30px;
  width: var(--search-width);
  min-width: 200px;
  max-width: 50vw;
  background: var(--bg-search);
  border-left: none;
  z-index: 100;
  display: flex;
  flex-direction: column;
  transform: translateX(100%);
  transition: transform 0.25s;
}

#search-panel.open {
  transform: translateX(0);
}

/* --- Search field (top right) ------------------------------------------ */

#search-field {
  position: fixed; top: 10px; right: 16px;
  z-index: 200;
  display: flex;
  align-items: center;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 4px 10px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  width: 240px;
  transition: right 0.25s, width 0.2s, border-color 0.2s;
}

#search-field:focus-within {
  border-color: var(--accent);
  width: 320px;
}

body.search-open #search-field {
  right: calc(var(--search-width) + 8px + 16px);
}

#search-field-icon {
  font-size: 1rem;
  margin-right: 6px;
  color: var(--text-muted);
  flex-shrink: 0;
}

#search-field input {
  border: none;
  outline: none;
  font-size: 0.9rem;
  width: 100%;
  background: transparent;
}

/* --- Navigation -------------------------------------------------------- */

.nav-logo {
  padding: 16px;
  text-align: center;
  border-bottom: 1px solid var(--border);
  background: var(--bg-nav);
}

.nav-logo img {
  max-width: 250px;
  width: 100%;
  height: auto;
}

.nav-header {
  padding: 12px 16px;
  font-weight: 700;
  font-size: 1rem;
  color: var(--accent);
  border-bottom: 1px solid var(--border);
  position: sticky; top: 0;
  background: var(--bg-nav);
}

.nav-content { padding: 8px 0; }

#sidebar ul {
  list-style: none;
  padding-left: 0;
}

#sidebar ul.nav-level-2 { padding-left: 12px; }
#sidebar ul.nav-level-3 { padding-left: 12px; }

#sidebar ul.collapsed { display: none; }

#sidebar li { margin: 0; }

#sidebar li.has-children {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
}

#sidebar li.has-children > ul {
  width: 100%;
}

#sidebar li.has-children > a {
  padding-left: 2px;
}

#sidebar li a {
  display: block;
  padding: 4px 16px;
  color: var(--text);
  text-decoration: none;
  border-left: 3px solid transparent;
  transition: background 0.15s;
  flex: 1;
  min-width: 0;
}

#sidebar li a:hover {
  background: rgba(0,0,0,0.05);
}

#sidebar li a.active {
  border-left-color: var(--accent);
  color: var(--accent);
  font-weight: 600;
}

.nav-level-1 > li > a { font-weight: 700; font-size: 0.95rem; padding: 8px 16px; }

.nav-toggle-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  align-self: stretch;
  font-size: 0.55em;
  cursor: pointer;
  transition: transform 0.2s;
  flex-shrink: 0;
  order: -1;
  border-radius: 3px;
}

.nav-toggle-arrow:hover {
  background: rgba(0,0,0,0.08);
}

#sidebar li.has-children.expanded > .nav-toggle-arrow {
  transform: rotate(90deg);
}

/* --- Search Panel ------------------------------------------------------ */

#search-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-bottom: 1px solid var(--border);
}

#search-panel-header span { font-weight: 600; font-size: 0.9rem; color: var(--accent); }

#search-close {
  background: none; border: none;
  font-size: 1.2rem; cursor: pointer;
  color: var(--text-muted);
  padding: 2px 6px; border-radius: 4px;
}
#search-close:hover { background: rgba(0,0,0,0.08); color: var(--text); }

.search-result.focused { background: rgba(139,69,19,0.08); }

#search-results {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.search-result {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  transition: background 0.15s;
}

.search-result:hover { background: rgba(0,0,0,0.04); }

.search-result-title {
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--accent);
  margin-bottom: 4px;
}

.search-result-snippet {
  font-size: 0.8rem;
  color: var(--text-muted);
  line-height: 1.4;
}

.search-no-results {
  padding: 20px 16px;
  color: var(--text-muted);
  font-size: 0.85rem;
  text-align: center;
}

.search-result-snippet mark {
  background: var(--highlight);
  padding: 0 2px;
  border-radius: 2px;
}

#search-count {
  padding: 8px 16px;
  font-size: 0.8rem;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border);
}

/* --- Content ----------------------------------------------------------- */

#main-content h1 {
  font-size: 1.8rem;
  margin: 2.5rem 0 1rem;
  color: var(--accent);
  border-bottom: 2px solid var(--accent-light);
  padding-bottom: 0.3rem;
}

#main-content h2 {
  font-size: 1.4rem;
  margin: 2rem 0 0.8rem;
  color: #444;
  border-bottom: 1px solid var(--border);
  padding-bottom: 0.2rem;
}

#main-content h3 { font-size: 1.15rem; margin: 1.5rem 0 0.6rem; }
#main-content h4 { font-size: 1.05rem; margin: 1.2rem 0 0.5rem; font-style: italic; }
#main-content h5 { font-size: 1rem; margin: 1rem 0 0.4rem; }

#main-content p { margin: 0.6rem 0; max-width: 55em; }

#main-content ul, #main-content ol {
  margin: 0.5rem 0 0.5rem 1.5rem;
  max-width: 55em;
}

#main-content blockquote {
  border-left: 4px solid var(--accent-light);
  padding: 0.5rem 1rem;
  margin: 1rem 0;
  background: rgba(139,69,19,0.04);
  max-width: 55em;
}

#main-content table {
  border-collapse: collapse;
  margin: 1rem 0;
  font-size: 0.9rem;
  width: max-content;
  max-width: 100%;
}

#main-content th, #main-content td {
  border: 1px solid var(--border);
  padding: 6px 12px;
  text-align: left;
}

#main-content td, #main-content th {
  max-width: 30em;
}

#main-content td:first-child,
#main-content th:first-child {
  white-space: nowrap;
  max-width: none;
}

#main-content td:last-child,
#main-content th:last-child {
  max-width: 35em;
}

#main-content th {
  background: var(--bg-nav);
  font-weight: 600;
}

#main-content tr:nth-child(even) { background: rgba(0,0,0,0.02); }

#main-content em { color: #555; }
#main-content strong { color: #333; }

#main-content a { color: var(--accent); }
#main-content a:hover { text-decoration: underline; }

#main-content hr {
  border: none;
  border-top: 1px solid var(--border);
  margin: 2rem 0;
}

#main-content .section { scroll-margin-top: 1rem; }

.highlight-target {
  animation: highlight-fade 2s ease;
}

@keyframes highlight-fade {
  0% { background: var(--highlight); }
  100% { background: transparent; }
}

/* --- Link-Hover Tooltip ------------------------------------------------ */

.link-tooltip {
  position: fixed;
  z-index: 300;
  max-width: 420px;
  min-width: 200px;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  padding: 0;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.15s;
  font-size: 0.85rem;
  line-height: 1.5;
  overflow: hidden;
}

.link-tooltip.visible {
  opacity: 1;
  pointer-events: auto;
}

.link-tooltip-title {
  padding: 8px 12px;
  font-weight: 700;
  font-size: 0.9rem;
  color: var(--accent);
  background: var(--bg-nav);
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.link-tooltip-body {
  padding: 8px 12px;
  color: var(--text);
  max-height: 150px;
  overflow: hidden;
  position: relative;
}

.link-tooltip-body p { margin: 0 0 0.4em; }

.link-tooltip-body table {
  font-size: 0.8rem;
  border-collapse: collapse;
  width: 100%;
}

.link-tooltip-body th,
.link-tooltip-body td {
  border: 1px solid var(--border);
  padding: 2px 6px;
  text-align: left;
}

.link-tooltip-body th { background: var(--bg-nav); }

.link-tooltip-body ul,
.link-tooltip-body ol {
  margin: 0 0 0 1.2em;
  padding: 0;
}

.link-tooltip-body blockquote {
  border-left: 3px solid var(--accent-light);
  padding: 4px 8px;
  margin: 0;
  background: rgba(139,69,19,0.04);
}

.link-tooltip-fade {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 30px;
  background: linear-gradient(transparent, #fff);
  pointer-events: none;
}

@media (max-width: 800px) {
  .link-tooltip { display: none !important; }
}

@media (prefers-reduced-motion: reduce) {
  .link-tooltip { transition: none; }
}

/* --- Nav toggle (mobile) ----------------------------------------------- */

#nav-toggle {
  display: none;
  position: fixed; top: 12px; left: 12px;
  z-index: 200;
  background: var(--accent);
  color: #fff;
  border: none; border-radius: 6px;
  padding: 8px 12px;
  cursor: pointer;
  font-size: 1.1rem;
}

/* --- Footer ------------------------------------------------------------ */

#page-footer {
  position: fixed; bottom: 0; left: 0; right: 0;
  padding: 6px 20px;
  border-top: 1px solid var(--border);
  font-size: 0.75rem;
  color: var(--text-muted);
  line-height: 1.5;
  background: var(--bg-nav);
  z-index: 99;
  text-align: center;
}

#page-footer a { color: var(--accent); }

/* --- Responsive -------------------------------------------------------- */

@media (max-width: 1100px) {
  #sidebar {
    transform: translateX(-100%);
  }
  #sidebar.open {
    transform: translateX(0);
  }
  #main-content, #page-footer {
    margin-left: 0;
    transition: margin-left 0.25s;
  }
  body.nav-open #main-content,
  body.nav-open #page-footer {
    margin-left: var(--nav-width);
  }
  #nav-toggle { display: block; }
  #nav-resize, #search-resize { display: none !important; }
}

@media (max-width: 800px) {
  #main-content { padding: 1.5rem 1rem; }
  #search-panel { width: 100%; }
}

/* --- Print ------------------------------------------------------------- */

@media print {
  #sidebar, #search-panel, #search-field, #nav-toggle, #nav-resize, #search-resize, .link-tooltip { display: none !important; }
  #main-content, #page-footer { margin: 0; padding: 1cm; }
  #main-content a { color: inherit; text-decoration: none; }
}
"""


def get_worker_js(fuse_js: str) -> str:
    """Erzeugt den Web-Worker-Script-Code (Fuse.js + Suchlogik)."""
    handler = """\
function normalize(s) {
  return s.replace(/[äÄ]/g, 'a').replace(/[öÖ]/g, 'o')
           .replace(/[üÜ]/g, 'u').replace(/ß/g, 'ss').toLowerCase();
}

var fuseInstance = null;

self.onmessage = function(e) {
  if (e.data.type === 'init') {
    var items = e.data.index.map(function(item, i) {
      return { idx: i, title: normalize(item.title), text: normalize(item.text) };
    });

    fuseInstance = new Fuse(items, {
      keys: [
        { name: 'title', weight: 2 },
        { name: 'text', weight: 1 }
      ],
      threshold: 0.35,
      ignoreLocation: true,
      minMatchCharLength: 2,
      findAllMatches: false,
      limit: 50,
    });

    self.postMessage({ type: 'ready' });
  }

  if (e.data.type === 'search') {
    if (!fuseInstance) return;
    var results = fuseInstance.search(e.data.query);
    self.postMessage({
      type: 'results',
      query: e.data.query,
      hits: results.map(function(r) { return r.item.idx; })
    });
  }
};
"""
    return fuse_js + "\n" + handler


def get_js(search_index_json: str) -> str:
    return f"""\
(function() {{
  'use strict';

  const searchIndex = {search_index_json};

  // --- Umlaut-Normalisierung (für Snippet-Highlighting auf dem Hauptthread) ---
  function normalizeForSearch(text) {{
    return text.replace(/[äÄ]/g, 'a').replace(/[öÖ]/g, 'o')
               .replace(/[üÜ]/g, 'u').replace(/ß/g, 'ss').toLowerCase();
  }}

  // --- Web Worker für Fuse.js ---
  const workerScript = document.getElementById('search-worker-script').textContent;
  const searchWorker = new Worker(URL.createObjectURL(
    new Blob([workerScript], {{ type: 'application/javascript' }})
  ));
  let searchReady = false;
  let pendingQuery = '';

  searchWorker.postMessage({{ type: 'init', index: searchIndex }});

  searchWorker.onmessage = function(e) {{
    if (e.data.type === 'ready') {{
      searchReady = true;
      if (pendingQuery.length >= 2) doSearch();
      return;
    }}
    if (e.data.type === 'results') {{
      const currentNormQuery = normalizeForSearch(searchInput.value.trim());
      if (e.data.query !== currentNormQuery) return;
      renderSearchResults(e.data.hits, pendingQuery);
    }}
  }};

  // --- DOM refs ---
  const sidebar = document.getElementById('sidebar');
  const searchPanel = document.getElementById('search-panel');
  const searchInput = document.getElementById('search-input');
  const searchResults = document.getElementById('search-results');
  const searchCount = document.getElementById('search-count');
  const searchClose = document.getElementById('search-close');
  const navToggle = document.getElementById('nav-toggle');
  const navLinks = sidebar.querySelectorAll('a[href^="#"]');

  function openSearch() {{
    searchPanel.classList.add('open');
    document.body.classList.add('search-open');
  }}

  function closeSearch() {{
    searchPanel.classList.remove('open');
    document.body.classList.remove('search-open');
  }}

  // --- Nav open/close helpers ---
  const narrowQuery = window.matchMedia('(max-width: 1100px)');

  function openNav() {{
    sidebar.classList.add('open');
    document.body.classList.add('nav-open');
  }}
  function closeNav() {{
    sidebar.classList.remove('open');
    document.body.classList.remove('nav-open');
  }}

  // --- Search close button ---
  searchClose.addEventListener('click', function() {{
    closeSearch();
    searchInput.blur();
  }});

  // --- Open search on input focus or typing ---
  searchInput.addEventListener('focus', openSearch);
  searchInput.addEventListener('input', function() {{
    if (searchInput.value.length > 0) openSearch();
  }});

  // --- Nav toggle (mobile) ---
  navToggle.addEventListener('click', function() {{
    if (sidebar.classList.contains('open')) closeNav();
    else openNav();
  }});

  // --- Close nav on main-content click ---
  document.getElementById('main-content').addEventListener('click', function() {{
    if (sidebar.classList.contains('open')) closeNav();
  }});

  // --- Toggle arrow: only expand/collapse, no navigation ---
  sidebar.addEventListener('click', function(e) {{
    const arrow = e.target.closest('.nav-toggle-arrow');
    if (!arrow) return;
    e.stopPropagation();
    const li = arrow.closest('li.has-children');
    if (!li) return;
    li.classList.toggle('expanded');
    const childUl = li.querySelector(':scope > ul');
    if (childUl) childUl.classList.toggle('collapsed');
  }});

  // --- Nav link click: always navigate ---
  sidebar.addEventListener('click', function(e) {{
    const link = e.target.closest('a[href^="#"]');
    if (!link) return;
    e.preventDefault();
    const targetId = link.getAttribute('href');
    if (narrowQuery.matches) {{
      closeNav();
      setTimeout(function() {{
        const target = document.getElementById(targetId.slice(1));
        if (target) {{
          target.scrollIntoView();
          history.replaceState(null, '', targetId);
        }}
      }}, 260);
    }} else {{
      const target = document.getElementById(targetId.slice(1));
      if (target) {{
        target.scrollIntoView({{ behavior: 'smooth' }});
        history.replaceState(null, '', targetId);
      }}
    }}
  }});

  function expandParents(link) {{
    let li = link.closest('li');
    while (li) {{
      const parentUl = li.parentElement;
      if (parentUl && parentUl.classList.contains('collapsed')) {{
        parentUl.classList.remove('collapsed');
      }}
      const parentLi = parentUl?.closest('li.has-children');
      if (parentLi) {{
        parentLi.classList.add('expanded');
      }}
      li = parentLi;
    }}
  }}

  // Expand parent nav items on page load based on URL hash
  function expandToHash() {{
    const hash = window.location.hash;
    if (!hash) return;
    const link = sidebar.querySelector('a[href="' + CSS.escape(hash) + '"]');
    if (link) expandParents(link);
  }}
  expandToHash();

  // --- Scroll Spy ---
  let headingEls = [];
  navLinks.forEach(link => {{
    const id = link.getAttribute('href').slice(1);
    const el = document.getElementById(id);
    if (el) headingEls.push({{ el, link }});
  }});

  let scrollTimer;
  window.addEventListener('scroll', function() {{
    clearTimeout(scrollTimer);
    scrollTimer = setTimeout(updateActiveNav, 80);
  }});

  function updateActiveNav() {{
    const scrollY = window.scrollY + 100;
    let current = null;

    for (let i = headingEls.length - 1; i >= 0; i--) {{
      if (headingEls[i].el.offsetTop <= scrollY) {{
        current = headingEls[i];
        break;
      }}
    }}

    navLinks.forEach(l => l.classList.remove('active'));
    if (current) {{
      current.link.classList.add('active');
      expandParents(current.link);
      current.link.scrollIntoView({{ block: 'nearest' }});
    }}
  }}

  // --- Search ---
  let searchTimer;
  let selectedIndex = -1;
  let currentResults = [];

  searchInput.addEventListener('input', function() {{
    clearTimeout(searchTimer);
    searchTimer = setTimeout(doSearch, 200);
  }});

  function navigateToResult(item) {{
    closeSearch();
    searchInput.blur();
    setTimeout(function() {{
      const target = document.getElementById(item.id);
      if (target) {{
        target.scrollIntoView();
        history.replaceState(null, '', '#' + item.id);
        target.classList.add('highlight-target');
        setTimeout(function() {{ target.classList.remove('highlight-target'); }}, 2500);
      }}
    }}, 160);
  }}

  function updateFocus() {{
    const items = searchResults.querySelectorAll('.search-result');
    items.forEach((el, i) => el.classList.toggle('focused', i === selectedIndex));
    if (items[selectedIndex]) {{
      items[selectedIndex].scrollIntoView({{ block: 'nearest' }});
    }}
  }}

  searchInput.addEventListener('keydown', function(e) {{
    const count = currentResults.length;
    if (!count) return;

    if (e.key === 'ArrowDown') {{
      e.preventDefault();
      selectedIndex = Math.min(selectedIndex + 1, count - 1);
      updateFocus();
    }} else if (e.key === 'ArrowUp') {{
      e.preventDefault();
      selectedIndex = Math.max(selectedIndex - 1, 0);
      updateFocus();
    }} else if (e.key === 'Enter' && selectedIndex >= 0) {{
      e.preventDefault();
      navigateToResult(currentResults[selectedIndex].item);
    }}
  }});

  function doSearch() {{
    const query = searchInput.value.trim();
    searchResults.innerHTML = '';
    selectedIndex = -1;

    if (query.length < 2) {{
      searchCount.textContent = '';
      currentResults = [];
      pendingQuery = '';
      return;
    }}

    pendingQuery = query;

    if (!searchReady) {{
      searchCount.textContent = 'Index wird aufgebaut…';
      return;
    }}

    searchCount.textContent = 'Suche…';
    searchWorker.postMessage({{ type: 'search', query: normalizeForSearch(query) }});
  }}

  function renderSearchResults(hits, query) {{
    searchResults.innerHTML = '';
    selectedIndex = -1;
    currentResults = hits.map(function(idx) {{ return {{ item: searchIndex[idx] }}; }});
    searchCount.textContent = currentResults.length + ' Treffer';

    if (currentResults.length === 0) {{
      const noRes = document.createElement('div');
      noRes.className = 'search-no-results';
      noRes.textContent = 'Keine Treffer gefunden.';
      searchResults.appendChild(noRes);
      return;
    }}

    currentResults.forEach(function(r) {{
      const item = r.item;
      const div = document.createElement('div');
      div.className = 'search-result';
      div.addEventListener('click', function() {{
        navigateToResult(item);
      }});

      const titleDiv = document.createElement('div');
      titleDiv.className = 'search-result-title';
      titleDiv.textContent = item.title;
      div.appendChild(titleDiv);

      const snippet = buildSnippet(item.text, query);
      const snippetDiv = document.createElement('div');
      snippetDiv.className = 'search-result-snippet';
      snippetDiv.innerHTML = snippet;
      div.appendChild(snippetDiv);

      searchResults.appendChild(div);
    }});
  }}

  function buildSnippet(text, query) {{
    if (!text) return '';
    const normText = normalizeForSearch(text);
    const normQuery = normalizeForSearch(query);
    const idx = normText.indexOf(normQuery);

    let start, end;
    if (idx >= 0) {{
      start = Math.max(0, idx - 50);
      end = Math.min(text.length, idx + query.length + 110);
    }} else {{
      start = 0;
      end = Math.min(text.length, 160);
    }}

    let snippet = (start > 0 ? '...' : '') + text.slice(start, end) + (end < text.length ? '...' : '');
    const escaped = query.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&');
    snippet = snippet.replace(new RegExp('(' + escaped + ')', 'gi'), '<mark>$1</mark>');
    return snippet;
  }}

  // Close search/nav with Escape
  document.addEventListener('keydown', function(e) {{
    if (e.key === 'Escape') {{
      if (searchPanel.classList.contains('open')) {{
        closeSearch();
        searchInput.blur();
      }} else if (sidebar.classList.contains('open')) {{
        closeNav();
      }}
    }}
    if ((e.ctrlKey || e.metaKey) && e.key === 'f') {{
      e.preventDefault();
      openSearch();
      searchInput.focus();
      searchInput.select();
    }}
  }});

  // --- Resize handles ---
  function initResize(handleId, panel, cssVar, side) {{
    const handle = document.getElementById(handleId);
    if (!handle) return;
    let startX, startWidth;

    handle.addEventListener('mousedown', function(e) {{
      e.preventDefault();
      startX = e.clientX;
      startWidth = panel.getBoundingClientRect().width;
      handle.classList.add('active');
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';

      function onMove(e) {{
        let delta = e.clientX - startX;
        if (side === 'right') delta = -delta;
        const newWidth = Math.max(180, Math.min(window.innerWidth * 0.5, startWidth + delta));
        panel.style.width = newWidth + 'px';
        document.documentElement.style.setProperty(cssVar, newWidth + 'px');
      }}

      function onUp() {{
        handle.classList.remove('active');
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
      }}

      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onUp);
    }});
  }}

  initResize('nav-resize', sidebar, '--nav-width', 'left');
  initResize('search-resize', searchPanel, '--search-width', 'right');

  // --- Link-Hover Tooltips ---
  (function initTooltips() {{
    if ('ontouchstart' in window && !window.matchMedia('(hover: hover)').matches) return;

    var mainContent = document.getElementById('main-content');
    if (!mainContent) return;

    var tooltip = document.createElement('div');
    tooltip.className = 'link-tooltip';
    tooltip.id = 'link-tooltip';
    tooltip.setAttribute('role', 'tooltip');
    tooltip.setAttribute('aria-hidden', 'true');
    tooltip.innerHTML = '<div class="link-tooltip-title"></div>'
      + '<div class="link-tooltip-body"></div>'
      + '<div class="link-tooltip-fade"></div>';
    document.body.appendChild(tooltip);

    var tooltipTitle = tooltip.querySelector('.link-tooltip-title');
    var tooltipBody = tooltip.querySelector('.link-tooltip-body');
    var tooltipFade = tooltip.querySelector('.link-tooltip-fade');

    var showTimer = null;
    var hideTimer = null;
    var currentLink = null;
    var resizing = false;
    var cache = {{}};

    var navResize = document.getElementById('nav-resize');
    var searchResize = document.getElementById('search-resize');
    if (navResize) navResize.addEventListener('mousedown', function() {{ resizing = true; }});
    if (searchResize) searchResize.addEventListener('mousedown', function() {{ resizing = true; }});
    document.addEventListener('mouseup', function() {{ resizing = false; }});

    function extractContent(targetId) {{
      if (targetId in cache) return cache[targetId];

      var el = document.getElementById(targetId);
      if (!el || !/^H[1-6]$/.test(el.tagName)) {{
        cache[targetId] = null;
        return null;
      }}

      var title = el.textContent.trim();
      var level = parseInt(el.tagName[1], 10);
      var bodyHTML = '';
      var charCount = 0;
      var elCount = 0;
      var sib = el.nextElementSibling;

      while (sib && elCount < 3) {{
        if (sib.tagName === 'HR') {{ sib = sib.nextElementSibling; continue; }}
        var sibMatch = sib.tagName.match(/^H([1-6])$/);
        if (sibMatch && parseInt(sibMatch[1], 10) <= level) break;
        if (sibMatch) break;

        var html = sib.outerHTML;
        var text = sib.textContent || '';

        if (sib.tagName === 'TABLE') {{
          var thead = sib.querySelector('thead');
          var rows = sib.querySelectorAll('tbody tr');
          var tableHTML = '<table>';
          if (thead) tableHTML += thead.outerHTML;
          tableHTML += '<tbody>';
          for (var r = 0; r < Math.min(2, rows.length); r++) {{
            tableHTML += rows[r].outerHTML;
          }}
          if (rows.length > 2) {{
            tableHTML += '<tr><td colspan="99">…</td></tr>';
          }}
          tableHTML += '</tbody></table>';
          html = tableHTML;
          text = sib.textContent.slice(0, 100);
        }}

        charCount += text.length;
        if (charCount > 300 && elCount > 0) break;

        bodyHTML += html;
        elCount++;
        if (charCount > 300) break;
        sib = sib.nextElementSibling;
      }}

      var result = bodyHTML ? {{ title: title, bodyHTML: bodyHTML }} : null;
      cache[targetId] = result;
      return result;
    }}

    function positionTooltip(linkRect) {{
      var gap = 8;
      var margin = 12;
      var footerH = 30;
      var tw = tooltip.offsetWidth;
      var th = tooltip.offsetHeight;

      var left = linkRect.left + linkRect.width / 2 - tw / 2;
      left = Math.max(margin, Math.min(left, window.innerWidth - tw - margin));

      var top = linkRect.bottom + gap;
      if (top + th > window.innerHeight - footerH - margin) {{
        top = linkRect.top - gap - th;
        if (top < margin) top = margin;
      }}

      tooltip.style.left = left + 'px';
      tooltip.style.top = top + 'px';
    }}

    function showTooltip(link) {{
      var href = link.getAttribute('href');
      if (!href || href.charAt(0) !== '#') return;
      var targetId = href.slice(1);
      if (!targetId) return;

      var data = extractContent(targetId);
      if (!data) return;

      tooltipTitle.textContent = data.title;
      tooltipBody.innerHTML = data.bodyHTML;

      positionTooltip(link.getBoundingClientRect());

      var bodyOverflows = tooltipBody.scrollHeight > tooltipBody.clientHeight;
      tooltipFade.style.display = bodyOverflows ? '' : 'none';

      tooltip.classList.add('visible');
      tooltip.setAttribute('aria-hidden', 'false');
      link.setAttribute('aria-describedby', 'link-tooltip');
    }}

    function hideTooltip() {{
      tooltip.classList.remove('visible');
      tooltip.setAttribute('aria-hidden', 'true');
      if (currentLink) {{
        currentLink.removeAttribute('aria-describedby');
      }}
      currentLink = null;
    }}

    function clearTimers() {{
      if (showTimer) {{ clearTimeout(showTimer); showTimer = null; }}
      if (hideTimer) {{ clearTimeout(hideTimer); hideTimer = null; }}
    }}

    function findAnchorLink(el) {{
      while (el && el !== mainContent) {{
        if (el.tagName === 'A' && el.getAttribute('href')
            && el.getAttribute('href').charAt(0) === '#') {{
          return el;
        }}
        el = el.parentElement;
      }}
      return null;
    }}

    mainContent.addEventListener('mouseover', function(e) {{
      if (resizing) return;
      var link = findAnchorLink(e.target);
      if (!link) return;
      if (link === currentLink) return;

      clearTimers();
      if (tooltip.classList.contains('visible')) hideTooltip();
      currentLink = link;

      showTimer = setTimeout(function() {{
        showTooltip(link);
      }}, 500);
    }});

    mainContent.addEventListener('mouseout', function(e) {{
      var link = findAnchorLink(e.target);
      if (!link && !tooltip.contains(e.target)) return;

      var related = e.relatedTarget;
      if (related && link && link.contains(related)) return;
      if (related && tooltip.contains(related)) return;
      if (related && findAnchorLink(related) === currentLink) return;

      clearTimers();
      hideTimer = setTimeout(hideTooltip, 150);
    }});

    tooltip.addEventListener('mouseenter', function() {{
      if (hideTimer) {{ clearTimeout(hideTimer); hideTimer = null; }}
    }});

    tooltip.addEventListener('mouseleave', function(e) {{
      var related = e.relatedTarget;
      if (related && findAnchorLink(related) === currentLink) return;
      clearTimers();
      hideTimer = setTimeout(hideTooltip, 150);
    }});

    window.addEventListener('scroll', function() {{
      if (tooltip.classList.contains('visible')) {{
        clearTimers();
        hideTooltip();
      }}
    }}, {{ passive: true }});

    document.addEventListener('keydown', function(e) {{
      if (e.key === 'Escape' && tooltip.classList.contains('visible')) {{
        clearTimers();
        hideTooltip();
      }}
    }});
  }})();

  // Initial scroll spy
  updateActiveNav();
}})();
"""


def build_html(body_html: str, nav_html: str, css: str, js: str,
               worker_js: str, title: str, logo_b64: str) -> str:
    esc_title = html.escape(title)
    return f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta http-equiv="content-language" content="de">
  <meta name="google" content="notranslate">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc_title}</title>
  <style>
{css}
  </style>
</head>
<body>

<button id="nav-toggle" aria-label="Navigation">&#9776;</button>

<div id="search-field">
  <span id="search-field-icon">&#128269;</span>
  <input type="search" id="search-input" placeholder="Suche im Regelwerk..." autocomplete="off">
</div>

{nav_html}
<div id="nav-resize"></div>

<div id="search-resize"></div>
<div id="search-panel">
  <div id="search-panel-header">
    <span>Suchergebnisse</span>
    <button id="search-close" aria-label="Suche schliessen">&times;</button>
  </div>
  <div id="search-count"></div>
  <div id="search-results"></div>
</div>

<main id="main-content">
{body_html}
</main>

<footer id="page-footer">
  <a href="https://atlas-games.com/arsmagica/openars">Ars Magica Open License</a> &middot;
  <a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a> &middot;
  &copy;1993–2024 Trident, Inc. d/b/a Atlas Games&reg; &middot;
  Ars Magica, Mythic Europe &trade; Trident, Inc. &middot;
  Order of Hermes, Tremere, Doissetep, Grimgroth &trade; Paradox Interactive AB
</footer>

<script id="search-worker-script" type="text/js-worker">
{worker_js}
</script>
<script>
{js}
</script>
</body>
</html>
"""


def process(input_dir: str, output_dir: str,
            files: list[str] | None = None) -> None:
    fuse_path = SCRIPT_DIR / "fuse.min.js"
    if not fuse_path.is_file():
        print(f"Fehler: fuse.min.js nicht gefunden in {SCRIPT_DIR}", file=sys.stderr)
        sys.exit(1)

    fuse_js = fuse_path.read_text(encoding="utf-8")
    worker_js = get_worker_js(fuse_js)

    logo_path = Path(input_dir).parent / "arm5openlicenselogo.png"
    if logo_path.is_file():
        logo_b64 = base64.b64encode(logo_path.read_bytes()).decode("ascii")
    else:
        logo_b64 = ""
        print(f"Warnung: Logo nicht gefunden: {logo_path}", file=sys.stderr)

    if files:
        md_files = []
        for f in files:
            p = Path(f)
            if not p.is_file():
                print(f"Fehler: Datei nicht gefunden: {f}", file=sys.stderr)
                sys.exit(1)
            if p.suffix.lower() != ".md":
                print(f"Fehler: Keine Markdown-Datei: {f}", file=sys.stderr)
                sys.exit(1)
            md_files.append(p)
    else:
        md_files = sorted(Path(input_dir).glob("*.md"))

    if not md_files:
        print(f"Keine .md-Dateien in {input_dir} gefunden.", file=sys.stderr)
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    for md_file in md_files:
        print(f"Verarbeite: {md_file.name}")

        body_html = pandoc_to_html(md_file)
        nav_tree, search_index = extract_nav_and_index(body_html)

        print(f"  Navigation: {len(nav_tree)} Einträge")
        print(f"  Suchindex:  {len(search_index)} Abschnitte")

        nav_html = build_nav_html(nav_tree, logo_b64)
        search_index_json = json.dumps(search_index, ensure_ascii=False)

        title = md_file.stem
        if "Deutsch" in title:
            title = title.replace(" Deutsch", "")

        css = get_css()
        js = get_js(search_index_json)
        full_html = build_html(body_html, nav_html, css, js, worker_js, title, logo_b64)

        out_path = Path(output_dir) / (md_file.stem + ".html")
        out_path.write_text(full_html, encoding="utf-8")

        size_mb = out_path.stat().st_size / (1024 * 1024)
        print(f"  Ausgabe:    {out_path} ({size_mb:.1f} MB)")

    print("\nFertig.")


def main():
    parser = argparse.ArgumentParser(
        description="Konvertiert deutsche Ars-Magica-Regelwerke nach HTML."
    )
    parser.add_argument(
        "--input-dir", "-i", default="german-ordered",
        help="Eingabeverzeichnis mit Markdown-Dateien",
    )
    parser.add_argument(
        "--output-dir", "-o", default="german-html",
        help="Ausgabeverzeichnis für HTML-Dateien",
    )
    parser.add_argument(
        "files", nargs="*",
        help="Einzelne Markdown-Dateien (optional). Ohne Angabe: alle .md in --input-dir.",
    )
    args = parser.parse_args()

    if not args.files and not os.path.isdir(args.input_dir):
        print(f"Fehler: Verzeichnis nicht gefunden: {args.input_dir}", file=sys.stderr)
        sys.exit(1)

    process(args.input_dir, args.output_dir, args.files or None)


if __name__ == "__main__":
    main()
