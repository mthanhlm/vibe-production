---
name: production-standards
description: Production-grade engineering standards with citable rule IDs, for use when designing or building APIs and endpoints, handling errors and exceptions, writing or planning tests, reviewing security (auth, input validation, secrets), or architecting services and system design. Also applies when working inside a low-quality codebase — flag deviations instead of copying bad patterns. Consult the matching reference file before writing such code.
---

# Production standards

You are working with a user who may not know what production-grade looks like.
Your job: deliver it by default, and say so when the codebase doesn't.

## How to use this skill

1. Identify which domain the current work touches.
2. Read ONLY the matching reference file(s) below — each is short and self-contained.
3. Apply the rules; cite the rule ID when you make a standards-driven choice
   ("using RFC 9457 problem+json per API-3") so the user learns what to expect.

| When the work involves | Read |
|---|---|
| HTTP APIs, endpoints, contracts, versioning, pagination | `references/api-design.md` |
| errors, exceptions, logging, failure paths | `references/error-handling.md` |
| tests: what/how many/what kind, coverage decisions | `references/testing.md` |
| auth, user input, secrets, crypto, uploads | `references/security.md` |
| service structure, config, retries, migrations, scaling | `references/system-design.md` |

## Non-negotiables (the short list)

These hold in every codebase, greenfield or legacy. Details and examples live
in the reference files — read them; do not guess.

- Validate ALL external input at the boundary; whitelist, don't blacklist [ASVS V5].
- Parameterized queries only — never build SQL from strings [ASVS 5.3.4].
- No secrets in code or commits; config comes from the environment [ASVS 2.10.4, 12factor III].
- Never swallow an exception silently; log with context or re-raise [error-handling ref].
- Every network call has a timeout; every retry has a cap and backoff [system-design ref].
- API errors use a machine-readable envelope (RFC 9457 problem+json) with correct status codes.
- New behavior ships with at least one test that fails without the change [testing ref].
- Write operations that can be retried need idempotency (keys or natural idempotence).

## Flag, don't conform (brownfield protocol)

When the existing codebase violates one of these standards:

1. **Match house style** for naming, layout, and framework idioms — consistency there is a virtue.
2. **Never copy correctness/security violations.** Write the new code to standard.
3. **Flag once, briefly**: one or two sentences naming the violated rule ID and the fix,
   e.g. "Existing handlers swallow exceptions (violates error-handling E-1);
   I wrote the new one to standard and suggest adding the old ones to .vibe/ROADMAP.md."
4. **Don't lecture.** One flag per pattern per session; offer the roadmap, then move on.
5. If fixing the surrounding code is cheap and in scope (boy-scout rule), offer it —
   never do a big-bang refactor uninvited [Strangler Fig, system-design ref].

## Keep it token-cheap

Read one reference at a time, only when the domain is actually in play.
Never paste reference content back into the conversation — apply it and cite the ID.
