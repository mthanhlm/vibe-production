# Working agreements (binding, promoted by /vibe:act)

- WA-1 (2026-07-10): Every `commands/<name>.md` body is exactly one
  Skill-tool invocation of `vibe:<name>`; skills stay
  `user-invocable: false` and must NOT set `disable-model-invocation`
  (the Skill tool can only call model-invocable skills).
- WA-2 (2026-07-10): Never generate PPTX XML from scratch — always clone
  `skills/slide/assets/template.pptx` (regenerate via `make_template.py`)
  and swap text through `scripts/build_pptx.py`.
- WA-3 (2026-07-10): No `.drawio` file is delivered until
  `scripts/lint_drawio.py` exits 0 on it.
- WA-4 (2026-07-10): Hook scripts are tested subprocess-level via
  `tests/hookrunner.py` (JSON on stdin; assert exit code/stderr/stdout) —
  never imported as modules; stdlib `unittest` only, no pytest.
- WA-5 (2026-07-10): Every `git push` variant — including
  `--force-with-lease` — requires `VIBE_GIT=allow`; force-with-lease is
  exempt only from the destructive classification, never from approval.
- WA-6 (2026-07-10): Every except-swallow in hook scripts calls
  `_debug(context, exc)` so `VIBE_DEBUG=1` leaves evidence; no naked
  `except: pass`.
