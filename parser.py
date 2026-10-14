# -*- coding: utf-8 -*-
"""Парсер резюме из .txt / .md / .pdf.

Определяет разделы резюме по заголовкам (пишем промежуточный JSON),
извлекает ФИО и контакты. Поддерживает кириллицу и латынь.
"""

import re

# Сопоставление: id секции -> (русское название, варианты заголовков)
SECTION_ALIASES = {
    "fio": ("ФИО", [
        "ф.и.о.", "фио", "фамилия и имя", "имя и фамилия",
        "full name", "name", "фамилия, имя",
    ]),
    "position": ("Желаемая должность / позиция", [
        "желаемая должность", "желаемая позиция", "желаемое направление",
        "должность", "позиция", "специализация", "профессия",
        "целевое направление", "направление", "role",
        "desired position", "desired role", "target position",
        "job title", "position", "title", "career objective",
    ]),
    "contacts": ("Контакты", [
        "контакты", "контактная информация", "контактные данные",
        "связь", "contact", "contacts", "contact info",
        "contact information",
    ]),
    "about": ("О себе / краткое саммари", [
        "о себе", "самоописание", "личное описание", "профиль",
        "краткая информация", "кратко о себе", "резюме",
        "about me", "summary", "professional summary", "profile",
        "personal summary", "objective",
    ]),
    "experience": ("Опыт работы", [
        "опыт работы", "опыт", "трудовая деятельность", "места работы",
        "карьера", "work experience", "experience",
        "employment history", "career history",
        "professional experience", "work history",
    ]),
    "education": ("Образование", [
        "образование", "education", "educational background",
        "учебные заведения",
    ]),
    "skills": ("Навыки", [
        "навыки", "умения", "ключевые навыки", "профессиональные навыки",
        "ключевые умения", "skills", "key skills", "technical skills",
        "competencies", "professional skills",
    ]),
    "languages": ("Языки", [
        "языки", "знание языков", "foreign languages", "languages",
        "language skills", "иностранные языки",
    ]),
    "courses": ("Курсы и сертификаты", [
        "курсы", "повышение квалификации", "сертификаты", "сертификация",
        "courses", "certifications", "certificates", "training",
    ]),
    "achievements": ("Достижения", [
        "достижения", "achievements", "accomplishments", "awards",
    ]),
    "portfolio": ("Портфолио и ссылки", [
        "портфолио", "ссылки", "portfolio", "links", "projects",
    ]),
    "additional": ("Дополнительная информация", [
        "дополнительная информация", "дополнительно", "примечания",
        "additional information", "notes", "additional info",
    ]),
}

NAME_RE = re.compile(
    r"^[А-ЯЁ][А-ЯЁа-яё]{1,}(?:[- ][А-ЯЁ][А-ЯЁа-яё]{1,}){1,3}$"
)
LATIN_NAME_RE = re.compile(
    r"^[A-Z][A-Za-z]+(?:[-'][A-Z][A-Za-z]+)?"
    r"(?: [A-Z][A-Za-z]+(?:[-'][A-Z][A-Za-z]+)?){1,2}(?: [A-Z]\.?)?$"
)
EMAIL_RE = re.compile(r"[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}", re.I)
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s\-]?)?(?:\(?\d{3}\)?[\s\-]?){1,2}\d{2}[\s\-]?\d{2}(?:[\s\-]?\d{2})?", re.I)
TELEGRAM_RE = re.compile(r"(?:telegram|тг)[:\s]*@?[a-z_][a-z0-9_]{4,}", re.I)
SKYPE_RE = re.compile(r"skype[:\s]*[a-z0-9._\-]{4,}", re.I)
URL_RE = re.compile(r"https?://[^\s,;)\"']+", re.I)
BULLET_RE = re.compile(r"^[\s]*[-*•▪◦+] |^\s*\d+[.)]\s")
HEADING_MD_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")


def _norm(line: str) -> str:
    s = line.strip().strip("═—–-").strip()
    s = s.rstrip(":.").strip().lower()
    return re.sub(r"\s+", " ", s)


