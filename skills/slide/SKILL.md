---
name: slide
description: Build a board-ready .pptx deck from a topic or the current .vibe work, per the SL slide standards. Invoked by the /vibe:slide command.
user-invocable: false
argument-hint: "[topic — omit to present the current .vibe work]"
---

# /vibe:slide — executive deck (.pptx)

Arguments: $ARGUMENTS

Produce ONE `.pptx` at `.vibe/exports/<YYYY-MM-DD>-<slug>.pptx` for a
NON-TECHNICAL leadership audience: they want the concept, the logic, and
the ask — never the implementation. Read `references/slide-design.md`
(the SL rules) BEFORE outlining; every structural choice should be
citable (e.g. "exec summary first — SL-3").

## Steps

1. **Subject & language.** Use $ARGUMENTS as the topic; if empty, present
   the current work (read `.vibe/plan.md`, `.vibe/ROADMAP.md`,
   `.vibe/STATE.md`). Write slide text in the language the user made the
   request in; if the audience's language is genuinely unclear, ask one
   question, no more.
2. **Story before slides (SL-1, SL-2).** Decide the single
   recommendation — that sentence is the deck title — then frame it as
   SCQA. Draft ALL slide titles first and read them alone: they must
   tell the complete story by themselves (SL-4), in ≤12 slides (SL-6).
3. **Outline.** Executive summary slide with 3–5 bold claims mapping 1:1
   in order to the later slide titles (SL-3). Every title a
   full-sentence action title, ≤15 words (SL-7); one message per slide
   (SL-9); ≤4 bullets each, no narration on slides (SL-11); everything
   framed as cost, risk, time, or revenue — one clean analogy for any
   unavoidable technical concept (SL-15); close with the explicit
   ask/decision (SL-16).
4. **Build.** Write the deck-spec JSON (schema in the
   `scripts/build_pptx.py` docstring — the plugin root is two
   directories above this SKILL.md) to a temp file, then:
   `python3 <plugin-root>/scripts/build_pptx.py spec.json
   .vibe/exports/<YYYY-MM-DD>-<slug>.pptx`
   Slide types: `exec_summary`, `section`, `content`, `closing` — the
   title slide is built automatically from the spec's top-level
   `title`/`subtitle`/`meta`. Heed any SL-6 budget warning it prints.
5. **Verify, then deliver.** If `soffice` is available, convert the
   deck to PDF in a temp dir and LOOK at it: titles ≤2 lines, no
   overflowing body text, exec-summary claims match later titles — fix
   the spec and rebuild until clean. Report the .pptx path (and PDF
   preview if made), and keep the spec JSON around for quick edits.
