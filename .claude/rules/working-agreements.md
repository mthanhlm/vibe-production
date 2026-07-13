# Working agreements (binding, promoted by /vibe:act)

- WA-1 (2026-07-10): Every `commands/<name>.md` body is exactly one
  Skill-tool invocation of `vibe:<name>`; skills stay
  `user-invocable: false` and must NOT set `disable-model-invocation`
  (the Skill tool can only call model-invocable skills).
- WA-4 (2026-07-10, amended 2026-07-13: absorbs WA-6, WA-10): Hook-script
  craft — test subprocess-level via `tests/hookrunner.py` (JSON on stdin;
  assert exit code/stderr/stdout; stdlib `unittest` only, never imported
  as modules); every except-swallow calls `_debug(context, exc)` (no naked
  `except: pass`); every text-mode `open()` passes `encoding="utf-8"`
  (binary streams exempt).
- WA-5 (2026-07-10): Every `git push` variant — including
  `--force-with-lease` — requires `VIBE_GIT=allow`; force-with-lease is
  exempt only from the destructive classification, never from approval.
- WA-7 (2026-07-11, amended 2026-07-11): Never run `git add`/`git commit`/
  `git push` unless the user explicitly asks in their own words —
  `/vibe:act` archives the plan and updates state, writes no commit
  message, never touches git; every commit is the user's. `/vibe:release`
  is the maintainer's own automation, exempt. Act is otherwise fully
  automatic (no mid-run questions).
- WA-8 (2026-07-11): Retired working-agreement numbers are never reused or
  renumbered — delete the entry; survivors keep their numbers.
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
- WA-12 (2026-07-13, amended 2026-07-13: absorbs WA-14): Nothing installs
  without the user's consent — a team-shared `.vibe/config.json` key gates
  the feature only; machine-local consent is the artifact's presence on
  that machine's disk (a committed key never licenses an install
  elsewhere). A criterion that can't be driven live is reported
  UNVERIFIABLE-live with exact manual steps — never silently skipped.
- WA-13 (2026-07-13): Operational skill guidance longer than a few lines
  lives in a bundled `references/` file loaded on demand — SKILL.md
  always-on cost stays flat, and instructions must be executable as
  written (verified by fresh agents given only the files).
- WA-15 (2026-07-13): `bin/` CLIs print machine-parseable output only —
  one decision line on stdout, failures on stderr; advisory prose lives in
  skill/reference text, never in terminal output.
- WA-17 (2026-07-14): The plugin's scope is the PDCA loop and production
  standards only — no artifact-generating skills (decks, diagrams, media).
  A new skill earns its place only by making the loop understand the
  codebase or the user's intent better (maintainer decision removing the
  visual suite after two verified builds).
