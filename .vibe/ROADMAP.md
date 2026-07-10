# Uplift roadmap (gradual — one item per feature touched)

Strangler-Fig uplift: fix-as-you-touch, one improvement per feature, NOT a
big-bang refactor. Context: this repo is a Claude Code plugin (4 stdlib-only
Python hook scripts, 1 bash wrapper, markdown skills). No web/API surface, so
API-* and most S-* rules apply only where noted. The scripts' fail-open
philosophy ("a hook must never brick the session") is deliberate and documented
inline — items below uplift within that philosophy, not against it.

- [ ] R-1 (high, T-1/T-3): zero automated tests for the four hook scripts
  (`scripts/gate.py`, `nudge.py`, `stamp_plan.py`, `git_guard.py`) and
  `bin/vibe-verify` — every release ships on `plugin validate` alone. On next
  touch of any script, add a pytest suite that feeds stdin-JSON fixtures and
  asserts exit codes / stdout decisions, covering the unhappy paths (malformed
  JSON, missing plan.md, config off-switches).
- [ ] R-2 (high, E-3): `scripts/git_guard.py:49-53,67-72` — the destructive-git
  guard fails OPEN on malformed input or unreadable config, i.e. a bad payload
  disables the safeguard. On next touch, fail closed for the block-decision
  path (unparseable input on a Bash hook → block with explanatory stderr),
  keeping fail-open only for the advisory paths.
- [ ] R-3 (med, E-1): ~9 silent `except Exception: pass/return` swallow points
  (`nudge.py:85-139` ×5, `gate.py:41-46,72-83`, `stamp_plan.py:18-21,35-40`)
  leave zero evidence when a hook misbehaves. On next touch, add an opt-in
  `VIBE_DEBUG=1` breadcrumb (single stderr line or `.vibe/debug.log`) inside
  each swallow — keeps fail-open, restores the evidence E-1 exists for.
- [ ] R-4 (med, E-3/D-3): non-atomic `.vibe/` state writes —
  `stamp_plan.py:52,56` write `plan.md`/`STATE.md` directly (and unguarded: a
  write failure raises uncaught), `nudge.py:136` same for the seen-set; the
  gate reads `plan.md` concurrently. On next touch, write temp-file +
  `os.replace()` and guard the writes.
- [ ] R-5 (med, T-4): no CI — `.github/workflows` absent; releases are
  validated only by hand-run `claude plugin validate`. Add a workflow running
  `.vibe/verify.sh` on push once R-1's tests exist to make it worthwhile.
- [ ] R-6 (low, S-1): hook stdin fields (`tool_input.file_path`, `.command`,
  `cwd`) are used without shape validation — safe today only because every use
  is wrapped in broad catches. Validate types positively at the top of each
  `main()` as scripts are touched.
- [ ] R-7 (low, S-1): `git_guard.py:19-46,64` regex-parses raw command strings —
  subshells/`$IFS`/heredocs can slip past, and `VIBE_GIT=allow` detection is
  string-match. Accepted as nudge-grade by design; document that in the script
  header on next touch rather than chasing regex completeness.
- [ ] R-8 (low, S-5): `stamp_plan.py:52-56` writes `.vibe/plan.md`/`STATE.md`
  without resolving symlinks first (gate.py realpaths its paths, stamp_plan
  doesn't) — add `os.path.realpath` before writing. Distinct from R-4's
  atomicity. (uplift-scout, 2026-07-10)
- [ ] R-9 (low, S-1): `nudge.py:117` interpolates the hook payload's
  `session_id` into a temp filename unsanitized — path traversal possible;
  filter to `[\w-]` before use. Fold into R-6's stdin validation.
  (uplift-scout, 2026-07-10)
