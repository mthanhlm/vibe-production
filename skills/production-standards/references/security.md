# Security standards

Distilled from OWASP ASVS 5.0 and the OWASP Cheat Sheet Series (both
CC-BY-SA-4.0). ASVS requirement IDs are cited so flags are verifiable at
https://owasp.org/www-project-application-security-verification-standard/.

## Rules

- **S-1 (MUST)** Validate all external input at the trust boundary against a
  positive schema (types, lengths, ranges, allowed values). Query params,
  headers, cookies, webhook bodies, and file names are all external input
  [ASVS V5.1].
- **S-2 (MUST)** SQL/NoSQL/OS commands use parameterized APIs only. String
  building with user data is injection, full stop [ASVS 5.3.4, 5.3.8;
  SQLi Cheat Sheet].
- **S-3 (MUST)** Output encoding by context: template auto-escaping stays on;
  anything inserted into HTML/JS/URLs is encoded for that context [ASVS 5.3.1].
- **S-4 (MUST)** Enforce authorization server-side on every request, by
  resource ownership — not by hiding buttons. `GET /orders/{id}` must check
  the order belongs to the caller (IDOR) [ASVS V4.1, V4.2].
- **S-5 (MUST)** Secrets live in env vars or a secret manager; never in
  source, logs, or error messages. Rotate anything that ever leaked into
  git history — deleting the line does not delete the commit [ASVS 2.10.4].
- **S-6 (MUST)** Passwords: bcrypt/argon2 with per-user salt (never MD5/SHA-x),
  compare in constant time. Sessions: HttpOnly, Secure, SameSite cookies;
  regenerate the session ID at login [ASVS V2, V3].
- **S-7 (MUST)** File uploads: whitelist extensions AND verify content type,
  cap size, store outside the web root under generated names [ASVS V12;
  File Upload Cheat Sheet].
- **S-8 (SHOULD)** Rate-limit authentication and expensive endpoints;
  lock/step-up after repeated failures [ASVS 2.2.1].
- **S-9 (SHOULD)** Log security events (logins, failures, permission
  denials, admin actions) with actor, action, target, timestamp — without
  logging credentials or tokens [ASVS V7].

## Examples

Bad (violates S-2):

    db.execute(f"SELECT * FROM users WHERE email = '{email}'")

Good:

    db.execute("SELECT * FROM users WHERE email = %s", (email,))

Bad (violates S-4 — IDOR):

    @app.get("/invoices/<id>")
    def invoice(id): return repo.get(id)          # any logged-in user, any invoice

Good:

    @app.get("/invoices/<id>")
    def invoice(id):
        inv = repo.get(id)
        if inv is None or inv.owner_id != current_user.id:
            abort(404)                             # 404, not 403: don't confirm existence
        return inv

## Attribution

Contains material adapted from OWASP ASVS and the OWASP Cheat Sheet Series,
© OWASP Foundation, CC-BY-SA-4.0. This file is likewise CC-BY-SA-4.0.
