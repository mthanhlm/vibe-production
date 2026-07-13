---
name: check
description: Vibe Check phase — project checks (failures only), criterion-by-criterion review with evidence, live end-to-end verification, retry budget respected; always stops for the user's own test before Act. Invoked by the /vibe:check command.
user-invocable: false
---

# /vibe:check — Check (PDCA: Check)

Verify outcomes against `.vibe/plan.md`'s "Done means" list. Outcome-based
("does the check pass"), never step-based ("did it use try-catch").
Check's job is to test everything a machine can test — the loop still ends
with the user's own hands: Check never invokes act.

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
3. **Live verification (only if stage 2 has no FAILs).** Drive the real
   feature end-to-end, per the plan's Verification section — tests passing
   is not the same as the feature working. First read
   `references/live-verification.md` (bundled with this skill); it gives
   the tool ladder — reuse the repo's own e2e tooling, else no-install
   built-ins (real commands, live hook payloads, curl, headless Chrome
   flags), else the consent-gated Playwright recipe
   (`references/playwright-cli.md` — drives the user's own Chrome, never
   downloads a browser, installs nothing without their OK) — plus Docker
   drivers, stuck-run timeout discipline, and how
   to slice complex features. Observe actual behavior and keep the
   evidence (output, exit codes, screenshots). If live driving is truly
   impossible here, mark the criterion UNVERIFIABLE-live and hand the user
   exact manual steps instead of skipping silently. A criterion whose live
   run contradicts its test evidence is a FAIL.
4. **Uplift scout (only if stages 2–3 have no FAILs).** Launch
   `uplift-scout` with the changed file list. It returns at most 3 advisory
   improvement opportunities near the touched code. Present them as
   optional; if the user declines, add them to `.vibe/ROADMAP.md` instead.
   Never block on them.

## Report

One compact table in chat: each DM criterion → PASS/FAIL + one-line
evidence (from tests AND the live run). Then findings (if any), then uplift
suggestions (if any).

- Every criterion PASS (UNVERIFIABLE is not a PASS) → update
  `.vibe/STATE.md`: `status: checked`, `next_action: user confirm →
  /vibe:act`. Tick the `- [x]` boxes in `.vibe/plan.md` and mirror the
  ticks in `.vibe/plan.<lang>.md` if it exists. Then **stop — always.**
  End the report with:
  - **Test it yourself:** 2–3 concrete actions derived from the plan's
    Verification section (exact commands to run, URL to open, thing to
    click) and what the user should see.
  - The breadcrumb: "When it looks good to you, run /vibe:act (or just
    say so) to close the loop."
  The user's manual confirmation is the real end of Check; act is theirs
  to trigger. `auto_chain` has no value that changes this — `"off"`
  disables the Do→Check hop, and legacy values (`"on"`, `"full"`,
  `"check"`) all behave like the default: check runs, then stops here.
- Any UNVERIFIABLE (and no FAIL) → do not mark checked — an unverifiable
  criterion is a plan defect; report it and ask the user.
- Any FAIL and budget remains → fix, then re-enter this skill from the
  top: the retry-budget gate runs on every re-entry — stop if exhausted,
  otherwise increment `check_attempts` — before any further fixing.
- Budget exhausted → stop and report, as above.

## After the stop — user feedback

- Feedback on the **same objective** ("the button is wrong", "the index
  misses X") → this same loop: re-enter this skill from the top. The
  budget gate is evaluated BEFORE any fix — an exhausted budget stops
  and asks even when the fix looks easy.
- Feedback that **changes scope** (new capability, different behavior than
  the plan's Objective) → suggest a fresh /vibe:plan; don't stretch this
  plan around it.

`vibe:act` is never invoked from check. It runs only when the user
explicitly asks — by typing /vibe:act or saying so in their own words.
