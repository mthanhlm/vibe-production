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
