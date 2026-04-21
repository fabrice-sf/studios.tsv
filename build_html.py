"""
build_html.py - render the dashboard HTML from a snapshot dict.

The HTML template is the single raw-string variable HTML below. Edit fonts,
colours, and layout there; the template contains a __DATA_PLACEHOLDER__ marker
where the snapshot JSON is embedded at render time.
"""
from __future__ import annotations
import json
from pathlib import Path

HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Marketing Performance — Cross-Platform Ledger</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,500;0,9..144,600;0,9..144,700;1,9..144,400&family=IBM+Plex+Mono:wght@300;400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #f4f0e4;
  --bg-rule: #d9d2bf;
  --ink: #1a1a1a;
  --ink-dim: #5c5448;
  --ink-mute: #8a7f6e;
  --paper: #faf6eb;
  --oxblood: #6f1b1b;
  --oxblood-hover: #8a2525;
  --signal: #c94a16;
  --positive: #2d5a2d;
  --chart-a: #1a1a1a;
  --chart-b: #6f1b1b;
  --chart-c: #8a7f6e;
  --chart-d: #c94a16;
  --serif: 'Fraunces', 'EB Garamond', Georgia, serif;
  --sans: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
  --mono: 'IBM Plex Mono', 'SF Mono', Menlo, monospace;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { background: var(--bg); color: var(--ink); }
body {
  font-family: var(--sans);
  font-size: 14px;
  line-height: 1.5;
  min-height: 100vh;
  font-feature-settings: 'kern', 'liga', 'tnum';
  -webkit-font-smoothing: antialiased;
}
.paper-texture {
  position: fixed; inset: 0; pointer-events: none; z-index: 0;
  opacity: 0.5;
  background-image:
    radial-gradient(circle at 20% 30%, rgba(180,160,120,0.03) 0%, transparent 40%),
    radial-gradient(circle at 80% 70%, rgba(111,27,27,0.02) 0%, transparent 40%);
}
.container { max-width: 1440px; margin: 0 auto; padding: 32px 48px 96px; position: relative; z-index: 1; }

/* MASTHEAD */
.masthead {
  border-bottom: 2px solid var(--ink);
  padding-bottom: 24px; margin-bottom: 32px;
}
.masthead-top {
  display: flex; justify-content: space-between; align-items: baseline;
  font-family: var(--mono);
  font-size: 10.5px;
  letter-spacing: 0.15em; text-transform: uppercase;
  color: var(--ink-dim);
  padding-bottom: 20px;
  border-bottom: 1px solid var(--bg-rule);
}
.masthead-top .edition { letter-spacing: 0.2em; }
.masthead h1 {
  font-family: var(--serif);
  font-weight: 400;
  font-size: clamp(44px, 6vw, 76px);
  line-height: 0.95;
  letter-spacing: -0.02em;
  margin-top: 24px;
  font-feature-settings: 'kern', 'liga', 'dlig';
}
.masthead h1 em {
  font-style: italic;
  font-weight: 400;
  color: var(--oxblood);
  opacity: 0.9;
}
.masthead .subhead {
  margin-top: 16px;
  font-family: var(--serif);
  font-weight: 400;
  font-style: italic;
  font-size: 18px;
  color: var(--ink-dim);
  max-width: 640px;
  line-height: 1.4;
}
.masthead-meta {
  display: flex; gap: 32px; margin-top: 20px;
  font-family: var(--mono);
  font-size: 11px;
  color: var(--ink-dim);
  letter-spacing: 0.05em;
}
.masthead-meta span strong { color: var(--ink); font-weight: 500; }

/* SECTION HEADERS */
.section-rule {
  display: flex; align-items: baseline; gap: 16px;
  margin: 40px 0 20px;
  border-bottom: 1px solid var(--ink);
  padding-bottom: 8px;
}
.section-rule .num {
  font-family: var(--mono);
  font-size: 11px;
  color: var(--oxblood);
  font-weight: 500;
}
.section-rule h2 {
  font-family: var(--serif);
  font-weight: 500;
  font-size: 22px;
  letter-spacing: -0.01em;
  flex: 1;
}
.section-rule .meta {
  font-family: var(--mono);
  font-size: 10.5px;
  color: var(--ink-mute);
  text-transform: uppercase;
  letter-spacing: 0.12em;
}

