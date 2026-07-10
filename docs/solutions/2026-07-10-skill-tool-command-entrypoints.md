---
problem: A thin slash command that says "invoke the Skill tool with vibe:<name>" silently cannot work while the target skill has `disable-model-invocation: true` — that flag removes the skill from the Skill tool's callable list entirely, so the command's instruction hits an unknown-skill error.
solution: Flip the pairing — commands keep `disable-model-invocation: true` (picker-only entries), while the skills behind them drop `disable-model-invocation` and set `user-invocable: false` with one-line descriptions.
rules: [WA-1]
---

Verified empirically: in a session with the 0.2.2 plugin, only
`vibe:production-standards` (the one skill without the flag) appears in the
Skill tool's list — the five flagged workflow skills are absent.

The working pairing per name in {plan, check, act, setup, release, slide,
drawio}:

- `commands/<name>.md` — description + optional argument-hint +
  `disable-model-invocation: true`; body: "Invoke the Skill tool now with
  skill `vibe:<name>` and args: $ARGUMENTS" (args line only if the skill
  consumes $ARGUMENTS).
- `skills/<name>/SKILL.md` — `name: <name>`, `user-invocable: false`, NO
  disable-model-invocation line, short description ending "Invoked by the
  /vibe:<name> command." (keeps idle tokens low and discourages
  spontaneous model invocation, which becomes possible once the flag drops).

Hidden cost of this design: model-invocable skill descriptions load every
session (~1 line each) — keep them one line.
