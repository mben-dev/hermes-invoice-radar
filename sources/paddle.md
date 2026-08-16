# Paddle

Method: email

- Receipts arrive by email as HTML with tracking links. The links expire.
- Pipeline: Gmail search -> extract link -> Playwright -> PDF.
  See `scripts/gmail_to_pdf.py`.
- Pitfall: receipts that look "missing" can already be matched. The
  `matched_invoices` check in `adapters/pennylane/scan_missing.py` must be run
  before importing, otherwise you import duplicates (8 out of 11 candidates
  were false positives in one pass).
