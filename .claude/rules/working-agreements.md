# Working agreements (binding, promoted by /vibe:act)

- WA-1 (2026-07-10): Every `commands/<name>.md` body is exactly one
  Skill-tool invocation of `vibe:<name>`; skills stay
  `user-invocable: false` and must NOT set `disable-model-invocation`
  (the Skill tool can only call model-invocable skills).
- WA-2 (2026-07-10, amended 2026-07-11): Prototype-first — all deck and
  layout chrome comes from cloning `skills/slide/assets/template.pptx`
  (regenerated via `make_template.py`) with content swapped through
  `scripts/build_pptx.py`; never hand-author per-deck PPTX XML. Parametric
  component emitters live only in `scripts/pptx_components.py` (invoked by
  `build_pptx.py`), restricted to its EMITTERS registry: kpi_row, bars,
  column, waterfall, line, ring, harvey, icon, image, photo, flow,
  timeline, matrix, gradient_field. Each emitter ships with a golden-file
  test in `tests/` and every built deck must pass
  `scripts/validate_pptx.py` before delivery. New components require a
  template prototype or a further WA amendment.
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
- WA-7 (2026-07-11): Never run `git add`/`git commit`/`git push` unless the
  user explicitly asks in their own words — `/vibe:act` writes
  `.vibe/commit-message.txt` and stops; the commit itself is always the
  user's. Act runs fully automatic otherwise (no mid-run questions).
