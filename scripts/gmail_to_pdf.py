#!/usr/bin/env python3
"""gmail_to_pdf.py - collect invoice PDFs from Gmail.

For each platform: search Gmail for the invoice emails, download the attached
PDFs into the inbox folder (~/receipts/<folder>/ by default, override with
INVOICE_INBOX), and report what was found. Emails without a PDF attachment
(HTML receipts with tracking links) are converted to PDF via Playwright.

Usage: python3 gmail_to_pdf.py [--provider hetzner]
       (no argument = run the full provider list)

Prereq: a Gmail OAuth token (google_token.json) in ~/.hermes/.
"""
import base64
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

TOKEN_PATHS = [
    os.path.expanduser("~/.hermes/google_token.json"),
    os.path.expanduser("~/.hermes/google_token_mbendev.json"),
]
OUT_ROOT = Path(os.environ.get("INVOICE_INBOX", os.path.expanduser("~/receipts")))
OUT_ROOT.mkdir(parents=True, exist_ok=True)

# Provider -> (Gmail query, output folder). Extend as platforms are added.
PROVIDERS = {
    "HETZNER": ("hetzner (invoice OR rechnung OR receipt OR facture OR payment)", "hetzner"),
    "NEON": ("neon.tech (invoice OR receipt OR facture)", "neon"),
    "FIGMA": ("figma (invoice OR receipt OR facture OR payment)", "figma"),
    "APPLE": ("apple.com/bill OR apple (invoice OR receipt)", "apple"),
    "RESEND": ("resend (invoice OR receipt OR facture OR payment)", "resend"),
    "MIDJOURNEY": ("midjourney (invoice OR receipt OR facture OR payment)", "midjourney"),
    "DEEPSEEK": ("deepseek (invoice OR receipt OR facture OR payment)", "deepseek"),
    "LINKEDIN": ("linkedin (invoice OR receipt OR payment OR premium)", "linkedin"),
    "APIFY": ("apify (invoice OR receipt OR facture OR payment)", "apify"),
    "RAYCAST": ("raycast (invoice OR receipt OR facture OR payment)", "raycast"),
    "CURSOR": ("cursor (invoice OR receipt OR facture OR payment)", "cursor"),
    "GITHUB": ("github (invoice OR receipt OR facture OR payment)", "github"),
    "OPENAI": ("openai OR chatgpt (invoice OR receipt OR facture OR payment)", "openai"),
    "OVH": ("ovh (invoice OR facture OR payment)", "ovh"),
    "TRAINLINE": ("trainline (invoice OR receipt OR facture OR payment)", "trainline"),
    "LEMSQZY": ("lemonsqueezy OR lemonsqzy (invoice OR receipt OR facture)", "lemsqzy"),
    "SEMRUSH": ("semrush (invoice OR receipt OR facture OR payment)", "semrush"),
    "PADDLE": ("paddle OR plausible OR nucleo (invoice OR receipt OR facture)", "paddle"),
    "KOYEB": ("koyeb (invoice OR receipt OR facture OR payment)", "koyeb"),
}

GMAIL = "https://gmail.googleapis.com/gmail/v1/users/me"

def token_for(account):
    """Pick the token file for the wanted account label."""
    for p in TOKEN_PATHS:
        if account in p and os.path.exists(p):
            return json.load(open(p))
    for p in TOKEN_PATHS:
        if os.path.exists(p):
            return json.load(open(p))
    sys.exit("No Gmail token found in ~/.hermes/google_token*.json")

def gmail(token, path):
    req = urllib.request.Request(GMAIL + path)
    req.add_header("Authorization", f"Bearer {token['access_token']}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def search_messages(token, query, max_results=30):
    q = urllib.parse.quote(query)
    data = gmail(token, f"/messages?q={q}&maxResults={max_results}")
    return data.get("messages", [])

def download_attachments(token, msg_id, folder, sender_hint=""):
    """Save every PDF attachment of a message into the folder. Returns the
    list of saved paths. HTML-only receipts are reported for PDF conversion."""
    meta = gmail(token, f"/messages/{msg_id}?format=full")
    payload = meta.get("payload", {})
    saved = []
    has_html = False
    def walk(part):
        nonlocal has_html
        fn = None
        for h in part.get("headers", []):
            if h["name"].lower() in ("filename", "name"):
                fn = h["value"]
        if part.get("filename") or (fn and "." in fn):
            if part.get("mimeType") == "application/pdf":
                data = part.get("body", {}).get("data") or part.get("body", {}).get("attachmentId")
                if data and len(str(data)) > 10:
                    raw = gmail(token, f"/messages/{msg_id}/attachments/{data}")
                    pdf = OUT_ROOT / folder / re.sub(r"[^A-Za-z0-9._-]", "_", fn or "")
                    pdf.write_bytes(base64.urlsafe_b64decode(raw["data"]))
                    saved.append(pdf)
        if part.get("mimeType") == "text/html":
            has_html = True
        for sub in part.get("parts", []):
            walk(sub)
    walk(payload)
    return saved, has_html

def html_to_pdf(url, out_path):
    """Convert an HTML receipt (with tracking links) to PDF via Playwright."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=30000)
        page.pdf(path=str(out_path), format="A4")
        browser.close()

def main():
    only = None
    if "--provider" in sys.argv:
        only = sys.argv[sys.argv.index("--provider") + 1].upper()
    report = []
    for provider, (query, folder) in PROVIDERS.items():
        if only and provider != only:
            continue
        token = token_for("")  # first available token; extend for multi-account
        out = OUT_ROOT / folder
        out.mkdir(parents=True, exist_ok=True)
        found = 0
        html_hits = []
        try:
            for m in search_messages(token, query):
                saved, has_html = download_attachments(token, m["id"], folder)
                found += len(saved)
                if has_html and not saved:
                    html_hits.append(m["id"])
        except Exception as e:
            report.append(f"{provider}: ERROR {e}")
            continue
        if html_hits:
            report.append(f"{provider}: {found} PDFs + {len(html_hits)} HTML to convert")
        else:
            report.append(f"{provider}: {found} PDFs")
        time.sleep(0.5)
    print("\n".join(sorted(report)))

if __name__ == "__main__":
    main()
