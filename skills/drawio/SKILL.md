---
name: drawio
description: Author an executive-readable .drawio diagram from a topic or the current .vibe work, per the DG rules, linted before delivery. Invoked by the /vibe:drawio command.
user-invocable: false
argument-hint: "[topic — omit to diagram the current .vibe work]"
---

# /vibe:drawio — executive diagram (.drawio)

Arguments: $ARGUMENTS

Produce ONE `.drawio` file at `.vibe/exports/<YYYY-MM-DD>-<slug>.drawio`
for a NON-TECHNICAL audience: one idea, few boxes, plain language. Read
`references/drawio-diagrams.md` (DG rules + XML authoring essentials)
BEFORE authoring any XML.

## Steps

1. **Subject & language.** Use $ARGUMENTS as the topic; if empty,
   diagram the current work (read `.vibe/plan.md`, `.vibe/ROADMAP.md`,
   `.vibe/STATE.md`). Labels in the language the user made the request in.
2. **Pick ONE diagram kind (DG-3)**, by what the audience must grasp:
   - **concept map** — an idea and how its parts relate
   - **swimlane process** — who does what, in what order (DG-5)
   - **system context (C4 L1)** — the system, its users, its
     neighbors; never internals (DG-1, DG-2)
   - **timeline/roadmap** — phases and milestones; use a before/after
     pair for change proposals (DG-6)
3. **Design before XML.** One-sentence takeaway as the diagram title
   (DG-8); ≤9 boxes, cluster the rest (DG-4); plain business labels
   (DG-9); semantic colors only — red=risk, green=on-track — and never
   color alone (DG-12, DG-13); grid layout with 40–60px gutters and zero
   overlaps (DG-14); orthogonal edges, no hand-placed waypoints (DG-15).
   Pick a theme: light (default) or dark (hero one-pagers only). Build
   every style from the reference's verbatim tokens (DG-17) and lay out
   on the 8px grid — `gridSize="8"`, every vertex x/y/width/height a
   multiple of 8 (DG-18).
3b. **Layout oracle (optional).** For >6 nodes or non-linear topology,
   write a small `.dot` file (`node [shape=box, fixedsize=true,
   width=1.9444, height=0.8333]` — token box sizes) and run
   `python3 <plugin-root>/scripts/drawio_layout.py <file>.dot`: it prints
   snapped mxGeometry positions as JSON. Exit 1 means dot is absent —
   fall back to the DG-14 hand grid.
4. **Author the XML** — uncompressed mxfile, following the reference's
   skeleton and its 11-pitfall checklist: structural cells 0/1, unique
   ids, vertices before edges, every edge with
   `<mxGeometry relative="1" as="geometry"/>`, no XML comments (DG-16).
5. **Lint until clean.**
   `python3 <plugin-root>/scripts/lint_drawio.py <file>` (the plugin
   root is two directories above this SKILL.md) — fix every error AND
   warning, re-lint to exit 0. Never deliver an unlinted file. The
   linter also enforces DG-17..21 (palette, grid, edge discipline,
   icons, effects) — a style warning means redesign, not annotation.
6. **Deliver.** Report the path and how to open it: app.diagrams.net,
   the draw.io desktop app, or the VS Code draw.io extension (export to
   PNG/PDF from there via File → Export). Name any viewer-version-
   dependent feature used (e.g. blurred-shadow keys need draw.io ≥24.0)
   and point at the reference's "Fidelity self-check" checklist.
