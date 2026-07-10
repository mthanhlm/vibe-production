# Layout catalog — spec v2 (operational reference)

The 12 archetype layouts `build_pptx.py` implements, the beat→layout map,
and one JSON example per exhibit. Principles live in `slide-design.md`
(SL rules); this file is the how-to. Word budgets are `board_preread` /
`keynote` body-word caps enforced at build time (SL-19).

## Spec v2 top level

```json
{ "version": 2,
  "title": "Deck title = the single recommendation (≤15 words, no 'and')",
  "subtitle": "Why this matters now", "meta": "2026-07-10 · Prepared for …",
  "mode": "board_preread",        // or "keynote" (live; tighter budgets)
  "theme": "light",               // or "dark" (default when keynote)
  "slides": [ { "beat": "…", "layout": "…", … } ] }
```

The title slide is synthesized from the top level — never listed in
`slides`. Every slide needs a `beat`; `layout` defaults to the beat's
primary.

## BEAT_LAYOUT (beat → allowed layouts, primary first)

| beat | layouts |
|---|---|
| hook | big_number, hero_statement |
| problem | chart_takeaway, before_after, big_number |
| insight | big_number, matrix_2x2, chart_takeaway |
| solution | three_cards, before_after |
| how_it_works | process_flow, before_after, content |
| proof | chart_takeaway, quote_evidence, kpi_strip |
| risks | chart_takeaway, content, kpi_strip |
| roadmap | timeline_roadmap |
| ask | exec_summary_3col, big_number, hero_statement |
| status | kpi_strip, chart_takeaway |
| transition | section_divider |
| context | content, before_after |
| agenda | content |

## The 12 archetypes

Budgets shown as board/keynote body words. Common fields: `kicker`
(small gold label), `title` (action sentence, ≤15 words, no "and"),
`source` (mandatory on quantitative exhibits, SL-20).

1. **hero_statement** (24/12) — hook or closing ask at billboard scale.
   `{"beat":"ask","layout":"hero_statement","statement":"Approve the rollout today","support":"The pilot already proved it works"}`
   Statement ≤9 words.
2. **section_divider** (7/7) — chapter transition; `kicker` holds the
   section number tag.
   `{"beat":"transition","kicker":"01","title":"Why chat was expensive"}`
3. **exec_summary_3col** (90/60) — answer-first summary; exactly 3
   columns, ≤5 lines each.
   `{"beat":"ask","layout":"exec_summary_3col","title":"…","columns":[{"head":"Situation","lines":["…"]},{"head":"Findings","lines":["…"]},{"head":"Recommendation","lines":["…"]}]}`
4. **big_number** (20/15) — one metric IS the story.
   `{"beat":"hook","layout":"big_number","value":"34,000","context":"signups per day since launch","source":"Source: analytics (2026)"}`
5. **kpi_strip** (40/30) — status check-in; 2–6 tiles, delta chips get
   semantic color from `direction` (+ optional `sentiment:
   good|bad|neutral` when up ≠ good, e.g. churn down).
   `{"beat":"status","layout":"kpi_strip","title":"…","tiles":[{"label":"Revenue","value":"4.2M","delta":"+8%","direction":"up"}],"source":"…"}`
6. **chart_takeaway** (45/30) — THE proof workhorse: one exhibit left,
   "So what" callout right (`callout_head` + `callout_lines`, ≤5).
   Exhibit kinds below.
7. **three_cards** (36/24) — solution pillars; exactly 3, strictly
   parallel; icon names from `assets/icons.json`.
   `{"beat":"solution","layout":"three_cards","title":"…","cards":[{"icon":"bot","head":"Deflect","line":"Answer the top 20 questions automatically"},…]}`
8. **before_after** (48/30) — transformation contrast; ≤4 mirrored lines
   per side; left renders de-emphasized, right accent-tinted.
   `{"beat":"problem","layout":"before_after","title":"…","left":{"head":"Before","lines":["…"]},"right":{"head":"After","lines":["…"]}}`
