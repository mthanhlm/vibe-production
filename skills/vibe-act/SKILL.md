---
name: vibe-act
description: Close the loop after a checked change — promote accepted patterns to committed working agreements, record one learning, tick the uplift roadmap, archive the plan, and prepare the commit.
disable-model-invocation: true
---

# /vibe:act — Act (PDCA: Act)

The step that makes the next loop better. Requires `.vibe/STATE.md` status
`checked` (if not, suggest /vibe:check first). All writes go to
git-committed files — never to plugin storage, never only to conversation.

## Steps

1. **Promote working agreements.** From this feature's review findings and
   user corrections, propose 0–3 one-line binding rules (e.g. "All new
   endpoints return RFC 9457 problem+json (API-3)"). Confirm with the user
   via AskUserQuestion, then append accepted ones to
   `.claude/rules/working-agreements.md`. Keep that file **under 60 lines
   total** — it loads every session; when it grows past that, merge or
   retire the weakest rules. Rules must be project decisions, not generic
   advice (generic advice already lives in production-standards).
2. **Record ONE learning.** Exactly one file per Act run:
   `docs/solutions/<YYYY-MM-DD>-<slug>.md` with frontmatter
   (`problem:`, `solution:`, `rules:` [IDs touched]) and ≤ 20 lines of body.
   Write it for the future agent that hits the same problem.
3. **Tick the roadmap.** In `.vibe/ROADMAP.md`: mark items this change
   completed, add items discovered during the work (from uplift-scout
   declines, deviation nudges, review findings out of scope). Keep it
   prioritized, top item first.
4. **Archive the plan.** Move `.vibe/plan.md` and `.vibe/plan.html` to
   `.vibe/archive/<YYYY-MM-DD>-<slug>.*`. This CLOSES the plan gate — the
   next feature starts with /vibe:plan again.
5. **Update state.** `.vibe/STATE.md`: `status: done`,
   `next_action: /vibe:plan`, one line naming what shipped.
6. **Offer the commit.** Propose a single-feature commit including the
   `.vibe/` state, rules, and learning files. Do not commit without the
   user's go-ahead; once they approve, prefix the git commands with
   `VIBE_GIT=allow ` (the guard blocks unapproved add/commit/push).

Keep the whole Act pass short — it's bookkeeping, not a second review.
