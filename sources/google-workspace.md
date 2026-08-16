# Google Workspace

Method: email

- Invoices arrive from Google Payments by email (billing id anonymized).
- Lag: the invoice dated 01/XX matches the transaction of the FOLLOWING month.
- Pitfall: an invoice can already exist in the DMS as an orphan document
  (409 "document already exists" on import). In that case, match the existing
  document in the UI (about 10 seconds).
- Result: 2/3 matched; one needed the UI workaround.