/* KPI GRID */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  border: 1px solid var(--ink);
  background: var(--paper);
}
.kpi {
  padding: 20px 18px 18px;
  border-right: 1px solid var(--bg-rule);
  min-width: 0;
}
.kpi:last-child { border-right: none; }
.kpi-label {
  font-family: var(--mono);
  font-size: 9.5px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--ink-mute);
  margin-bottom: 12px;
}
.kpi-value {
  font-family: var(--serif);
  font-weight: 500;
  font-size: clamp(22px, 2.2vw, 32px);
  line-height: 1;
  letter-spacing: -0.015em;
  font-feature-settings: 'tnum';
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.kpi-value .cur { font-size: 0.65em; color: var(--ink-mute); margin-right: 2px; font-weight: 400; }
.kpi-value .suffix { font-size: 0.55em; color: var(--ink-mute); margin-left: 4px; font-weight: 400; letter-spacing: 0.05em; }
.kpi-sub {
  margin-top: 10px;
  font-family: var(--mono);
  font-size: 10.5px;
  color: var(--ink-dim);
  display: flex; align-items: center; gap: 6px;
}
.kpi-sub .bullet {
  width: 5px; height: 5px; background: var(--oxblood); border-radius: 50%;
  display: inline-block;
}

/* FILTERS */
.filters-card {
  background: var(--paper);
  border: 1px solid var(--ink);
  padding: 20px 24px;
  display: grid;
  grid-template-columns: auto 1fr 1fr 1fr auto;
  gap: 24px;
  align-items: center;
}
.filters-label {
  font-family: var(--serif);
  font-style: italic;
  font-size: 15px;
  color: var(--ink-dim);
  padding-right: 20px;
  border-right: 1px solid var(--bg-rule);
}
.filter-group { display: flex; flex-direction: column; gap: 6px; }
.filter-group label {
  font-family: var(--mono);
  font-size: 9.5px;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--ink-mute);
}
.filter-group select {
  font-family: var(--sans);
  font-size: 13px;
  padding: 7px 10px 7px 0;
  border: none;
  border-bottom: 1px solid var(--ink);
  background: transparent;
  color: var(--ink);
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='6' viewBox='0 0 10 6'><path d='M1 1l4 4 4-4' stroke='%231a1a1a' fill='none' stroke-width='1.2'/></svg>");
  background-repeat: no-repeat;
  background-position: right center;
  padding-right: 20px;
}
.filter-group select:focus { outline: none; border-bottom-color: var(--oxblood); }
.reset-btn {
  font-family: var(--mono);
  font-size: 10.5px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  background: transparent;
  border: 1px solid var(--ink);
  color: var(--ink);
  padding: 9px 14px;
  cursor: pointer;
  transition: all 0.15s;
}
.reset-btn:hover { background: var(--ink); color: var(--paper); }

/* TWO COLUMN */
.two-col {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 32px;
  margin-top: 32px;
}

/* CHART */
.chart-card {
  background: var(--paper);
  border: 1px solid var(--ink);
  padding: 24px;
  position: relative;
}
.chart-head {
  display: flex; justify-content: space-between; align-items: baseline;
  margin-bottom: 20px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--bg-rule);
}
.chart-title {
  font-family: var(--serif);
  font-size: 18px;
  font-weight: 500;
  letter-spacing: -0.01em;
}
.chart-meta {
  font-family: var(--mono);
  font-size: 10.5px;
  color: var(--ink-mute);
  letter-spacing: 0.1em;
  text-transform: uppercase;
}
.bar-row {
  display: grid;
  grid-template-columns: 110px 1fr 90px;
  align-items: center;
  padding: 10px 0;
  gap: 16px;
  border-bottom: 1px dotted var(--bg-rule);
  font-size: 13px;
}
.bar-row:last-child { border-bottom: none; }
.bar-label {
  font-family: var(--sans);
  font-size: 13px;
  color: var(--ink);
  font-weight: 400;
}
.bar-track { height: 20px; background: transparent; position: relative; }
.bar-fill {
  height: 100%;
  background: var(--ink);
  transition: width 0.6s cubic-bezier(0.22, 1, 0.36, 1);
  position: relative;
}
.bar-fill.a { background: var(--oxblood); }
.bar-fill.b { background: var(--ink); }
.bar-fill.c { background: var(--ink-dim); }
.bar-fill.d { background: var(--signal); }
.bar-value {
  font-family: var(--mono);
  font-size: 12px;
  color: var(--ink);
  text-align: right;
  font-variant-numeric: tabular-nums;
  font-weight: 500;
}

