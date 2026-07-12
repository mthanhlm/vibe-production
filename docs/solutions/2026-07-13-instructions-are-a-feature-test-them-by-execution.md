---
problem: Prompt-level features (skill wording) ship with no test suite, so
  plausible-but-unrunnable instructions slip through — a live-verification
  stage that named Playwright but gave no tool ladder, no Docker/timeout
  discipline, and no answer for machines without it.
solution: Test instructions by execution, adversarially — fresh agents get
  ONLY the edited files plus one concrete scenario and must state what they
  would do next (or which commands they would run); mismatches and
  ambiguity flags are wording defects to fix in the same loop.
rules: [WA-9, WA-12, WA-13]
---

Scenario agents caught what re-reading never would: a retry-budget
loophole ("re-run from stage 1" skipped the gate), a stale sibling skill
(setup still taught the removed auto-chain), and the executability gap in
live verification itself. Cover the corners deliberately: legacy config
values that must NOT change behavior, budget exhausted exactly at the
limit, feedback arriving after the stop. For operational guidance, the
fix pattern is a bundled references/ file (loaded only when the stage
runs) with a no-install-by-default tool ladder and consent-gated heavy
tools — then re-verify by giving agents hard cases (no Playwright but
Chrome present; compose stack; server never ready) and requiring runnable
command plans with bounds and cleanup. Instructions the model cannot
execute as written are AI slop, exactly what this plugin exists to stop.
