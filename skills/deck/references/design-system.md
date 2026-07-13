# Deck design system — tokens (every value cites a DR rule)

The single visual vocabulary for /vibe:deck — "Ink & Signal": a near-monochrome
navy base with ONE accent. Rules and thresholds come from
`.vibe/research/2026-07-13-deck-taste-anti-slop.md` (DR-1..11); the code tokens
live in `scripts/deck_lib.py` (`TOKENS`, `TYPE`, `SEM`, `GANTT_PHASES`) and the
hard gates in `scripts/validate_deck.py` (DK-*). Change a number in the research
report first, then here and in both scripts in lockstep.

## Palette (DR-5) — one accent, everything else neutral

| token | hex | role |
|---|---|---|
| `ink` | `#16283F` | deep navy — dark backgrounds (cover/section/closing) and all body text |
| `paper` | `#FFFFFF` | light slide background, text on ink/accent |
| `panel` | `#EEF2F7` | card / grouping-band fill |
| `grey` | `#5C6675` | captions, sources, secondary text on light |
| `mist` | `#93A1B2` | secondary text on the navy background |
| `hairline` | `#DCE3EC` | dividers, table rules, card borders |
| `accent` | `#1F5FA8` | the ONE accent — kickers, rules, connectors, emphasis, "new" state. Never body text |
| `accentTint` | `#D7E3F1` | light-accent fill for "after"/"new"/in-scope cards |

Neutrals carry structure; the accent carries emphasis only. **Chrome is
single-accent** — DK-7 hard-fails >4 non-neutral hues *outside* diagrams. A
rebrand needs only three hexes: `deck_lib.derive(ink, paper, accent)`
reconstructs the neutral ramp by RGB-lerp. All text is ink/grey on white/panel
or paper/mist on navy, which clears WCAG AA (DR-6) by construction.

## Semantic diagram palette (DR-8) — allowed only inside diagrams

Typed nodes carry meaning by colour (colour-blind-safe draw.io swatches). These
hues are allowed (DK-5) and are **exempt from the ≤4-hue chrome limit (DK-7)** —
a real diagram is not rainbow slop. Used by `flow()`, `two_loops()`,
`gate_loop()`, `hub()`, `progression()` via node `type`:

| type | fill / line | shape | meaning |
|---|---|---|---|
| `action` | `#DAE8FC` / `#6C8EBF` | rounded rect | a work step |
| `decision` | `#FFF2CC` / `#D6B656` | diamond | a check / gate |
| `success` | `#D5E8D4` / `#82B366` | rounded rect | an exit / done |
| `error` | `#F8CECC` / `#B85450` | rounded rect | a failure / blocked path |
| `data` | `#E1D5E7` / `#9673A6` | rounded rect | a store |
| `external` | `#F5F5F5` / `#666666` | rounded rect | an actor / outside system |

Roadmap `gantt()` uses a 3-step month ramp `GANTT_PHASES` = `#3E7CBF` (near) →
`#1F5FA8` → `#123A66` (far); also DK-7-exempt.

## Type scale (DR-4) — one hero per slide, hard floors

| token | pt | use |
|---|---|---|
| `fig` | 80 | one hero number — at most once per slide |
| `h1` | 42 | cover / statement / closing headline |
| `h2` | 28 | slide + section headline (assertion titles) |
| `h2w` | 25 | headline on a dark panel |
| `num` | 23 | card numbers |
| `chev` | 22 | `>` gutter chevrons |
| `sub` | 18 | subtitle |
| `card` | 16 | card titles |
| `body` | 15 | body text / diagram node labels |
| `eye` | 14 | eyebrow / kicker (UPPERCASE, tracked) |
| `cap` | 14 | captions, sources, node notes — **absolute floor (DK-2)** |

One neutral geometric sans throughout: **Noto Sans** (stack falls back to
Liberation Sans; deliberately NOT Inter — an "AI tell"). No font mixing.

## Layout (DR-7)

- Left margin `0.9"`; content column = slide width − both margins. On-slide
  bounds are the hard floor (DK-3).
- Body text left-aligned; only titles, statements, and closing lines center.
- 30%+ breathing room — leave a lower third empty rather than fill it.
- No prose-shape overlap (DK-4); diagram labels are placed by the layout and
  checked by the render review, so they are exempt from the overlap gate.

## Titles & words (DR-1, DR-2, DR-3)

- One idea per slide. Body-slide title = a complete sentence stating that idea,
  active voice, ≤15 words / ≤2 lines (DK-6). Section/cover slides may use short
  topic labels + an accent kicker.
- ≤30 words of **prose** per slide is the target; >50 hard-fails (DK-1). The
  budget counts prose only — diagram node labels and table cells are exempt, so
  a status matrix or a labelled diagram is never mistaken for a text wall.

## Diagrams (DR-8)

Native PowerPoint shapes only. Typed semantic nodes (above), thin orthogonal
connectors, shadowless (`_flatten()` strips every theme effectRef). Prefer a
diagram or a number over a text slide. No clip-art, no icon spam.

## Anti-slop (DR-9, DR-11) — what never ships

No bullet walls, decorative icons/emoji, gradients, drop shadows, uniform filler
card grids, or centered body text. **No em/en-dashes** — the #1 AI tell (DK-8);
ranges use a plain hyphen. These are the render-review failure signals; the
model rejects any slide showing them (DR-10).
