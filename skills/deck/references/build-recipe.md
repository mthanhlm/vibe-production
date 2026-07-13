# Build recipe — brief → validated, render-reviewed deck

The end-to-end procedure. Every command here ran successfully on a real
machine before it was written down. Work in the target project; the deck and
its evidence land under `.vibe/` (gate-exempt).

## 1. Consent (WA-12 / WA-14)

Read `deck` from the target project's `.vibe/config.json`. The key gates the
feature; the toolkit's presence on disk
(`~/.claude/vibe-pptx/bin/python` importing `pptx`) is the machine-local
consent — a committed key never licenses an install on a colleague's box.

| config key | toolkit on disk | do |
|---|---|---|
| `"deck": "python-pptx"` | yes | proceed silently |
| `"deck": "python-pptx"` | no | ask one line: "This project enables deck building; install the toolkit to ~/.claude/vibe-pptx now? One pip package (python-pptx), no system changes." Decline → stop, offer the brief as an outline only |
| absent | — | ask once. Yes → record `"deck": "python-pptx"` + install. No → record `"deck": "none"` |
| `"deck": "none"` | — | already declined — don't re-ask |

Install: `vibe-pptx-setup` (bundled; idempotent; prints one
`PPTX: ready|no-python3|venv-failed|install-failed` line). Anything but
`ready` → report the status and stop.

## 2. Outline (DR-1, DR-2)

Turn the brief into a slide list BEFORE writing code. One idea per slide;
write each slide's assertion title first (the storyline test — the titles
read alone must convey the argument). Pick a layout per slide from
`layouts.md`. Prefer a big number or diagram over a text slide (DR-3). A
typical deck is 6-12 slides.

## 3. Build script (run in a per-deck dir under the toolkit)

Never author raw python-pptx — compose `deck_lib` layout calls only.

```bash
PPTX="$HOME/.claude/vibe-pptx"
mkdir -p "$PPTX/runs"
RUN=$(mktemp -d "$PPTX/runs/XXXXXX")
OUT="<project>/.vibe/exports/$(date +%F)-<slug>"; mkdir -p "$OUT/preview"
```

Write `$RUN/build.py`: `sys.path.insert(0, "<plugin>/scripts")`, `from
deck_lib import Deck`, add slides from the outline, `d.save("$OUT/deck.pptx")`.
Run it with the toolkit python:

```bash
"$PPTX/bin/python" "$RUN/build.py"
```

## 4. Validate (DR-1..9, hard gate)

```bash
"$PPTX/bin/python" <plugin>/scripts/validate_deck.py "$OUT/deck.pptx"
```

Exit 0 = `DECK PASS`. Any `slide N: DK-x …` line → fix the build script and
rebuild. Do not proceed to review with validator failures outstanding.

## 5. Render + review (DR-10 — the required stage, never skip)

```bash
timeout 120 soffice --headless --convert-to pdf --outdir "$OUT" "$OUT/deck.pptx"
timeout 60 pdftoppm -png -r 110 "$OUT/deck.pdf" "$OUT/preview/slide"
```

PNG count MUST equal slide count. Then **look at every PNG** and judge each
against the 15-second glance test (DR-10) and the slop tells (DR-9): assertion
title reads as a conclusion? one idea? breathing room? no bullet wall / icon
spam / gradient / drop shadow / centered body? diagram connectors clean
(DR-8)? Quote a one-line verdict per slide in the report. Any fail → fix the
build script, rebuild, re-validate, re-render, re-review until a full pass
finds nothing new. A slide that only *validates* is not done until it also
*looks* right.

## 6. Deliver + teardown

Keep `$OUT/deck.pptx` and `$OUT/preview/*.png` (the evidence). Delete the run
dir: `rm -rf "$RUN"`. The target repo shows changes only under `.vibe/`
(`git status --porcelain`). Report the deck path, the per-slide review
verdicts, and the validator PASS line. Offer, once, an `exports/` line in
`.vibe/.gitignore` if the PNGs shouldn't be committed.
