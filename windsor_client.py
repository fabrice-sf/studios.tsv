"""
Thin wrapper around the Windsor.ai connectors REST API.

Docs: https://windsor.ai/api-information/
Endpoint pattern: https://connectors.windsor.ai/{connector}?api_key=...
"""
from __future__ import annotations
import os
import time
import json
import logging
from typing import Any
from urllib.parse import urlencode

import requests

log = logging.getLogger(__name__)

BASE_URL = "https://connectors.windsor.ai"
DEFAULT_TIMEOUT = 180  # Facebook with many accounts can be slow
MAX_RETRIES = 3
RETRY_BACKOFF = 5  # seconds, doubled on each retry


class WindsorError(Exception):
    """Raised when a Windsor API call fails after retries."""


def _api_key() -> str:
    key = os.environ.get("WINDSOR_API_KEY")
    if not key:
        raise WindsorError(
            "WINDSOR_API_KEY is not set. "
            "Get your key from https://onboard.windsor.ai (API Access section) "
            "and add it as a repository secret named WINDSOR_API_KEY."
        )
    return key


def pull(
    connector: str,
    fields: list[str],
    date_preset: str = "last_30d",
    extra_params: dict[str, Any] | None = None,
) -> list[dict]:
    """
    Pull data from a Windsor connector.

    Args:
        connector: connector id, e.g. 'facebook', 'google_ads', 'tiktok'
        fields: list of field names to retrieve
        date_preset: 'last_7d', 'last_30d', etc.
        extra_params: additional query string params

    Returns list of row dicts (from the 'data' key of the JSON response,
    falling back to the raw response if already a list).
    """
    params = {
        "api_key": _api_key(),
        "fields": ",".join(fields),
        "date_preset": date_preset,
    }
    if extra_params:
        params.update(extra_params)

    url = f"{BASE_URL}/{connector}"
    log.info("→ pulling %s (%s, %d fields)", connector, date_preset, len(fields))

    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
            resp.raise_for_status()
            payload = resp.json()
            # Windsor sometimes wraps the list in {"data": [...]} and sometimes returns the list directly
            if isinstance(payload, dict) and "data" in payload:
                rows = payload["data"]
            elif isinstance(payload, list):
                rows = payload
            else:
                log.warning("unexpected response shape from %s: %s", connector, type(payload))
                rows = []
            log.info("← %s returned %d rows", connector, len(rows))
            return rows
        except requests.exceptions.Timeout as e:
            last_err = e
            log.warning("timeout on %s attempt %d/%d", connector, attempt, MAX_RETRIES)
        except requests.exceptions.HTTPError as e:
            # Auth errors are fatal, no point retrying
            if e.response is not None and e.response.status_code in (401, 403):
                raise WindsorError(f"authentication failed for {connector}: {e}") from e
            last_err = e
            log.warning("HTTP error on %s attempt %d/%d: %s", connector, attempt, MAX_RETRIES, e)
        except requests.exceptions.RequestException as e:
            last_err = e
            log.warning("request error on %s attempt %d/%d: %s", connector, attempt, MAX_RETRIES, e)

        if attempt < MAX_RETRIES:
            wait = RETRY_BACKOFF * (2 ** (attempt - 1))
            log.info("retrying %s in %ds…", connector, wait)
            time.sleep(wait)

    raise WindsorError(f"failed to pull {connector} after {MAX_RETRIES} attempts: {last_err}")


def filter_positive_spend(rows: list[dict]) -> list[dict]:
    """Client-side filter: keep only rows with spend > 0."""
    return [r for r in rows if (r.get("spend") or 0) > 0]
