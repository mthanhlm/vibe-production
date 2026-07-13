# Deck design system — tokens (every value cites a DR rule)

The single visual vocabulary for /vibe:deck. Rules and thresholds come from
`.vibe/research/2026-07-13-deck-taste-anti-slop.md` (DR-1..10); the code
tokens live in `scripts/deck_lib.py` (`TOKENS`, `TYPE`) and the hard gates
in `scripts/validate_deck.py` (DK-*). Change a number in the research report
first, then here and in both scripts in lockstep.

## Palette (DR-5) — one accent, everything else neutral

| token | hex | role |
|---|---|---|
| `ink` | `#1A1A2E` | all titles and body text |
| `muted` | `#6B7280` | captions, eyebrows, sources, secondary |
| `accent` | `#2B59C3` | the ONE accent — emphasis, hero numbers, connectors, bullets-dots. Never body text, never decoration |
| `panel` | `#F2F4F8` | card / diagram-box fill |
| `border` | `#E5E7EB` | hairline separators |
| `white` | `#FFFFFF` | slide background |

≤4 non-neutral hues per slide (DK-7); accent carries emphasis only. Semantic
mapping stays constant deck-wide. All text is ink/muted on white/panel, which
clears WCAG AA (DR-6) by construction — do not introduce low-contrast tints.

## Type scale (DR-4) — one hero per slide, hard floors

| token | pt | use |
|---|---|---|
| `hero` | 104 | one big number / cover payoff — at most once per slide |
| `display` | 54 | cover + closing title |
| `h1` | 34 | assertion titles, card heads |
| `eyebrow` | 16 | accent "so-what" kicker above a title |
| `body` | 18 | body text — **hard floor**; never smaller for prose |
| `caption` | 14 | sources, attributions — absolute min (DK-2) |

Title ≥ ~1.8× body. One neutral geometric sans throughout (`Arial` → renders
as Liberation Sans under LibreOffice). No font mixing.

## Layout (DR-7)

- Left margin `0.9"`; content column = slide width − both margins. ≥0.5"
  from every edge (DK-3 hard-fails off-slide).
- Body text left-aligned; only titles, statements, and closing lines center.
- 30%+ breathing room — deliberately leave a lower third empty rather than
  fill it. Asymmetry beats centered-everything.
- No shape overlap (DK-4).

## Titles & words (DR-1, DR-2, DR-3)

- One idea per slide. Body-slide title = a complete sentence stating that
  idea, active voice, ≤15 words / ≤2 lines (DK-6). Section/cover slides may
  use short topic labels + an accent eyebrow.
- ≤30 words of prose per slide is the target; >50 hard-fails (DK-1). Let the
  hero number or diagram carry the weight.

## Diagrams (DR-8)

Native PowerPoint shapes only — `deck_lib.flow()` draws 3-5 rounded-rect
nodes with 2-3-word labels, joined by thin straight accent connectors, and
`_flatten()`s each shape to kill the theme drop-shadow (shadowless is the
reference-deck signature). No clip-art, no icon spam.

## Anti-slop (DR-9) — what never ships

No bullet walls, decorative icons/emoji, gradients, drop shadows, uniform
filler card grids, or centered body text. These are the render-review
failure signals; the model rejects any slide showing them (DR-10).
