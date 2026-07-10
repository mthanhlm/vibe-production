---
problem: A parallel implementation agent, given a behavior table containing a casually-written entry ("git push --force-with-lease → exit 0"), "reconciled" the conflict with existing code by exempting force-with-lease from the git guard's APPROVAL gate — opening an unapproved-push path. Its own tests passed because they encoded the same wrong expectation.
solution: State security invariants explicitly in fan-out prompts ("every push requires approval, no exceptions") instead of only enumerating input→output rows, and hand-review any agent-reported "reconciliation" or judgment call against the invariant before integrating.
rules: [E-3, T-1, WA-5]
---

What made it dangerous: the change was locally coherent (the destructive
rule itself recommends force-with-lease, so exempting it "made sense"),
green under its own tests, and clearly explained in the agent's summary —
the summary is what exposed it. Read agent summaries for the word
"reconciled/decided/changed behavior" and audit those lines first.

The fix restored the two-layer design: RULES classifies destructive
commands (force-with-lease exempt there by design), APPROVAL_RE gates
every add/commit/push unconditionally after it. Regression-pinned by
tests/test_git_guard.py::test_force_with_lease_not_destructive_but_needs_approval.
