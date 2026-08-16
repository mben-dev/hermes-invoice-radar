# Secrets and 2FA/TOTP handling

## Absolute rule

Zero seed in a shared .env or in the repo. The seed is the key to the account.
A committed seed is a critical incident.

## Chosen method

1Password, vault "Hermes TOTP", with a scoped Service Account token:

```
op read "op://Hermes TOTP/<item>/<field>"
op read "op://Hermes TOTP/<item>/<field>?attribute=otp"   # direct 6-digit code
```

## Alternatives (in order of preference)

- Local encrypted vault (age).
- Push approval (zero risk).
- Manual read.

## Forbidden

- Plaintext seed stored by the agent (high risk).
- Seed committed to a repo (critical).

## Practical notes

- `oathtool` computes the code from the seed (base32) outside 1Password.
- Read the code right before sending it (30 second window).
- Some platforms (Uber) lock the TOTP for about an hour after a few failed
  attempts. Do not retry in a loop.
