---
problem: Automating check→act (and Do→check) risked runaway skill loops,
  approval-gate bypass, or a stuck loop when a chain dies mid-hop.
solution: Chain at prompt level via the Skill tool only, from the
  every-criterion-PASS branch, writing STATE.md before each hop — so any
  skipped or interrupted chain degrades to the existing manual breadcrumb,
  never to a wrong action.
rules: [WA-1, WA-7, WA-9]
---

# Prompt-level chaining degrades to the breadcrumb

- The sanctioned seam already existed: WA-1 keeps `vibe:*` skills
  model-invocable precisely so the Skill tool can call them — no Stop
  hook, no new command, no infra.
- Write STATE.md BEFORE invoking the next skill: act's `status: checked`
  precondition holds, and if the session dies between hops a plain
  /vibe:act resumes the loop from the breadcrumb.
- Prove the chain graph is acyclic before shipping it: plan→check fires
  once per completion claim, check→check is bounded by retry_budget,
  check→act only on all-PASS, act→nothing (explicit "STOP means stop").
- UNVERIFIABLE is not a PASS — an unverifiable criterion is a plan
  defect and must stop the chain, not ride through it.
- Kill-switch follows the house config pattern (`auto_chain`, absent =
  on) and the chain announcement names it, so users discover the new
  behavior the first time it fires.
