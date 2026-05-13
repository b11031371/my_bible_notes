#!/usr/bin/env python3
"""
update_index.py — Regenerate index.html for the GitHub Pages bible notes site.
Scans the repo for all date-named directories and builds a browsable index.
Usage: python3 update_index.py
"""

import os
import json
import base64
import urllib.request
import urllib.error
from datetime import datetime
from collections import defaultdict

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "resource", "config.json")

MONTH_NAMES_ZH = {
    1: "一月", 2: "二月", 3: "三月", 4: "四月",
    5: "五月", 6: "六月", 7: "七月", 8: "八月",
    9: "九月", 10: "十月", 11: "十一月", 12: "十二月",
}

def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)

def api_get(url, headers):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def get_file_sha(api_url, headers):
    try:
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read()).get("sha")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise

def list_date_dirs(owner, repo, headers):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/"
    items = api_get(url, headers)
    dirs = []
    for item in items:
        if item["type"] == "dir" and len(item["name"]) == 10:
            try:
                datetime.strptime(item["name"], "%Y-%m-%d")
                dirs.append(item["name"])
            except ValueError:
                pass
    return sorted(dirs)  # ascending

def group_by_month(dates):
    groups = defaultdict(list)
    for d in dates:
        dt = datetime.strptime(d, "%Y-%m-%d")
        key = (dt.year, dt.month)
        groups[key].append(d)
    return sorted(groups.items())  # ascending by year-month

def generate_html(dates, owner, repo):
    grouped = group_by_month(dates)
    total = len(dates)

    sections = []
    for (year, month), month_dates in grouped:
        month_zh = MONTH_NAMES_ZH[month]
        month_en = datetime(year, month, 1).strftime("%B")

        rows = []
        for d in month_dates:
            dt = datetime.strptime(d, "%Y-%m-%d")
            day_zh = f"{dt.day}日"
            day_en = dt.strftime("%b %-d")
            zh_url = f"https://{owner}.github.io/{repo}/{d}/note_zh.pdf"
            en_url = f"https://{owner}.github.io/{repo}/{d}/note_en.pdf"
            rows.append(f"""
          <div class="entry">
            <span class="entry-date">{day_zh} <span class="entry-date-en">/ {day_en}</span></span>
            <span class="entry-links">
              <a href="{zh_url}" target="_blank">中文</a>
              <a href="{en_url}" target="_blank">English</a>
            </span>
          </div>""")

        rows_html = "\n".join(rows)
        sections.append(f"""
      <section class="month-section">
        <h2 class="month-heading">
          <span class="month-zh">{year}年 {month_zh}</span>
          <span class="month-en">{month_en} {year}</span>
        </h2>
        <div class="entries">{rows_html}
        </div>
      </section>""")

    sections_html = "\n".join(sections)

    return f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>每日讀經筆記</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}

    body {{
      font-family: "PingFang TC", "Heiti TC", -apple-system, Georgia, serif;
      margin: 0;
      padding: 0;
      background: #f5f3ef;
      color: #2c2c2c;
      min-height: 100vh;
    }}

    header {{
      background: linear-gradient(135deg, #4a3000 0%, #7a5200 100%);
      color: #fff;
      padding: 40px 24px 32px;
      text-align: center;
    }}

    header h1 {{
      margin: 0 0 6px;
      font-size: 1.8em;
      font-weight: 600;
      letter-spacing: 0.02em;
    }}

    header p {{
      margin: 0;
      font-size: 0.88em;
      opacity: 0.75;
      letter-spacing: 0.03em;
    }}

    .badge {{
      display: inline-block;
      margin-top: 14px;
      background: rgba(255,255,255,0.15);
      border: 1px solid rgba(255,255,255,0.3);
      border-radius: 20px;
      padding: 4px 14px;
      font-size: 0.8em;
      opacity: 0.9;
    }}

    main {{
      max-width: 680px;
      margin: 0 auto;
      padding: 32px 20px 60px;
    }}

    .month-section {{
      margin-bottom: 32px;
    }}

    .month-heading {{
      display: flex;
      align-items: baseline;
      gap: 10px;
      margin: 0 0 12px;
      padding-bottom: 8px;
      border-bottom: 2px solid #c8a84b;
    }}

    .month-zh {{
      font-size: 1.1em;
      font-weight: 600;
      color: #5a3e00;
    }}

    .month-en {{
      font-size: 0.8em;
      color: #9a7a40;
      font-weight: normal;
    }}

    .entries {{
      background: #fff;
      border-radius: 10px;
      overflow: hidden;
      box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    }}

    .entry {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 13px 18px;
      border-bottom: 1px solid #f0ebe0;
      transition: background 0.15s;
    }}

    .entry:last-child {{
      border-bottom: none;
    }}

    .entry:hover {{
      background: #fdf8ee;
    }}

    .entry-date {{
      font-size: 0.95em;
      color: #3a2800;
      font-weight: 500;
    }}

    .entry-date-en {{
      color: #9a7a40;
      font-size: 0.85em;
      font-weight: normal;
    }}

    .entry-links {{
      display: flex;
      gap: 10px;
    }}

    .entry-links a {{
      display: inline-block;
      padding: 5px 14px;
      border-radius: 6px;
      font-size: 0.82em;
      text-decoration: none;
      font-weight: 500;
      transition: opacity 0.15s;
    }}

    .entry-links a:first-child {{
      background: #5a3e00;
      color: #fff;
    }}

    .entry-links a:last-child {{
      background: #e8dfc8;
      color: #5a3e00;
    }}

    .entry-links a:hover {{
      opacity: 0.8;
    }}

    footer {{
      text-align: center;
      font-size: 0.78em;
      color: #bbb;
      padding: 20px;
    }}
  </style>
</head>
<body>
  <header>
    <h1>📖 每日讀經筆記</h1>
    <p>Daily Bible Notes</p>
    <div class="badge">共 {total} 篇 · {total} notes</div>
  </header>
  <main>
{sections_html}
  </main>
  <footer>點擊連結，在瀏覽器內直接閱讀 PDF</footer>
</body>
</html>"""

def upload_html(html, owner, repo, headers):
    content_b64 = base64.b64encode(html.encode("utf-8")).decode("utf-8")
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/index.html"
    sha = get_file_sha(api_url, headers)
    payload = {"message": "Update index.html", "content": content_b64}
    if sha:
        payload["sha"] = sha
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(api_url, data=data, headers=headers, method="PUT")
    with urllib.request.urlopen(req) as resp:
        json.loads(resp.read())
    print(f"✓ 索引已更新：https://{owner}.github.io/{repo}/")

def main():
    config = load_config() if os.path.exists(CONFIG_PATH) else {}
    token = os.environ.get("GH_TOKEN") or config.get("github", {}).get("token")
    owner = os.environ.get("GITHUB_OWNER") or config.get("github", {}).get("owner")
    repo  = os.environ.get("GITHUB_REPO")  or config.get("github", {}).get("repo")
    if not all([token, owner, repo]):
        print("Error: 缺少 GitHub 憑證。請設定 GH_TOKEN / GITHUB_OWNER / GITHUB_REPO 環境變數，或提供 config.json。")
        import sys; sys.exit(1)
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
        "User-Agent": "my-daily-bible-note-skill",
    }
    print("掃描 repo 中的日期資料夾…")
    dates = list_date_dirs(owner, repo, headers)
    print(f"找到 {len(dates)} 筆：{', '.join(dates[:5])}{'…' if len(dates) > 5 else ''}")
    html = generate_html(dates, owner, repo)
    upload_html(html, owner, repo, headers)

if __name__ == "__main__":
    main()