9. **process_flow** (40/28) — how-it-works; 2–5 steps, `highlight` names
   the step that matters (rendered accent with white text).
   `{"beat":"how_it_works","layout":"process_flow","title":"…","highlight":"Resolve","steps":[{"label":"Intake","detail":"One form, one queue"},…]}`
10. **timeline_roadmap** (50/35) — phases above a spine, diamond
    milestones on it (`final: true` = accent, larger), optional `today`.
    All times are numbers on one scale (weeks, months — your choice).
    `{"beat":"roadmap","layout":"timeline_roadmap","title":"…","timeline":{"phases":[{"label":"Pilot","start":0,"end":3}],"milestones":[{"label":"All regions","at":9,"final":true}],"today":2}}`
11. **quote_evidence** (40/30) — qualitative proof; quote ≤150 chars,
    numbers inside quotes persuade most.
    `{"beat":"proof","layout":"quote_evidence","quote":"Resolution time dropped 41% in the first month.","attribution":"— Head of Support"}`
12. **matrix_2x2** (30/20) — trade-off field; 1–6 items with x/y in
    0..1 (0,0 = bottom-left), `accent: true` marks the winner; optional
    `quadrants` labels q1(top-left) q2(top-right) q3(bottom-left)
    q4(bottom-right).
    `{"beat":"insight","layout":"matrix_2x2","title":"…","matrix":{"x_label":"Effort: low to high","y_label":"Impact: low to high","quadrants":{"q1":"Quick wins"},"items":[{"label":"Automation","x":0.25,"y":0.8,"accent":true}]}}`

Plus **content** (60/30) — the legacy bullets layout, legitimate ONLY for
agendas and next-steps lists (≤5 bullets, SL-17).

## chart_takeaway exhibit kinds

All quantitative kinds require a `source` on the slide (SL-20). One
accent datum per chart — `highlight` names it, everything else renders
grey (SL-21).

- `bars` — comparison/ranking, horizontal, sorted desc:
  `{"type":"bars","unit":"%","highlight":"North","items":[{"label":"North","value":46},…]}` (2–8 items)
- `column` — change over time, order preserved:
  `{"type":"column","highlight":"Jun","items":[{"label":"Mar","value":240},…]}` (2–8)
- `waterfall` — bridge between two totals; every bar labelled:
  `{"type":"waterfall","unit":"M","start":{"label":"2025","value":4.2},"deltas":[{"label":"New logos","value":1.1},{"label":"Churn","value":-0.5}],"end_label":"2026"}` (1–7 deltas)
- `line` — trends, ≤4 series, direct end labels, no legend:
  `{"type":"line","unit":"","highlight":"Actual","series":[{"name":"Actual","points":[["Q1",120],["Q2",180]]},{"name":"Plan","points":[["Q1",100],["Q2",160]]}]}`
- `ring` — single progress percentage:
  `{"type":"ring","pct":72,"label":"of migration complete"}`
- `harvey` — scorecard rows, quarter-quantized balls:
  `{"type":"harvey","items":[{"label":"Security review","pct":100},{"label":"Load testing","pct":50}]}` (1–6)
- `image` — user-supplied PNG/JPEG, aspect-fit; hard error if missing:
  `{"type":"image","path":"shots/console.png","alt":"console"}`
- `photo` — optional photography; missing/broken path degrades to the
  branded gradient field with the `alt`/`query` as caption (SL-23):
  `{"type":"photo","path":"…from fetch_photo.py…","attribution":"…","alt":"team at work"}`

## Modes & themes

`board_preread` (default): fuller budgets, light theme — a deck that
stands alone as a pre-read (SL-16). `keynote`: for live presentation —
roughly 60% budgets, dark theme by default (near-black canvas, white
type, gold accent). Theme can be overridden independently with `theme`.

## CLI contract

`build_pptx.py SPEC.json OUT.pptx [--force]` → exit 0 ok · 1 spec/budget
error (all findings listed with SL IDs) · 3 built-but-invalid (validator
findings, file kept). `--showcase [OUT]` builds the all-layouts fixture.
`validate_pptx.py DECK.pptx` → 0/1/2. `fetch_photo.py QUERY DIR` → 0 +
JSON manifest, or 4 = fall back silently.
