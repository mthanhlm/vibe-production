---
problem: Removing a feature by deleting only its skill/command entry points
  leaves dead build scripts, tests, license attributions, and binding
  working agreements that keep running in CI and mislead readers.
solution: Treat removal as a footprint inventory, then one clean sweep.
rules: [WA-8]
---
Before deleting anything, run one exploration pass that inventories the
full footprint — exclusive scripts (check imports both ways), tests and
fixtures, docs/solutions notes, NOTICES attributions (Lucide rode along
with the slide skill), README counts, and working agreements that govern
the removed pipeline (WA-2/WA-3 here).

Then verify absence, not just deletion: a repo-wide
`git grep -ilE '<feature identifiers>'` that must print nothing is a
stronger done-criterion than a list of `rm` commands.

Two things made this sweep cheap: nothing else imported the feature's
scripts (self-contained unit), and commands/skills/scripts/tests are all
auto-discovered, so CI, hooks.json, and the plugin manifest needed zero
edits. Retired WA numbers are never reused or renumbered (WA-8).
