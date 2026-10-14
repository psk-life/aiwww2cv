# -*- coding: utf-8 -*-
"""Форматирование резюме из промежуточного JSON в стиль и выходные форматы
.txt / .md / .json / .html."""

import html as html_lib
import json
import re
from datetime import datetime, timezone

from parser import BULLET_RE
from styles import (
    STYLES_BY_ID,
    ONE_PAGE_KEEP_SHORT, ONE_PAGE_MAX_ABOUT_CHARS, ONE_PAGE_MAX_ABOUT_LINES,
    ONE_PAGE_MAX_SKILLS, ONE_PAGE_MAX_EXPERIENCE_LINES, ONE_PAGE_MAX_EDU_LINES,
    ONE_PAGE_MAX_CONTACTS,
)

JOB_HEADER_RE = re.compile(r"(\d{4}|[а-яё]+\s*\d{4})", re.I)


def build_styled_json(parsed: dict, style_id: str) -> dict:
    """Переформатирует промежуточный JSON в новый JSON по выбранному стилю."""
    style = STYLES_BY_ID[style_id]
    by_id = {s["id"]: s for s in parsed["sections"]}
    out_sections = []

    for sid in style["sections"]:
        sec = by_id.get(sid)
        if not sec:
            continue
        content = list(sec["content"])
        if style.get("one_page"):
            content = _trim_one_page(sid, content)
        if content:
            out_sections.append({"id": sid, "title": sec["title"],
                                 "content": content})

    return {
        "meta": {
            "style_id": style["id"],
            "style_name": style["name"],
            "site": style["site"],
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "source_file": parsed["source"]["filename"],
            "source_format": parsed["source"]["format"],
            "one_page": bool(style.get("one_page")),
            "print_spec": style.get("print_spec"),
        },
        "resume": out_sections,
    }


def _trim_one_page(sid: str, content: list) -> list:
    """Обрезает содержимое до «главной сути» для стиля 1 страницы A4/Legal."""
    if sid in ONE_PAGE_KEEP_SHORT:
        if sid == "contacts":
            return content[:ONE_PAGE_MAX_CONTACTS]
        return content
    if sid == "about":
        lines, chars = [], 0
        for line in content:
            if len(lines) >= ONE_PAGE_MAX_ABOUT_LINES or chars >= ONE_PAGE_MAX_ABOUT_CHARS:
                break
            lines.append(line)
            chars += len(line)
        return lines
    if sid == "skills":
        return content[:ONE_PAGE_MAX_SKILLS]
    if sid == "education":
        return content[:ONE_PAGE_MAX_EDU_LINES]
    if sid == "experience":
        entries = _split_experience_entries(content)
        if entries:
            last = _pick_latest_entry(entries)
            return last[:ONE_PAGE_MAX_EXPERIENCE_LINES]
        return content[-ONE_PAGE_MAX_EXPERIENCE_LINES:]
    return content[:2]


def _pick_latest_entry(entries: list) -> list:
    """Выбирает самую актуальную запись опыта:
    текущая работа (н.в./present) или запись с максимальным годом."""
    def score(entry):
        text = " ".join(entry).lower()
        if re.search(r"н\.?\s*в\.|present|по\s*сей|текущ", text):
            return (2, 0)
        years = [int(y) for y in re.findall(r"\b(?:19|20)\d{2}\b", text)]
        return (1, max(years) if years else 0)
    return max(entries, key=score)


def _split_experience_entries(content: list) -> list:
    """Группирует строки опыта на «записи» по заголовкам с годами/боллетам."""
    entries, current = [], []
    for line in content:
        looks_header = bool(JOB_HEADER_RE.search(line)) and len(line) < 120
        starts_bullet = bool(BULLET_RE.match(line))
        if (looks_header or starts_bullet) and current:
            if looks_header:
                entries.append(current)
                current = []
        current.append(line)
    if current:
        entries.append(current)
    return entries


# ---------------------------------------------------------------- .txt

def render_txt(data: dict) -> str:
    meta = data["meta"]
    lines = ["=" * 56,
             f"{meta['style_name']} — оптимизировано для {meta['site']}",
             f"Сформировано: {meta['generated_at']}",
             "=" * 56]
    for sec in data["resume"]:
        lines.append("")
        lines.append(sec["title"].upper())
        lines.append("-" * 56)
        for item in sec["content"]:
            if BULLET_RE.match(item):
                item = re.sub(r"^[\s]*[-*•▪◦+] ", "", item)
                item = re.sub(r"^\s*\d+[.)]\s", "", item)
                lines.append(f"• {item}")
            else:
                lines.append(item)
    lines.append("")
    lines.append("=" * 56)
    return "\n".join(lines)


# ---------------------------------------------------------------- .md

