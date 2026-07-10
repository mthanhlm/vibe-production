---
problem: Hand-built OOXML that opens fine in LibreOffice still triggers
  PowerPoint's repair prompt (or silently fails in PowerPoint for the web,
  which has NO repair path) — LO accepts every documented repair-trigger,
  so a render smoke test proves nothing about package validity.
solution: Gate every built deck on a stdlib package validator
  (scripts/validate_pptx.py) that checks the rules PowerPoint actually
  enforces; keep soffice only as a visual smoke test.
rules: [WA-2, SL-19, SL-20]
---

What the validator must assert (each one a real repair trigger found in
the 2026-07-10 research pass): every relationship Target exists and every
`r:embed`/`r:id` resolves in ITS part's rels; every part has a content
type and no Override points at a missing part; `prstGeom prst` is in the
ECMA ST_ShapeType list ("oval" is not a preset); child order p:sp =
nvSpPr→spPr→style→txBody and spPr = xfrm→geom→fill→ln→effectLst; custGeom
paths carry explicit w/h with in-bounds points; EMUs fit signed 32-bit;
docProps/core.xml AND app.xml exist; media bytes match their extension.
Emit only probe-proven XML verbatim as templates, keep zips deterministic
(fixed ZipInfo dates) so golden tests hold, and remember ET serializes
self-closing tags as `" />"` — assert attribute substrings, never tag
syntax. Icons: vendor SVG as M/L/C/Z-only path data (arcs→cubics at
vendor time); cubic control points may overshoot the icon grid, so fold a
margin into the path space instead of clamping.
