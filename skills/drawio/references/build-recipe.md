# Build recipe — brief → validated, render-reviewed .drawio

The end-to-end procedure. Every command ran on a real machine before it was
written here. No install needed — the diagram is pure XML; the preview
renders with LibreOffice (already present). Work in the target project; the
diagram and its preview land under `.vibe/` (gate-exempt).

## 1. Topology (DL-1, DL-2)

Read the brief and name the nodes and edges. One idea per diagram (DL-1,
≤12 nodes); if it holds two ideas, make two linked diagrams. Node labels
≤3 words (DL-2). Decide the shape: flow, tree, or hand-grid (layouts.md).

## 2. Layout

```bash
OUT="<project>/.vibe/exports/$(date +%F)-<slug>"; mkdir -p "$OUT"
```

Non-trivial graph (branching, tree, >~5 nodes): write a `.dot` (fixed box
size, layouts.md §1/§2) and lay it out with graphviz:

```bash
python3 <plugin>/scripts/drawio_layout.py flow.dot   # JSON positions on stdout
```

Exit 1 means `dot` isn't installed → fall back to the hand grid (layouts.md
§3), placing nodes on multiples of 8 yourself. Simple fixed arrangements use
the hand grid directly.

## 3. Build (compose the library — never raw XML)

Write a build script that imports `drawio_lib`, builds the `Diagram` from
the layout (`from_layout`) or hand-placed `node()`/`zone()`/`edge()` calls,
and `save()`s both files:

```bash
python3 build.py      # writes $OUT/diagram.drawio AND $OUT/diagram.svg
```

## 4. Validate (DL-1..7, hard gate)

```bash
python3 <plugin>/scripts/validate_drawio.py "$OUT/diagram.drawio"
```

Exit 0 = `DIAGRAM PASS`. Any `cell <id>: DL-x …` line → fix the build
script and rebuild. Don't proceed to review with failures outstanding.

## 5. Render + review (the required stage — DR-10, WA-16)

```bash
timeout 90 soffice --headless --convert-to png --outdir "$OUT" "$OUT/diagram.svg"
mv "$OUT/diagram.png" "$OUT/preview.png"
```

Then **look at `preview.png`** and judge it against DR-8 and the 15-second
glance: does the topology read at a glance? one idea? clean orthogonal
edges, few crossings? labels economical? single accent on the primary path?
no slop tells (DR-9: shadows, clip-art, gradients)? Quote a one-line
verdict. Any fail → fix the build script, rebuild, re-validate, re-render,
re-review until a full pass finds nothing new.

If no SVG renderer exists on the machine (`soffice` absent and no
fallback), the criterion is **UNVERIFIABLE-live**: report it with manual
steps — "open `diagram.drawio` at app.diagrams.net and confirm it reads" —
never skip silently (WA-12).

## 6. Deliver + teardown

Keep `$OUT/diagram.drawio` (the editable deliverable) and `$OUT/preview.png`
(the evidence). Tell the user the `.drawio` opens and edits at
app.diagrams.net. The target repo shows changes only under `.vibe/`
(`git status --porcelain`). Offer once an `exports/` line in
`.vibe/.gitignore` if the artifacts shouldn't be committed.
