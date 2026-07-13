# Diagram design system — DL rules (each cites a DR or DG source)

The visual vocabulary for /vibe:drawio. Chrome reuses the deck's "Ink &
Signal" palette so the two suite skills read as one system; diagram nodes are
**typed** by a semantic colour/shape swatch set (the lever that makes a
diagram readable at a glance). Sources: the deck research
`.vibe/research/2026-07-13-deck-taste-anti-slop.md` (DR-8 connectors, DR-5
palette, DR-1 one-idea) and the drawio research
`.vibe/research/2026-07-10-drawio-track-plan.md` (DG-17..21) + the semantic
skeleton in `2026-07-10-slide-drawio-rules.md`. Code tokens live in
`scripts/drawio_lib.py` (`TOKENS`, `SEM`); hard gates in
`scripts/validate_drawio.py` (DL-*). Change a number in research first, then
here and in both scripts in lockstep.

## Chrome palette (DL-3 ← DR-5) — Ink & Signal

| token | hex | role |
|---|---|---|
| `ink` | `#16283F` | node label text, start/end fill |
| `muted` | `#5C6675` | edge labels, note sublabels, boundary strokes |
| `accent` | `#1F5FA8` | the ONE accent — primary-path + loop edges |
| `panel` | `#EEF2F7` | neutral panel fill |
| `border` | `#DCE3EC` | hairline |
| `white` | `#FFFFFF` | canvas / label backgrounds |

## Semantic node palette (DL-3 ← DR-8) — type sets colour + shape

Pass `kind=` to `node()`. Each type is colour-blind-safe and carries meaning:

| kind | shape | fill / stroke | meaning |
|---|---|---|---|
| `action` | rounded rect | `#DAE8FC` / `#6C8EBF` | a work step |
| `decision` | rhombus | `#FFF2CC` / `#D6B656` | a check / gate (guard the out-edges) |
| `success` | rounded rect | `#D5E8D4` / `#82B366` | an exit / done |
| `error` | rounded rect | `#F8CECC` / `#B85450` | a failure / blocked path |
| `data` | cylinder | `#E1D5E7` / `#9673A6` | a store |
| `external` | rounded rect | `#F5F5F5` / `#666666` | an actor / outside system |
| `start` / `end` | ellipse | `#16283F` (start filled, end ring) | activity terminals |

A node may carry a `note=` — a grey bracketed second line (e.g. `[FastAPI]`)
for the concrete tech behind the concept. Every `fillColor`/`strokeColor`/
`fontColor` must be a chrome or semantic hex (DL-3 hard-fails off-palette).

## The DL rules (what the validator enforces)

- **DL-1 (← DR-1)** ≤12 content nodes/diagram; a denser topology is two
  linked diagrams. Legend swatches (id `legend-*`) don't count.
- **DL-2 (← DR-8)** node labels ≤3 words — the shape carries the meaning. The
  `note=` sublabel is exempt (measured on the main label only).
- **DL-3 (← DR-5/DR-8)** chrome + semantic palette only; off-palette hex fails.
- **DL-4 (← DR-8)** `shadow=0` everywhere — no drop shadows, no `shadowBlur`.
- **DL-5 (← DG-19)** every edge is `orthogonalEdgeStyle` with `jumpStyle=gap`.
  A **loop back-edge** (`edge(loop=True)`) is dashed accent and routed through
  a return lane below the row via explicit waypoints (so diagrams.net does not
  draw it straight through the intervening nodes); its guard is the `label`.
- **DL-6 (← DG-18)** 8px grid — every vertex `x/y/w/h` a multiple of 8.
- **DL-7 (← DR-7)** on-canvas bounds; content nodes never overlap (a node
  inside a zone, and legend cells, are exempt).
- **DL-8 (← DR-8 label economy)** label fit — a label that would wrap to more
  lines than its box is tall (≈6.5px/char at 12pt, per-shape usable width)
  fails; widen or shorten the box. draw.io wraps text but cannot grow a fixed
  box, so a too-long label spills out.

## Legend (DR-8) — auto key

`legend([(kind, label), …], x, y)` emits a swatch + label per type used, so a
multi-colour diagram is self-explaining. Legend cells are chrome (exempt from
DL-1/DL-7).

## Deliberately NOT enforced (DR-8 refuted-overreach)

Edges may cross objects, and bends need not be strictly right-angled — that
"never cross / only right angles" rule was adversarially refuted. Connector
quality is a **render-review** judgement, never a hard rejection.

## Zones (DG-19) & anti-slop (← DR-9)

A labelled boundary (logical grouping, security perimeter) is a `zone()` —
`fillColor=none`, dashed `muted` stroke, label top-left; zones don't count
toward node overlap. No clip-art/icon spam (typed shapes + labels only), no
gradients, no shadows, no rainbow beyond the semantic set, one accent for the
primary path. These are the render-review failure signals.
