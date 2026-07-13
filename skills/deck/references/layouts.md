# Deck layouts — the `deck_lib.Deck` methods

Every layout below was built, validated (DK-*), and render-reviewed on a real
machine before it was written here. Import the library from a per-deck build
script run with the toolkit venv python:

```python
import sys; sys.path.insert(0, "<plugin>/scripts")
from deck_lib import Deck
d = Deck()
# ... add slides ...
d.save("deck.pptx")
```

Pick the layout that fits the slide's ONE idea (DR-1). **Prefer a diagram, a
table, or a number over a text slide** (DR-3) — most content has a shape.
Common kwargs: `kicker=` (accent UPPERCASE eyebrow; `eyebrow=` is an alias),
`source=` (grey footnote). Keep body lines short — DK-1 hard-fails >50 prose
words (diagram/table labels are exempt).

## Cover, dividers, payoff

- **`title(headline, kicker=None, subtitle=None, footer=None)`** — cover: navy
  field, accent square + kicker, big headline, accent rule, subtitle, footer,
  and a nested-loop motif top-right.
  `d.title("Kx-Agent-Space: the July milestone", kicker="Milestone", subtitle="…", footer="…")`
- **`section(number, title)`** — navy section divider (accent number + title).
- **`statement(text, source=None, kicker=None)`** — one large payoff line on
  paper; the emphatic anchor. Use sparingly.
- **`closing(text, contact=None)`** — navy bookend with a loop motif.
- **`title_body(title, body_lines, eyebrow=None, source=None)`** — assertion
  title + up to ~4 short lines. NOT a bullet wall (DR-9); keep under the budget.

## Numbers

- **`big_number(value, context, title=None, source=None)`** — one hero metric
  (~6× body) on paper + a context line. `d.big_number("92%", "of revenue is repeat", title="…")`
- **`metric(value, label, src, heading=None, kicker=None)`** — hero number on
  navy; `src` is required (a figure with no source is a fabricated stat).

## Cards & columns

- **`cards(heading, items, kicker=None, last_accent=True, source=None)`** — 2-4
  numbered panel cards; the **last card is filled accent** (breaks the
  three-equal-cards tell). `items=[(title, desc), …]`.
- **`two_column(heading, left, right, kicker=None, source=None)`** — compare
  two cards (right is accent). `left={"title": .., "points": [..]}`.
- **`three_point(heading, points, kicker=None, source=None)`** — three columns,
  each an accent rule + title + line (no card fill). `points=[(title, desc), …]`.

## Diagrams (semantic native shapes)

Node `type` sets colour + shape: `action` `decision` `success` `error` `data`
`external` (see design-system.md). A bare string is treated as an `action` node.

- **`flow(heading, nodes, kicker=None, backedge=None, source=None, legend=None)`**
  — left-to-right process. `nodes=[("external","User"),("action","Plan"),…]`.
  `backedge={"label":"…", "crossed":True}` draws a greyed ⊘ "no loop"; without
  `crossed` it is a real re-run loop; `from_idx`/`to_idx` aim it.
  `legend=[("external","actor"),("action","step")]`.
- **`hub(heading, core, spokes, kicker=None, caption=None, source=None)`** — one
  core node → N spokes. `spokes=[("action","Orchestrator","plan · build"), …]`.
- **`two_loops(heading, team, inner, kicker=None, source=None)`** — the nested
  loop: an outer Team loop containing an inner Agent loop, each with a decision
  gate and a dashed re-run arrow.
  `team={"outer":"Team loop","steps":[("action","Plan"),…],"gate":"DoD met?","done":"Done","rerun":"no · re-run (max 3)","from_idx":2,"each":"each member runs one"}`,
  `inner={"label":"Agent loop","steps":["Use tools"],"gate":"done?","done":"Return","rerun":"no · iterate"}`.
- **`gate_loop(heading, work, gate, done, backlabel, properties, kicker=None, source=None)`**
  — a mini loop (work → gate → done, no → back) + property callouts.
  `properties=[(title, desc), …]`.
- **`progression(headline, steps, kicker=None, source=None)`** — connected nodes
  coloured by build status. `steps=[{"label":..,"note":..,"status":"Built"|"New"}]`.

## Tables & roadmap

- **`matrix(heading, columns, rows, emphasize=(), kicker=None, source=None, col_weights=None)`**
  — status table from native rects; `emphasize` = set of row indexes drawn with
  an accent edge. `rows=[["Agent Loop","Built","Hardened"], …]`.
- **`gantt(headline, months, bars, kicker=None, subtitle=None, source=None)`** —
  roadmap Gantt: month columns shaded near→far, bars spanning their months.
  `bars=[{"label":"Agent Loop","start":0.0,"end":0.95,"phase":0}, …]` (start/end
  in month units 0..len(months); `phase` indexes the shade ramp).
- **`timeline(headline, lanes, kicker=None, source=None)`** — roadmap swimlanes:
  month header pills + stacked item chips; `lanes=[{"month":"JULY","tone":"milestone"|"muted","items":[..]}]`.

## Before/after & scope

- **`transform(headline, before, after, kicker=None, source=None)`** — two
  panels with a big accent arrow. Each panel `{"tag":.., "glyph":MSO_SHAPE.*, "gcolor":TOKENS[..], "caption":..}`
  (e.g. `NO_SYMBOL` for "stop", `CIRCULAR_ARROW` for "loop").
- **`sequence(headline, left, right, kicker=None, source=None)`** — two ordered
  horizons with a connecting arrow. `left={"title":.., "items":[..]}`.
- **`scope_boundary(headline, in_label, in_items, out_items, kicker=None, source=None)`**
  — an in-scope box vs deferred items each marked ⊘.
  `out_items=[("The five upgrades","August"), …]`.

## Notes

- Every method returns the created slide, so a build script can nudge one thing
  without touching python-pptx internals.
- Text runs always carry an explicit size AND colour (DK-2) — set through the
  tokens, never a raw literal in a build script. No em/en-dashes (DK-8).
- Need a layout that isn't here? Add it to `deck_lib.py`, prove it (build →
  `validate_deck.py` → render → look), add a case to
  `tests/test_deck_validate.py`, then document it — never author raw python-pptx
  in a one-off (that is how slop and 5.2k lines crept in last time).
