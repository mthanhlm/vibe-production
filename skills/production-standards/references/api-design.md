# API design standards

Distilled from the Zalando RESTful API Guidelines (CC-BY-4.0), Google AIPs
(CC-BY-4.0), and RFC 9457. Rule IDs are stable — cite them when flagging.
Zalando rule numbers (#nnn) refer to https://opensource.zalando.com/restful-api-guidelines/.

## Contract

- **API-1 (MUST)** Design the contract first: resource nouns, methods, status
  codes, and error shape before handler code. A one-screen sketch in the plan
  is enough — the point is that the contract is a decision, not an accident
  [Zalando #100 API First].
- **API-2 (MUST)** Resources are plural nouns; verbs come from HTTP methods.
  `POST /orders`, `GET /orders/{id}` — never `/createOrder` [Zalando #134, #141; AIP-121].
- **API-3 (MUST)** Errors return RFC 9457 `application/problem+json`:
  `{"type","title","status","detail","instance"}`. One error shape for the
  whole API — clients should never parse prose [Zalando #176].
- **API-4 (MUST)** Use correct status codes: 400 validation, 401 unauthenticated,
  403 unauthorized, 404 absent, 409 conflict, 422 semantic error, 429 rate-limited,
  5xx only for server faults. Never 200-with-error-body [Zalando #150].

## Behavior

- **API-5 (MUST)** GET/HEAD are safe; GET/PUT/DELETE are idempotent. `POST`
  that a client may retry (payments, orders) accepts an `Idempotency-Key`
  header and returns the original result on replay [Zalando #229].
- **API-6 (MUST)** Collections paginate from day one — cursor-based preferred
  (`next` token), page/limit acceptable. An unbounded list endpoint is an
  outage waiting for growth [Zalando #159; AIP-158].
- **API-7 (SHOULD)** Version via the URL (`/v1/`) or media type, chosen once
  per API. Breaking changes require a new version; additive changes must not
  break existing clients (tolerant reader) [Zalando #109, #115].
- **API-8 (SHOULD)** Property names snake_case (or the language's JSON norm,
  applied consistently); timestamps RFC 3339 UTC (`2026-07-10T08:00:00Z`);
  money as string decimal + currency code, never float [Zalando #118, #126, #169].

## Examples

Bad (violates API-3, API-4):

    return jsonify({"success": False, "msg": "err"}), 200

Good:

    return jsonify({
        "type": "https://example.com/problems/insufficient-funds",
        "title": "Insufficient funds",
        "status": 422,
        "detail": f"Balance {balance} is below amount {amount}.",
        "instance": f"/accounts/{account_id}/withdrawals",
    }), 422

Bad (violates API-5 — double-charge on retry):

    @app.post("/payments")
    def create_payment(): charge(request.json)

Good:

    @app.post("/payments")
    def create_payment():
        key = require_header("Idempotency-Key")   # 400 if missing
        if (prior := payments.find_by_key(key)):
            return prior.response, prior.status   # replay, don't re-charge
        ...

## Attribution

Contains rules adapted from the Zalando RESTful API Guidelines © Zalando SE,
CC-BY-4.0, and Google API Improvement Proposals, CC-BY-4.0.
