# hermes-invoice-radar

An agent-driven system that scans accounting transactions, detects the ones
missing a supporting document (invoice or receipt PDF), collects the PDF from
the right platform (API, email or browser), imports it as a supplier invoice
and matches it to the transaction.

Real-world result: about 290 transactions justified in one day, across about
20 SaaS platforms.

## Method

For every transaction without a supporting document, try in this order:

1. **Official API** - call the API (Cloudflare, Railway, Pennylane, ...).
2. **Email** - search the receipt in Gmail (90% of cases).
3. **Browser** - log in and download (Gandi, Uber, ...).

The platform files in `sources/` describe the method that actually works for
each platform. The method is a platform constraint, not a choice: the file
states the constraint, where the PDF ends up, and the pitfalls.

## Structure

```
hermes-invoice-radar/
  README.md            why, method, decision tree, contribution
  SECRETS.md           2FA/TOTP handling (no real secret)
  sources/             ONE FILE PER PLATFORM (the method, not the content)
  adapters/            the output = the accounting software (pluggable)
  emails/senders.md    sender -> subject -> format lookup table
  scripts/             reusable pipelines (email to PDF, ...)
  assets/              images
```

## Contribution

To add a platform:

1. Create `sources/<platform>.md` following the existing files (method,
   destination, pitfalls).
2. Follow the decision tree: API first, email second, browser last.
3. Anonymize everything: no real amounts, no personal emails, no secrets.
4. Scripts must be readable by an agent: clear comments, explicit names.

## Security rules

- Zero seed in a shared .env or in the repo. See `SECRETS.md`.
- Zero personal email addresses and zero real amounts in this repo.
