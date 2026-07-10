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

## Style tokens (copy verbatim)

Single source of truth for every style string (probe-proven 2026-07-10;
research §6 in `.vibe/research/2026-07-10-enterprise-visual-uplift.md`).
Start from a token, never from scratch (DG-17).

Light theme (default):

```
node card:      rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#DDE3EA;strokeWidth=1;fontFamily=Helvetica;fontSize=12;fontColor=#1F2937;shadow=0;
zone container: rounded=1;arcSize=6;container=1;collapsible=0;verticalAlign=top;align=left;spacingLeft=12;spacingTop=8;fontStyle=1;fontSize=12;fillColor=#76B900;fillOpacity=6;strokeColor=#76B900;strokeWidth=1;whiteSpace=wrap;html=1;
neutral edge:   edgeStyle=orthogonalEdgeStyle;rounded=1;jettySize=auto;orthogonalLoop=1;strokeWidth=1.5;strokeColor=#8A8F98;endArrow=blockThin;endFill=1;startArrow=none;jumpStyle=gap;jumpSize=8;fontSize=11;labelBackgroundColor=#FFFFFF;
```

Dark theme (hero one-pagers):

```
hero band:      rounded=1;arcSize=10;fillColor=#1E1E1E;gradientColor=#2A3618;gradientDirection=south;strokeColor=#76B900;strokeWidth=1;fontColor=#FFFFFF;fontStyle=1;whiteSpace=wrap;html=1;
```

Official cloud notation (icon libraries bundled with draw.io):

```
AWS node:       sketch=0;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.lambda;fillColor=#ED7100;strokeColor=#ffffff;verticalLabelPosition=bottom;verticalAlign=top;align=center;fontSize=12;html=1;
```

Semantic colors (DG-12) reuse the draw.io defaults from pitfall 9:
risk/problem = fill `#F8CECC` stroke `#B85450`; good/on-target = fill
`#D5E8D4` stroke `#82B366`.

Frozen palette — `scripts/lint_drawio.py` warns (DG-17) on any
`fillColor/strokeColor/fontColor/gradientColor/labelBackgroundColor` value
outside this list (case-insensitive; `none` and `default` always allowed):
tokens `#FFFFFF #000000 #1E1E1E #1F2937 #2A3618 #76B900 #8A8F98 #DDE3EA
#ED7100` plus draw.io defaults `#DAE8FC #D5E8D4 #FFF2CC #F8CECC #6C8EBF
#82B366 #D6B656 #B85450` (pitfall 9).

### Style rules

- **DG-17 (MUST)** Start every style from a named token above; restrict
  colors to the frozen palette; ≤5 hues per diagram with exactly one
  accent, and put the accent only on the primary path.
- **DG-18 (MUST)** Lay out on an 8px grid: `gridSize="8"` on the model and
  every vertex x/y/width/height a multiple of 8 (the DG-14 standard sizes
  round to 144×64 boxes and 144×80 rhombus on this grid); sibling gaps
  ≥40px (24px hard floor); container children padded ≥24px from the
  container edge; containers nested at most 3 levels deep.
- **DG-19 (MUST)** Edge discipline: every edge carries
  `edgeStyle=orthogonalEdgeStyle;rounded=1` plus `jumpStyle=gap` (line
  jumps at crossings); `dashed=1` is reserved exclusively for
  logical/security boundary containers — never edges or plain nodes.
- **DG-20 (MUST)** Inline icons only as URL-encoded SVG data-URIs
  (`image=data:image/svg+xml,<urllib.parse.quote(svg, safe='')>`) — never
  `;base64`: the semicolon terminates the style key and corrupts the
  style. Recipe (stdlib, probe-proven):

  ```python
  import urllib.parse
  enc = urllib.parse.quote('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="#0B5FFF"/><path d="M7 12.5l3.2 3.2L17 9" stroke="#FFFFFF" stroke-width="2.4" fill="none"/></svg>', safe='')
  style = f'label;whiteSpace=wrap;html=1;rounded=1;arcSize=10;imageWidth=24;imageHeight=24;imageAlign=left;imageVerticalAlign=middle;spacingLeft=40;image=data:image/svg+xml,{enc};'
  ```

  Keep icon artwork on a 24×24 viewBox; `imageAlign=left;spacingLeft=40`
  clears the label text off the icon.
- **DG-21 (SHOULD)** Effects restraint: 2-stop gradients only
  (`gradientColor` + `gradientDirection`); `arcSize` between 2 and 24;
  blurred-shadow keys (`shadowBlur`/`shadowOpacity`/`shadowColor`/
  `shadowOffsetX`/`shadowOffsetY`) render only in draw.io ≥24.0 — plain
  `shadow=1` is the portable fallback; Helvetica is the portable font
  default (web fonts depend on the viewing environment).

## Fidelity self-check (no local renderer)

The linter proves structure, not looks — no draw.io renderer exists on the
delivery machine. Two layers of defense:

One-time human check (once per viewer generation, in app.diagrams.net):

- [ ] 2-stop and radial gradients render (hero band token)
- [ ] blurred-shadow keys render (draw.io ≥24.0; otherwise `shadow=1`)
- [ ] inline URL-encoded SVG icons render at 24×24
- [ ] diagram survives grayscale export — meaning intact without color
      (DG-13)

Pre-delivery model checklist (every diagram, before linting):

- [ ] every style string starts from a token, verbatim (DG-17)
- [ ] exactly one accent hue, on the primary path only (DG-17)
- [ ] every label fits its box: ~7px per character at 12pt plus 15% slack
      must not exceed the box width — widen the box or shorten the label
- [ ] any viewer-version-dependent feature used (e.g. blurred shadows) is
      named in the delivery note

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
