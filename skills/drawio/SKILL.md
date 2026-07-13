---
name: drawio
description: Vibe Drawio phase — turn a topology into a professional, editable draw.io diagram (opens in diagrams.net) with an anti-slop design system (one idea, ≤3-word labels, single accent, orthogonal edges, 8px grid), graphviz layout, and a mandatory render-and-review quality gate. Invoked by the /vibe:drawio command.
user-invocable: false
---

# /vibe:drawio — build an editable diagram (anti-slop, render-verified)

Turn a flow, architecture, or process into a `.drawio` file that reads in
seconds and edits in the free draw.io / diagrams.net app. Suite part 2,
built on the same pattern as /vibe:deck: one model → two serializations
(editable `.drawio` + a faithful SVG) → a validator → **the model looks at
the rendered diagram** before delivery (WA-16). No heavy install — the
preview renders with LibreOffice.

Heavy guidance is in bundled `references/`, loaded on demand (WA-13). The
design rules (DL-1..8) reuse the deck research DR-8/DR-5 and the drawio
research DG-17..21, plus the semantic-node uplift (typed nodes, loop
back-edges, legend, label-fit) recorded in the 2026-07-13 amendment.

## Stages

1. **Topology.** Read `references/build-recipe.md` §1 and
   `references/design-system.md`. Name nodes/edges; one idea per diagram
   (DL-1); labels ≤3 words (DL-2); give each node a semantic **kind**
   (action / decision / success / error / data / external / start / end) and
   pick a layout from `references/layouts.md`. Loops use a dashed back-edge;
   a multi-type diagram gets a `legend()`.
2. **Layout.** Non-trivial graph → write a `.dot` and run
   `scripts/drawio_layout.py` (graphviz). `dot` absent (exit 1) → hand grid
   on the 8px grid. Simple arrangements use the hand grid directly.
3. **Build.** Compose `scripts/drawio_lib.py` (`from_layout` or
   `node`/`zone`/`edge`) and `save()` both files — never author raw
   mxGraphModel XML (the slop road WA-16 forbids).
4. **Validate.** `scripts/validate_drawio.py` is the hard gate (DL-* →
   DR/DG). Fix and rebuild until `DIAGRAM PASS`.
5. **Render + review (required — DR-10).** SVG → `soffice` → `preview.png`,
   then look at it and judge against DR-8 + the 15-second glance; quote a
   verdict. Fix → rebuild → re-validate → re-render → re-review until clean.
   No renderer → UNVERIFIABLE-live with "open in diagrams.net" steps, never
   skipped (WA-12).
6. **Deliver.** Keep `diagram.drawio` + `preview.png` under
   `.vibe/exports/<date>-<slug>/`; the `.drawio` edits at app.diagrams.net;
   the target repo shows changes only under `.vibe/`. Report the paths, the
   validator PASS line, and the render-review verdict.

## Boundaries

Shapes and labels only — no icon/clip-art vendoring. Flow, tree, and layered
architecture (no sequence/mind-map layouts). No drawio-desktop install.
Git stays the user's (WA-7).
