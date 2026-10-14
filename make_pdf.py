# -*- coding: utf-8 -*-
"""Генерация тестового PDF-резюме (кириллица через встроенный шрифт)."""
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# Подбор бесплатного шрифта с кириллицей на Windows
candidates = [
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\times.ttf",
    r"C:\Windows\Fonts\calibri.ttf",
]
font_name = "Helvetica"
for path in candidates:
    if os.path.exists(path):
        try:
            pdfmetrics.registerFont(TTFont("Cyril", path))
            font_name = "Cyril"
            break
        except Exception:
            continue

text_lines = [
    "СМИРНОВ ДМИТРИЙ ОЛЕГОВИЧ",
    "Желаемая должность: DevOps-инженер",
    "",
    "КОНТАКТЫ",
    "email: d.smirnov@example.net",
    "телефон: +7 926 333-44-55",
    "telegram: @dsmirnov",
    "город: Казань",
    "",
    "О СЕБЕ",
    "DevOps с 6 годами опыта. Kubernetes, Terraform, CI/CD.",
    "",
    "ОПЫТ РАБОТЫ",
    "2020-н.в. - ООО «Облако Сервис», DevOps-инженер",
    "- инфраструктура как код на Terraform",
    "- кластеры Kubernetes, SRE-практики",
    "2017-2020 - АО «Системы», системный администратор",
    "- поддержка серверной инфраструктуры",
    "",
    "ОБРАЗОВАНИЕ",
    "2013-2017 - КФУ, информационные системы",
    "",
    "НАВЫКИ",
    "Kubernetes, Docker, Terraform, AWS, Linux, Ansible, GitLab CI, Prometheus, Python",
    "",
    "ЯЗЫКИ",
    "Русский - родной; Английский - B1",
]

c = canvas.Canvas("test_resume.pdf", pagesize=A4)
c.setFont(font_name, 11)
y = 800
for line in text_lines:
    c.drawString(50, y, line)
    y -= 16
c.save()
print("test_resume.pdf written with font:", font_name)
