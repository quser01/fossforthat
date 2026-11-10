#!/usr/bin/env node
/**
 * Refresh GitHub stars, license, and last commit for every alternative
 * in data/alternatives.json. Unauthenticated API with small delays.
 * Falls back to scraping the public repo page if rate-limited.
 *
 * Usage: node scripts/refresh.js
 */
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const DATA_PATH = path.join(ROOT, "data", "alternatives.json");
const UA = "FossForThat-refresh/1.0";
const DELAY_MS = 800;

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function fetchJson(url) {
  const res = await fetch(url, {
    headers: {
      Accept: "application/vnd.github+json",
      "User-Agent": UA,
    },
  });
  const text = await res.text();
  let body;
  try {
    body = JSON.parse(text);
  } catch {
    body = { raw: text.slice(0, 200) };
  }
  return { ok: res.ok, status: res.status, body, headers: res.headers };
}

async function fetchText(url) {
  const res = await fetch(url, { headers: { "User-Agent": UA } });
  return { ok: res.ok, status: res.status, text: await res.text() };
}

function parseRepoPage(html) {
  // Best-effort fallbacks from public HTML (may break if GitHub changes markup)
  const stars =
    Number((html.match(/id="repo-stars-counter-star"[^>]*>([\d,.kKmM]+)/) || [])[1]?.replace(/,/g, "")) ||
    null;
  // license link text
  let license = null;
  const lic = html.match(/href="[^"]*\/blob\/[^"]*LICENSE[^"]*"[^>]*>\s*([^<]+)/i);
  if (lic) license = lic[1].trim();
  // relative-time datetime for latest commit on overview is fragile; leave null if missing
  const pushed = (html.match(/datetime="(\d{4}-\d{2}-\d{2}T[^"]+)"/) || [])[1] || null;
  return { stars, license, pushed_at: pushed };
}

async function refreshRepo(fullName) {
  const api = `https://api.github.com/repos/${fullName}`;
  const { ok, status, body } = await fetchJson(api);
  if (ok) {
    let license =
      (body.license && (body.license.spdx_id || body.license.name)) || "not published";
    if (license === "NOASSERTION" || license === "Other") license = "custom / see repo";
    return {
      stars: body.stargazers_count,
      license,
      last_commit: (body.pushed_at || "").slice(0, 10) || "not published",
      url: body.html_url,
      homepage: body.homepage || null,
      full_name: body.full_name,
      source: "api",
    };
  }
  if (status === 403 || status === 429) {
    console.warn(`Rate limited on ${fullName}, falling back to Web page fetch…`);
    const page = await fetchText(`https://github.com/${fullName}`);
    if (!page.ok) throw new Error(`Fallback failed for ${fullName}: HTTP ${page.status}`);
    const parsed = parseRepoPage(page.text);
    return {
      stars: parsed.stars,
      license: parsed.license || "not published",
      last_commit: parsed.pushed_at ? parsed.pushed_at.slice(0, 10) : "not published",
      url: `https://github.com/${fullName}`,
      homepage: null,
      full_name: fullName,
      source: "html-fallback",
    };
  }
  throw new Error(`GitHub API ${status} for ${fullName}: ${JSON.stringify(body).slice(0, 180)}`);
}

async function main() {
  const data = JSON.parse(fs.readFileSync(DATA_PATH, "utf8"));
  const fetchedAt = new Date().toISOString();
  const date = fetchedAt.slice(0, 10);
  let updated = 0;
  const seen = new Map();

  for (const tool of data.tools) {
    for (const alt of tool.alternatives) {
      const key = alt.github;
      if (!key) {
        console.warn(`Skipping ${alt.name}: no github field`);
        continue;
      }
      process.stdout.write(`Refreshing ${key}… `);
      try {
        let info = seen.get(key);
        if (!info) {
          info = await refreshRepo(key);
          seen.set(key, info);
          await sleep(DELAY_MS);
        }
        // Fields listed in alt.locked_fields hold hand-verified editorial values
        // (e.g. a custom license summary GitHub reports as NOASSERTION, or a
        // homepage whose GitHub value is stale). Never overwrite them.
        const locked = new Set(Array.isArray(alt.locked_fields) ? alt.locked_fields : []);
        const setField = (field, value) => {
          if (locked.has(field)) {
            if (alt[field] !== value) {
              console.log(`  keeping editorial ${field} for ${alt.name}: ${JSON.stringify(alt[field])} (GitHub: ${JSON.stringify(value)})`);
            }
            return;
          }
          alt[field] = value;
        };
        if (typeof info.stars === "number") setField("stars", info.stars);
        if (info.license) setField("license", info.license);
        if (info.last_commit) setField("last_commit", info.last_commit);
        if (info.url) setField("url", info.url);
        if (info.homepage) setField("homepage", info.homepage);
        alt.stats_fetched_at = fetchedAt;
        updated += 1;
        console.log(`OK (${info.source}) ${alt.stars}★ ${alt.last_commit}`);
      } catch (err) {
        console.log(`FAIL ${err.message}`);
      }
    }
  }

  data.site.data_fetched_at = fetchedAt;
  data.site.data_fetched_date = date;
  fs.writeFileSync(DATA_PATH, JSON.stringify(data, null, 2) + "\n");
  console.log(`\nUpdated ${updated} alternatives. Wrote ${DATA_PATH}`);
  console.log("Run: python3 scripts/build.py");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
