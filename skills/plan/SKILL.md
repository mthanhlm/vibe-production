---
name: plan
description: Plan a feature before code — interview the user, explore the codebase, write a 1–3 page human-readable plan with verifiable "Done means" criteria and a retry budget to .vibe/plan.md, get approval, render the bilingual HTML view.
disable-model-invocation: true
---

# /vibe:plan — Plan (PDCA: Plan, with OKR-style expectations)

Produce ONE plan file at `.vibe/plan.md`, 1–3 pages maximum, that a
non-engineer can read. **DO NOT START IMPLEMENTING WITHOUT USER APPROVAL.**
If the user says "whatever you think is best", give your recommendation and
still get explicit confirmation.

## Quick mode

If the arguments contain `quick` (or the diff is describable in one
sentence), skip the interview and exploration: write a plan whose Objective
is that one sentence, with 1–2 Done-means lines, get a one-line confirmation,
stamp it, done. Never force ceremony on a trivial change.

Arguments: $ARGUMENTS

## Steps

1. **Ensure state dir.** If `.vibe/` doesn't exist, create it and suggest
   running /vibe:setup later for the roadmap and verify script.
2. **Interview.** Use AskUserQuestion for what's genuinely open: the goal,
   who uses it, constraints, what's explicitly out of scope. 2–4 questions,
   not a questionnaire.
3. **Explore.** Use Explore subagent(s) to find the files/patterns involved.
   Instruct them to return **file lists and one-line roles, not file
   contents**. If the work touches APIs/errors/tests/security/system design,
   read the matching `production-standards` reference now, so the plan is
   standards-correct from the start.
4. **Approaches.** Form 2–3 named options (e.g. minimal / clean / pragmatic)
   with one-paragraph trade-offs. Recommend one.
5. **Write the plan** to `.vibe/plan.md` in exactly this shape:

   ```markdown
   ---
   status: draft
   created: <YYYY-MM-DD>
   retry_budget: 5
   ---
   # <Plain-language title>

   ## Objective
   One paragraph, plain language: what will exist when this is done, and how
   it fits into the system. No jargon a product owner couldn't read.

   ## Done means
   - [ ] DM-1: WHEN <condition> THE SYSTEM SHALL <observable outcome>
         (check: <test name / command / threshold>)
   - [ ] DM-2: ...
   3–8 lines. Each must pass: "could two agents disagree whether this
   passed?" If no → rewrite. Name a machine check wherever possible.
   More than ~10 criteria means the task should be split.

   ## Approach
   The how, compactly: files to touch, new interfaces, chosen option and why.
   A reader should be able to skim this section and still trust the plan.

   ## Out of scope
   Bullets. What this change deliberately does not do.
   ```

6. **Render with translation.** The `.md` plan stays **English-only** — the
   translation lives only inside the HTML. Translate the full plan (same
   headings, same order; keep rule IDs, code identifiers, and DM-numbers in
   English) into Vietnamese — or the `plan_language` from
   `.vibe/config.json` if set (`"none"` = skip translation) — and pipe the
   translated markdown to the renderer via stdin:

   ```bash
   vibe-plan-html --vi - <<'VIBE_VI'
   # <tiêu đề dịch>
   ...
   VIBE_VI
   ```

   (Falls back to `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/render_plan_html.py" --vi -`.)
   Tell the user to open `.vibe/plan.html` — it has the EN/VI toggle.
   Later re-renders without `--vi` keep the embedded translation.
7. **Approval gate.** Show the user the Objective and Done-means (chat is
   fine) and the plan.html path. Ask for approval with AskUserQuestion
   (approve / edit / cancel). Only on approval set `status: approved` in
   `.vibe/plan.md`, re-run `vibe-plan-html` (no `--vi` — the embedded
   translation is reused), and update `.vibe/STATE.md`:

   ```markdown
   ---
   status: doing
   plan: .vibe/plan.md
   next_action: /vibe:check
   check_attempts: 0
   updated: <YYYY-MM-DD>
   ---
   # Current work
   <title> — approved, implementing.
   ```

## While implementing (Do)

Don't re-read the whole plan every turn: section-map it
(`rg -n '^#{1,3}' .vibe/plan.md`) and read only the active section.
One feature per plan; finish to a commit before planning the next.