/* PLATFORM BREAKDOWN */
.platform-card {
  background: var(--paper);
  border: 1px solid var(--ink);
  padding: 24px;
}
.platform-row {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 14px;
  align-items: baseline;
  padding: 18px 0;
  border-bottom: 1px solid var(--bg-rule);
}
.platform-row:last-child { border-bottom: none; }
.platform-name {
  font-family: var(--serif);
  font-size: 17px;
  font-weight: 500;
  letter-spacing: -0.005em;
}
.platform-stats {
  font-family: var(--mono);
  font-size: 10.5px;
  color: var(--ink-dim);
  letter-spacing: 0.03em;
}
.platform-spend {
  font-family: var(--serif);
  font-size: 19px;
  font-weight: 500;
  color: var(--ink);
  font-variant-numeric: tabular-nums;
}
.platform-bar {
  grid-column: 1 / -1;
  height: 3px;
  background: var(--bg-rule);
  margin-top: 4px;
  position: relative;
}
.platform-bar-fill {
  height: 100%;
  background: var(--oxblood);
  transition: width 0.6s cubic-bezier(0.22, 1, 0.36, 1);
}

/* TABLE */
.table-wrap {
  background: var(--paper);
  border: 1px solid var(--ink);
  overflow: hidden;
  margin-top: 32px;
}
.table-toolbar {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid var(--bg-rule);
  background: var(--paper);
}
.table-toolbar .count {
  font-family: var(--mono);
  font-size: 11px;
  color: var(--ink-dim);
  letter-spacing: 0.06em;
}
.table-toolbar .search {
  font-family: var(--sans);
  font-size: 13px;
  border: none;
  border-bottom: 1px solid var(--ink);
  padding: 5px 2px;
  min-width: 240px;
  background: transparent;
  color: var(--ink);
}
.table-toolbar .search::placeholder { color: var(--ink-mute); font-style: italic; }
.table-toolbar .search:focus { outline: none; border-bottom-color: var(--oxblood); }
.table-scroll {
  max-height: 640px;
  overflow-y: auto;
  overflow-x: auto;
}
table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
thead { position: sticky; top: 0; background: var(--paper); z-index: 2; }
thead tr { border-bottom: 1px solid var(--ink); }
th {
  font-family: var(--mono);
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--ink-dim);
  padding: 14px 16px 12px;
  text-align: left;
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
  position: relative;
}
th:hover { color: var(--ink); }
th.num { text-align: right; }
th .sort-arrow {
  display: inline-block; margin-left: 4px; font-size: 9px;
  opacity: 0.3;
}
th.sorted .sort-arrow { opacity: 1; color: var(--oxblood); }
tbody tr {
  border-bottom: 1px solid var(--bg-rule);
  transition: background 0.1s;
}
tbody tr:hover { background: rgba(111, 27, 27, 0.03); }
td {
  padding: 13px 16px;
  font-size: 13px;
  vertical-align: baseline;
}
td.num {
  text-align: right;
  font-family: var(--mono);
  font-size: 12.5px;
  font-weight: 400;
}
td.studio {
  font-family: var(--serif);
  font-weight: 400;
  font-size: 14px;
  letter-spacing: -0.005em;
  max-width: 280px;
}
td.meta {
  font-family: var(--mono);
  font-size: 11px;
  color: var(--ink-dim);
  letter-spacing: 0.03em;
}
td .platform-tag {
  font-family: var(--mono);
  font-size: 9.5px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  padding: 2px 6px;
  border: 1px solid var(--bg-rule);
  color: var(--ink-dim);
}
td .platform-tag.fb { border-color: #2d4373; color: #2d4373; }
td .platform-tag.g { border-color: #2d5a2d; color: #2d5a2d; }
td .platform-tag.tt { border-color: #000; color: #000; }
td .unmatched {
  font-family: var(--serif);
  font-style: italic;
  color: var(--ink-mute);
  font-size: 12.5px;
}

/* FX RATES FOOTNOTE */
.footnote {
  margin-top: 48px;
  padding-top: 32px;
  border-top: 2px solid var(--ink);
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 48px;
}
.footnote h3 {
  font-family: var(--serif);
  font-size: 17px;
  font-weight: 500;
  margin-bottom: 12px;
}
.footnote p {
  font-family: var(--serif);
  font-size: 14px;
  line-height: 1.65;
  color: var(--ink-dim);
  margin-bottom: 10px;
}
.footnote p em { color: var(--oxblood); font-style: italic; }
.footnote code {
  font-family: var(--mono);
  font-size: 12px;
  background: var(--paper);
  padding: 1px 5px;
  border: 1px solid var(--bg-rule);
}
.fx-table {
  background: var(--paper);
  border: 1px solid var(--ink);
  padding: 20px;
}
.fx-table h4 {
  font-family: var(--mono);
  font-size: 10px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--ink-dim);
  margin-bottom: 14px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--bg-rule);
}
.fx-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px 16px;
  font-family: var(--mono);
  font-size: 11.5px;
}
.fx-grid .cur { color: var(--ink-dim); letter-spacing: 0.05em; }
.fx-grid .rate { text-align: right; color: var(--ink); font-variant-numeric: tabular-nums; }

