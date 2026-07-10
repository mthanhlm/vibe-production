# Error handling standards

Written fresh; informed by OWASP Top-10 A09 (logging/monitoring failures,
CC-BY-SA-4.0), RFC 9457, and the OWASP Error Handling Cheat Sheet.

## Rules

- **E-1 (MUST)** Never swallow an exception. `except: pass` and empty `catch {}`
  destroy the only evidence of a production fault. Minimum: log with context
  and decide — recover, retry, or re-raise.
- **E-2 (MUST)** Catch the narrowest type that you can actually handle.
  A broad catch is allowed only at process boundaries (request handler,
  worker loop, main) where it logs and converts to a proper error response.
- **E-3 (MUST)** Fail closed. On unexpected errors in auth, payment, or data
  writes, the safe answer is refusal, not a guessed default.
- **E-4 (MUST)** User-facing error messages contain no stack traces, SQL,
  internal paths, or library names; full detail goes to logs with a
  correlation ID that also appears in the API error (`instance`/`trace_id`)
  so support can join the two [OWASP A09].
- **E-5 (MUST)** Log errors as structured events (JSON): level, message,
  correlation ID, and the fields needed to reproduce — never `print()` and
  never string-concatenated secrets/PII into messages.
- **E-6 (SHOULD)** Distinguish expected failures (validation, not-found —
  return typed results or 4xx, no stack trace logged) from unexpected ones
  (log at ERROR with stack, alert, return 5xx). Alert fatigue starts with
  logging validation errors as ERROR.
- **E-7 (SHOULD)** Wrap external-dependency errors at the integration
  boundary into your own error types, so callers depend on your contract,
  not a vendor SDK's exception zoo.

## Examples

Bad (violates E-1, E-4):

    try:
        order = place_order(cart)
    except Exception:
        pass  # failure silently discarded — the bug this rule exists for
    return {"error": str(e), "trace": traceback.format_exc()}

Good:

    try:
        order = place_order(cart)
    except PaymentDeclined as exc:          # expected: no stack, 422
        return problem(422, "Payment declined", detail=exc.public_reason)
    except Exception:                        # unexpected: log full, say little
        log.exception("place_order failed", extra={"cart_id": cart.id,
                                                   "trace_id": trace_id})
        return problem(500, "Internal error", instance=trace_id)

Bad (violates E-6 — alert noise):

    log.error(f"validation failed for {payload}")   # fires on every typo

Good:

    log.info("validation rejected", extra={"field": err.field})

## Attribution

Informed by the OWASP Cheat Sheet Series and OWASP Top 10, CC-BY-SA-4.0.
This file is likewise shared under CC-BY-SA-4.0.
