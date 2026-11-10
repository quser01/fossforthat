#!/usr/bin/env python3
"""Generate static HTML pages from data/alternatives.json (GitHub Pages–ready relative links)."""
from __future__ import annotations

import json
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "data" / "alternatives.json").read_text())
SITE = DATA["site"]
TOOLS = DATA["tools"]

def esc(s):
    return html.escape(str(s) if s is not None else "")

def stars_fmt(n):
    if n is None:
        return "not published"
    if n >= 1000:
        return f"{n:,}"
    return str(n)

def header():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
"""

def head_meta(title, description, path="/", og_type="website", prefix=""):
    # path is site path like / or /tools/chatgpt.html
    canon = SITE["url_base"].rstrip("/") + ("" if path == "/" else path)
    if path == "/":
        canon = SITE["url_base"].rstrip("/") + "/"
    css = f"{prefix}css/styles.css"
    return f"""<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canon)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="{esc(og_type)}">
<meta property="og:url" content="{esc(canon)}">
<meta property="og:site_name" content="{esc(SITE['name'])}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description)}">
<link rel="stylesheet" href="{esc(css)}">
"""

def chrome_top(active=None, prefix=""):
    def n(href, label, key):
        cur = ' aria-current="page"' if active == key else ""
        return f'<a href="{prefix}{href}"{cur}>{label}</a>'
    return f"""<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
  <div class="container header-inner">
    <a class="logo" href="{prefix}index.html"><span class="logo-mark">F</span> {esc(SITE['name'])}</a>
    <nav class="nav" aria-label="Primary">
      {n('index.html', 'Directory', 'home')}
      {n('submit.html', 'Submit', 'submit')}
      {n('sponsor.html', 'Sponsor', 'sponsor')}
    </nav>
  </div>
</header>
"""

def chrome_bottom(prefix=""):
    fetched = SITE.get("data_fetched_date", "unknown")
    return f"""
<footer class="site-footer">
  <div class="container footer-grid">
    <div>
      <h3>{esc(SITE['name'])}</h3>
      <p>{esc(SITE['tagline'])}</p>
      <p>GitHub stats last refreshed: <time datetime="{esc(SITE.get('data_fetched_at',''))}">{esc(fetched)}</time> (UTC date).</p>
    </div>
    <div>
      <h3>Explore</h3>
      <ul>
        <li><a href="{prefix}index.html">All tools</a></li>
        <li><a href="{prefix}submit.html">Submit a project</a></li>
        <li><a href="{prefix}sponsor.html">Sponsor / featured</a></li>
      </ul>
    </div>
    <div>
      <h3>Notes</h3>
      <ul>
        <li>Install difficulty = our estimate</li>
        <li>“What you lose” = our assessment</li>
        <li>Stars/license/commits from GitHub</li>
      </ul>
    </div>
  </div>
  <div class="container disclosure">
    <strong>Affiliate disclosure:</strong> Some links on this site may become affiliate links in the future.
    If that happens, we may earn a commission at no extra cost to you. Editorial listings are not paid placements unless marked as featured.
  </div>
</footer>
"""

def newsletter_block():
    return """
<section class="panel" id="newsletter" aria-labelledby="newsletter-heading">
  <h2 id="newsletter-heading">Newsletter — coming soon</h2>
  <p><strong>Coming soon.</strong> Email alerts are not live yet. No signup form is connected, and nothing you type here is collected or emailed.</p>
  <p class="note" role="status">This is a placeholder only. A real newsletter provider has not been connected.</p>
</section>
"""

def write_home():
    cats = DATA.get("categories", [])
    cat_opts = "".join(f'<option value="{esc(c)}">{esc(c)}</option>' for c in cats)
    cards = []
    for t in TOOLS:
        alt_names = ", ".join(a["name"] for a in t["alternatives"])
        diffs = sorted({a["install_difficulty"] for a in t["alternatives"]})
        search = " ".join([
            t["name"], t.get("vendor", ""), t.get("summary", ""),
            alt_names, t["category"], " ".join(a.get("github", "") for a in t["alternatives"]),
        ])
        cards.append(f"""
