# Slide design standards — executive decks

Written fresh from a multi-source research pass (2026-07-10, synthesis in
`.vibe/research/2026-07-10-slide-drawio-rules.md`); sources are cited inline
per rule. Cite rules by ID (e.g. "violates SL-4").

## Deck structure

- **SL-1 (MUST)** Lead with the answer: recommendation/conclusion first, then
  supporting arguments, then data (Minto Pyramid). Open from a decision the
  executive owns (budget, risk, deadline) — mechanism comes only after they
  know why they should care. [managementconsulted.com/pyramid-principle;
  okundata.com/blog/data-storytelling]
- **SL-2 (SHOULD)** Open with SCQA framing (Situation, Complication,
  Question, Answer) to anchor agreed facts, create why-now tension, and
  position the Answer as the top of the pyramid.
  [modelthinkers.com/mental-model/minto-pyramid-scqa]
- **SL-3 (MUST)** Include an executive-summary slide up front: 3–5 bold-claim
  bullets max, each mapping 1:1 in order to subsequent slide titles
  (BCG/McKinsey/Bain standard). [deckary.com/blog/executive-summary-slides]
- **SL-4 (MUST)** Pass horizontal logic: reading only the slide titles in
  sequence must tell the complete, convincing story — the title-only read is
  the de facto executive consumption mode.
  [storytellingwithdata.com/blog/2013/12/horizontal-logic]
- **SL-5 (MUST)** Group supporting points MECE (mutually exclusive,
  collectively exhaustive), ideally ~3 per grouping, so the logic is
  auditable at a glance. [modelthinkers.com/mental-model/minto-pyramid-scqa]
- **SL-6 (SHOULD)** Keep decks short: audiences absorb ~10 concepts per
  meeting; for pitch-style decks apply 10/20/30 (~10 slides, 20 minutes, no
  font below 30pt). [guykawasaki.com/the_102030_rule]

## Per-slide rules

- **SL-7 (MUST)** Write action titles: every title is a complete sentence
  stating the slide's takeaway ("so what"), ≤15 words, ≤2 lines, active
  voice, quantitative where possible — never a topic label like "Q3 Revenue
  Overview". [slideworks.io/resources/how-to-write-action-titles-like-mckinsey]
- **SL-8 (MUST)** Pass vertical logic: everything in the slide body must
  directly prove the title's claim; delete anything that doesn't.
  [slidescience.co/strategy-presentations]
- **SL-9 (MUST)** One message per slide — two ideas means two slides — and
  the main point must survive a 3-second glance test (Duarte "glance media").
  [deckary.com/blog/consulting-slide-standards;
  duarte.com/resources/guides-tools/the-glance-test]
- **SL-10 (SHOULD)** Use assertion-evidence structure: sentence headline
  supported by visual evidence (chart, diagram, photo), not bullet lists —
  controlled studies show better comprehension and recall (p < .01).
  [writing.engr.psu.edu/research.html]
- **SL-11 (MUST)** Cut extraneous words, images, and decoration (Mayer
  coherence principle); never put the presenter's full narration as on-screen
  text (redundancy principle). [Cambridge Handbook of Multimedia Learning]

## Data-viz on slides

- **SL-12 (MUST)** Declutter every chart to maximize data-ink — no 3D,
  decorative borders, heavy gridlines, or redundant labels (Tufte) — then
  highlight exactly one takeaway with preattentive attributes (color, size,
  position), stated in the title. An unhighlighted chart makes executives do
  the analysis themselves.
  [data.europa.eu/apps/data-visualisation-guide/chart-junk-and-data-ink-origins;
  Knaflic, Storytelling with Data ch. 4]

## Visual polish

- **SL-13 (MUST)** Keep type readable and restrained: body ≥18pt (24pt for
  projection), titles 28–36pt, max two typefaces, sans-serif for screens.
  [brightcarbon.com/blog/presentation-font-size]
- **SL-14 (SHOULD)** Leave ≥15–20% of each slide as whitespace and limit the
  palette to ~3 colors (primary, secondary, accent).
  [deckary.com/blog/pillar-powerpoint-design-guide]

## Audience fit (non-technical leadership)

- **SL-15 (MUST)** Frame every technical element as cost, risk, time, or
  revenue impact, never system properties ("removes the single point of
  failure that took payments down nine hours" — not "active-active cluster").
  Explain unavoidable technical concepts with one clean analogy from the
  audience's world.
  [winningpresentations.com/technical-presentation-non-technical-executives;
  leapica.com/explain-technical-concepts-non-technical-audiences]
- **SL-16 (MUST)** For board/leadership decks, design to stand alone as a
  pre-read (sent 1–2 days ahead) and surface what directors check first:
  cash/runway, metrics vs plan, and explicit asks/decisions needed.
  [articles.sequoiacap.com/preparing-a-board-deck]

## Beat-driven layouts (spec v2 — machine-enforced)

- **SL-17 (MUST)** Tag every slide with its story beat (hook, problem,
  insight, solution, how_it_works, proof, risks, roadmap, ask, status,
  transition, context, agenda); the beat — not taste — picks the layout from
  the catalog's BEAT_LAYOUT table. Bullets (`content`) are legitimate only
  for agendas and next-steps lists.
  [layout-catalog.md; Zelazny, Say It With Charts — message picks the form]
- **SL-18 (MUST)** Must-be-visual triggers: when the takeaway contains a
  comparison/ranking → bars; share change over time → column/line; a bridge
  between two numbers → waterfall; a process → flow; a plan with dates →
  timeline; a trade-off across two dimensions → 2×2; a single standout
  statistic → big_number. A slide whose takeaway matches a trigger may not
  be a bullet list. [Zelazny message→chart mapping; McKinsey exhibit craft]
- **SL-19 (MUST)** Respect the restraint budgets — they ARE the aesthetic:
  action titles ≤15 words with no "and"; per-layout body-word caps
  (board_preread vs keynote modes); exactly one exhibit per slide; ≤6 KPI
  tiles; ≤5 flow steps; exactly 3 cards; quote ≤150 chars; ≤4 line series.
  The builder fails on violations; `--force` downgrades them to warnings
  and is a user decision, never a reflex. [Duarte glance test; SL-9]
- **SL-20 (MUST)** Every quantitative exhibit carries a "Source: <origin>
  (year)" line. An unsourced number reads as an opinion.
  [Economist style guide; analyst-deck conventions]
- **SL-21 (MUST)** One semantic accent per slide: the accent color marks
  exactly the datum the title names — every other series/bar/step renders
  grey. Green/red only for genuinely good/bad deltas (kpi tiles use
  direction + sentiment), never decoration. [Knaflic preattentive focus;
  SL-12]
- **SL-22 (SHOULD)** Alternate quantitative exhibits (charts, tiles) with
  conceptual ones (flows, cards, matrices) so the deck breathes; three
  consecutive same-kind slides is a smell. [McKinsey deck pacing]
- **SL-23 (MUST)** Photos only from license-safe sources: user-supplied
  files or fetch_photo.py (Openverse CC0/Public-Domain, attribution kept on
  the slide). A missing photo degrades to the branded gradient field —
  delivery never blocks on photography, and license metadata is treated as
  unwarranted. [Openverse ToS; verify-photos research 2026-07-10]
