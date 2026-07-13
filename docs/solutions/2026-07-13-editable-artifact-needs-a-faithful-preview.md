---
problem: A skill must ship an EDITABLE artifact (a .drawio that opens in
  diagrams.net) yet still satisfy WA-16's render-and-look gate — but a
  .drawio only renders faithfully in the drawio engine, a ~100MB electron
  app the house already rejected as too heavy/fragile on WSL.
solution: Build ONE model in a tested library, serialize it two ways from
  that single model — the editable deliverable (.drawio) AND a faithful
  preview (SVG) rendered with tooling already on the box (LibreOffice). The
  model reviews the preview; because both come from one model, the preview
  represents the deliverable.
rules: [WA-16, WA-13, WA-14]
---

Proven building /vibe:drawio (2026-07-13), suite part 2:

- The preview must be FAITHFUL or the review is worthless. The dogfood's
  render-review caught the SVG router drawing edges straight through
  connected boxes and a fan-out collapsing — the preview overstated
  problems. Fixed to border-anchored orthogonal routing; the honest comment
  now says "approximate; the real diagrams.net router is cleaner." A preview
  that lies (either way) breaks WA-16.
- Reuse the layout oracle you already have: graphviz `dot -Tplain` gives
  node positions (inches, y-up, center-anchored → px with a y-flip + 8-grid
  snap). Keep it a pure geometry oracle; the library owns all styling.
- No install needed at all this time (lighter than the deck's python-pptx):
  the diagram is pure stdlib XML, `dot` is optional (hand-grid fallback,
  exit 1), and `soffice` renders the SVG. When no renderer exists →
  UNVERIFIABLE-live with "open in diagrams.net", never a silent skip.
- Two more dogfood-only bugs (accent path picked the alphabetic node not the
  graph root after sorted-JSON layout; zone label collided with a top node)
  — both invisible to the validator, both caught by looking. The fresh-agent
  dogfood is the test of the skill text AND the library.
