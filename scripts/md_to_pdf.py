#!/usr/bin/env python3
"""
md_to_pdf.py — Convert Bible Note Markdown to PDF
Flow: Markdown → HTML (in-memory) → PDF via Chrome/Chromium headless
Usage: python3 md_to_pdf.py input.md output.pdf
"""

import sys
import os
import re
import subprocess
import tempfile

CHROME_CANDIDATES = [
    # macOS
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    # Linux (GitHub Actions ubuntu-latest)
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium-browser",
    "/usr/bin/chromium",
]

CSS = """
body {
    font-family: "PingFang TC", "Heiti TC", "STHeiti", Georgia, serif;
    font-size: 14px;
    line-height: 1.9;
    margin: 45px 55px;
    color: #222;
}
h1 {
    font-size: 22px;
    border-bottom: 2px solid #333;
    padding-bottom: 8px;
    margin-bottom: 16px;
}
h2  { font-size: 17px; margin-top: 28px; color: #333; }
h3  { font-size: 15px; color: #555; margin-top: 18px; }
hr  { border: none; border-top: 1px solid #ddd; margin: 22px 0; }
blockquote {
    border-left: 4px solid #bbb;
    margin: 14px 0;
    padding: 8px 16px;
    color: #555;
    font-style: italic;
    background: #f9f9f9;
}
blockquote p { margin: 4px 0; }
ul  { padding-left: 22px; }
li  { margin: 5px 0; }
p   { margin: 6px 0; }
em  { color: #666; }
strong { font-weight: 600; }
"""

# ── Markdown → HTML ───────────────────────────────────────────────────────────

def inline(text):
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*",     r"<em>\1</em>",         text)
    return text

def md_to_html(md):
    lines = md.split("\n")
    out = []
    in_bq = in_ul = False

    def close_bq():
        nonlocal in_bq
        if in_bq:
            out.append("</blockquote>")
            in_bq = False

    def close_ul():
        nonlocal in_ul
        if in_ul:
            out.append("</ul>")
            in_ul = False

    for line in lines:
        stripped = line.strip()

        if re.match(r"^-{3,}$", stripped):
            close_bq(); close_ul()
            out.append("<hr>")

        elif line.startswith("# "):
            close_bq(); close_ul()
            out.append(f"<h1>{inline(line[2:].strip())}</h1>")

        elif line.startswith("## "):
            close_bq(); close_ul()
            out.append(f"<h2>{inline(line[3:].strip())}</h2>")

        elif line.startswith("### "):
            close_bq(); close_ul()
            out.append(f"<h3>{inline(line[4:].strip())}</h3>")

        elif line.startswith("> ") or line == ">":
            close_ul()
            if not in_bq:
                out.append("<blockquote>")
                in_bq = True
            content = line[2:].strip() if line.startswith("> ") else ""
            out.append(f"<p>{inline(content)}</p>")

        elif line.startswith("- "):
            close_bq()
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{inline(line[2:].strip())}</li>")

        elif stripped == "":
            close_bq(); close_ul()

        else:
            close_bq(); close_ul()
            if stripped:
                out.append(f"<p>{inline(stripped)}</p>")

    close_bq(); close_ul()

    body = "\n".join(out)
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>{CSS}</style>
</head>
<body>{body}</body>
</html>"""

# ── Chrome headless → PDF ─────────────────────────────────────────────────────

def find_chrome():
    for path in CHROME_CANDIDATES:
        if os.path.exists(path):
            return path
    return None

def convert(md_path, pdf_path):
    chrome = find_chrome()
    if not chrome:
        print("Error: 找不到 Chrome 或 Chromium。", file=sys.stderr)
        print("請安裝 Chrome，或在 CHROME_CANDIDATES 中加入正確路徑。", file=sys.stderr)
        sys.exit(1)

    with open(md_path, encoding="utf-8") as f:
        md = f.read()

    html = md_to_html(md)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", encoding="utf-8", delete=False
    ) as tmp:
        tmp.write(html)
        tmp_path = tmp.name

    try:
        subprocess.run(
            [
                chrome,
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                f"--print-to-pdf={os.path.abspath(pdf_path)}",
                "--no-pdf-header-footer",
                f"file://{tmp_path}",
            ],
            capture_output=True,
            timeout=30,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Chrome 轉換失敗：{e.stderr.decode()[:300]}", file=sys.stderr)
        sys.exit(1)
    finally:
        os.unlink(tmp_path)

    print(f"✓ PDF 已儲存：{pdf_path}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) != 3:
        print("用法：python3 md_to_pdf.py input.md output.pdf")
        sys.exit(1)

    md_path, pdf_path = sys.argv[1], sys.argv[2]

    if not os.path.exists(md_path):
        print(f"找不到檔案：{md_path}", file=sys.stderr)
        sys.exit(1)

    convert(md_path, pdf_path)

if __name__ == "__main__":
    main()
