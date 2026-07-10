# System design standards

Distilled from the Azure Cloud Design Patterns catalog (CC-BY-4.0) and
The Twelve-Factor App (CC-BY-4.0).

## Rules

- **D-1 (MUST)** Config comes from the environment; one build runs in every
  environment. No `if ENV == "prod"` forks of behavior, no committed
  per-environment config files with secrets [12factor I, III, V].
- **D-2 (MUST)** Every outbound call has a timeout; every retry is bounded
  with exponential backoff + jitter, and retries only idempotent operations.
  Retrying a non-idempotent POST is how one outage becomes two [Azure Retry
  pattern; API-5].
- **D-3 (MUST)** Schema migrations are additive and reversible in deploy
  order: expand (add nullable column) → migrate data → contract (drop old)
  as separate deploys. Never a destructive migration in the same deploy as
  the code that needs it.
- **D-4 (MUST)** Stateless processes: session and job state live in a store,
  not in process memory, so any instance can die or scale [12factor VI, VIII].
- **D-5 (SHOULD)** Protect against cascading failure at busy integration
  points: circuit breaker or bulkhead in front of flaky dependencies, and a
  defined degraded mode ("search down, browsing still works") [Azure Circuit
  Breaker, Bulkhead].
- **D-6 (SHOULD)** Long work (> a request timeout) goes to a queue/worker
  with an idempotent consumer and a dead-letter path; the API returns 202 +
  a status resource [Azure Queue-Based Load Leveling, Async Request-Reply].
- **D-7 (SHOULD)** Legacy modernization is incremental: route traffic
  feature-by-feature from old to new behind a facade until the old dies —
  never a big-bang rewrite [Azure **Strangler Fig**]. This is the pattern
  behind `.vibe/ROADMAP.md`: uplift what you touch, in order of risk.
- **D-8 (SHOULD)** Ship observability with the feature: health endpoint,
  structured logs with correlation IDs (E-4/E-5), and a metric for the thing
  the feature is supposed to improve.

## Examples

Bad (violates D-2):

    resp = requests.get(PARTNER_URL)           # no timeout, infinite patience
    while resp.status_code != 200:             # unbounded retry, no backoff
        resp = requests.get(PARTNER_URL)

Good:

    for attempt in range(3):
        try:
            resp = requests.get(PARTNER_URL, timeout=5)
            resp.raise_for_status()
            break
        except (requests.Timeout, requests.HTTPError):
            if attempt == 2:
                raise PartnerUnavailable()      # caller decides the degraded mode
            time.sleep((2 ** attempt) + random.random())

Bad (violates D-3): one deploy that renames the column and ships code reading
the new name — old instances crash during rollout, rollback is impossible.

Good: deploy 1 adds `customer_email` (nullable, backfilled, dual-written);
deploy 2 reads the new column; deploy 3 drops `email`. Each step reversible.

## Attribution

Contains material adapted from Microsoft Azure Architecture Center Cloud
Design Patterns, CC-BY-4.0, and The Twelve-Factor App © Adam Wiggins,
CC-BY-4.0.
