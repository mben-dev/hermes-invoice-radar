#!/usr/bin/env python3
"""scan_missing.py - list transactions without a supporting document.

Usage:
  python3 scan_missing.py            # groups by supplier (top lines) + total
  python3 scan_missing.py --all      # list every transaction individually

Prereq: PENNYLANE_API_KEY in the environment (scope transactions:read).

Key correction (validated 2026-08-16): a transaction justified through the
supplier_invoice + matched_transactions flow does NOT expose
file_attachment_id. The scan therefore calls GET /transactions/{id}/matched_invoices
for every candidate (non-empty items = already justified -> excluded).
Without this check, already-justified transactions come back as false
positives (Paddle: 11 "missing" of which 8 were actually matched).
"""
import json
import os
import sys
import time
import urllib.request
from collections import defaultdict

BASE = "https://app.pennylane.com/api/external/v2"

def api_key():
    """Read PENNYLANE_API_KEY from ~/.hermes/.env (never commit it)."""
    for line in open(os.path.expanduser("~/.hermes/.env")):
        if line.startswith("PENNYLANE_API_KEY="):
            return line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("PENNYLANE_API_KEY not found in ~/.hermes/.env")

def api_get(path, key, retries=3):
    """GET with retry on transient errors (rate limit)."""
    req = urllib.request.Request(BASE + path)
    req.add_header("Authorization", f"Bearer {key}")
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(1.5 * (attempt + 1))

def fetch_all_transactions(key):
    """Cursor pagination: items + has_more + next_cursor (no page numbers)."""
    items = []
    cursor = None
    while True:
        path = "/transactions?limit=100" + (f"&cursor={cursor}" if cursor else "")
        data = api_get(path, key)
        items.extend(data.get("items", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
        if len(items) > 3000:
            break
    return items

# Labels that are never supplier invoices: bank fees, internal transfers,
# state levies, salaries.
EXCLUDE_KW = [
    "FRAIS PAIE CB", "VIR ", "PRLV SEPA", "TVA", "URSSAF", "SIE PARIS",
    "DGFIP", "REMBOURSEMENT", "COMPTE ASSOCIE", "GOCARDLESS",
    "COTISATION", "PRELEVEMENT", "INTERETS", "FRAIS BANCAIRES",
    "APPORT", "Virement", "virement",
]

def is_excluded(label):
    upper = (label or "").upper()
    return any(k.upper() in upper for k in EXCLUDE_KW)

# Known providers. Extend as new ones are discovered; unmapped labels fall
# into "AUTRE" and are reviewed manually.
PROVIDERS = [
    "CLOUDFLARE", "PADDLE", "LEMSQZY", "LEMONSQUEEZY", "GANDI", "X CORP",
    "TWITTER", "HETZNER", "DIGITALOCEAN", "DIGITAL OCEAN", "GITHUB",
    "RAYCAST", "MIDJOURNEY", "APPLE", "MICROSOFT", "AZURE", "AWS",
    "AMAZON", "STRIPE", "SENTRY", "POSTHOG", "VERCEL", "SUPABASE",
    "NEON", "OPENAI", "CHATGPT", "ANTHROPIC", "CLAUDE", "DEEPSEEK",
    "NOTION", "FIGMA", "SLACK", "ZOOM", "SCALEWAY", "OVH", "IONOS",
    "MAILJET", "RESEND", "APIFY", "DATAFORSEO", "GOOGLE", "SPOTIFY",
    "LINKEDIN", "META", "FACEBOOK", "HUBSPOT", "AIRTABLE", "ZAPIER",
    "CURSOR", "SEMRUSH", "TESLA", "RAILWAY", "TRAINLINE", "SNAP",
]

def provider_of(label):
    upper = (label or "").upper()
    for kw in PROVIDERS:
        if kw in upper:
            return kw
    return "AUTRE"

def is_matched(tx, key):
    """Real match check. The matched_invoices FIELD on a transaction is only
    an endpoint URL present on EVERY transaction; never trust it. Call the
    endpoint instead."""
    tx_id = tx.get("id")
    for attempt in range(3):
        try:
            mi = api_get(f"/transactions/{tx_id}/matched_invoices", key)
            return bool(mi.get("items"))
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    return False

def main():
    key = api_key()
    all_flag = "--all" in sys.argv
    items = fetch_all_transactions(key)

    groups = defaultdict(list)
    already = 0
    for t in items:
        try:
            amount = float(t.get("amount") or 0)
        except (TypeError, ValueError):
            continue
        label = t.get("label") or ""
        if amount >= 0 or is_excluded(label):
            continue
        if t.get("file_attachment_id") or t.get("attachment_id"):
            already += 1
            continue
        if is_matched(t, key):
            already += 1
            continue
        groups[provider_of(label)].append(t)

    total = 0
    for provider, txs in sorted(groups.items(), key=lambda kv: -sum(
            float(x.get("amount") or 0) for x in kv[1])):
        prov_total = sum(float(x.get("amount") or 0) for x in txs)
        total += prov_total
        print(f"{provider}: {len(txs)} tx, {prov_total:.2f} EUR")
        if all_flag:
            for t in txs[:20]:
                print(f"  {t.get('date')} {t.get('amount')} {t.get('label')} [{t.get('id')}]")
    print(f"TOTAL missing: {total:.2f} EUR | already justified: {already}")

if __name__ == "__main__":
    main()
