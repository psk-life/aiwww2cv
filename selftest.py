# -*- coding: utf-8 -*-
"""Быстрый самотест парсера и рендереров."""
from parser import parse_resume
from renderers import build_styled_json, render_txt, render_md, \
    render_html, render_json

sample = """ИВАНОВ ИВАН ИВАНОВИЧ
Желаемая должность: старший инженер

КОНТАКТЫ
email: ivanov@example.com
телефон: +7 (921) 555-43-21
telegram: @ivanov_dev
город: Санкт-Петербург

О СЕБЕ
Опытный инженер с 8 годами опыта в разработке.
Знаю Python, Go, PostgreSQL.

ОПЫТ РАБОТЫ
2020—н.в. — ООО «Технократ», старший инженер
- проектирование нагруженных сервисов
- руководство группой из 5 человек
2016—2020 — АО «Промсвязь», инженер
- поддержка legacy-систем

ОБРАЗОВАНИЕ
2012—2016 — СПбГУ, факультет прикладной математики

НАВЫКИ
Python, Go, PostgreSQL, Docker, Kubernetes, Linux, Git, CI/CD, gRPC, Redis, Kafka

ЯЗЫКИ
Русский — родной
Английский — B2
"""

parsed = parse_resume(sample, "txt")
parsed["source"] = {"filename": "sample.txt", "format": "txt"}
print("=== PARSED ===")
print(render_json(parsed)[:700])

for sid in ("linkedin", "onepage", "hhru", "xing", "indeed",
            "glassdoor", "europass", "monster"):
    styled = build_styled_json(parsed, sid)
    print(f"=== STYLE: {sid} ===")
    print("sections:", [s["id"] for s in styled["resume"]])
    if sid == "onepage":
        print("print_spec:", styled["meta"]["print_spec"])
        html = render_html(styled)
        assert "font-size: 12pt" in html, "12pt missing"
        assert "line-height: 1.5" in html, "line-height 1.5 missing"
        assert "@page" in html, "@page missing"
        print("onepage HTML print constraints: OK")

print("=== TXT (onepage) ===")
print(render_txt(build_styled_json(parsed, "onepage")))
print("=== MD (linkedin) head ===")
print(render_md(build_styled_json(parsed, "linkedin"))[:420])
print("=== HTML (onepage) head ===")
print(render_html(build_styled_json(parsed, "onepage"))[:420])