<article class="card" data-tool-card
  data-category="{esc(t['category'])}"
  data-difficulties="{esc(','.join(diffs))}"
  data-search="{esc(search)}">
  <div><span class="pill cat">{esc(t['category'])}</span></div>
  <h2><a href="tools/{esc(t['id'])}.html">Open-source alternatives to {esc(t['name'])}</a></h2>
  <p>{esc(t['summary'])}</p>
  <p class="alts"><strong>{len(t['alternatives'])}</strong> listed: {esc(alt_names)}</p>
  <p><a class="btn secondary" href="tools/{esc(t['id'])}.html">View swaps →</a></p>
</article>""")

    title = f"{SITE['name']} — {SITE['tagline']}"
    desc = SITE["description"]
    body = f"""{header()}
{head_meta(title, desc, "/", prefix="")}
</head>
<body>
{chrome_top('home', prefix="")}
<main id="main" class="container">
  <section class="hero">
    <div class="badge-row">
      <span class="badge">{len(TOOLS)} paid tools</span>
      <span class="badge">{sum(len(t['alternatives']) for t in TOOLS)} FOSS / self-hosted swaps</span>
      <span class="badge">Stats fetched {esc(SITE.get('data_fetched_date',''))} UTC</span>
    </div>
    <h1>{esc(SITE['tagline'])}</h1>
    <p class="lead">{esc(SITE['description'])} Install difficulty and “what you lose” are labeled as our estimates/assessments. Stars, license, and last commit come from the public GitHub API.</p>
  </section>

  <section class="controls" aria-label="Filter directory">
    <div>
      <label for="search">Search</label>
      <input id="search" type="search" placeholder="e.g. Midjourney, Whisper, Copilot…" autocomplete="off">
    </div>
    <div>
      <label for="category">Category</label>
      <select id="category">
        <option value="">All categories</option>
        {cat_opts}
      </select>
    </div>
    <div>
      <label for="difficulty">Has install difficulty</label>
      <select id="difficulty">
        <option value="">Any</option>
        <option value="easy">easy</option>
        <option value="medium">medium</option>
        <option value="hard">hard</option>
      </select>
    </div>
  </section>
  <p class="meta-line"><span id="result-count">{len(TOOLS)} tools</span> shown</p>

  <section class="grid" id="tool-grid" aria-label="Paid tools">
    {''.join(cards)}
  </section>
  <p id="empty-state" class="empty" hidden>No tools match those filters.</p>

  {newsletter_block()}
</main>
{chrome_bottom(prefix="")}
<script src="js/app.js"></script>
</body>
</html>
"""
    (ROOT / "index.html").write_text(body)
    print("Wrote index.html")

def alt_block(a):
    hw = a.get("minimum_hardware") or "not published"
    lic = a.get("license") or "not published"
    stars = stars_fmt(a.get("stars"))
    last = a.get("last_commit") or "not published"
    homepage = a.get("homepage")
    home_html = f' · <a href="{esc(homepage)}" rel="noopener noreferrer">homepage</a>' if homepage else ""
    notes = a.get("notes")
    notes_html = f'<p class="note">{esc(notes)}</p>' if notes else ""
    return f"""
