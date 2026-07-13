# Deck layouts — the eight `deck_lib.Deck` methods

Every layout below was built, validated (DK-*), and render-reviewed on a
real machine before it was written here. Import the library from a per-deck
build script run with the toolkit venv python:

```python
import sys; sys.path.insert(0, "<plugin>/scripts")
from deck_lib import Deck
d = Deck()
# ... add slides ...
d.save("deck.pptx")
```

Pick the layout that fits the slide's ONE idea (DR-1). Prefer a big number
or diagram over a text slide whenever the content allows (DR-3). Keep body
lines short — the validator hard-fails >50 words/slide (DK-1).

## `title(title, subtitle=None, eyebrow=None)`
Cover. Display-size title, optional accent eyebrow + muted subtitle.
```python
d.title("Faster deploys, fewer incidents",
        subtitle="Platform Engineering review — Q3 2026", eyebrow="Internal")
```

## `section(number, title)`
Section divider. Accent number tag + display title. Topic label is fine here
(DR-2 exempts section/cover slides).
```python
d.section("01", "Where we are today")
```

## `big_number(value, context, title=None, source=None)`
One hero metric (~6× body) + one context line — the single anchor of the
slide (DR-4 one hero). Use for the KPI that matters.
```python
d.big_number("40%", "of engineering time goes to manual release steps",
             title="Manual work dominates the release path",
             source="Source: internal DORA survey, Aug 2026")
```

## `title_body(title, body_lines, eyebrow=None)`
Assertion title + up to ~4 short lines. NOT a bullet wall (DR-9) — each line
is one short clause; keep the total under the word budget (DR-3).
```python
d.title_body("Three bottlenecks slow every release",
             ["Environments drift between staging and production.",
              "Rollbacks need a human in three separate consoles.",
              "Approval waits average 6 hours per change."],
             eyebrow="Problem")
```

## `cards(title, items, eyebrow=None)`
2-4 panel cards, each a bold head + one supporting line. Raises if not 2-4
(anti uniform-grid-filler, DR-9). Cards are flattened — no drop shadow.
```python
d.cards("What the new pipeline changes",
        [("Deploy", "One command, all environments"),
         ("Verify", "Automated checks gate promotion"),
         ("Roll back", "Single click, under a minute")], eyebrow="Solution")
```

## `flow(title, steps, eyebrow=None)`
Native-shape process diagram (DR-8): 3-5 rounded-rect nodes with 2-3-word
labels, joined by thin accent connectors. Raises if not 3-5 steps. This is
the diagram slide DM-7 requires — crisp, editable, shadowless.
```python
d.flow("How a change reaches production",
       ["Commit", "Build", "Verify", "Promote"], eyebrow="Pipeline")
```

## `statement(text, attribution=None)`
One large payoff line, vertically centered — the slide's emphatic anchor
(DR-2 statement style). Use sparingly, one per deck or section.
```python
d.statement("We can cut release time from days to under an hour.")
```

## `closing(text, contact=None)`
Bookend. Short closing line + optional accent contact.
```python
d.closing("Questions?", contact="platform-eng@example.com")
```

## Notes

- Every method returns the created slide, so a build script can reach in and
  nudge one thing without touching python-pptx internals.
- Text runs always carry an explicit size AND color (DK-2 requires both) —
  set through the tokens, never a raw literal in a build script.
- Need a layout that isn't here? Add it to `deck_lib.py`, prove it (build →
  `validate_deck.py` → render → look), then document it — never author raw
  python-pptx in a one-off build script (that's how slop and 5.2k lines
  crept in last time).