/* COLOPHON */
.colophon {
  margin-top: 64px;
  padding-top: 24px;
  border-top: 1px solid var(--bg-rule);
  font-family: var(--mono);
  font-size: 10.5px;
  letter-spacing: 0.08em;
  color: var(--ink-mute);
  text-transform: uppercase;
  display: flex; justify-content: space-between; align-items: baseline;
  flex-wrap: wrap; gap: 12px;
}

/* RESPONSIVE */
@media (max-width: 1100px) {
  .kpi-grid { grid-template-columns: repeat(4, 1fr); }
  .kpi:nth-child(4) { border-right: none; }
  .kpi:nth-child(n+5) { border-top: 1px solid var(--bg-rule); }
  .two-col { grid-template-columns: 1fr; }
  .filters-card { grid-template-columns: 1fr 1fr; gap: 18px; }
  .filters-label { display: none; }
  .footnote { grid-template-columns: 1fr; }
}
@media (max-width: 700px) {
  .container { padding: 20px 20px 64px; }
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .kpi { border-right: 1px solid var(--bg-rule) !important; border-top: 1px solid var(--bg-rule); }
  .filters-card { grid-template-columns: 1fr; }
  .masthead h1 { font-size: 38px; }
}

/* PRINT STYLES - for exporting to PDF */
@media print {
  body { background: white; }
  .container { padding: 0; max-width: 100%; }
  .paper-texture { display: none; }
  .filters-card { display: none; }
  .table-scroll { max-height: none; overflow: visible; }
}
</style>
</head>
<body>
<div class="paper-texture"></div>
<div class="container">

  <header class="masthead">
    <div class="masthead-top">
      <span class="edition">The Portfolio Ledger · No. 001</span>
      <span class="vol">Vol. 1 — Marketing Performance</span>
      <span class="date" id="masthead-date"></span>
    </div>
    <h1>Cross-Platform <em>Performance</em> Ledger</h1>
    <p class="subhead">A consolidated view of paid media across Facebook, Google Ads and TikTok for the global studio portfolio — normalised to sterling, reconciled to geography.</p>
    <div class="masthead-meta">
      <span>PERIOD <strong id="meta-period">Last 30 days</strong></span>
      <span>SNAPSHOT <strong id="meta-snapshot"></strong></span>
      <span>ACCOUNTS <strong id="meta-accounts"></strong></span>
      <span>STUDIOS <strong id="meta-studios"></strong></span>
    </div>
  </header>

  <!-- I. KPIs -->
  <div class="section-rule">
    <span class="num">I.</span>
    <h2>Headline Metrics</h2>
    <span class="meta" id="kpi-meta">Filtered view</span>
  </div>
  <div class="kpi-grid" id="kpi-grid"></div>

  <!-- II. Filters -->
  <div class="section-rule">
    <span class="num">II.</span>
    <h2>Slice the Ledger</h2>
    <span class="meta">Region · Country · Platform</span>
  </div>
  <div class="filters-card">
    <div class="filters-label">Adjust the lens</div>
    <div class="filter-group">
      <label>Region</label>
      <select id="f-region"><option value="">All regions</option></select>
    </div>
    <div class="filter-group">
      <label>Country</label>
      <select id="f-country"><option value="">All countries</option></select>
    </div>
    <div class="filter-group">
      <label>Platform</label>
      <select id="f-platform"><option value="">All platforms</option></select>
    </div>
    <button class="reset-btn" id="reset-btn">Reset</button>
  </div>

  <!-- III. Breakdowns -->
  <div class="section-rule">
    <span class="num">III.</span>
    <h2>Distribution</h2>
    <span class="meta">By region &amp; platform</span>
  </div>
  <div class="two-col">
    <div class="chart-card">
      <div class="chart-head">
        <div class="chart-title">Spend by Country</div>
        <div class="chart-meta">GBP · Top 12</div>
      </div>
      <div id="bar-chart"></div>
    </div>
    <div class="platform-card">
      <div class="chart-head">
        <div class="chart-title">By Platform</div>
        <div class="chart-meta">Share of spend</div>
      </div>
      <div id="platform-breakdown"></div>
    </div>
  </div>

  <!-- IV. Detail Table -->
  <div class="section-rule">
    <span class="num">IV.</span>
    <h2>The Ledger</h2>
    <span class="meta">Per-account, sortable</span>
  </div>
  <div class="table-wrap">
    <div class="table-toolbar">
      <span class="count" id="row-count"></span>
      <input type="search" class="search" id="search-input" placeholder="Search studio or account…">
    </div>
    <div class="table-scroll">
      <table id="ledger-table">
        <thead>
          <tr>
            <th data-sort="studio_name">Studio <span class="sort-arrow">↕</span></th>
            <th data-sort="platform">Platform <span class="sort-arrow">↕</span></th>
            <th data-sort="country">Country <span class="sort-arrow">↕</span></th>
            <th data-sort="region">Region <span class="sort-arrow">↕</span></th>
            <th class="num sorted" data-sort="spend_gbp" data-dir="desc">Spend £ <span class="sort-arrow">▼</span></th>
            <th class="num" data-sort="impressions">Impressions <span class="sort-arrow">↕</span></th>
            <th class="num" data-sort="clicks">Clicks <span class="sort-arrow">↕</span></th>
            <th class="num" data-sort="ctr">CTR <span class="sort-arrow">↕</span></th>
            <th class="num" data-sort="cpm">CPM <span class="sort-arrow">↕</span></th>
            <th class="num" data-sort="leads">Leads <span class="sort-arrow">↕</span></th>
            <th class="num" data-sort="cpl">CPL <span class="sort-arrow">↕</span></th>
          </tr>
        </thead>
        <tbody id="ledger-body"></tbody>
      </table>
    </div>
  </div>

  <!-- V. Footnotes -->
  <div class="footnote">
    <div>
      <h3>Notes on the snapshot</h3>
      <p>Spend across Facebook (<em>account_currency</em>), Google Ads (<em>account_currency_code</em>) and TikTok is converted to sterling using the fixed rates at right. These rates are <em>editable</em> in the processing script and held constant for the period — they are not daily rates.</p>
      <p>Studio matching uses fuzzy name matching (similarity ≥ 0.72) against your studios list. Accounts that could not be matched are grouped under <em>Unmatched</em> — typically HQ-level, test, or franchise-sales accounts that don't correspond to a single location.</p>
      <p>Leads are pulled from Google Ads <code>conversions</code>. Facebook and TikTok lead data were not retrieved in this snapshot and are shown as <em>—</em>. CTR, CPM and CPL are computed client-side and will recalculate with every filter change.</p>
      <p><strong>Refresh:</strong> Ask Claude to regenerate this dashboard to pull fresh data. For true daily automation see the accompanying README — a small script on a free cron will replace the need to ask.</p>
    </div>
    <aside class="fx-table">
      <h4>FX to GBP · constant</h4>
      <div class="fx-grid" id="fx-grid"></div>
    </aside>
  </div>

  <div class="colophon">
    <span>Generated <span id="gen-date"></span> · Snapshot static, filters reactive</span>
    <span>The Portfolio Ledger · Typeset in Fraunces &amp; IBM Plex</span>
  </div>

