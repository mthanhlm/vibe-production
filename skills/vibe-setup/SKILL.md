---
name: vibe-setup
description: Onboard a project onto the vibe loop — discover house patterns, diff them against production standards into a prioritized uplift ROADMAP, write the verify script, initialize .vibe/ state, and optionally default the project to plan mode.
disable-model-invocation: true
user-invocable: false
---

# /vibe:setup — onboarding (activates the loop for this project)

Creating `.vibe/` is what switches the plan gate and nudges on for this
project — say so to the user before you do it.

## Steps

1. **Initialize state.** Create:
   - `.vibe/config.json` → `{"gate": "on", "plan_language": "vi"}`
     (ask the user for their preferred plan translation language; `vi`
     unless they say otherwise; `"none"` disables translation)
   - `.vibe/STATE.md` → `status: idle`, `next_action: /vibe:plan`
   - Everything in `.vibe/` (including the translated `plan.<lang>.md`) is
     meant to be committed and team-shared — no .gitignore entries needed.
2. **Discover house patterns.** Use Explore subagent(s) to map: language(s)
   and frameworks, how errors are handled today, how endpoints are shaped,
   test setup and coverage reality, config/secrets handling, migration
   story. File lists and short characterizations, not file dumps.
3. **Gap analysis.** Read the five `production-standards` reference files
   and diff them against the discovered patterns. For each gap: rule ID,
   one-line evidence (file:line), risk (high/med/low).
4. **Write `.vibe/ROADMAP.md`.** Prioritized by risk × touch-frequency,
   framed as **Strangler-Fig uplift**: fix-as-you-touch, one improvement per
   feature, explicitly NOT a big-bang refactor. Format:

   ```markdown
   # Uplift roadmap (gradual — one item per feature touched)
   - [ ] R-1 (high, S-2): raw SQL in src/db/*.py — parameterize on next touch
   - [ ] R-2 (high, E-1): 14 empty catch blocks in src/api/ — log or re-raise
   - [ ] R-3 (med, API-3): error responses are ad-hoc JSON — adopt problem+json
   ```

5. **Write `.vibe/verify.sh`.** The project's real test/lint/typecheck
   commands, one per line, `set -e` at top. Confirm the commands with the
   user if ambiguous. Make it executable. (`vibe-verify` will use it and
   show only failures.)
6. **Offer plan-mode default.** Ask the user: add
   `{"permissions": {"defaultMode": "plan"}}` to `.claude/settings.json`?
   (A plugin cannot set this itself; the settings write is their consent.)
   Skip silently if they decline.
7. **Report.** Summarize in chat: top-3 roadmap risks, the verify commands,
   and the loop: `/vibe:plan → code → /vibe:check → /vibe:act`.
