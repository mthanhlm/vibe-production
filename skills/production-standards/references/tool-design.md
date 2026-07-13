# Tool-design standards (tools for LLM agents)

Distilled from Anthropic tool-use docs + "Writing effective tools for AI
agents", the MCP spec, OWASP LLM06:2025, Claude Code permissions/hooks
docs, Stripe idempotency, and Google AIP-155. Rule IDs are stable — cite
them when flagging. Sources verified in
`.vibe/research/2026-07-14-tool-design-standards.md`.

## The contract

- **TD-1 (MUST)** The description is the contract: what the tool does,
  WHEN to use it, when NOT to, what each parameter means, caveats — "at
  least 3-4 sentences per tool description". Prevents should-call misses
  and overtriggering [Anthropic define-tools; writing-tools post].
- **TD-2 (MUST)** Strict schemas: enums for closed sets,
  `additionalProperties: false`, a description on every property, minimal
  schema surface with optionality made explicit (strict modes differ:
  Anthropic allows optional fields; OpenAI wants all-required + nullable).
  Prevents hallucinated or invalid arguments [Anthropic strict tool use;
  OpenAI function calling].
- **TD-9 (MUST)** Tool definitions serialize byte-identically across
  requests — "changes... invalidate the entire cache"; **(SHOULD)** evolve
  additively (add optional params; renames measurably shift tool-choice
  behavior) [Anthropic prompt caching; writing-tools namespacing finding].

## Execution

- **TD-3 (MUST)** Failures return an instructive error the model can see
  (`is_error: true` result): what went wrong AND what to try next — "Rate
  limit exceeded. Retry after 60 seconds." Never dropped, never raised
  past the loop; the model can only recover from what it sees [Anthropic
  handle-tool-calls; MCP isError].
- **TD-4 (MUST)** Side-effectful tools are idempotent (keys/request-ids —
  a replay "must not... perform the update twice") or confirmation-gated
  (human in the loop for sensitive operations). Models auto-retry failed
  calls; never trust client-provided hints as the enforcement [Stripe;
  AIP-155; MCP; OWASP LLM06:2025].
- **TD-5 (MUST)** Least privilege per tool credential: minimum
  permissions, executed as the requesting user, minimum functionality.
  Under injection the model can do anything the key allows [OWASP
  LLM06:2025 Excessive Agency].

## The loop's economy

- **TD-6 (MUST)** Budget the tool count: selection quality degrades past
  ~20 tools and measurably by 30-50; consolidate related operations and
  defer/load-on-demand beyond that [Anthropic tool-search docs; OpenAI].
- **TD-7 (MUST)** Size outputs for the context loop: paginate, filter,
  truncate with a fetch-more pointer and sensible defaults; return
  high-signal fields only. An unbounded tool result is a context outage
  [Anthropic writing-tools; define-tools].
- **TD-8 (SHOULD)** Promote a bash-string action to a dedicated tool when
  the harness must gate, audit, or render it — "Bash permission patterns
  that try to constrain command arguments are fragile"; a first-class tool
  gates on structured input [Claude Code permissions/hooks; OWASP
  LLM06:2025 granular-function guidance].

## Examples

Bad (violates TD-1, TD-2):

    {"name": "search", "description": "Searches.",
     "input_schema": {"type": "object", "properties": {"q": {}}}}

Good:

    {"name": "search_orders",
     "description": "Search the orders DB by customer or SKU. Use when the
       user asks about order status or history; do NOT use for refunds
       (use process_refund). Returns at most 20 matches, newest first.",
     "input_schema": {"type": "object", "additionalProperties": false,
       "required": ["query"], "properties": {"query": {"type": "string",
         "description": "Customer name, email, or SKU."}}}}

Bad (violates TD-3): `raise RateLimitError` — the loop dies, the model
learns nothing. Good: return `is_error: true`, "Rate limited; retry after
60s or narrow the date range."
