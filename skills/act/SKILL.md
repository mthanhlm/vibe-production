---
name: act
description: Vibe Act phase — promote working agreements, record one learning, tick the roadmap, archive the plan, prepare the commit message (never commits). Invoked by the /vibe:act command.
user-invocable: false
---

# /vibe:act — Act (PDCA: Act)

The step that makes the next loop better. Requires `.vibe/STATE.md` status
`checked` (if not, suggest /vibe:check first). All writes go to
git-committed files — never to plugin storage, never only to conversation.
Act runs **fully automatic** — no AskUserQuestion, no mid-run approval
gates. The one thing it never does is touch git: the user commits manually
(their commit process has rules that require it), unless they explicitly
ask for a commit in their own words.

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
5. **Update state.** `.vibe/STATE.md`: `status: done`,
   `next_action: /vibe:plan`, one line naming what shipped.
6. **Prepare the commit message — NEVER run git.** Write a single-feature
   commit message to `.vibe/commit-message.txt` and show it in chat with
   the list of files that belong in the commit (rules, learning, and the
   feature changes). Do NOT run `git add`, `git commit`, or `git push`
   from this skill under any circumstances — the user commits manually.
   Only when the user separately and explicitly asks for a commit in
   their own words may git commands run, prefixed with `VIBE_GIT=allow `
   (the guard blocks unapproved add/commit/push either way).

Keep the whole Act pass short — it's bookkeeping, not a second review.
