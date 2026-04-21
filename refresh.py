#!/usr/bin/env python3
"""
refresh.py — daily orchestrator

Pulls Facebook, Google Ads, and TikTok data from Windsor.ai, processes it into
a unified snapshot (GBP-normalised, studio-matched), and renders the dashboard
HTML into ./public/ for GitHub Pages.

Run manually:
    WINDSOR_API_KEY=xxx python scripts/refresh.py

Run in GitHub Actions:
    See .github/workflows/refresh.yml
"""
from __future__ import annotations
import json
import logging
import sys
from pathlib import Path

# Make sibling modules importable
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from windsor_client import pull, filter_positive_spend, WindsorError  # noqa: E402
import build_data  # noqa: E402
import build_html  # noqa: E402

REPO_ROOT = SCRIPT_DIR.parent
RAW_DIR = REPO_ROOT / "raw"
PUBLIC_DIR = REPO_ROOT / "public"

log = logging.getLogger(__name__)


def pull_all() -> dict[str, list[dict]]:
    """Pull all four Windsor queries. Facebook needs two (names in 7d, metrics in 30d)."""
    out: dict[str, list[dict]] = {}

    # Facebook 7-day with names — used as ID → name lookup
    out["fb_7d"] = filter_positive_spend(pull(
        connector="facebook",
        fields=["account_id", "account_name", "spend", "impressions", "clicks", "account_currency"],
        date_preset="last_7d",
    ))

    # Facebook 30-day without names (adding names causes consistent timeouts at scale)
    out["fb_30d"] = filter_positive_spend(pull(
        connector="facebook",
        fields=["account_id", "spend", "impressions", "clicks", "account_currency"],
        date_preset="last_30d",
    ))

    # Google Ads 30-day
    out["google_ads_30d"] = filter_positive_spend(pull(
        connector="google_ads",
        fields=["account_id", "account_name", "spend", "impressions", "clicks",
                "conversions", "account_currency_code"],
        date_preset="last_30d",
    ))

    # TikTok 30-day
    out["tiktok_30d"] = filter_positive_spend(pull(
        connector="tiktok",
        fields=["account_id", "account_name", "spend", "impressions", "clicks", "account_currency"],
        date_preset="last_30d",
    ))

    return out


def save_raw(datasets: dict[str, list[dict]]) -> None:
    RAW_DIR.mkdir(exist_ok=True)
    for name, rows in datasets.items():
        path = RAW_DIR / f"{name}.json"
        path.write_text(json.dumps(rows, separators=(",", ":")))
        log.info("saved %s (%d rows, %d bytes)", path.name, len(rows), path.stat().st_size)


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    try:
        log.info("=== stage 1: pull from Windsor.ai ===")
        datasets = pull_all()
        save_raw(datasets)

        log.info("=== stage 2: build snapshot ===")
        snapshot = build_data.build(
            raw_dir=RAW_DIR,
            studios_path=REPO_ROOT / "studios.tsv",
        )
        snapshot_path = RAW_DIR / "snapshot.json"
        snapshot_path.write_text(json.dumps(snapshot, separators=(",", ":")))
        log.info("saved snapshot with %d rows", len(snapshot["rows"]))

        log.info("=== stage 3: render HTML ===")
        PUBLIC_DIR.mkdir(exist_ok=True)
        html_path = PUBLIC_DIR / "index.html"
        build_html.render(snapshot=snapshot, out_path=html_path)
        log.info("rendered %s (%d bytes)", html_path, html_path.stat().st_size)

        # Summary
        totals = _totals(snapshot["rows"])
        log.info("=== summary ===")
        log.info("accounts: %d", len(snapshot["rows"]))
        log.info("matched: %d (%.0f%%)",
                 totals["matched"],
                 100 * totals["matched"] / max(len(snapshot["rows"]), 1))
        log.info("total spend: £%s", f"{totals['spend']:,.2f}")
        log.info("impressions: %s", f"{totals['impressions']:,}")
        log.info("clicks: %s", f"{totals['clicks']:,}")

        return 0

    except WindsorError as e:
        log.error("Windsor API error: %s", e)
        return 2
    except Exception as e:
        log.exception("unexpected error: %s", e)
        return 1


def _totals(rows: list[dict]) -> dict:
    return {
        "spend": sum(r["spend_gbp"] for r in rows),
        "impressions": sum(r["impressions"] for r in rows),
        "clicks": sum(r["clicks"] for r in rows),
        "matched": sum(1 for r in rows if r.get("studio_id")),
    }


if __name__ == "__main__":
    sys.exit(main())