</div>

<script id="snapshot-data" type="application/json">__DATA_PLACEHOLDER__</script>
<script>
(function() {
  'use strict';

  const DATA = JSON.parse(document.getElementById('snapshot-data').textContent);
  const rawRows = DATA.rows;
  const studios = DATA.studios;
  const fxRates = DATA.fx_rates_to_gbp;

  // ---- Enrich rows with CTR/CPM/CPL ----
  rawRows.forEach(r => {
    r.ctr = r.impressions > 0 ? (r.clicks / r.impressions) * 100 : 0;
    r.cpm = r.impressions > 0 ? (r.spend_gbp / r.impressions) * 1000 : 0;
    r.cpl = (r.leads && r.leads > 0) ? (r.spend_gbp / r.leads) : null;
  });

  // ---- Formatters ----
  const fmtCurrency = v => {
    if (v == null) return '—';
    if (v >= 1e6) return (v / 1e6).toFixed(2) + 'M';
    if (v >= 1e3) return (v / 1e3).toFixed(1) + 'k';
    return v.toFixed(0);
  };
  const fmtCurrencyFull = v => v == null ? '—' : v.toLocaleString('en-GB', { maximumFractionDigits: 0 });
  const fmtCurrencyDec = v => v == null ? '—' : v.toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const fmtInt = v => v == null ? '—' : v.toLocaleString('en-GB');
  const fmtPct = v => v == null ? '—' : v.toFixed(2) + '%';
  const fmtNumCompact = v => {
    if (v == null) return '—';
    if (v >= 1e6) return (v / 1e6).toFixed(1) + 'M';
    if (v >= 1e3) return (v / 1e3).toFixed(1) + 'k';
    return v.toFixed(0);
  };

  // ---- Populate filter options ----
  function populateFilters() {
    const regions = [...new Set(rawRows.map(r => r.region).filter(r => r && r !== 'Unmatched'))].sort();
    const countries = [...new Set(rawRows.map(r => r.country).filter(c => c && c !== 'Unmatched'))].sort();
    const platforms = [...new Set(rawRows.map(r => r.platform))].sort();

    const rSel = document.getElementById('f-region');
    const cSel = document.getElementById('f-country');
    const pSel = document.getElementById('f-platform');

    regions.forEach(r => { const o = document.createElement('option'); o.value = r; o.textContent = r; rSel.appendChild(o); });
    countries.forEach(c => { const o = document.createElement('option'); o.value = c; o.textContent = c; cSel.appendChild(o); });
    platforms.forEach(p => { const o = document.createElement('option'); o.value = p; o.textContent = p; pSel.appendChild(o); });

    // Add "Unmatched" at end for visibility
    const optUn = document.createElement('option'); optUn.value = 'Unmatched'; optUn.textContent = '— Unmatched —'; rSel.appendChild(optUn);
  }

  // ---- Cascading region → country filter ----
  function updateCountryOptions() {
    const region = document.getElementById('f-region').value;
    const cSel = document.getElementById('f-country');
    const currentVal = cSel.value;

    // Determine applicable countries
    const applicable = region
      ? [...new Set(rawRows.filter(r => r.region === region).map(r => r.country).filter(c => c && c !== 'Unmatched'))].sort()
      : [...new Set(rawRows.map(r => r.country).filter(c => c && c !== 'Unmatched'))].sort();

    cSel.innerHTML = '<option value="">All countries</option>';
    applicable.forEach(c => {
      const o = document.createElement('option'); o.value = c; o.textContent = c; cSel.appendChild(o);
    });
    // Preserve selection if still valid
    if (applicable.includes(currentVal)) cSel.value = currentVal;
  }

  // ---- Filter state & core apply fn ----
  function getFilters() {
    return {
      region: document.getElementById('f-region').value,
      country: document.getElementById('f-country').value,
      platform: document.getElementById('f-platform').value,
      search: document.getElementById('search-input').value.trim().toLowerCase(),
    };
  }

  function applyFilters(rows, f) {
    return rows.filter(r => {
      if (f.region && r.region !== f.region) return false;
      if (f.country && r.country !== f.country) return false;
      if (f.platform && r.platform !== f.platform) return false;
      if (f.search) {
        const hay = ((r.studio_name || '') + ' ' + (r.account_name || '') + ' ' + (r.country || '')).toLowerCase();
        if (!hay.includes(f.search)) return false;
      }
      return true;
    });
  }

  // ---- Compute aggregates ----
  function aggregate(rows) {
    const totals = { spend: 0, impressions: 0, clicks: 0, leads: 0, accounts: rows.length };
    rows.forEach(r => {
      totals.spend += r.spend_gbp;
      totals.impressions += r.impressions;
      totals.clicks += r.clicks;
      if (r.leads) totals.leads += r.leads;
    });
    totals.ctr = totals.impressions > 0 ? (totals.clicks / totals.impressions) * 100 : 0;
    totals.cpm = totals.impressions > 0 ? (totals.spend / totals.impressions) * 1000 : 0;
    totals.cpl = totals.leads > 0 ? (totals.spend / totals.leads) : null;
    return totals;
  }

  // ---- Render KPIs ----
  function renderKPIs(totals) {
    const tiles = [
      { label: 'Total Spend', value: '<span class="cur">£</span>' + fmtCurrencyFull(totals.spend), sub: 'normalised to GBP' },
      { label: 'Impressions', value: fmtCurrency(totals.impressions), sub: fmtInt(totals.impressions) + ' served' },
      { label: 'Clicks', value: fmtCurrency(totals.clicks), sub: fmtInt(totals.clicks) + ' recorded' },
      { label: 'CTR', value: totals.ctr.toFixed(2) + '<span class="suffix">%</span>', sub: 'click-through rate' },
      { label: 'CPM', value: '<span class="cur">£</span>' + totals.cpm.toFixed(2), sub: 'per thousand views' },
      { label: 'Leads', value: fmtCurrency(totals.leads), sub: 'Google Ads only' },
      { label: 'CPL', value: totals.cpl ? '<span class="cur">£</span>' + totals.cpl.toFixed(2) : '—', sub: totals.cpl ? 'per lead' : 'no lead data' },
    ];
    document.getElementById('kpi-grid').innerHTML = tiles.map(t => `
      <div class="kpi">
        <div class="kpi-label">${t.label}</div>
        <div class="kpi-value">${t.value}</div>
        <div class="kpi-sub"><span class="bullet"></span>${t.sub}</div>
      </div>
    `).join('');
  }

  // ---- Render bar chart (spend by country) ----
  function renderBarChart(rows) {
    const byCountry = {};
    rows.forEach(r => {
      const c = r.country || 'Unknown';
      if (c === 'Unmatched') return;
      byCountry[c] = (byCountry[c] || 0) + r.spend_gbp;
    });
    const sorted = Object.entries(byCountry).sort((a, b) => b[1] - a[1]).slice(0, 12);
    const max = sorted.length > 0 ? sorted[0][1] : 1;

    const classes = ['a', 'b', 'c', 'd'];
    const html = sorted.map(([k, v], i) => {
      const pct = (v / max) * 100;
      return `
        <div class="bar-row">
          <div class="bar-label">${k}</div>
          <div class="bar-track"><div class="bar-fill ${classes[i % 4]}" style="width:${pct}%"></div></div>
          <div class="bar-value">£${fmtCurrencyFull(v)}</div>
        </div>
      `;
    }).join('');
    document.getElementById('bar-chart').innerHTML = html || '<p style="color:var(--ink-mute);font-style:italic;padding:20px 0">No data for current filter.</p>';
  }

  // ---- Render platform breakdown ----
  function renderPlatformBreakdown(rows) {
    const byP = {};
    rows.forEach(r => {
      if (!byP[r.platform]) byP[r.platform] = { spend: 0, clicks: 0, impressions: 0, count: 0 };
      byP[r.platform].spend += r.spend_gbp;
      byP[r.platform].clicks += r.clicks;
      byP[r.platform].impressions += r.impressions;
      byP[r.platform].count += 1;
    });
    const sorted = Object.entries(byP).sort((a, b) => b[1].spend - a[1].spend);
    const maxSpend = sorted.length > 0 ? sorted[0][1].spend : 1;

    const html = sorted.map(([name, s]) => {
      const pct = (s.spend / maxSpend) * 100;
      return `
        <div class="platform-row">
          <div class="platform-name">${name}</div>
          <div class="platform-stats">${s.count} acc · ${fmtNumCompact(s.clicks)} clicks · ${fmtNumCompact(s.impressions)} imp</div>
          <div class="platform-spend">£${fmtCurrencyFull(s.spend)}</div>
          <div class="platform-bar"><div class="platform-bar-fill" style="width:${pct}%"></div></div>
        </div>
      `;
    }).join('');
    document.getElementById('platform-breakdown').innerHTML = html || '<p style="color:var(--ink-mute);font-style:italic;padding:20px 0">No data.</p>';
  }

  // ---- Render table ----
  let sortField = 'spend_gbp';
  let sortDir = 'desc';

  function sortRows(rows) {
    return [...rows].sort((a, b) => {
      let av = a[sortField], bv = b[sortField];
      if (av == null) av = -Infinity;
      if (bv == null) bv = -Infinity;
      if (typeof av === 'string') return sortDir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av);
      return sortDir === 'asc' ? av - bv : bv - av;
    });
  }

  function renderTable(rows) {
    const sorted = sortRows(rows);
    const tbody = document.getElementById('ledger-body');
    const platformClass = p => p === 'Facebook' ? 'fb' : p === 'Google Ads' ? 'g' : 'tt';
    const platformShort = p => p === 'Facebook' ? 'FB' : p === 'Google Ads' ? 'GOOGLE' : 'TIKTOK';
    tbody.innerHTML = sorted.map(r => `
      <tr>
        <td class="studio">${r.studio_name || `<span class="unmatched">${r.account_name}</span>`}</td>
        <td><span class="platform-tag ${platformClass(r.platform)}">${platformShort(r.platform)}</span></td>
        <td class="meta">${r.country === 'Unmatched' ? '<span class="unmatched">—</span>' : r.country}</td>
        <td class="meta">${r.region === 'Unmatched' ? '<span class="unmatched">—</span>' : r.region}</td>
        <td class="num">£${fmtCurrencyFull(r.spend_gbp)}</td>
        <td class="num">${fmtInt(r.impressions)}</td>
        <td class="num">${fmtInt(r.clicks)}</td>
        <td class="num">${r.ctr.toFixed(2)}%</td>
        <td class="num">£${r.cpm.toFixed(2)}</td>
        <td class="num">${r.leads != null ? fmtInt(Math.round(r.leads)) : '—'}</td>
        <td class="num">${r.cpl != null ? '£' + r.cpl.toFixed(2) : '—'}</td>
      </tr>
    `).join('');

    // Update sort arrows
    document.querySelectorAll('th[data-sort]').forEach(th => {
      th.classList.remove('sorted');
      const arrow = th.querySelector('.sort-arrow');
      if (th.dataset.sort === sortField) {
        th.classList.add('sorted');
        arrow.textContent = sortDir === 'asc' ? '▲' : '▼';
      } else {
        arrow.textContent = '↕';
      }
    });

    document.getElementById('row-count').textContent = `${sorted.length} accounts · sorted by ${sortField.replace('_', ' ')} (${sortDir})`;
  }

  // ---- Render FX table ----
  function renderFX() {
    const grid = document.getElementById('fx-grid');
    grid.innerHTML = Object.entries(fxRates).map(([k, v]) => `
      <span class="cur">${k}</span><span class="rate">${v === 1 ? '1.0000' : v.toFixed(4)}</span>
    `).join('');
  }

  // ---- Re-render everything ----
  function redraw() {
    const f = getFilters();
    const rows = applyFilters(rawRows, f);
    const totals = aggregate(rows);
    renderKPIs(totals);
    renderBarChart(rows);
    renderPlatformBreakdown(rows);
    renderTable(rows);

    // Update meta text
    const bits = [];
    if (f.region) bits.push(f.region);
    if (f.country) bits.push(f.country);
    if (f.platform) bits.push(f.platform);
    document.getElementById('kpi-meta').textContent = bits.length > 0 ? bits.join(' · ') : 'All accounts · all regions';
  }

  // ---- Meta strings ----
  function initMeta() {
    const genDate = new Date(DATA.generated_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });
    document.getElementById('masthead-date').textContent = genDate;
    document.getElementById('meta-period').textContent = 'Last 30 days';
    document.getElementById('meta-snapshot').textContent = DATA.generated_at;
    document.getElementById('meta-accounts').textContent = rawRows.length;
    document.getElementById('meta-studios').textContent = studios.length;
    document.getElementById('gen-date').textContent = genDate;
  }

  // ---- Wire events ----
  function wire() {
    document.getElementById('f-region').addEventListener('change', () => { updateCountryOptions(); redraw(); });
    document.getElementById('f-country').addEventListener('change', redraw);
    document.getElementById('f-platform').addEventListener('change', redraw);
    document.getElementById('search-input').addEventListener('input', redraw);
    document.getElementById('reset-btn').addEventListener('click', () => {
      document.getElementById('f-region').value = '';
      document.getElementById('f-country').value = '';
      document.getElementById('f-platform').value = '';
      document.getElementById('search-input').value = '';
      updateCountryOptions();
      redraw();
    });
    document.querySelectorAll('th[data-sort]').forEach(th => {
      th.addEventListener('click', () => {
        const field = th.dataset.sort;
        if (sortField === field) {
          sortDir = sortDir === 'asc' ? 'desc' : 'asc';
        } else {
          sortField = field;
          sortDir = (field === 'studio_name' || field === 'platform' || field === 'country' || field === 'region') ? 'asc' : 'desc';
        }
        redraw();
      });
    });
  }

  // ---- Go ----
  populateFilters();
  initMeta();
  renderFX();
  wire();
  redraw();
})();
</script>
</body>
</html>
"""


def render(snapshot: dict, out_path: Path) -> None:
    """Render the dashboard HTML with the given snapshot embedded."""
    data_json = json.dumps(snapshot, separators=(",", ":"))
    # Escape any </script> in the data to avoid breaking the script block
    data_json = data_json.replace("</script>", "<\\/script>")
    html_out = HTML.replace("__DATA_PLACEHOLDER__", data_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_out, encoding="utf-8")


# CLI entry for standalone use
if __name__ == "__main__":
    import sys
    here = Path(__file__).resolve().parent.parent
    snapshot_path = here / "raw" / "snapshot.json"
    out_path = here / "public" / "index.html"
    snapshot = json.loads(snapshot_path.read_text())
    render(snapshot=snapshot, out_path=out_path)
    print(f"wrote {out_path}")
