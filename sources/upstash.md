# Upstash

Method: email (Stripe)

- Sender: `"Upstash, Inc." <invoice+statements+acct_...>` (Stripe).
- Subject: `Your receipt from Upstash, Inc. #XXXX-XXXX`.
- Each email carries 2 PDFs: Invoice and Receipt. Import the Invoice.
- Gmail query: `from:"Upstash, Inc." (receipt OR invoice)` + date window.
- Result: 2/2 matched.
- To watch: payment failures seen in July (Stripe retries); they are not
  final, do not import them as supporting documents.
