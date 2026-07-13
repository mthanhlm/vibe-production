# Working agreements (binding, promoted by /vibe:act)

- WA-1 (2026-07-10): Every `commands/<name>.md` body is exactly one
  Skill-tool invocation of `vibe:<name>`; skills stay
  `user-invocable: false` and must NOT set `disable-model-invocation`
  (the Skill tool can only call model-invocable skills).
- WA-4 (2026-07-10): Hook scripts are tested subprocess-level via
  `tests/hookrunner.py` (JSON on stdin; assert exit code/stderr/stdout) —
  never imported as modules; stdlib `unittest` only, no pytest.
- WA-5 (2026-07-10): Every `git push` variant — including
  `--force-with-lease` — requires `VIBE_GIT=allow`; force-with-lease is
  exempt only from the destructive classification, never from approval.
- WA-6 (2026-07-10): Every except-swallow in hook scripts calls
  `_debug(context, exc)` so `VIBE_DEBUG=1` leaves evidence; no naked
  `except: pass`.
- WA-7 (2026-07-11, amended 2026-07-11): Never run `git add`/`git commit`/
  `git push` unless the user explicitly asks in their own words —
  `/vibe:act` archives the plan and updates state, writes no commit
  message, never touches git; every commit is the user's. `/vibe:release`
  is the maintainer's own automation, exempt. Act is otherwise fully
  automatic (no mid-run questions).
- WA-8 (2026-07-11): Retired working-agreement numbers are never reused or
  renumbered — delete the entry, survivors keep their numbers, so
  historical references stay valid (first applied removing WA-2/WA-3).
- WA-10 (2026-07-12): Every text-mode `open()` in hook scripts passes
  `encoding="utf-8"` (binary streams exempt) — a platform-default encoding
  must never silently disable a switch or corrupt state.
- WA-11 (2026-07-12): The chat-history archive (`~/.claude/vibe-history`)
  is append-forever; `index.jsonl` is a rebuildable cache — append-only
  writes, readers dedup latest-wins by `session_id`, never rewritten in
  place; lifecycle hooks stay side-effect-only (exit 0, empty stdout).
- WA-9 (2026-07-12, amended 2026-07-12): The PDCA auto-chain is
  prompt-level only (Skill-tool invocations, never hooks) with exactly ONE
  hop: Do self-invokes check when implementation completes; check ends with
  live verification + a test-it-yourself list then always stops (never
  invokes act); act runs only when the user explicitly asks and is always
  last. `"auto_chain": "off"` disables the hop; every other value (incl.
  legacy "on"/"full") is the default.
- WA-12 (2026-07-13): Live verification installs nothing without the
  user's consent; when a criterion can't be driven, it is reported
  UNVERIFIABLE-live with exact manual steps — never silently skipped.
- WA-13 (2026-07-13): Operational skill guidance longer than a few lines
  lives in a bundled `references/` file loaded on demand — SKILL.md
  always-on cost stays flat, and instructions must be executable as
  written (verified by fresh agents given only the files).
- WA-14 (2026-07-13): Team-shared `.vibe/config.json` keys gate features
  only; machine-local consent for any install is the artifact's presence
  on that machine's disk (e.g. `~/.claude/vibe-e2e`) — a committed key
  never licenses an install on a colleague's machine (WA-12 corollary,
  first applied to the Playwright e2e toolkit).
- WA-15 (2026-07-13): `bin/` CLIs print machine-parseable output only —
  one decision line (`CAPABILITY: …`-style) on stdout, failures on
  stderr; advisory prose lives in skill/reference text, never in
  terminal output (user correction removing the WSL NOTE line).
- WA-16 (2026-07-13): A skill emitting a visual artifact
  (deck/diagram/image) verifies it two ways — a machine validator with
  cited rule IDs AND a render-to-image review the model looks at
  (structural pass alone is never "done") — and composes it from a tested
  shipped library, never raw one-off authoring (first: /vibe:deck).
