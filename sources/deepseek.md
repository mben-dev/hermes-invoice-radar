# DeepSeek

Method: user-provided receipts

- Receipts are provided by the user (USD top-ups).
- Pitfall: a top-up receipt may precede the matching transaction by several
  days (receipt on the 7th, transaction on the 11th). A receipt for a top-up
  done in advance is not in the ledger yet; do not force a match.
- Result: 1/1 matched for the first receipt; the second one is a prepaid
  top-up, still unmatched by design.
