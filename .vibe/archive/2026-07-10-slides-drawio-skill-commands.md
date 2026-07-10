---
status: approved
created: 2026-07-10
retry_budget: 5
---
# Executive slides & draw.io diagrams from one command

## Objective

Add two new commands to the vibe plugin. `/vibe:slide` turns a topic — or the
work currently in progress — into a professional PowerPoint deck (.pptx) built
for leaders and business audiences: answer first, one message per slide, plain
business language, no technical jargon. `/vibe:drawio` does the same for
diagrams: a draw.io file (concept map, process flow with swimlanes, system
context, or timeline) that a non-technical reader understands at first glance.
Both follow written, citable quality rules (SL-* for slides, DG-* for
diagrams) distilled from enterprise research — consulting-style deck standards
(Minto Pyramid, action titles, executive summary) and executive diagram
conventions (few boxes, semantic colors, one takeaway per diagram) — saved in
`.vibe/research/2026-07-10-slide-drawio-rules.md`. At the same time we
simplify how ALL vibe commands work: today each command is a small file that
tells the AI to "read the skill file and execute it"; we remove that extra
layer so the skill itself IS the command — same `/vibe:...` names, one less
moving part.

## Done means

- [x] DM-1: WHEN `/vibe:slide <topic>` is invoked THE SYSTEM SHALL write
      `.vibe/exports/<date>-<slug>.pptx` that opens in PowerPoint/LibreOffice
      without a repair prompt (check: `python3 scripts/build_pptx.py
      --selftest` exits 0; when `soffice` is installed,
      `soffice --headless --convert-to pdf` on the output exits 0)
- [ ] DM-2: WHEN `/vibe:slide` is invoked with no arguments and
      `.vibe/plan.md` exists THE SYSTEM SHALL produce the deck about the
      current plan/roadmap (check: smoke run; deck's title slide names the
      plan's title)
- [x] DM-3: WHEN `/vibe:drawio` is invoked THE SYSTEM SHALL write a `.drawio`
      file that passes `python3 scripts/lint_drawio.py` — well-formed XML,
      unique ids, valid parent/source/target references, edge geometry
      present (check: lint exits 0 on a generated sample)
- [x] DM-4: Each new skill SHALL ship a references file with citable rules
      (`skills/slide/references/slide-design.md` SL-1.., 
      `skills/drawio/references/drawio-diagrams.md` DG-1..) and its SKILL.md
      SHALL cite at least 8 rule IDs (check: `grep -c 'SL-[0-9]'` /
      `grep -c 'DG-[0-9]'` in each SKILL.md ≥ 8)
- [x] DM-5: WHEN a user types `/vibe:plan|check|act|setup|release|slide|drawio`
      THE SYSTEM SHALL run the matching skill through a native Skill-tool
      invocation from a thin command (check: all 7 `commands/*.md` bodies
      instruct the Skill-tool call and pass arguments where the skill takes
      them; all 7 skills are model-invocable and hidden from the picker;
      `claude plugin validate --strict .` passes; fresh-session smoke of
      `/vibe:plan quick`)
- [x] DM-6: Every generated deck SHALL contain an executive-summary slide and
      full-sentence action titles by construction (check: `--selftest` asserts
      the exec-summary slide exists; standards-reviewer verifies SKILL.md
      mandates SL-3 and SL-7)
- [x] DM-7: `.vibe/verify.sh` SHALL remain green with the two new scripts
      included by its `scripts/*.py` glob (check: run it, exit 0)

## Approach

Chosen option: **Clean — native skills + zero-dependency builder** (over
"Minimal": keep the command wrappers and use the `python-pptx` library, which
would add a pip install requirement and keep the double layer; and over
"Pragmatic": support both a library path and a fallback path, which doubles
the code to test for no user-visible gain).

- **Entry points** (revised at user request mid-plan). Keep thin commands
  as the picker entries — `commands/plan|check|act|setup|release.md` plus
  new `slide.md` and `drawio.md` — but each body is now a single native
  invocation: "Invoke the Skill tool with `vibe:<name>` (and args)",
  replacing the old "read the skill file and execute it" prompt. To make
  that invocation work, the skill directories keep their short names
  (`skills/plan/` → `vibe:plan`), drop `disable-model-invocation` (the
  Skill tool can only call model-invocable skills), and set
  `user-invocable: false` with one-line descriptions, so the picker shows
  exactly one `/vibe:<name>` entry and idle-token cost stays minimal.
  `production-standards` stays a knowledge skill, unchanged.
- **`skills/slide/`** — SKILL.md pipeline: pick subject (args, else current
  `.vibe` work) → outline per SL rules (SCQA opening, executive summary with
  3–5 claims, one message per slide, action titles ≤15 words, ≤12 slides,
  everything framed as cost/risk/time/revenue) → emit a deck-spec JSON →
  run `scripts/build_pptx.py spec.json out.pptx`. The builder is stdlib-only
  Python (zipfile + ElementTree): it clones slides from a professionally
  themed `skills/slide/assets/template.pptx` shipped with the plugin
  (designed once, validated once — consistent quality every run) and injects
  the text. References file distilled from the research synthesis.
- **`skills/drawio/`** — SKILL.md pipeline: pick subject and diagram kind
  (concept map / swimlane / C4 context / timeline) per DG rules → author
  uncompressed mxfile XML following the validated skeleton and the 11-item
  pitfalls checklist (ids, parents, edge geometry, XML escaping, semantic
  colors, ≤9 boxes) → validate with stdlib `scripts/lint_drawio.py` →
  write to `.vibe/exports/`. No template needed; drawio files are plain text.
- **Files touched:** `commands/*` (rewritten as one-line Skill-tool
  invokers + 2 new), `skills/*` (renamed + 2 new),
  `scripts/build_pptx.py`, `scripts/lint_drawio.py` (new),
  `skills/slide/assets/template.pptx` (new), `.claude-plugin/plugin.json`
  (version bump at release), README.
- **Risk & mitigation:** hand-built OOXML is fiddly — mitigated by the
  template-clone approach (we never generate a full PPTX from scratch, only
  swap text in a known-good file), the `--selftest`, and the soffice
  conversion smoke where available.

## Out of scope

- The roadmap fixes R-1..R-7 (tests, fail-closed guard, debug breadcrumbs,
  atomic writes, CI, input validation, guard docs) — agreed to ship as the
  **next plan immediately after this one**, not in this change.
- Editable-in-PowerPoint charts/graphs on slides (v1 ships text, tables and
  image placeholders; native charts later if needed).
- Auto-committing generated decks/diagrams; exports land in `.vibe/exports/`
  and committing them is the user's call.
- Any change to the hook scripts' behavior (that's plan 2).
- PDF export pipeline beyond the optional soffice smoke test.
