# Cloudflare

Method: API (undocumented endpoint)

- Account id: anonymized (constant in the file's environment).
- Endpoint:
  `GET https://api.cloudflare.com/client/v4/accounts/{account_id}/billing/receipts/{invoice_id}/pdf?doctype=invoice`
- The billing endpoint is NOT documented. It was discovered by watching the
  browser network traffic while downloading an invoice manually.
- Result: 7/7 invoices downloaded with this single endpoint.

Destination: PDF file, then Pennylane import (see adapters).
