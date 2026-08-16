# Koyeb

Method: email (Stripe)

- Sender: `Koyeb <invoice+statements+acct_...>` (Stripe).
- Subject: `Your receipt from Koyeb #XXXX-XXXX`.
- Each email carries 2 PDFs: Invoice and Receipt. Import the Invoice.
- Gmail query: `from:koyeb (receipt OR invoice)` + date window.
- Result: 2/2 matched.
- To watch: "reached 100% of your spending limit" emails mean the usage cap
  was hit; report them.
