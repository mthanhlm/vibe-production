# DELIVERABLE 1: DRAFT `slide-design.md`

```markdown
# Slide Design Standards — Executive Decks (SL rules)

Standards for decks aimed at non-technical leadership. Cite rules by ID (e.g. "violates SL-4").

## Deck structure

- **SL-1 (MUST)** Lead with the answer: recommendation/conclusion first, then supporting arguments, then data (Minto Pyramid). Open from a decision the executive owns (budget, risk, deadline) — mechanism comes only after they know why they should care. [managementconsulted.com/pyramid-principle; okundata.com/blog/data-storytelling]
- **SL-2 (SHOULD)** Open with SCQA framing (Situation, Complication, Question, Answer) to anchor agreed facts, create why-now tension, and position the Answer as the top of the pyramid. [modelthinkers.com/mental-model/minto-pyramid-scqa]
- **SL-3 (MUST)** Include an executive-summary slide up front: 3–5 bold-claim bullets max, each mapping 1:1 in order to subsequent slide titles (BCG/McKinsey/Bain standard). [deckary.com/blog/executive-summary-slides]
- **SL-4 (MUST)** Pass horizontal logic: reading only the slide titles in sequence must tell the complete, convincing story — the title-only read is the de facto executive consumption mode. [storytellingwithdata.com/blog/2013/12/horizontal-logic]
- **SL-5 (MUST)** Group supporting points MECE (mutually exclusive, collectively exhaustive), ideally ~3 per grouping, so the logic is auditable at a glance. [modelthinkers.com/mental-model/minto-pyramid-scqa]
- **SL-6 (SHOULD)** Keep decks short: audiences absorb ~10 concepts per meeting; for pitch-style decks apply 10/20/30 (~10 slides, 20 minutes, no font below 30pt). [guykawasaki.com/the_102030_rule]

## Per-slide rules

- **SL-7 (MUST)** Write action titles: every title is a complete sentence stating the slide's takeaway ("so what"), ≤15 words, ≤2 lines, active voice, quantitative where possible — never a topic label like "Q3 Revenue Overview". [slideworks.io/resources/how-to-write-action-titles-like-mckinsey]
- **SL-8 (MUST)** Pass vertical logic: everything in the slide body must directly prove the title's claim; delete anything that doesn't. [slidescience.co/strategy-presentations]
- **SL-9 (MUST)** One message per slide — two ideas means two slides — and the main point must survive a 3-second glance test (Duarte "glance media"). [deckary.com/blog/consulting-slide-standards; duarte.com/resources/guides-tools/the-glance-test]
- **SL-10 (SHOULD)** Use assertion-evidence structure: sentence headline supported by visual evidence (chart, diagram, photo), not bullet lists — controlled studies show better comprehension and recall (p < .01). [writing.engr.psu.edu/research.html]
- **SL-11 (MUST)** Cut extraneous words, images, and decoration (Mayer coherence principle, 23/23 experiments, median effect 0.86); never put the presenter's full narration as on-screen text (redundancy principle). [cambridge.org, Cambridge Handbook of Multimedia Learning]

## Data-viz on slides

- **SL-12 (MUST)** Declutter every chart to maximize data-ink — no 3D, decorative borders, heavy gridlines, or redundant labels (Tufte) — then highlight exactly one takeaway with preattentive attributes (color, size, position), stated in the title. An unhighlighted chart makes executives do the analysis themselves. [data.europa.eu/apps/data-visualisation-guide/chart-junk-and-data-ink-origins; Knaflic, onlinelibrary.wiley.com/doi/10.1002/9781119055259.ch4]

## Visual polish

- **SL-13 (MUST)** Keep type readable and restrained: body ≥18pt (24pt for projection), titles 28–36pt, max two typefaces, sans-serif for screens. [brightcarbon.com/blog/presentation-font-size]
- **SL-14 (SHOULD)** Leave ≥15–20% of each slide as whitespace and limit the palette to ~3 colors (primary, secondary, accent). [deckary.com/blog/pillar-powerpoint-design-guide]

## Audience fit (non-technical leadership)

- **SL-15 (MUST)** Frame every technical element as cost, risk, time, or revenue impact, never system properties ("removes the single point of failure that took payments down nine hours" — not "active-active cluster"). Explain unavoidable technical concepts with one clean analogy from the audience's world. [winningpresentations.com/technical-presentation-non-technical-executives; leapica.com/explain-technical-concepts-non-technical-audiences]
- **SL-16 (MUST)** For board/leadership decks, design to stand alone as a pre-read (sent 1–2 days ahead) and surface what directors check first: cash/runway, metrics vs plan, and explicit asks/decisions needed. [articles.sequoiacap.com/preparing-a-board-deck]
```

