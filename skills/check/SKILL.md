---
name: check
description: Verify the current work against the plan — run project checks (failures only), have the standards-reviewer verify each "Done means" criterion with evidence, surface up to 3 uplift suggestions. Respects the plan's retry budget.
disable-model-invocation: true
---

# /vibe:check — Check (PDCA: Check)

Verify outcomes against `.vibe/plan.md`'s "Done means" list. Outcome-based
("does the check pass"), never step-based ("did it use try-catch").

## Retry budget — read this first

Read `retry_budget` from `.vibe/plan.md` frontmatter and `check_attempts`
from `.vibe/STATE.md`. If `check_attempts >= retry_budget`: **STOP. Do not
fix anything.** Report what passes, what fails, and your best diagnosis, and
ask the user how to proceed (split the task, change approach, raise budget).
Burning tokens on a thrashing loop is the failure mode this gate exists for.
Otherwise increment `check_attempts` in STATE.md now.

## Stages (cheap first)

1. **Deterministic checks.** Run `vibe-verify` (bundled; uses
   `.vibe/verify.sh` when present, autodetects otherwise). It prints only
   failure lines. If it fails: fix, re-run — that's one loop inside this
   same attempt; don't launch the reviewer until it's green or you're
   blocked.
2. **Standards review.** Launch the `standards-reviewer` agent (subagent —
   keeps the analysis out of this context). Give it: the "Done means" list
   verbatim, and the changed files (`git diff --name-only` + `git status
   --short`). It returns PASS/FAIL/UNVERIFIABLE per criterion with
   file:line evidence, plus at most 10 findings at ≥80 confidence.
3. **Uplift scout (only if stage 2 has no FAILs).** Launch `uplift-scout`
   with the changed file list. It returns at most 3 advisory improvement
   opportunities near the touched code. Present them as optional; if the
   user declines, add them to `.vibe/ROADMAP.md` instead. Never block on
   them.

## Report

One compact table in chat: each DM criterion → PASS/FAIL + one-line
evidence. Then findings (if any), then uplift suggestions (if any).

- All criteria PASS → update `.vibe/STATE.md`: `status: checked`,
  `next_action: /vibe:act`. Tick the `- [x]` boxes in `.vibe/plan.md` and
  re-run `vibe-plan-html` so the HTML view shows progress.
- Any FAIL and budget remains → fix and re-run from stage 1.
- Budget exhausted → stop and report, as above.
