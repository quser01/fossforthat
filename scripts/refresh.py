#!/usr/bin/env python3
"""Refresh GitHub stats in data/alternatives.json (Python fallback)."""
from __future__ import annotations
import json, time, re, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "alternatives.json"
UA = "FossForThat-refresh/1.0"
DELAY = 0.8

def api_get(url: str):
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": UA,
    })
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return resp.status, json.load(resp), dict(resp.headers)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = {"raw": body[:200]}
        return e.code, parsed, {}

def html_fallback(full_name: str):
    req = urllib.request.Request(f"https://github.com/{full_name}", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    stars = None
    m = re.search(r'id="repo-stars-counter-star"[^>]*>([\d,.]+)', html)
    if m:
        stars = int(m.group(1).replace(",", ""))
    lic = None
    m = re.search(r'href="[^"]*/blob/[^"]*LICENSE[^"]*"[^>]*>\s*([^<]+)', html, re.I)
    if m:
        lic = m.group(1).strip()
    pushed = None
    m = re.search(r'datetime="(\d{4}-\d{2}-\d{2}T[^"]+)"', html)
    if m:
        pushed = m.group(1)
    return stars, lic, pushed

def refresh_repo(full_name: str):
    status, body, _ = api_get(f"https://api.github.com/repos/{full_name}")
    if status == 200:
        lic = (body.get("license") or {}).get("spdx_id") or (body.get("license") or {}).get("name") or "not published"
        if lic in ("NOASSERTION", "Other"):
            lic = "custom / see repo"
        return {
            "stars": body.get("stargazers_count"),
            "license": lic,
            "last_commit": (body.get("pushed_at") or "")[:10] or "not published",
            "url": body.get("html_url"),
            "homepage": body.get("homepage") or None,
            "source": "api",
        }
    if status in (403, 429):
        print(f"  rate limited — HTML fallback for {full_name}")
        stars, lic, pushed = html_fallback(full_name)
        return {
            "stars": stars,
            "license": lic or "not published",
            "last_commit": (pushed or "")[:10] or "not published",
            "url": f"https://github.com/{full_name}",
            "homepage": None,
            "source": "html-fallback",
        }
    raise RuntimeError(f"HTTP {status} for {full_name}: {str(body)[:180]}")

def main():
    data = json.loads(DATA_PATH.read_text())
    fetched_at = datetime.now(timezone.utc).isoformat()
    date = fetched_at[:10]
    cache = {}
    updated = 0
    for tool in data["tools"]:
        for alt in tool["alternatives"]:
            key = alt.get("github")
            if not key:
                print(f"skip {alt.get('name')}: no github")
                continue
            print(f"Refreshing {key}…", end=" ", flush=True)
            try:
                if key not in cache:
                    cache[key] = refresh_repo(key)
                    time.sleep(DELAY)
                info = cache[key]
                if isinstance(info.get("stars"), int):
                    alt["stars"] = info["stars"]
                if info.get("license"):
                    alt["license"] = info["license"]
                if info.get("last_commit"):
                    alt["last_commit"] = info["last_commit"]
                if info.get("url"):
                    alt["url"] = info["url"]
                if info.get("homepage"):
                    alt["homepage"] = info["homepage"]
                alt["stats_fetched_at"] = fetched_at
                updated += 1
                print(f"OK ({info['source']}) {alt.get('stars')}★ {alt.get('last_commit')}")
            except Exception as e:
                print(f"FAIL {e}")
    data["site"]["data_fetched_at"] = fetched_at
    data["site"]["data_fetched_date"] = date
    DATA_PATH.write_text(json.dumps(data, indent=2) + "\n")
    print(f"Updated {updated}. Wrote {DATA_PATH}")

if __name__ == "__main__":
    main()
