---
problem: A programmatic PowerPoint (or any visual-artifact) generator can
  pass every structural check and still look like AI slop — drop shadows,
  overflowing diagrams, off-system spacing that no .pptx-reading validator
  flags. The old deck unit shipped on structural validity alone and produced
  slop across 5.2k lines of raw XML authoring.
solution: Two-tier verification, both required before delivery — a code
  validator with cited rule IDs (structural) AND a render-to-image pass the
  model actually looks at (visual). Compose from a tested shipped library,
  never raw one-off authoring.
rules: [WA-16, WA-13, WA-14]
---

Proven building /vibe:deck (2026-07-13):

- The render review is not optional polish — it caught two real bugs the
  validator could not: `flow()` overflowed at its documented 5-step max
  (fixed: derive box width from step count), and native-shape connectors
  kept a theme drop-shadow (fixed: drop the shape's `<p:style>` effectRef;
  `shadow.inherit = False` and an empty `<a:effectLst/>` both fail under
  LibreOffice — only removing the style ref works).
- Ground the design rules, don't invent them: a verified deep-research pass
  (assertion-evidence, WCAG, consulting practice) + first-hand reads of real
  reference decks → a numbered DR-1..10 report every skill file cites. Two
  refuted overreaches (image-on-every-slide, right-angle-only connectors)
  were kept OUT of the hard validator — adversarial verification earns its
  keep on the "what NOT to enforce" side too.
- Render pipeline with zero new heavy installs: python-pptx (venv) builds,
  LibreOffice `--convert-to pdf` + `pdftoppm` renders, the model Reads the
  PNG. Toolkit is consent-gated per WA-14 (config key gates the feature,
  on-disk venv is the machine-local consent).
- A fresh-agent dogfood given only the skill files is the real test of
  WA-13: it exercised the recipe end-to-end AND surfaced the two bugs above.
