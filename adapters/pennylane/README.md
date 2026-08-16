# Pennylane adapter

The output side of the radar: the accounting software.

Base URL: `https://app.pennylane.com/api/external/v2`
API key scope: `supplier_invoices` (scan needs `transactions:read`).

## Flow (exact)

```
1. GET  /transactions?per_page=100[&cursor=...]   -> items + next_cursor (NO page pagination)
2. POST /file_attachments (multipart, field "file") -> file_attachment_id
3. POST /supplier_invoices/import                   -> creates the supplier invoice
4. POST /supplier_invoices/{id}/matched_transactions {"transaction_id": N} -> 204
```

## Pitfalls (the most time-consuming ones)

- The import endpoint is `/supplier_invoices/import`, NOT `/supplier_invoices`
  (404).
- Amounts must be STRINGS, not floats (`"currency_amount_before_tax": "18.22"`),
  otherwise 400 ValidateError.
- `409` = the PDF is already imported. Recover the existing id (regex
  `ID (\d+)` in the body) and match on it.
- Verify the match with `GET /transactions/{id}/matched_invoices` (non-empty
  items = matched).
- The `matched_invoices` FIELD on a transaction is just an endpoint URL
  present on EVERY transaction. Never trust it to detect a match.
- Upload: the response can be `{"id": N}` at the root or under
  `file_attachment`. Handle both.
- Pagination: `items` + `next_cursor` (not `transactions`, not `page`).
- Supplier creation: `POST /suppliers` with `{"name": "X"}` -> id at the root
  or under `supplier`.

## Scripts

- `scan_missing.py` - list transactions without a supporting document,
  grouped by supplier. THE source of truth for "what is missing". The
  `list_restants` variant is NOT reliable (silent rate limit); always use
  this one.
- `import_invoice.py` - upload -> import -> match for one PDF, with the 409
  handling and the amount-matching helpers (`pdf_amounts`, `find_pdf_for`).

## Runner pattern (per platform)

```
from import_invoice import already_matched, upload_pdf, import_and_match

pdf = find_pdf_for("cloudflare", 18.22)
if pdf and not already_matched(KEY, tx_id):
    fid, err = upload_pdf(KEY, pdf)
    if fid:
        print(import_and_match(KEY, fid, "Cloudflare", "2026-07-11",
                               "18.22", tx_id, "Cloudflare"))
```
