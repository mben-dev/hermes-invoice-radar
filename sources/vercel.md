# Vercel

Method: email (Stripe)

- `GET /v1/billing/charges` returns JSONL without PDFs. Useless for
  supporting documents.
- The real receipts come by email from Stripe (22 PDFs in one pass).
- Gmail query: `from:stripe vercel` + subject + date window.
- Alert to watch: "Payment Failed And Shutdown Coming Soon" emails mean an
  unpaid charge; report them, do not hide them.
