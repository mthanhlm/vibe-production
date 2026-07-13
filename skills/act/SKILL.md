---
name: act
description: Vibe Act phase — promote working agreements, record one learning, tick the roadmap, archive the plan (never touches git); runs only when the user explicitly asks, after their own test. Invoked by the /vibe:act command.
user-invocable: false
---

# /vibe:act — Act (PDCA: Act)

The step that makes the next loop better. Three preconditions, then run
start-to-finish:

- **Gate.** Run only when BOTH hold: `.vibe/STATE.md` says
  `status: checked` (`doing` → suggest /vibe:check first; `done` → the
  loop is already closed, stop) AND the user explicitly asked for act this
  turn — typed /vibe:act or said so in their own words after testing the
  feature themselves. Act is never model-initiated; the human confirmation
  between Check and Act is the point of the loop.
- **Mode.** Fully automatic once started — no AskUserQuestion, no mid-run
  approval gates. Every write goes to git-committed files, never to plugin
  storage or only to conversation.
- **Git.** Act never touches git: no staging, no commit, no commit-message
  file — committing is entirely the user's (their commit process has rules
  that require it). Only if they separately and explicitly ask for git
  actions may git commands run, prefixed `VIBE_GIT=allow `.
  (`/vibe:release` is separate maintainer automation.)

## Steps

1. **Promote working agreements — automatically.** From this feature's
   review findings and user corrections, derive 0–3 one-line binding rules
   (e.g. "All new endpoints return RFC 9457 problem+json (API-3)") and
   append ALL of them to `.claude/rules/working-agreements.md` without
   asking; list what was promoted in the final summary so any rule can be
   reverted on request. Keep that file **under 60 lines total** — it loads
   every session; when it grows past that, merge or retire the weakest
   rules. Rules must be project decisions, not generic advice (generic
   advice already lives in production-standards).
2. **Record ONE learning.** Exactly one file per Act run:
   `docs/solutions/<YYYY-MM-DD>-<slug>.md` with frontmatter
   (`problem:`, `solution:`, `rules:` [IDs touched]) and ≤ 20 lines of body.
   Write it for the future agent that hits the same problem.
3. **Tick the roadmap.** In `.vibe/ROADMAP.md`: mark items this change
   completed, add items discovered during the work (from uplift-scout
   declines, deviation nudges, review findings out of scope). Keep it
   prioritized, top item first.
4. **Archive the plan.** Move `.vibe/plan.md` (and `.vibe/plan.<lang>.md`
   if present) to `.vibe/archive/<YYYY-MM-DD>-<slug>.*`. This CLOSES the
   plan gate — the next feature starts with /vibe:plan again.
5. **Update state — then STOP.** `.vibe/STATE.md`: `status: done`,
   `next_action: /vibe:plan`, one line naming what shipped. In the final
   summary, list the files that belong in the feature's commit (rules,
   learning, and the feature changes) — nothing more. No commit message
   is written and no git command runs; committing is entirely the user's,
   done manually. Never invoke another skill from here — starting the
   next feature is the user's decision.

Keep the whole Act pass short — it's bookkeeping, not a second review.
