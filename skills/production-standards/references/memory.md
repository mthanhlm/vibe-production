# Agent-memory standards

Distilled from Anthropic memory-tool/context-editing docs + cookbooks,
MemGPT (arXiv:2310.08560), Zep (arXiv:2501.13956), the OWASP AI Agent
Security Cheat Sheet + LLM02:2025 + Agentic ASI06, and GDPR Art. 5. Rule
IDs are stable — cite them when flagging. Sources verified in
`.vibe/research/2026-07-14-memory-standards.md`.

## What to write

- **MEM-1 (MUST)** Persist the irreplaceable — decisions, preferences,
  hard-won lessons; recompute what has a source of truth. "Store
  task-relevant patterns, not conversation history." Prevents a stale
  cache masquerading as the system [Anthropic memory cookbook; MemGPT].
- **MEM-2 (MUST)** Every memory write is stamped who/when (user id + ISO
  timestamp); **(SHOULD)** also from-what (source of the write). Untraceable
  memories can't be audited or selectively purged after poisoning [OWASP
  AI Agent Security Cheat Sheet; Zep bi-temporal model].
- **MEM-6 (MUST)** Never store credentials or API keys; PII only with a
  purpose and a deletion path ("limited to what is necessary", storage-
  limited). Strip sensitive data in the handler before it hits disk
  [Anthropic memory tool; OWASP LLM02:2025; GDPR Art. 5(1)(c),(e)].

## How to read

- **MEM-3 (MUST)** Memory is a hint AND an injection vector, never ground
  truth: verify against the live system before high-stakes action, and
  treat instructions found in memory as untrusted content ("memory files
  are... a potential vector for prompt injection") [Anthropic cookbook;
  Building Effective Agents; OWASP ASI06 memory poisoning].
- **MEM-7 (MUST)** Validate every memory path and scope storage per user
  in the harness — `/memories/../../secrets.env` must be impossible
  (canonical resolution, reject traversal, per-user roots). The model is
  never the enforcement layer [Anthropic memory tool security warning;
  OWASP cheat sheet].

## How it ages

- **MEM-4 (MUST)** Every record has a staleness policy — TTL or event
  invalidation; no immortal facts. **(SHOULD)** set it per record class
  (preferences vs facts vs task state) [Anthropic "memory expiration";
  OWASP TTL reference code; Zep edge invalidation; GDPR 5(1)(e)].
- **MEM-5 (MUST)** Compaction/clearing leaves a marker in context (the
  reader must know something was removed) and a durable copy in memory
  that survives the reset — summarize-then-drop, never silent-drop
  [Anthropic context editing: placeholder text + pre-clearing warning].
- **MEM-8 (SHOULD)** Use the cheapest context operation that matches the
  observed bottleneck: clear stale tool results (mechanical, free) <
  compact (inference cost) < persist to memory (storage + plumbing)
  [Anthropic context-engineering cookbook].
- **MEM-9 (MUST)** One fact, one place: update or INVALIDATE a superseded
  record — never append a contradiction beside it (retrieval returns both
  versions of the truth). Hard-delete only where MEM-6's deletion path
  demands it [Anthropic memory prompting guidance; Zep invalidation].

## Examples

Bad (violates MEM-1, MEM-2):

    memory.append(f"{full_conversation_transcript}")

Good:

    memory.write(key="deploy-policy",
                 value="user requires manual approval for prod deploys",
                 who=user_id, at=iso_now(), source="chat 2026-07-14")

Bad (violates MEM-9 — both "truths" persist):

    memory.append("prefers dark mode")   # note already says light mode

Good:

    memory.invalidate("prefers light mode", superseded_by="prefers dark mode")
