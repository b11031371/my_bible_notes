#!/usr/bin/env python3
"""revalidate.py — Notify the Sproutiv app to refresh its note cache."""

import os
import json
import urllib.request
import urllib.error

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "resource", "config.json")

def main():
    config = {}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, encoding="utf-8") as f:
            config = json.load(f)

    app = config.get("app", {})
    url    = os.environ.get("REVALIDATE_URL")    or app.get("revalidate_url")
    secret = os.environ.get("REVALIDATE_SECRET") or app.get("revalidate_secret")

    if not url or not secret:
        print("⚠️  config.json 缺少 app.revalidate_url 或 app.revalidate_secret，略過快取刷新")
        return

    req = urllib.request.Request(
        url,
        data=b"{}",
        headers={
            "x-revalidate-secret": secret,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"✓ App 快取已刷新")
    except urllib.error.HTTPError as e:
        print(f"⚠️  快取刷新失敗：{e.code} {e.reason}")
    except Exception as e:
        print(f"⚠️  快取刷新失敗：{e}")

if __name__ == "__main__":
    main()
