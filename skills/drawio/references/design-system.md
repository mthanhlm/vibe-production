# Diagram design system — DL rules (each cites a DR or DG source)

The visual vocabulary for /vibe:drawio. It reuses the deck's palette so the
two suite skills read as one system. Sources: the deck research
`.vibe/research/2026-07-13-deck-taste-anti-slop.md` (DR-8 connector
discipline, DR-5 palette, DR-1 one-idea) and the drawio research
`.vibe/research/2026-07-10-drawio-track-plan.md` (DG-17..21). Code tokens
live in `scripts/drawio_lib.py` (`TOKENS`); the hard gates in
`scripts/validate_drawio.py` (DL-*).

## Palette (DL-3 ← DR-5 / DG-17) — one accent, everything else neutral

| token | hex | role |
|---|---|---|
| `ink` | `#1A1A2E` | node label text |
| `muted` | `#6B7280` | edge labels, boundary strokes, secondary |
| `accent` | `#2B59C3` | the ONE accent — node stroke, primary-path edges |
| `panel` | `#F2F4F8` | node fill |
| `border` | `#E5E7EB` | non-accent node stroke |
| `white` | `#FFFFFF` | canvas / label backgrounds |

Every `fillColor`/`strokeColor`/`fontColor` must be a token (DL-3 hard-fails
off-palette hexes). The accent is reserved for the primary path — one accent
hue, never rainbow, never decoration.

## The DL rules (what the validator enforces)

- **DL-1 (← DR-1)** ≤12 nodes/diagram; a denser topology is two linked
  diagrams, each with one idea.
- **DL-2 (← DR-8)** node labels ≤3 words — label economy; the shape carries
  the meaning, not a sentence.
- **DL-3 (← DR-5/DG-17)** token palette only; one accent hue.
- **DL-4 (← DR-8/DG-21)** `shadow=0` everywhere — no drop shadows, no
  `shadowBlur` (the reference-deck / diagram signature).
- **DL-5 (← DG-19)** every edge is `edgeStyle=orthogonalEdgeStyle` with
  `jumpStyle=gap` — clean right-angle routing with line jumps at crossings.
- **DL-6 (← DG-18)** 8px grid — every vertex `x/y/w/h` is a multiple of
  `gridSize=8`. `drawio_layout.py` snaps `dot` output; the hand grid uses
  multiples of 8 directly.
- **DL-7 (← DR-7)** on-canvas bounds; nodes never overlap each other (a node
  inside a zone is expected and allowed).

## Deliberately NOT enforced (DR-8 refuted-overreach)

Edges may cross objects, and bends need not be strictly right-angled — the
old "connectors must never cross / only right angles" rule was adversarially
refuted. Connector quality is a **render-review** judgement (does it read?),
never a hard rejection. Minimizing crossings and bends is a goal, not a gate.

## Zones (DG-19)

A labelled boundary (logical grouping, security perimeter) is a `zone()` —
`fillColor=none`, dashed stroke in `muted`, label top-left. Zones frame
nodes; they don't count toward node overlap.

## Anti-slop (← DR-9)

No clip-art or icon spam (shapes + labels only), no gradients on nodes, no
shadows, no rainbow palettes, no more than one accent. These are the
render-review failure signals — the model rejects any diagram showing them.
