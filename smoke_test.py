# -*- coding: utf-8 -*-
"""Smoke-тест: все 8 стилей через HTTP + проверка файлов."""
import io
import urllib.request
import urllib.parse
import re

BASE = "http://127.0.0.1:5000"
sample = open("test_resume.txt", "rb").read()

ok = True
for style in ["linkedin", "xing", "hhru", "indeed", "glassdoor",
              "europass", "monster", "onepage"]:
    boundary = "----smoke" + style
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="resume"; '
        f'filename="smoke.txt"\r\n'
        f"Content-Type: text/plain\r\n\r\n"
    ).encode() + sample + (
        f"\r\n--{boundary}\r\n"
        f'Content-Disposition: form-data; name="style"\r\n\r\n'
        f"{style}\r\n--{boundary}--\r\n"
    ).encode()
    req = urllib.request.Request(
        BASE + "/", data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    html = urllib.request.urlopen(req).read().decode("utf-8")

    cid = re.search(r"Конвертация #([a-f0-9]{12})", html)
    files = re.findall(r'href="(/download/[a-f0-9]{12}/[^"]+)"', html)
    alerts = re.search(r'role="alert"', html)
    status = "OK" if (cid and len(files) == 4 and not alerts) else "FAIL"
    if status == "FAIL":
        ok = False
    print(f"{style:10s} {status}  cid={cid.group(1) if cid else '-'}  files={len(files)}")

    # проверяем каждый скачанный файл
    for f in files:
        data = urllib.request.urlopen(BASE + f).read()
        if not data:
            print(f"  EMPTY FILE: {f}")
            ok = False

    if style == "onepage":
        html_file = [f for f in files if f.endswith(".html")][0]
        content = urllib.request.urlopen(BASE + html_file).read().decode("utf-8")
        assert "font-size: 12pt" in content
        assert "line-height: 1.5" in content
        assert "@page { size: A4" in content
        assert "СМИРНОВ" in content or "ПЕТРОВ" in content
        print("  onepage print spec (A4, 12pt, 1.5): OK")

print("ALL STYLES:", "PASS" if ok else "FAIL")
