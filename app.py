# -*- coding: utf-8 -*-
"""Конвертер резюме: загрузка .pdf/.txt/.md -> выбор стиля ->
выгрузка .txt/.md/.json/.html. Промежуточное хранение — JSON."""

import os
import re
import shutil
import time
import uuid
from pathlib import Path

from flask import (Flask, flash, redirect, render_template, request,
                   send_from_directory, url_for)

from parser import parse_resume
from styles import STYLES, STYLES_BY_ID
from renderers import build_styled_json, render_txt, render_md, \
    render_html, render_json

BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)

ALLOWED_EXT = {".pdf", ".txt", ".md"}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 МБ
TEMP_TTL = 2 * 3600  # жизни временных файлов, секунд

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
app.secret_key = os.environ.get("RESUME_SECRET", "dev-only-change-me")


def prune_temp():
    """Удаляет устаревшие временные папки конвертаций."""
    now = time.time()
    for d in TEMP_DIR.iterdir():
        if d.is_dir() and (now - d.stat().st_mtime) > TEMP_TTL:
            shutil.rmtree(d, ignore_errors=True)


def extract_pdf_text(stream) -> str:
    text = ""
    try:
        from pypdf import PdfReader  # pypdf >= 4
    except ImportError:
        from PyPDF2 import PdfReader  # legacy fallback
    reader = PdfReader(stream)
    for page in reader.pages:
        try:
            text += (page.extract_text() or "") + "\n"
        except Exception:
            continue
    return text


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None
    if request.method == "POST":
        prune_temp()
        style_id = request.form.get("style", "linkedin")
        if style_id not in STYLES_BY_ID:
            error = "Неизвестный стиль резюме."
        else:
            f = request.files.get("resume")
            if not f or not f.filename:
                error = "Выберите файл резюме (.pdf, .txt или .md)."
            else:
                ext = Path(f.filename).suffix.lower()
                if ext not in ALLOWED_EXT:
                    error = ("Неподдерживаемый формат. "
                             "Допустимы: .pdf, .txt, .md.")
                else:
                    try:
                        if ext == ".pdf":
                            raw_text = extract_pdf_text(f.stream)
                        else:
                            raw_text = f.stream.read().decode(
                                "utf-8-sig", errors="replace")
                        if not raw_text.strip():
                            error = "Файл пуст или текст не извлечён."
                        else:
                            cid = uuid.uuid4().hex[:12]
                            out_dir = TEMP_DIR / cid
                            out_dir.mkdir()

                            # 1) промежуточный JSON с распознанными
                            #    разделами исходного резюме
                            parsed = parse_resume(raw_text, ext[1:])
                            parsed["source"] = {
                                "filename": secure_name(f.filename),
                                "format": ext.lstrip("."),
                            }
                            (out_dir / f"{cid}_input.json").write_text(
                                render_json(parsed), encoding="utf-8")

                            # 2) переформатирование в выбранный стиль
                            styled = build_styled_json(parsed, style_id)
                            (out_dir / f"{cid}_styled.json").write_text(
                                render_json(styled), encoding="utf-8")

                            # 3) финальные файлы для скачивания
                            stem = safe_filename(
                                styled["resume"][0]["content"][0]
                                if styled["resume"] and
                                styled["resume"][0]["id"] == "fio"
                                else "resume")
                            outputs = {
                                "txt": (f"{stem}_{style_id}.txt",
                                        render_txt(styled)),
                                "md": (f"{stem}_{style_id}.md",
                                       render_md(styled)),
                                "json": (f"{stem}_{style_id}.json",
                                         render_json(styled)),
                                "html": (f"{stem}_{style_id}.html",
                                         render_html(styled)),
                            }
                            for ext_out, (fname, content) in outputs.items():
                                (out_dir / fname).write_text(
                                    content, encoding="utf-8")

                            result = {
                                "conversion_id": cid,
                                "style": STYLES_BY_ID[style_id],
                                "files": {k: v[0] for k, v
                                          in outputs.items()},
                                "parsed_stats": parsed["stats"],
                                "sections_found": [
                                    s["title"] for s in parsed["sections"]
                                ],
                                "parsed": parsed,
                                "styled": styled,
                            }
                    except Exception as exc:  # noqa: BLE001
                        app.logger.exception("conversion failed")
                        error = ("Ошибка обработки файла: "
                                 f"{type(exc).__name__}. "
                                 "Проверьте содержимое файла.")

    return render_template("index.html", styles=STYLES, result=result,
                           error=error,
                           selected=request.form.get("style", "linkedin"))


@app.route("/download/<cid>/<fname>")
def download(cid, fname):
    """Отдаёт готовый файл, если имя входит в папку конвертации."""
    # \w в Python-3 включает кириллицу; слеши запрещены → traversal невозможен
    if not re.fullmatch(r"[\w\-.]+\.(?:txt|md|json|html)", fname):
        return "Некорректное имя файла", 400
    out_dir = (TEMP_DIR / cid).resolve()
    if not out_dir.is_dir() or out_dir.parent != TEMP_DIR.resolve():
        return "Файл устарел или не найден", 404
    target = (out_dir / fname).resolve()
    if target.parent != out_dir or not target.is_file():
        return "Файл не найден", 404
    prune_temp()
    return send_from_directory(out_dir, fname, as_attachment=True)


def secure_name(filename: str) -> str:
    return re.sub(r"[^\w.\- ]", "_", filename)[:120]


def safe_filename(text: str) -> str:
    text = re.sub(r"\s+", "_", text.strip())
    text = re.sub(r"[^\w\-а-яёА-ЯЁa-zA-Z0-9_]", "", text, flags=re.I)
    return (text or "resume")[:60]


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
