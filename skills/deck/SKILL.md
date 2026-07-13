---
name: deck
description: Vibe Deck phase — build a professional PowerPoint from a brief with the consent-gated python-pptx toolkit, an anti-slop design system (one idea per slide, assertion titles, single accent, 15-second readable), native-shape diagrams, and a mandatory render-and-review quality gate. Invoked by the /vibe:deck command.
user-invocable: false
---

# /vibe:deck — build an enterprise deck (anti-slop, render-verified)

Turn a brief into a `.pptx` that reads in 15 seconds a slide, for engineers
and executives alike. The whole point of this rebuild is the last stage:
**the model looks at what it made** and fixes it — a deck that only
validates is not done until it also looks right.

All heavy guidance is in bundled `references/` files, loaded on demand
(always-on cost stays flat). The design rules (DR-1..10) come from
`.vibe/research/2026-07-13-deck-taste-anti-slop.md`.

## Stages

1. **Consent + toolkit.** Follow the consent matrix in
   `references/build-recipe.md` §1. Install (once, with the user's OK) via
   `vibe-pptx-setup`; anything but `PPTX: ready` → report and stop. Never
   install without consent (WA-12/WA-14).
2. **Outline.** Read `references/build-recipe.md` §2 and
   `references/design-system.md`. One idea per slide (DR-1); write each
   assertion title first (DR-2); choose a layout per slide from
   `references/layouts.md`; prefer a number or diagram over a text slide.
3. **Build.** Compose `scripts/deck_lib.py` layout calls in a per-deck build
   script run with the toolkit venv python — never author raw python-pptx
   (that is how the old unit grew to 5,200 lines of slop). Include ≥1
   native-shape diagram slide where the content warrants (`flow()`).
4. **Validate.** `scripts/validate_deck.py` is the hard gate (DK-* → DR-*).
   Fix and rebuild until `DECK PASS`.
5. **Render + review (required — DR-10).** Render every slide to PNG
   (`soffice` → pdf → `pdftoppm`), then look at each and judge it against the
   15-second glance test and the slop tells (DR-9); quote a per-slide
   verdict. Fix → rebuild → re-validate → re-render → re-review until a full
   pass finds nothing new. This stage is never skipped.
6. **Deliver.** Keep `deck.pptx` + `preview/*.png` under
   `.vibe/exports/<date>-<slug>/`; delete the run dir; the target repo shows
   changes only under `.vibe/`. Report the deck path, the validator PASS
   line, and the per-slide review verdicts.

## Boundaries

Native-shape diagrams only — no drawio-CLI export (that is suite part 2). No
stock photos, no live-data charts (static values from the brief). Git stays
the user's (WA-7).
