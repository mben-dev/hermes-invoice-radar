#!/usr/bin/env python3
"""import_invoice.py - upload a PDF, import it as a supplier invoice, match it.

Pipeline:
  1. GET  /transactions/{id}/matched_invoices     (skip if already matched)
  2. POST /file_attachments (multipart, field "file")
  3. POST /supplier_invoices/import
  4. POST /supplier_invoices/{id}/matched_transactions

Prereq: PENNYLANE_API_KEY in the environment (scope supplier_invoices).
"""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://app.pennylane.com/api/external/v2"
INBOX = Path(os.path.expanduser("~/justificatifs"))  # per-provider subfolders

def api_key():
    for line in open(os.path.expanduser("~/.hermes/.env")):
        if line.startswith("PENNYLANE_API_KEY="):
            return line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("PENNYLANE_API_KEY not found in ~/.hermes/.env")

def penny(key, method, path, body=None, binary=None, ctype=None):
    """Small HTTP helper returning (status, parsed_json)."""
    req = urllib.request.Request(BASE + path, method=method)
    req.add_header("Authorization", f"Bearer {key}")
    data = None
    if binary is not None:
        req.add_header("Content-Type", ctype)
        data = binary
    elif body is not None:
        req.add_header("Content-Type", "application/json")
        data = json.dumps(body).encode()
    try:
        with urllib.request.urlopen(req, data, timeout=40) as r:
            raw = r.read()
            return r.status, (json.loads(raw.decode() or "{}") if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw.decode() or "{}")
        except Exception:
            return e.code, {}

def get_supplier(key, name, keywords=None):
    """Find an existing supplier by name or keywords, else create it."""
    status, data = penny(key, "GET", "/suppliers?limit=200")
    for s in data.get("items", []):
        sname = (s.get("name") or "").lower()
        if name.lower() in sname:
            return s.get("id")
        if keywords:
            for kw in keywords:
                if kw.lower() in sname:
                    return s.get("id")
    status, data = penny(key, "POST", "/suppliers", {"name": name})
    return data.get("supplier", {}).get("id") or data.get("id")

def already_matched(key, tx_id):
    status, data = penny(key, "GET", f"/transactions/{tx_id}/matched_invoices")
    return bool(data.get("items"))

def upload_pdf(key, pdf_path):
    """POST /file_attachments. The response may carry the id at the root or
    under file_attachment; handle both."""
    payload = (
        b"--b\r\nContent-Disposition: form-data; name=\"file\"; filename=\""
        + Path(pdf_path).name.encode() + b"\"\r\nContent-Type: application/pdf\r\n\r\n"
        + open(pdf_path, "rb").read() + b"\r\n--b--\r\n"
    )
    status, data = penny(key, "POST", "/file_attachments",
                         binary=payload, ctype="multipart/form-data; boundary=b")
    if status == 409:
        # Already imported: the body carries the existing invoice id.
        return None, "already-imported"
    if status not in (200, 201):
        return None, f"upload {status} {json.dumps(data)[:120]}"
    return data.get("id") or data.get("file_attachment", {}).get("id"), None

def import_and_match(key, file_id, supplier_name, date, amount_eur, tx_id,
                     label, supplier_kw=None):
    """Import the attachment as a supplier invoice, then match the tx.

    Pitfalls (the most time-consuming ones):
    - The import endpoint is /supplier_invoices/import, NOT /supplier_invoices
      (404).
    - Amounts must be STRINGS, not floats ("currency_amount_before_tax":
      "18.22"), otherwise 400 ValidateError.
    - 409 on import = the PDF already exists; recover the id from the body
      (regex ID (\\d+)) and match on it.
    """
    supplier_id = get_supplier(key, supplier_name, supplier_kw)
    before = str(round(float(amount_eur) / 1.2, 2))
    tax = str(round(float(amount_eur) - float(amount_eur) / 1.2, 2))
    status, data = penny(key, "POST", "/supplier_invoices/import", {
        "file_attachment_id": file_id,
        "supplier_id": supplier_id,
        "date": date,
        "currency": "EUR",
        "currency_amount_before_tax": before,
        "currency_amount": str(amount_eur),
        "currency_tax": tax,
        "invoice_lines": [{
            "label": label,
            "currency_amount": str(amount_eur),
            "currency_tax": tax,
            "vat_rate": "FR_200",
        }],
    })
    inv_id = data.get("supplier_invoice", {}).get("id") or data.get("id")
    if status == 409:
        match = re.search(r"ID\s+(\d+)", json.dumps(data))
        inv_id = match.group(1) if match else None
    if not inv_id:
        return f"import {status} {json.dumps(data)[:120]}"
    status2, _ = penny(key, "POST",
                       f"/supplier_invoices/{inv_id}/matched_transactions",
                       {"transaction_id": tx_id})
    return f"ok inv {inv_id} match {status2}"

def pdf_amounts(pdf_path):
    """Extract the TTC amounts (EUR/USD) from a PDF via pdftotext."""
    r = subprocess.run(["pdftotext", str(pdf_path), "-"],
                       capture_output=True, text=True, timeout=25)
    txt = r.stdout
    amounts = set()
    for m in __import__("re").finditer(r"([€$])\s*(\d{1,4}[.,]\d{2})", txt):
        cur = "EUR" if m.group(1) == "€" else "USD"
        amounts.add((round(float(m.group(2).replace(",", ".")), 2), cur))
    for m in __import__("re").finditer(r"(\d{1,4}[.,]\d{2})\s*(?:EUR|€|USD)", txt):
        cur = "USD" if "USD" in m.group(0) else "EUR"
        amounts.add((round(float(m.group(1).replace(",", ".")), 2), cur))
    return amounts

def find_pdf_for(folder, target_eur, target_usd=None):
    """Find a PDF whose amount matches the transaction (0.01 tolerance)."""
    d = INBOX / folder
    if not d.exists():
        return None
    for f in sorted(d.glob("*.pdf")):
        try:
            amts = pdf_amounts(f)
        except Exception:
            continue
        if (round(target_eur, 2), "EUR") in amts:
            return f
        if target_usd and (round(target_usd, 2), "USD") in amts:
            return f
    return None

if __name__ == "__main__":
    import re
    KEY = api_key()
    # Example call shape (the caller provides folder/pdf/date/amount/tx_id):
    #   pdf = find_pdf_for("cloudflare", 18.22)
    #   if pdf and not already_matched(KEY, tx_id):
    #       fid, err = upload_pdf(KEY, pdf)
    #       if fid:
    #           print(import_and_match(KEY, fid, "Cloudflare", "2026-07-11",
    #                                  "18.22", tx_id, "Cloudflare"))
    print("Library module: import it from a runner script.")
