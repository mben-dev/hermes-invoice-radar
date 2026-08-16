# Email senders lookup table

The biggest time saver. For each platform, the exact Gmail query, the subject
pattern and the output format.

| Source | Gmail query | Subject | Format |
|---|---|---|---|
| Upstash | `from:"Upstash, Inc." (receipt OR invoice)` | `Your receipt from Upstash, Inc. #XXXX` | 2 PDFs (Invoice + Receipt) |
| Koyeb | `from:koyeb (receipt OR invoice)` | `Your receipt from Koyeb #XXXX` | 2 PDFs |
| Trainline | `from:auto-confirm@info.thetrainline.com "vos billets"` | `Vos billets...` | Ticket PDF |
| Screen Studio | `from:lemonsqueezy "Screen Studio"` | `Your Screen Studio Subscription... receipt` | HTML (convert to PDF) |
| OVH | `from:support@services.ovhcloud.com "facture"` | `Votre facture est disponible...` | Link in client area |
| Paddle | script `paddle_receipts.py` | Paddle receipts | HTML to PDF |
| Anthropic | handled | `Invoice` + `Receipt` | 2 PDFs |
| Google Workspace | Google Payments billing | Invoice | PDF (1 month lag) |

## Gmail pitfalls

1. `in:anywhere "cursor"` returns saturated results. Always use `from:` +
   `subject:` + an `after:`/`before:` window.
2. Screen Studio receipts come from lemonsqueezy (LEMSQZY on the card is
   Lemon Squeezy, the payment platform, not "Screen Studio").
3. Upstash and Koyeb send from `invoice+statements+acct_...` (Stripe).
4. A receipt can precede the transaction (receipt on the 13th, transaction on
   the 14th): search plus or minus 3 days.
