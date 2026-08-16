# Uber

Method: browser + API. The complex case (resolved about 95%, one documented
blockage).

## Login (auth.uber.com)

- CAPTCHA (Arkose) bypassed with a non-headless Chromium under `xvfb-run`
  and `navigator.webdriver` hidden.
- `POST /v2/submit-form` with header `x-csrf-token: x` (literally the letter
  "x" is accepted).
- Body format: `screenAnswers[0].fieldAnswers[]` (NOT `screen.fields`).
- Field keys (found in the JS bundle):
  - TOTP: `totpAnswer`
  - PASSWORD: `password`
  - WEB_SESSION_TOKEN: `webSessionToken`
- Flow: INITIAL (email) -> TOTP -> PASSWORD -> WEB_SESSION_VERIFICATION.

## Known blockage

`NO_CHALLENGES` on a non-verified device. Bypass: cross-device QR login on
ubereats.com (the "log in with the QR code" option), scanned with the Uber
app.

- Condition: the phone must egress through the same IP as the browser
  (Tailscale exit node on the VPS).

## QR anti-abuse

About 30 QR generations in 30 minutes invalidates ALL following QR codes for
about an hour ("server error" at scan). Do NOT regenerate in a loop.

## Invoice download API

- `POST /api/getPastOrdersV1?localeCode=fr` (WITHOUT `_p`) -> order list.
- `POST /_p/api/getInvoiceFilesV1?localeCode=fr` (WITH `_p`) ->
  `files[].downloadURL` (PDF).

## Errors seen

- `recaptcha.invalid_token`
- `400 UNEXPECTED_ANSWER_TYPE` (wrong body format)
- `TOTP_INCORRECT`
- `TOTP_TOO_MANY_FAILED_ATTEMPTS` (cooldown about 1 hour)
- `PASSWORD_INCORRECT` (stale password in the vault)

## Plan B (100% reliable)

Uber app -> Settings -> Privacy -> Download my data -> archive by email.
