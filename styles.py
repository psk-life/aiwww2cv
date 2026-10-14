# -*- coding: utf-8 -*-
"""Определения стилей резюме для международных сайтов по подбору персонала.

Каждый стиль описывает:
- id            — машинное имя стиля (ключ формы);
- name / site   — отображаемое название и сайт, для которого он оптимизирован;
- sections      — порядок и состав секций итогового резюме;
- one_page      — флаг ограничения «1 страница A4/Legal, 12 pt, интерлиньяж 1.5»;
- print_spec    — спецификация печатного листа (для one_page стилей);
- features      — ключевые особенности стиля (краткое описание для UI).
"""

STYLES = [
    {
        "id": "linkedin",
        "name": "LinkedIn Modern",
        "site": "LinkedIn",
        "desc": "Профессиональный заголовок, акцент на навыках и саммари — формат ленты LinkedIn.",
        "features": ["headline + about", "навыки первыми", "ссылки/портфолио"],
        "sections": ["fio", "position", "contacts", "about", "experience",
                     "education", "skills", "languages", "courses", "portfolio"],
        "one_page": False,
    },
    {
        "id": "xing",
        "name": "Xing Klassik",
        "site": "Xing",
        "desc": "Сдержанная европейская структура: ФИО, должность, опыт, образование, навыки.",
        "features": ["классический порядок", "без лишних деталей", "де-юре стиль DACH"],
        "sections": ["fio", "position", "contacts", "experience", "education",
                     "skills", "languages", "about"],
        "one_page": False,
    },
    {
        "id": "hhru",
        "name": "hh.ru Профиль",
        "site": "hh.ru",
        "desc": "Формат карточки hh.ru: желаемая должность, ключевые навыки, опыт и контакты.",
        "features": ["ключевые навыки вначале", "желаемая позиция", "компактные блоки"],
        "sections": ["fio", "position", "skills", "experience", "about",
                     "education", "contacts", "languages"],
        "one_page": False,
    },
    {
        "id": "indeed",
        "name": "Indeed ATS",
        "site": "Indeed",
        "desc": "Максимально «плоский» текст для ATS-систем: чёткие заголовки разделов, без таблиц.",
        "features": ["ATS-friendly", "плоский текст", "ключевые слова в разделах"],
        "sections": ["fio", "position", "contacts", "about", "experience",
                     "education", "skills", "languages", "courses"],
        "one_page": False,
    },
    {
        "id": "glassdoor",
        "name": "Glassdoor Insight",
        "site": "Glassdoor",
        "desc": "Акцент на достижениях и саммари: сильное about, навыки и опыт с акцентом на результаты.",
        "features": ["summary-first", "достижения", "карьерный фокус"],
        "sections": ["fio", "position", "about", "achievements", "experience",
                     "skills", "education", "languages", "contacts"],
        "one_page": False,
    },
    {
        "id": "europass",
        "name": "Europass EU",
        "site": "Europass",
        "desc": "Стандарт Europass: строгий порядок разделов, языки и дополнительное образование.",
        "features": ["стандарт ЕС", "языки отдельным блоком", "курсы и сертификаты"],
        "sections": ["fio", "contacts", "position", "about", "experience",
                     "education", "courses", "skills", "languages"],
        "one_page": False,
    },
    {
        "id": "monster",
        "name": "Monster Career",
        "site": "Monster",
        "desc": "Универсальный стиль Monster: полное резюме с портфолио и дополнительной информацией.",
        "features": ["полный формат", "портфолио", "дополнительные сведения"],
        "sections": ["fio", "position", "contacts", "about", "experience",
                     "education", "skills", "languages", "courses",
                     "achievements", "portfolio", "additional"],
        "one_page": False,
    },
    {
        "id": "onepage",
        "name": "A4 One-Pager (12 pt / 1.5)",
        "site": "Универсальный печатный (A4/Legal)",
        "desc": "Строго 1 страница A4/Legal: шрифт 12 pt, межстрочный интервал 1.5. "
                "Сохраняются только ФИО, контакты и последняя актуальная информация.",
        "features": ["1 страница A4/Legal", "12 pt, интерлиньяж 1.5", "только суть + контакты + ФИО"],
        "sections": ["fio", "position", "contacts", "about", "experience",
                     "skills", "education"],
        "one_page": True,
        "print_spec": {"page": "A4 (Legal совместимо)", "font_size_pt": 12,
                       "line_height": 1.5, "max_pages": 1},
    },
]

STYLES_BY_ID = {s["id"]: s for s in STYLES}

# Секции, которые гарантированно сохраняются в «компактном» стиле (one page):
# только ФИО, контакты и главная суть.
ONE_PAGE_KEEP_SHORT = {"fio", "position", "contacts"}
ONE_PAGE_MAX_ABOUT_CHARS = 240
ONE_PAGE_MAX_ABOUT_LINES = 2
ONE_PAGE_MAX_SKILLS = 8
ONE_PAGE_MAX_EXPERIENCE_LINES = 6
ONE_PAGE_MAX_EDU_LINES = 2
ONE_PAGE_MAX_CONTACTS = 4
