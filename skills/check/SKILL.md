---
name: check
description: Vibe Check phase — deterministic checks (failures only), criterion-by-criterion review with evidence, live end-to-end verification, all within the retry budget; always stops for the user's own test before Act. Invoked by the /vibe:check command.
user-invocable: false
---

# /vibe:check — Check (PDCA: Check)

Verify outcomes against `.vibe/plan.md`'s "Done means" list — outcome-based
("does it work"), never step-based ("did it use try-catch"). How you verify
each stage is your judgment; the invariants below are not.

## Retry budget — the circuit breaker (evaluate on EVERY entry, before any fix)

Read `retry_budget` from `.vibe/plan.md` frontmatter and `check_attempts`
from `.vibe/STATE.md`. If `check_attempts >= retry_budget`: **STOP. Do not
fix anything.** Report what passes, what fails, and your best diagnosis,
and ask the user how to proceed (split the task, change approach, raise
budget). Burning tokens on a thrashing loop is the failure mode this gate
exists for. Otherwise increment `check_attempts` in STATE.md now.

## Stages (cheap first — each states the outcome it must produce)

1. **Deterministic.** Outcome: `vibe-verify` green (bundled; it prints
   failure lines only). Fix-and-rerun inside this same attempt.
2. **Standards review.** Outcome: PASS/FAIL/UNVERIFIABLE per Done-means
   criterion with file:line evidence — launch the `standards-reviewer`
   subagent with the criteria verbatim plus the changed files.
3. **Live verification** (when stage 2 has no FAILs). Outcome: the real
   feature observed working, per the plan's Verification section, with
   evidence kept (output, exit codes, screenshots). Read
   `references/live-verification.md` now for the tool ladder. Invariants:
   nothing installs without the user's consent; a criterion you can't
   drive is reported UNVERIFIABLE-live with exact manual steps, never
   silently skipped (WA-12); a live run that contradicts test evidence is
   a FAIL.
4. **Uplift scout** (when nothing FAILed). Outcome: ≤3 advisory
   suggestions via `uplift-scout` on the changed files; declined ones go
   to `.vibe/ROADMAP.md`. Never block on them.

## Report — one compact table, then exactly one branch

Each Done-means criterion → verdict + one-line evidence (from tests AND
the live run), then findings and uplift suggestions if any.

- Every criterion PASS (UNVERIFIABLE is not a PASS) → `.vibe/STATE.md`:
  `status: checked`, `next_action: user confirm → /vibe:act`; tick the
  `- [x]` boxes in `.vibe/plan.md` and mirror `.vibe/plan.<lang>.md` if it
  exists. Then **stop — always.** End with:
  - **Test it yourself:** 2–3 concrete actions from the plan's
    Verification section and what the user should see.
  - The breadcrumb: "When it looks good to you, run /vibe:act (or just
    say so) to close the loop."
- Any UNVERIFIABLE — plain or -live — with no FAIL → not checked: an
  unverifiable criterion is a plan defect; report it and ask the user.
- Any FAIL with budget remaining → fix, then re-enter this skill from the
  top (the budget gate above runs before any further fixing).
- Budget exhausted → the gate above already stopped you.

## Feedback after the stop

Same objective → the pass is void: set `.vibe/STATE.md` back to
`status: doing`, then re-enter this skill from the top; the budget gate
runs before any fix, even an easy-looking one. Changed scope (new
capability, different behavior than the plan's Objective) → suggest a
fresh /vibe:plan; don't stretch this plan around it.

`vibe:act` is never invoked from check — it runs only when the user
explicitly asks (see the act skill).
