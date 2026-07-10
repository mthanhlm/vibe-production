# vibe

**The lightweight production-standards and PDCA-loop layer for vibe coding.**

Fixes the three ways AI coding sessions go wrong:

1. **You don't know what production-grade looks like** → citation-grade
   standards (Zalando, Google AIPs, OWASP ASVS, Azure patterns, RFC 9457)
   loaded on demand, with stable rule IDs so every flag cites chapter and verse.
2. **The AI copies your codebase's bad patterns, compounding tech debt** →
   flag-don't-conform: new code is written to standard, deviations are flagged
   once with the rule ID, and a Strangler-Fig `ROADMAP.md` uplifts the codebase
   one touch at a time — never a big-bang rewrite.
3. **Token burn and retry thrash** → plan-before-code is enforced by a
   zero-token hook, tests reach the model as failure lines only, every plan
   carries a retry budget that stops thrashing loops, and the plugin itself
   costs **well under 500 always-on tokens** (one skill description + your
   working agreements). No MCP server — nothing here ever invalidates the
   prompt cache.

## The loop (PDCA + upfront expectations)

```
/vibe:plan   Plan  — interview → explore → 1–3 page plan: plain-language
                     Objective, verifiable "Done means" criteria, retry
                     budget. Approval required. Bilingual HTML view (EN/VI
                     toggle) at .vibe/plan.html.
  (code)     Do    — normal Claude coding. The plan gate blocks writes
                     without an approved plan; deviation nudges fire once
                     per pattern; standards load only when relevant.
/vibe:check  Check — vibe-verify (failures only) → standards-reviewer
                     verifies each criterion with evidence → uplift-scout
                     offers ≤3 optional improvements. Stops at the retry
                     budget instead of thrashing.
/vibe:act    Act   — promote working agreements, record one learning, tick
                     the roadmap, archive the plan (closes the gate), commit.
```

`/vibe:plan quick` stamps a one-line plan for one-sentence diffs — no ceremony.
`/vibe:setup` onboards a repo: discovers house patterns, writes the gap
roadmap and `.vibe/verify.sh`, and (with your consent) defaults the project
to plan mode.

## Install

From a marketplace checkout:

```
/plugin marketplace add mthanhlm/vibe-production
/plugin install vibe@vibe-marketplace
```

For local development:

```
claude --plugin-dir /path/to/vibe-production
```

Requirements: `bash` and `python3` on PATH (hooks and renderers are
stdlib-only). The plan gate and nudges are **opt-in per project** — they
activate only after `.vibe/` exists (created by `/vibe:setup` or
`/vibe:plan`), so installing the plugin never gates other repos.
Emergency bypass: `VIBE_GATE=off` or `"gate": "off"` in `.vibe/config.json`.

## Git safeguard (always on)

A PreToolUse hook guards git in every project while the plugin is enabled,
in two tiers:

- **Destructive — blocked with a safer alternative**: force-push
  (`--force-with-lease` stays allowed), remote branch deletion,
  `reset --hard`, `clean -f`, `checkout/restore .`, `branch -D`,
  `stash drop/clear`.
- **Approval-required — blocked until you say go**: `git add`, `git commit`,
  `git push`. The model never stages, commits, or pushes on its own
  initiative; after your explicit go-ahead it re-runs the command prefixed
  with `VIBE_GIT=allow `.

Read-only git (status, diff, log, stash list) is never touched. Disable per
project with `"git_guard": "off"` in `.vibe/config.json` or globally with
`VIBE_GIT_GUARD=off`.

## Releasing (maintainer)

`/vibe:release [patch|minor|major] [note]` validates the plugin, bumps the
semver (explicit versions pin installs — no bump, no update), commits,
pushes, then refreshes the installed copy **through the marketplace**:
`claude plugin marketplace update vibe-marketplace` +
`claude plugin update vibe@vibe-marketplace`. Running sessions pick the new
version up after `/reload-plugins`.

## What's inside

| Component | Type | Idle token cost |
|---|---|---|
| `production-standards` + 5 reference files | skill (model-invocable) | ~1 description line |
| `/vibe:plan` `/vibe:check` `/vibe:act` `/vibe:setup` `/vibe:release` | thin commands (namespaced in the picker) | 0 |
| `vibe-plan` … `vibe-release` | skills holding the full workflows, `disable-model-invocation` | 0 |
| plan gate, git safeguard, deviation nudge, plan stamp | hooks (PreToolUse / PostToolUse) | 0 |
| `standards-reviewer` (sonnet), `uplift-scout` (haiku) | agents, read-only | 0 until invoked |
| `vibe-verify`, `vibe-plan-html` | bin CLIs | 0 |

State lives in **your repo, committed**: `.vibe/plan.md` (the gate token),
`.vibe/STATE.md` (any fresh session knows the next command), `.vibe/ROADMAP.md`
(the uplift backlog), `.claude/rules/working-agreements.md` (rules the Act
step promotes), `docs/solutions/` (one learning per feature).

## Bilingual plans

`.vibe/plan.md` is **English-only** — the single source of truth agents work
from. `/vibe:plan` additionally renders `.vibe/plan.html`: a styled,
self-contained page with an **EN/VI toggle button** (default Vietnamese —
set `plan_language` in `.vibe/config.json`, or `"none"` to skip). The
translation is embedded only in the HTML and survives re-renders, so ticking
progress checkboxes never loses it.

## License

MIT for the plugin code. Reference files adapt CC-BY-4.0 and CC-BY-SA-4.0
material — see [NOTICES.md](NOTICES.md).
