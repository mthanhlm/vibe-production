# draw.io diagram standards — executive audiences

Written fresh from a multi-source research pass (2026-07-10, synthesis in
`.vibe/research/2026-07-10-slide-drawio-rules.md`); sources are cited inline
per rule. Cite rules by ID (e.g. "violates DG-4").

## Diagram choice & audience fit

- **DG-1 (MUST)** Show executives only context-level views (C4 Level 1): the
  system, its users, and neighboring systems — people and business systems,
  never technologies, protocols, or infrastructure. "Works in a boardroom."
  [c4model.com/diagrams/system-context]
- **DG-2 (MUST NOT)** Use UML class, ER, sequence, or dense
  infrastructure/deployment diagrams for executives — the notation is
  undecodable to them, and an undecodable diagram has zero value. Use context
  views, swimlanes, or simple flows.
  [ben-morris.com/most-architecture-diagrams-are-useless]
- **DG-3 (MUST)** Give each diagram exactly one purpose and message — never
  one mega-diagram for all audiences; split into focused views per audience
  and abstraction level.
  [icepanel.io/blog/2023-02-21-top-6-mistakes-in-software-architecture-diagrams]
- **DG-4 (MUST)** Cap any single exec-facing diagram at ~5–9 boxes (Miller's
  7±2); group extras into named clusters. [lawsofux.com/millers-law]
- **DG-5 (SHOULD)** Use swimlane diagrams for business processes: one lane
  per department/role, horizontal lanes, left-to-right flow, with cross-lane
  handoff arrows visually flagged — handoffs are where delay and
  miscommunication concentrate. [atlassian.com swimlane-diagram;
  creately.com/guides/what-is-a-swimlane-diagram]
- **DG-6 (SHOULD)** Frame change proposals as a before/after (as-is vs to-be)
  pair with matched layouts, so the pitch becomes a visible delta to approve.
  [signavio.com/wiki/process-discovery/as-is-to-be-process-mapping]
- **DG-7 (SHOULD)** Sequence multiple diagrams as a narrative arc (context →
  tension → resolution) with progressive disclosure: one high-level summary
  visual first, detail on demand, at most two levels of depth.
  [thoughtspot.com data-storytelling; ixdf.org progressive-disclosure]

## Readability & labeling

- **DG-8 (MUST)** Title every diagram with a full-sentence takeaway (action
  title), not a topic label — see SL-7; everything in the diagram exists to
  prove that assertion.
  [slideworks.io/resources/how-to-write-action-titles-like-mckinsey]
- **DG-9 (MUST)** Label boxes and arrows in plain business language and frame
  elements by cost, risk, time, or revenue impact — never jargon or system
  properties (see SL-15).
  [winningpresentations.com/technical-presentation-non-technical-executives]
- **DG-10 (SHOULD)** Arrange sparse visual layouts along a Z-pattern: story
  starts top-left, outcome/call-to-action bottom-right; never fight natural
  reading order. [99designs.com/blog/tips/visual-hierarchy-landing-page-designs]
- **DG-11 (SHOULD)** Declutter aggressively: remove every element that
  doesn't support the takeaway; gray/desaturate everything except the one
  focal element highlighted in an accent color.
  [storytellingwithdata.com/blog/2017/3/29/declutter-this-graph]

## Color semantics

- **DG-12 (MUST)** Use color semantically and consistently across the whole
  diagram set: red only for problem/risk, green only for good/on-target,
  never decoratively. [deckary.com/blog/pillar-consulting-presentations-guide]
- **DG-13 (MUST NOT)** Rely on color alone to carry meaning (WCAG 1.4.1) —
  add labels, icons, patterns, or position; the diagram must survive
  grayscale printing and red/green color-blindness.
  [a11y-collective.com/blog/accessible-charts]

## Layout & generation quality

