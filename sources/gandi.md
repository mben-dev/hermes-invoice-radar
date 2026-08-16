# Gandi

Method: browser + TOTP

- Invoices live on the organization account (id anonymized), NOT on the
  personal account. Log in with the organization credentials.
- Login: admin.gandi.net + TOTP from 1Password (see SECRETS.md).
- The invoice page is a SPA: capture the PDF via a Playwright download event.
- Result: 4/4 invoices matched.
