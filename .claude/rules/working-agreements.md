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