- **DG-14 (MUST)** Lay out on a coarse grid with non-intersecting bounding
  boxes: ~`x = col*180 + 40`, `y = row*120 + 40` (40–60px gutters); standard
  sizes 140×60 rectangles, 140×80 rhombus. Layout is entirely the generator's
  job — draw.io will not fix overlaps.
  [drawio.com/docs/reference/diagram-generation]
- **DG-15 (MUST)** Route edges with `edgeStyle=orthogonalEdgeStyle;rounded=1`
  and let the router route: no hand-placed waypoints or exit/entry points
  except back-edges and container-crossing edges.
  [drawio.com/docs/reference/diagram-generation]
- **DG-16 (MUST)** Emit plain uncompressed XML with no XML comments, then
  validate before returning: run `scripts/lint_drawio.py` — draw.io does not
  repair malformed files ("Not a diagram file"), and dangling references
  degrade silently. [drawio.com/docs/reference/diagram-generation;
  github.com/jgraph/drawio issues #2499, #3643]

## XML authoring essentials

Canonical skeleton (uncompressed; a bare `<mxGraphModel>` without the wrapper
is also accepted for single-page output):

```xml
<mxfile host="app.diagrams.net" type="device">
  <diagram id="page-1" name="Page-1">
    <mxGraphModel dx="0" dy="0" grid="1" gridSize="10" page="0" pageWidth="850" pageHeight="1100">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <mxCell id="n1" value="Start" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#DAE8FC;strokeColor=#6C8EBF;" vertex="1" parent="1">
          <mxGeometry x="40" y="40" width="140" height="60" as="geometry" />
        </mxCell>
        <mxCell id="n2" value="Decision?" style="rhombus;whiteSpace=wrap;html=1;fillColor=#FFF2CC;strokeColor=#D6B656;" vertex="1" parent="1">
          <mxGeometry x="40" y="180" width="140" height="80" as="geometry" />
        </mxCell>
        <mxCell id="e1" value="yes" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;endArrow=classic;" edge="1" parent="1" source="n1" target="n2">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

Generation pitfalls (all machine-checked by `scripts/lint_drawio.py`):

1. Always include structural cells `id="0"` and `id="1" parent="0"`; every
   other cell's `parent` must reference an existing id (usually `"1"`).
2. Unique ids (`n1..nN`, `e1..eN`); emit all vertices before any edge;
   `source`/`target` must name existing vertex ids.
3. Exactly one of `vertex="1"` xor `edge="1"` per cell.
4. Every cell needs an `<mxGeometry ... as="geometry"/>` child; edges use
   exactly `<mxGeometry relative="1" as="geometry" />` — a self-closing edge
   cell with no geometry child is the classic LLM bug.
5. XML-escape all attribute content (`&amp; &lt; &gt; &quot;`); unescaped `&`
   is the #1 cause of "Not a diagram file" — prefer "and" over "&" in labels.
   Line breaks: `&#xa;`.
6. Vertex styles need `html=1;whiteSpace=wrap;`; hex colors keep the `#`, no
   quotes inside the style string.
7. Non-rectangular shapes need matching `perimeter=` (e.g.
   `ellipse;perimeter=ellipsePerimeter;`) for clean edge attachment.
8. Container children (`parent="containerId"`) use coordinates relative to
   the container's top-left, below the swimlane title bar
   (`swimlane;startSize=30;horizontal=1;`); edges crossing container
   boundaries use `parent="1"`.
9. Default palette (draw.io's own): fills `#DAE8FC/#D5E8D4/#FFF2CC/#F8CECC`
   with strokes `#6C8EBF/#82B366/#D6B656/#B85450` — map to DG-12 semantics.
10. Multi-page = multiple `<diagram>` siblings under one `<mxfile>`; cells
    cannot be referenced across pages.
11. Expect first-pass semantic accuracy well under 100% — always run the
    linter and self-correct before returning the file.
    [arxiv.org/html/2601.05162v1]