<article class="alt-card">
  <div class="alt-head">
    <h2><a href="{esc(a['url'])}" rel="noopener noreferrer">{esc(a['name'])}</a></h2>
    <div>
      <span class="pill diff-{esc(a['install_difficulty'])}">{esc(a['install_difficulty'])} install</span>
      <span class="pill">our estimate</span>
    </div>
  </div>
  <p>
    <a href="{esc(a['url'])}" rel="noopener noreferrer">{esc(a.get('github', a['url']))}</a>{home_html}
  </p>
  <div class="stats">
    <div class="stat"><div class="k">License</div><div class="v mono">{esc(lic)}</div></div>
    <div class="stat"><div class="k">GitHub stars</div><div class="v">{esc(stars)}</div></div>
    <div class="stat"><div class="k">Last commit</div><div class="v mono">{esc(last)}</div></div>
    <div class="stat"><div class="k">Stats fetched</div><div class="v mono">{esc((a.get('stats_fetched_at') or '')[:10] or 'unknown')}</div></div>
  </div>
  <div class="stat" style="margin-bottom:.75rem">
    <div class="k">Minimum hardware</div>
    <div class="v">{esc(hw)}</div>
  </div>
  <div class="lose">
    <strong>What you lose vs the paid tool <span class="pill">our assessment</span></strong>
    {esc(a.get('what_you_lose', 'estimate'))}
  </div>
  {notes_html}
</article>
"""

def write_tool_pages():
    tools_dir = ROOT / "tools"
    tools_dir.mkdir(exist_ok=True)
    prefix = "../"
    for t in TOOLS:
        title = f"Open-source alternatives to {t['name']} | {SITE['name']}"
        desc = f"Self-hosted and open-source alternatives to {t['name']}: " + ", ".join(a["name"] for a in t["alternatives"]) + ". Licenses, stars, install difficulty, and what you lose."
        path = f"/tools/{t['id']}.html"
        alts = "\n".join(alt_block(a) for a in t["alternatives"])
        body = f"""{header()}
{head_meta(title, desc, path, og_type="article", prefix=prefix)}
</head>
<body>
{chrome_top(prefix=prefix)}
<main id="main" class="container">
  <section class="page-hero">
    <p class="breadcrumb"><a href="{prefix}index.html">Directory</a> / {esc(t['category'])} / {esc(t['name'])}</p>
    <h1>Open-source alternatives to {esc(t['name'])}</h1>
    <p class="lead" style="color:var(--muted);max-width:42rem">{esc(t['summary'])} Vendor: {esc(t.get('vendor','—'))}.</p>
    <div class="badge-row">
      <span class="badge">{esc(t['category'])}</span>
      <span class="badge">{len(t['alternatives'])} alternatives</span>
      <span class="badge">GitHub stats: {esc(SITE.get('data_fetched_date',''))} UTC</span>
    </div>
  </section>

  <section class="alt-list" aria-label="Alternatives">
    {alts}
  </section>

  <section class="panel">
    <h2>How we score this page</h2>
    <p>Stars, license SPDX (or “custom / see repo”), and last commit date are pulled from the public GitHub API. Install difficulty is <strong>our estimate</strong>. “What you lose” is <strong>our assessment</strong>. Minimum hardware is only shown when published by the project; otherwise “not published”.</p>
  </section>

  {newsletter_block()}
</main>
{chrome_bottom(prefix=prefix)}
</body>
</html>
"""
        (tools_dir / f"{t['id']}.html").write_text(body)
    print(f"Wrote {len(TOOLS)} tool pages")

def write_submit():
    title = f"Submit a project | {SITE['name']}"
    desc = "Suggest an open-source or self-hosted alternative for the FossForThat directory."
    body = f"""{header()}
{head_meta(title, desc, "/submit.html", prefix="")}
</head>
<body>
{chrome_top('submit', prefix="")}
<main id="main" class="container prose">
  <section class="page-hero">
    <h1>Submit a project — coming soon</h1>
    <p><strong>Coming soon.</strong> Project submissions are not open yet. There is no working form on this page, and nothing is sent or stored.</p>
  </section>
  <section class="panel">
    <h2>What you will be able to suggest later</h2>
    <ul>
      <li>Paid tool the project replaces</li>
      <li>Project name and source URL</li>
      <li>Why it belongs in the directory</li>
    </ul>
    <p class="note" role="status">Coming soon — no backend or issue tracker is connected. Do not expect a submit button to work.</p>
    <div class="form-actions">
      <button class="btn" type="button" disabled title="Coming soon">Submit (coming soon)</button>
      <a class="btn secondary" href="index.html">Back to directory</a>
    </div>
  </section>