---

# DELIVERABLE 2: DRAFT `drawio-diagrams.md`

```markdown
# draw.io Diagram Standards — Executive Audiences (DG rules)

Standards for diagrams aimed at non-technical leadership, plus draw.io XML authoring essentials. Cite rules by ID (e.g. "violates DG-4").

## Diagram choice & audience fit

- **DG-1 (MUST)** Show executives only context-level views (C4 Level 1): the system, its users, and neighboring systems — people and business systems, never technologies, protocols, or infrastructure. "Works in a boardroom." [c4model.com/diagrams/system-context]
- **DG-2 (MUST NOT)** Use UML class, ER, sequence, or dense infrastructure/deployment diagrams for executives — the notation is undecodable to them, and an undecodable diagram has zero value. Use context views, swimlanes, or simple flows. [ben-morris.com/most-architecture-diagrams-are-useless]
- **DG-3 (MUST)** Give each diagram exactly one purpose and message — never one mega-diagram for all audiences; split into focused views per audience and abstraction level. [icepanel.io/blog/2023-02-21-top-6-mistakes-in-software-architecture-diagrams]
- **DG-4 (MUST)** Cap any single exec-facing diagram at ~5–9 boxes (Miller's 7±2); group extras into named clusters. [lawsofux.com/millers-law]
- **DG-5 (SHOULD)** Use swimlane diagrams for business processes: one lane per department/role, horizontal lanes, left-to-right flow, with cross-lane handoff arrows visually flagged — handoffs are where delay and miscommunication concentrate. [atlassian.com swimlane-diagram; creately.com/guides/what-is-a-swimlane-diagram]
- **DG-6 (SHOULD)** Frame change proposals as a before/after (as-is vs to-be) pair with matched layouts, so the pitch becomes a visible delta to approve. [signavio.com/wiki/process-discovery/as-is-to-be-process-mapping]
- **DG-7 (SHOULD)** Sequence multiple diagrams as a narrative arc (context → tension → resolution) with progressive disclosure: one high-level summary visual first, detail on demand, at most two levels of depth. [thoughtspot.com data-storytelling; ixdf.org progressive-disclosure]

## Readability & labeling

- **DG-8 (MUST)** Title every diagram with a full-sentence takeaway (action title), not a topic label — see SL-7; everything in the diagram exists to prove that assertion. [slideworks.io/resources/how-to-write-action-titles-like-mckinsey]
- **DG-9 (MUST)** Label boxes and arrows in plain business language and frame elements by cost, risk, time, or revenue impact — never jargon or system properties (see SL-15). [winningpresentations.com/technical-presentation-non-technical-executives]
- **DG-10 (SHOULD)** Arrange sparse visual layouts along a Z-pattern: story starts top-left, outcome/call-to-action bottom-right; never fight natural reading order. [99designs.com/blog/tips/visual-hierarchy-landing-page-designs]
- **DG-11 (SHOULD)** Declutter aggressively: remove every element that doesn't support the takeaway; gray/desaturate everything except the one focal element highlighted in an accent color. [storytellingwithdata.com/blog/2017/3/29/declutter-this-graph]

## Color semantics

- **DG-12 (MUST)** Use color semantically and consistently across the whole diagram set: red only for problem/risk, green only for good/on-target, never decoratively. [deckary.com/blog/pillar-consulting-presentations-guide]
- **DG-13 (MUST NOT)** Rely on color alone to carry meaning (WCAG 1.4.1) — add labels, icons, patterns, or position; the diagram must survive grayscale printing and red/green color-blindness. [a11y-collective.com/blog/accessible-charts]

## Layout & generation quality

- **DG-14 (MUST)** Lay out on a coarse grid with non-intersecting bounding boxes: ~`x = col*180 + 40`, `y = row*120 + 40` (40–60px gutters); standard sizes 140×60 rectangles, 140×80 rhombus. Layout is entirely the generator's job — draw.io will not fix overlaps. [drawio.com/docs/reference/diagram-generation]
- **DG-15 (MUST)** Route edges with `edgeStyle=orthogonalEdgeStyle;rounded=1` and let the router route: no hand-placed waypoints or exit/entry points except back-edges and container-crossing edges. [drawio.com/docs/reference/diagram-generation]
- **DG-16 (MUST)** Emit plain uncompressed XML with no XML comments, then validate before returning: parse as XML and run the structural checklist below — draw.io does not repair malformed files ("Not a diagram file"), and dangling references degrade silently. [drawio.com/docs/reference/diagram-generation; github.com/jgraph/drawio issues #2499, #3643]

## XML authoring essentials

Canonical skeleton (uncompressed; a bare `<mxGraphModel>` without the wrapper is also accepted for single-page output):

```xml
<mxfile host="app.diagrams.net" type="device">
  <diagram id="page-1" name="Page-1">
    <mxGraphModel dx="0" dy="0" grid="1" gridSize="10" page="0" pageWidth="850" pageHeight="1100">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <!-- vertices first -->
        <mxCell id="n1" value="Start" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#DAE8FC;strokeColor=#6C8EBF;" vertex="1" parent="1">
          <mxGeometry x="40" y="40" width="140" height="60" as="geometry" />
        </mxCell>
        <mxCell id="n2" value="Decision?" style="rhombus;whiteSpace=wrap;html=1;fillColor=#FFF2CC;strokeColor=#D6B656;" vertex="1" parent="1">
          <mxGeometry x="40" y="180" width="140" height="80" as="geometry" />
        </mxCell>
        <!-- edges last, expanded form -->
        <mxCell id="e1" value="yes" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;endArrow=classic;" edge="1" parent="1" source="n1" target="n2">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