def render_md(data: dict) -> str:
    meta = data["meta"]
    parts = [f"# {meta['style_name']}",
             f"*{meta['site']} — сформировано {meta['generated_at']}*", ""]
    for sec in data["resume"]:
        if sec["id"] == "fio":
            # ФИО — заголовок первого уровня
            parts.append(f"# {sec['content'][0]}")
            parts.extend(f"- {x}" for x in sec["content"][1:])
            parts.append("")
            continue
        if sec["id"] == "position":
            # должность — подпись под именем
            parts.append(f"**{sec['content'][0]}**")
            parts.extend(f"- {x}" for x in sec["content"][1:])
            parts.append("")
            continue
        parts.append(f"## {sec['title']}")
        for item in sec["content"]:
            if BULLET_RE.match(item):
                parts.append(item)
            else:
                parts.append(f"- {item}")
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


# ---------------------------------------------------------------- .html

FONT_STACK = ("'Inter', 'DejaVu Sans', 'Liberation Sans', 'Segoe UI', "
              "system-ui, -apple-system, Arial, sans-serif")


def render_html(data: dict) -> str:
    meta = data["meta"]
    one_page = meta.get("one_page")
    name = ""
    position = ""
    for sec in data["resume"]:
        if sec["id"] == "fio" and sec["content"]:
            name = sec["content"][0]
        if sec["id"] == "position" and sec["content"]:
            position = sec["content"][0]

    e = html_lib.escape
    head_parts, sec_parts = [], []
    if name:
        head_parts.append(f"      <h1>{e(name)}</h1>")
    if position:
        head_parts.append(f"      <p class=\"tagline\">{e(position)}</p>")
    for sec in data["resume"]:
        if sec["id"] == "fio":
            rest = sec["content"][1:]
            if rest:
                sec_parts.append(f"      <section aria-labelledby='s-{sec['id']}'>")
                sec_parts.append(f"        <h2 id='s-{sec['id']}'>{e(sec['title'])}</h2>")
                sec_parts.append("        <ul>")
                sec_parts.extend(f"          <li>{e(i)}</li>" for i in rest)
                sec_parts.append("        </ul>")
                sec_parts.append("      </section>")
            continue
        sec_parts.append(f"      <section aria-labelledby='s-{sec['id']}'>")
        sec_parts.append(f"        <h2 id='s-{sec['id']}'>{e(sec['title'])}</h2>")
        if sec["id"] == "contacts":
            sec_parts.append("        <address>")
            sec_parts.extend(f"          <p>{e(i)}</p>" for i in sec["content"])
            sec_parts.append("        </address>")
        else:
            sec_parts.append("        <ul>")
            sec_parts.extend(f"          <li>{e(i)}</li>" for i in sec["content"])
            sec_parts.append("        </ul>")
        sec_parts.append("      </section>")

    print_css = ""
    if one_page:
        print_css = """
  @page { size: A4; margin: 14mm; }
  body { font-size: 12pt; line-height: 1.5; }
  @media print {
    body { font-size: 12pt; line-height: 1.5; }
    section { break-inside: avoid; }
  }"""

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(name or 'Резюме')} — {e(meta['style_name'])}</title>
<style>
  :root {{
    --bg: #0E1117; --card: #151B26; --text: #EDF1FA; --muted: #A9B4CC;
    --blue: #7D8BFF; --teal: #57D6C2; --amber: #F2B544;
  }}
  html {{ font-family: {FONT_STACK}; }}
  body {{
    margin: 0; background: var(--bg); color: var(--text);
    font-size: 16px; line-height: 1.6;
    padding: 1.5rem clamp(1rem, 4vw, 3rem);
  }}
  h1 {{ color: var(--blue); font-size: 1.7rem; margin: 0 0 .25rem; }}
  .tagline {{ color: var(--teal); margin: 0 0 1.5rem; font-size: 1.05rem; }}
  h2 {{
    color: var(--amber); font-size: 1.05rem; text-transform: uppercase;
    letter-spacing: .06em; border-bottom: 2px solid var(--teal);
    padding-bottom: .25rem; margin: 1.5rem 0 .6rem;
  }}
  ul {{ margin: 0; padding-left: 1.25rem; }}
  li {{ margin: .15rem 0; }}
  address {{ font-style: normal; }}
  address p {{ margin: .1rem 0; color: var(--muted); }}
  .meta {{
    color: var(--muted); font-size: .8rem; margin-top: 2rem;
    border-top: 1px solid #2A3345; padding-top: .75rem;
  }}{print_css}
</style>
</head>
<body>
  <header>
{chr(10).join(head_parts)}
  </header>
  <main>
{chr(10).join(sec_parts)}
  </main>
  <footer class="meta">
    <p>Стиль: {e(meta['style_name'])} · {e(meta['site'])} ·
       Источник: {e(meta['source_file'])} ·
       Сформировано: {e(meta['generated_at'])}</p>
    <p>Шрифт: Inter / DejaVu Sans (SIL OFL — бесплатная коммерческая лицензия).</p>
  </footer>
</body>
</html>
"""


def render_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"