</main>
{chrome_bottom(prefix="")}
</body>
</html>
"""
    (ROOT / "submit.html").write_text(body)
    print("Wrote submit.html")

def write_sponsor():
    title = f"Sponsor / featured listing | {SITE['name']}"
    desc = "Featured listing and sponsorship options for FossForThat. Pricing coming."
    body = f"""{header()}
{head_meta(title, desc, "/sponsor.html", prefix="")}
</head>
<body>
{chrome_top('sponsor', prefix="")}
<main id="main" class="container prose">
  <section class="page-hero">
    <h1>Sponsor / featured listing</h1>
    <p>Support the directory and reach people searching for open-source AI swaps.</p>
  </section>
  <section class="panel">
    <h2>What we plan to offer</h2>
    <ul>
      <li>Featured placement on a paid-tool page</li>
      <li>Homepage highlight rotation</li>
      <li>Newsletter sponsorship (when the list is live)</li>
    </ul>
    <p><strong>Pricing coming.</strong> We are not publishing rates until the site has traffic baselines and a billing setup. Do not treat any third-party quote as ours.</p>
    <p class="note" role="status">Coming soon — no checkout or contact form is connected on this static build.</p>
    <div class="form-actions">
      <button class="btn" type="button" disabled title="Coming soon">Request a spot (coming soon)</button>
      <a class="btn secondary" href="index.html">Back to directory</a>
    </div>
  </section>
</main>
{chrome_bottom(prefix="")}
</body>
</html>
"""
    (ROOT / "sponsor.html").write_text(body)
    print("Wrote sponsor.html")

def write_robots_sitemap():
    base = SITE["url_base"].rstrip("/")
    (ROOT / "robots.txt").write_text(f"""User-agent: *
Allow: /

Sitemap: {base}/sitemap.xml
""")
    urls = ["/", "/submit.html", "/sponsor.html"] + [f"/tools/{t['id']}.html" for t in TOOLS]
    items = []
    for u in urls:
        loc = base + "/" if u == "/" else base + u
        items.append(f"""  <url>
    <loc>{esc(loc)}</loc>
    <changefreq>weekly</changefreq>
  </url>""")
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(items) + "\n</urlset>\n"
    )
    print("Wrote robots.txt and sitemap.xml")

def write_readme():
    (ROOT / "README.md").write_text(f"""# {SITE['name']}

{SITE['tagline']}

Static directory of open-source / self-hosted alternatives to paid AI tools.

Live (GitHub Pages): {SITE['url_base']}/

## Local preview

```bash
python3 -m http.server 8765
# open http://127.0.0.1:8765/
```

## Refresh GitHub stats

```bash
./scripts/refresh.sh
# or: node scripts/refresh.js
python3 scripts/build.py
```

## Build

```bash
python3 scripts/build.py
```

## Notes

- Install difficulty = our estimate
- “What you lose” = our assessment
- Stars / license / last commit from public GitHub API (see `data/alternatives.json` → `stats_fetched_at`)
- Editorial overrides: list field names in an alternative's `locked_fields` (e.g. `["license"]`) and the refresh scripts will never overwrite them; `locked_reason` says why
- Newsletter & submit are **coming soon** placeholders (not working forms)
- Do not invent prices on the sponsor page
""")
    print("Wrote README.md")

def write_nojekyll():
    (ROOT / ".nojekyll").write_text("")
    print("Wrote .nojekyll")

def main():
    write_home()
    write_tool_pages()
    write_submit()
    write_sponsor()
    write_robots_sitemap()
    write_readme()
    write_nojekyll()
    print("Build complete.")

if __name__ == "__main__":
    main()
