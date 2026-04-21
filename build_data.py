"""
build_data.py — process raw Windsor.ai pulls into a unified snapshot.

Handles:
  - Loading the studios list (TSV)
  - Fuzzy-matching account names to studios
  - Normalising spend across currencies to GBP
  - Emitting a single snapshot dict for the dashboard
"""
from __future__ import annotations
import json
import re
import csv
from difflib import SequenceMatcher
from pathlib import Path
from datetime import date
from typing import Any

# ------------------------------------------------------------------------
# FX rates to GBP — held constant for the snapshot period.
# Edit these here; no other changes needed.
# ------------------------------------------------------------------------
FX_TO_GBP: dict[str, float] = {
    "GBP": 1.0,
    "USD": 0.79,
    "EUR": 0.85,
    "AUD": 0.51,
    "CAD": 0.57,
    "AED": 0.215,
    "SGD": 0.59,
    "HKD": 0.10,
    "KRW": 0.00056,
    "CHF": 0.88,
    "NZD": 0.47,
    "SAR": 0.21,
}

# Fuzzy match threshold (0.0–1.0). Lower = looser matching.
MATCH_THRESHOLD = 0.72


# ------------------------------------------------------------------------
# Name normalisation & matching
# ------------------------------------------------------------------------
_NOISE_TOKENS = [
    "ads", "ad account", "ad", "account", "spare", "old", "do not use",
    "don't use", "not in use", "disabled", "back up", "backup",
    "former mmp", "mmp", "csg", "former", "budget", "previous",
    "previously", "new", " to ", " ca ", " us ", " uk ", "paused",
]


def normalize_name(s: str) -> str:
    """Lowercase, strip brackets/noise, collapse whitespace."""
    s = s.lower()
    s = re.sub(r"\([^)]*\)", "", s)
    s = re.sub(r"\[[^\]]*\]", "", s)
    # Expand common abbreviations BEFORE stripping noise
    s = re.sub(r"\baf\s*-\s*", "anytime fitness ", s)
    s = re.sub(r"\bar\s*-\s*af\s*", "anytime fitness ", s)
    s = re.sub(r"\bar\s*-\s*", "anytime fitness ", s)
    for n in _NOISE_TOKENS:
        s = s.replace(n, " ")
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def load_studios(path: Path) -> list[dict]:
    studios = []
    with open(path) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            studios.append({
                "studio_id": row["Studio ID"].strip(),
                "studio_name": row["Studio Name"].strip(),
                "country": (row.get("Country") or "Unknown").strip() or "Unknown",
                "region": (row.get("Region") or "Unknown").strip() or "Unknown",
                "normalized": normalize_name(row["Studio Name"]),
            })
    return studios


def match_account(account_name: str, studios: list[dict]) -> dict | None:
    """Return the best studio match above threshold, or None."""
    norm = normalize_name(account_name)
    if not norm:
        return None
    # Reject numeric-only names (account-ID fallbacks)
    if re.fullmatch(r"[\d\s]+", norm):
        return None
    # Require at least 3 alpha characters of signal
    alpha = re.sub(r"[^a-z]", "", norm)
    if len(alpha) < 3:
        return None

    best = None
    best_score = MATCH_THRESHOLD
    for s in studios:
        if not s["normalized"]:
            continue
        score = _similarity(norm, s["normalized"])
        if score > best_score:
            best_score = score
            best = s
    return best


def to_gbp(amount: float | None, currency: str | None) -> float | None:
    if amount is None or currency is None:
        return None
    rate = FX_TO_GBP.get(currency)
    if rate is None:
        return None
    return amount * rate


# ------------------------------------------------------------------------
# Core build function
# ------------------------------------------------------------------------
def build(raw_dir: Path, studios_path: Path) -> dict:
    """
    Load raw datasets from `raw_dir` and produce a unified snapshot dict.

    Expects these files in raw_dir:
      - fb_7d.json
      - fb_30d.json
      - google_ads_30d.json
      - tiktok_30d.json
    """
    studios = load_studios(studios_path)

    fb_7d = _read_json(raw_dir / "fb_7d.json")
    fb_30d = _read_json(raw_dir / "fb_30d.json")
    google = _read_json(raw_dir / "google_ads_30d.json")
    tiktok = _read_json(raw_dir / "tiktok_30d.json")

    # Build account_id → (name, currency) map from the 7d FB data
    fb_name_map = {
        r["account_id"]: (r.get("account_name") or r["account_id"],
                           r.get("account_currency") or "USD")
        for r in fb_7d
    }

    rows: list[dict] = []

    # Facebook
    for r in fb_30d:
        aid = r["account_id"]
        name, lookup_ccy = fb_name_map.get(aid, (aid, "USD"))
        currency = r.get("account_currency") or lookup_ccy
        spend_raw = r.get("spend", 0) or 0
        spend_gbp = to_gbp(spend_raw, currency)
        if spend_gbp is None:
            continue
        match = match_account(name, studios)
        rows.append(_row("Facebook", aid, name, currency, spend_raw, spend_gbp, r, match, leads=None))

    # Google Ads — leads from conversions field
    for r in google:
        aid = r.get("account_id", "")
        name = r.get("account_name") or aid
        currency = r.get("account_currency_code", "USD")
        spend_raw = r.get("spend", 0) or 0
        spend_gbp = to_gbp(spend_raw, currency)
        if spend_gbp is None:
            continue
        match = match_account(name, studios)
        leads = r.get("conversions", 0) or 0
        rows.append(_row("Google Ads", aid, name, currency, spend_raw, spend_gbp, r, match, leads=round(leads, 2)))

    # TikTok
    for r in tiktok:
        aid = r.get("account_id", "")
        name = r.get("account_name") or aid
        currency = r.get("account_currency", "GBP")
        spend_raw = r.get("spend", 0) or 0
        spend_gbp = to_gbp(spend_raw, currency) or spend_raw  # fallback to native if FX missing
        match = match_account(name, studios)
        rows.append(_row("TikTok", aid, name, currency, spend_raw, spend_gbp, r, match, leads=None))

    return {
        "generated_at": date.today().isoformat(),
        "period": "last_30_days",
        "fx_rates_to_gbp": FX_TO_GBP,
        "match_threshold": MATCH_THRESHOLD,
        "rows": rows,
        "studios": studios,
    }


def _read_json(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


def _row(platform: str, aid: str, name: str, currency: str,
         spend_raw: float, spend_gbp: float, r: dict, match: dict | None,
         leads: float | None) -> dict:
    return {
        "platform": platform,
        "account_id": aid,
        "account_name": name,
        "currency": currency,
        "spend_native": round(spend_raw, 2),
        "spend_gbp": round(spend_gbp, 2),
        "impressions": int(r.get("impressions", 0) or 0),
        "clicks": int(r.get("clicks", 0) or 0),
        "leads": leads,
        "studio_id": match["studio_id"] if match else None,
        "studio_name": match["studio_name"] if match else None,
        "country": match["country"] if match else "Unmatched",
        "region": match["region"] if match else "Unmatched",
    }


# ------------------------------------------------------------------------
# CLI entry (for standalone debugging)
# ------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    here = Path(__file__).resolve().parent.parent
    snapshot = build(raw_dir=here / "raw", studios_path=here / "studios.tsv")
    out = here / "raw" / "snapshot.json"
    out.write_text(json.dumps(snapshot, separators=(",", ":")))
    print(f"wrote {out} ({len(snapshot['rows'])} rows)")
