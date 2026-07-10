---
name: slide
description: Build a board-ready .pptx deck from a topic or the current .vibe work, per the SL slide standards. Invoked by the /vibe:slide command.
user-invocable: false
argument-hint: "[topic — omit to present the current .vibe work]"
---

# /vibe:slide — executive deck (.pptx)

Arguments: $ARGUMENTS

Produce ONE `.pptx` at `.vibe/exports/<YYYY-MM-DD>-<slug>.pptx` for a
NON-TECHNICAL leadership audience: they want the concept, the logic, and
the ask — never the implementation. Read `references/slide-design.md`
(the SL rules) and `references/layout-catalog.md` (the 12 archetype
layouts + spec v2 schema with one JSON example per exhibit) BEFORE
outlining; every structural choice should be citable (e.g. "exec summary
first — SL-3", "proof beat must be a visual — SL-18").

The builder is spec v2: every slide is tagged with a story **beat**, the
beat picks a **layout** from the catalog, and word budgets are enforced
as build errors (SL-19). Decks come out visual by construction — charts,
icons, KPI tiles, timelines are drawn as native editable PowerPoint
shapes; bullets exist only for agendas.

## Steps

1. **Subject & language.** Use $ARGUMENTS as the topic; if empty, present
   the current work (read `.vibe/plan.md`, `.vibe/ROADMAP.md`,
   `.vibe/STATE.md`). Write slide text in the language the user made the
   request in; if the audience's language is genuinely unclear, ask one
   question, no more. Localize kickers and axis/source labels too.
2. **Story before slides (SL-1, SL-2).** Decide the single
   recommendation — that sentence is the deck title — then frame it as
   SCQA. Draft ALL slide titles first and read them alone: they must
   tell the complete story by themselves (SL-4), in ≤12 slides (SL-6).
3. **Beat-tag every slide (SL-17).** Assign each slide one beat —
   `hook, problem, insight, solution, how_it_works, proof, risks,
   roadmap, ask, status, transition, context, agenda` — then take the
   layout from the beat's row in the catalog's BEAT_LAYOUT table.
   Apply the must-be-visual triggers (SL-18): a comparison is `bars`, a
   trend is `column`/`line`, a bridge between two numbers is
   `waterfall`, a plan with dates is `timeline_roadmap`, one standout
   statistic is `big_number` — never bullets. Alternate quantitative and
   conceptual exhibits (SL-22). Pick `mode`: `board_preread` (default)
   or `keynote` for a live-presented deck (tighter budgets, dark theme).
4. **Gather visuals.** Charts/tiles/flows/timelines need only numbers in
   the spec. Icons: pick names from `skills/slide/assets/icons.json`
   (~225 Lucide icons). User images: `image` exhibit with a local path.
   Optional real photography (needs network): run
   `python3 <plugin-root>/scripts/fetch_photo.py "QUERY" .vibe/exports/media/`
   and put the returned `path` + `attribution` into a `photo` exhibit;
   if it exits non-zero just omit the path — the deck degrades to a
   branded gradient field (SL-23). Never block delivery on a photo.
5. **Build.** Write the spec v2 JSON (schema + examples in
   `references/layout-catalog.md`; authoritative field list in the
   `scripts/build_pptx.py` docstring — plugin root is two directories
   above this SKILL.md) to a temp file, then:
   `python3 <plugin-root>/scripts/build_pptx.py spec.json
   .vibe/exports/<YYYY-MM-DD>-<slug>.pptx`
   Budget failures (SL-19) mean the CONTENT is too heavy — tighten the
   story and rebuild. `--force` downgrades budgets to warnings; treat it
   as a last resort the user explicitly asked for, never a reflex.
6. **Validation is automatic.** Every build runs
   `scripts/validate_pptx.py` (exit 3 = invalid package, file kept). If
   you ever edit a deck by other means, re-run the validator by hand
   before delivering — LibreOffice opening a file does NOT prove
   PowerPoint will.
7. **Self-review, then deliver.** If `soffice` is available, convert the
   deck to PDF in a temp dir and LOOK at it: titles ≤2 lines, exhibits
   not overflowing their zones, exec-summary claims matching later
   titles, one accent color per slide — fix the spec and rebuild until
   clean. Report the .pptx path (and PDF preview if made), and keep the
   spec JSON next to the deck for quick edits.