(Note: the comments above are illustrative only — per DG-16, real output must contain no `<!-- -->` comments.)

Top generation pitfalls [drawio.com/docs/reference/diagram-generation; github.com/jgraph/drawio-mcp shared/]:

1. Always include structural cells `id="0"` and `id="1" parent="0"`; every other cell's `parent` must reference an existing id (usually `"1"`).
2. Unique ids (`n1..nN`, `e1..eN`); emit all vertices before any edge; `source`/`target` must name existing vertex ids.
3. Exactly one of `vertex="1"` xor `edge="1"` per cell.
4. Every cell needs a `<mxGeometry ... as="geometry"/>` child; edges use exactly `<mxGeometry relative="1" as="geometry" />` — a self-closing edge cell with no geometry child is the classic LLM bug.
5. XML-escape all attribute content (`&amp; &lt; &gt; &quot;`); unescaped `&` is the #1 cause of "Not a diagram file" — prefer "and" over "&" in labels. Line breaks: `&#xa;`.
6. Vertex styles need `html=1;whiteSpace=wrap;`; hex colors keep the `#`, no quotes inside the style string.
7. Non-rectangular shapes need matching `perimeter=` (e.g. `ellipse;perimeter=ellipsePerimeter;`) for clean edge attachment.
8. Container children (`parent="containerId"`) use coordinates relative to the container's top-left, below the swimlane title bar (`swimlane;startSize=30;horizontal=1;`); edges crossing container boundaries use `parent="1"`.
9. Default palette (draw.io's own): fills `#DAE8FC/#D5E8D4/#FFF2CC/#F8CECC` with strokes `#6C8EBF/#82B366/#D6B656/#B85450` — map to DG-12 semantics.
10. Multi-page = multiple `<diagram>` siblings under one `<mxfile>`; cells cannot be referenced across pages.
11. Expect first-pass semantic accuracy well under 100% (~90% XML validity, 58–94% component accuracy in studies) — always run the DG-16 checklist and self-correct. [arxiv.org/html/2601.05162v1]
```

---

# DELIVERABLE 3: TOOLING RECOMMENDATION (slide output)

**Default:** agent-authored, self-contained single-file `deck.html` (all CSS/JS inline, assets as data URIs, keyboard nav) with print CSS `@page { size: 1280px 720px }` so browser Print→PDF yields a true slide PDF. Zero dependencies, highest polish ceiling, fully offline. Always also emit a Marp-flavored `slides.md` as the editable source of truth.

**Degradation/enhancement chain (probe at runtime, in order):**
1. Always: `deck.html` + `slides.md` — cannot fail.
2. Node ≥18 present: `npx @marp-team/marp-cli slides.md` → themed HTML; if Chrome/Edge/Firefox also detected, add `--pdf`/`--pptx` (warn: PPTX is image-based, not editable).
3. Editable PPTX needed: prefer `pandoc --reference-doc` if installed; else Python ≥3.8 + `pip install python-pptx` → agent-written script with simple layouts (title/bullets/images).
4. `soffice` present: converter of last resort — PPTX→PDF only; never HTML→PPTX (poor fidelity); Marp `--pptx-editable` only with an explicit fidelity warning.
5. Never Slidev: heaviest deps (scaffold + playwright-chromium), hard-fails without them, image-based PPTX anyway.

[Sources: github.com/marp-team/marp-cli; python-pptx.readthedocs.io; sli.dev/guide/exporting; deckary.com/blog/markdown-to-powerpoint; github.com/scivision/office-headless]
