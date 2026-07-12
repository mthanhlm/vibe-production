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
  `/vibe:act` ends after archiving the plan and updating state; it writes
  no commit message and never touches git. Every commit is the user's,
  done manually. `/vibe:release` is the maintainer's own quick-release
  automation and is exempt from this rule. Act runs fully automatic
  otherwise (no mid-run questions).
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
  prompt-level only (Skill-tool invocations, never hooks) and has exactly
  ONE hop: plan's Do section self-invokes check when implementation
  completes. Check ends with live end-to-end verification and a
  test-it-yourself list, then always stops — it never invokes act. Act
  runs only when the user explicitly asks (typed /vibe:act or their own
  words) and is always the loop's last step. `"auto_chain": "off"`
  disables the single Do→Check hop; every other value (incl. legacy
  "on"/"full") is the default; STATE.md is written before the hop so an
  interrupted chain resumes manually.
- WA-12 (2026-07-13): Live verification installs nothing without the
  user's consent; when a criterion can't be driven, it is reported
  UNVERIFIABLE-live with exact manual steps — never silently skipped.
- WA-13 (2026-07-13): Operational skill guidance longer than a few lines
  lives in a bundled `references/` file loaded on demand — SKILL.md
  always-on cost stays flat, and instructions must be executable as
  written (verified by fresh agents given only the files).