def _match_section(line: str):
    """Возвращает (section_id, rest) если строка — заголовок раздела."""
    norm = _norm(line)
    if not norm:
        return None
    for sid, (_title, aliases) in SECTION_ALIASES.items():
        for alias in aliases:
            if norm == alias:
                return sid, ""
            # заголовок с inline-содержимым, напр. «Должность: инженер»
            if norm.startswith(alias + " ") and len(norm) - len(alias) < 80:
                return sid, line.split(":", 1)[1].strip() if ":" in line else line[len(alias):].strip()
            if norm.startswith(alias + ":") and len(norm) - len(alias) < 80:
                return sid, line.split(":", 1)[1].strip()
    return None


def _strip_bullet(line: str) -> str:
    """Убирает маркер markdown/списка из начала строки."""
    s = re.sub(r"^[-*•▪◦+]\s+", "", line)
    return re.sub(r"^\d{1,2}[.)]\s+", "", s)


def _split_md(text: str):
    """Разбор markdown: заголовки # / ##, списки, абзацы."""
    sections = {}
    current = None
    lines = text.splitlines()
    for raw in lines:
        m = HEADING_MD_RE.match(raw)
        if m:
            hit = _match_section(m.group(2))
            if hit:
                current = hit[0]
                sections.setdefault(current, [])
                rest = hit[1]
                if rest:
                    sections[current].append(rest)
                continue
        if current:
            stripped = _strip_bullet(raw.strip())
            if stripped:
                sections[current].append(stripped)
    # h1 в начале файла — часто ФИО (markdown-резюме)
    if lines:
        first = HEADING_MD_RE.match(lines[0])
        if first and not _match_section(first.group(2)):
            cand = first.group(2).strip()
            if NAME_RE.match(cand) or LATIN_NAME_RE.match(cand):
                sections.setdefault("fio", []).insert(0, cand)
    return sections


def _split_plain(text: str):
    """Разбор plain text: строки-заголовки разделов."""
    sections = {}
    current = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        hit = _match_section(line)
        if hit:
            current = hit[0]
            sections.setdefault(current, [])
            if hit[1]:
                sections[current].append(hit[1])
            continue
        if current:
            sections[current].append(line.strip())
    return sections


def _find_contacts(text: str):
    found = []
    for m in EMAIL_RE.finditer(text):
        found.append("email: " + m.group(0))
    for m in PHONE_RE.finditer(text):
        digits = re.sub(r"\D", "", m.group(0))
        if 7 <= len(digits) <= 15:
            found.append("телефон: " + m.group(0).strip())
    for m in TELEGRAM_RE.finditer(text):
        found.append("telegram: " + m.group(0).split(":", 1)[1].strip())
    for m in SKYPE_RE.finditer(text):
        found.append("skype: " + m.group(0).split(":", 1)[1].strip())
    for m in URL_RE.finditer(text):
        found.append(m.group(0))
    # дедупликация с сохранением порядка
    seen = set()
    out = []
    for c in found:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def _find_name(sections, text: str):
    if "fio" in sections and sections["fio"]:
        return sections["fio"][0].lstrip(":- ").strip()
    for line in text.splitlines()[:6]:
        line = line.strip().lstrip("#").strip()
        if 3 <= len(line) <= 60 and (NAME_RE.match(line) or LATIN_NAME_RE.match(line)):
            return line
    return ""


def parse_resume(text: str, fmt: str) -> dict:
    """Возвращает структуру разделов резюме (промежуточное представление)."""
    text = text.replace(" ", " ").replace("\r\n", "\n").replace("\u200b", "")
    if fmt == "md":
        sections = _split_md(text)
    else:
        sections = _split_plain(text)

    # если ни один раздел не распознан — складываем всё в about
    if not sections:
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if lines:
            sections["about"] = lines

    contacts = _find_contacts(text)
    if contacts and "contacts" not in sections:
        sections["contacts"] = contacts

    name = _find_name(sections, text)

    # ФИО найдено вне явного раздела — добавляем его первым
    if name and "fio" not in sections:
        sections["fio"] = [name]

    result_sections = []
    for sid, (_title, _aliases) in SECTION_ALIASES.items():
        if sid in sections and sections[sid]:
            result_sections.append({"id": sid, "title": _title,
                                    "content": sections[sid]})

    return {
        "name": name,
        "sections": result_sections,
        "detected_contacts": contacts,
        "stats": {"chars": len(text), "lines": len(text.splitlines()),
                  "sections_found": len(result_sections)},
    }
