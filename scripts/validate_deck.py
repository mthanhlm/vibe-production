#!/usr/bin/env python3
"""validate_deck.py — machine gate for generated .pptx decks (DK rules).

Run with a python that can import pptx (the vibe-pptx toolkit venv):
    ~/.claude/vibe-pptx/bin/python scripts/validate_deck.py <deck.pptx>

Prints one line per violation ("slide N: DK-x …") and exits 1 if any;
exits 0 with a single PASS line otherwise. Validates decks built by the
deck skill — explicit-everything is the contract (inherited/None font
sizes are violations, not unknowns).

Thresholds live in RULES only, cited to the deck-taste research report
(.vibe/research/*deck-taste-anti-slop.md) — change them there, not
inline.
"""
import sys

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Emu

RULES = {
    # Thresholds cite DR numbers in the deck-taste research report
    # (.vibe/research/2026-07-13-deck-taste-anti-slop.md). Only the code-
    # checkable half of the DR set lives here; the qualitative rules
    # (assertion-vs-topic titles, "relevant graphic", 15-second glance,
    # slop tells) are enforced by the model's render review, not this gate.
    "DK-1_max_words_per_slide": 50,      # DR-3 hard ceiling (target ~30; slop above)
    "DK-2_min_font_pt": 14,              # DR-4 absolute floor (caption min; body is 18pt by token)
    "DK-3_bounds_tolerance_emu": 9525,   # DR-7 on-slide bounds, 1px @96dpi tolerance
    "DK-4_overlap_tolerance_emu2": 91440 * 91440,  # DR-7 ~1% sq-inch (0.1in x 0.1in) overlap
    "DK-5_palette": {                    # DR-5 allowed non-neutral RGBs (deck accent tokens)
        "1A1A2E", "2B59C3", "F2F4F8",
    },
    "DK-5_neutrals": {"000000", "FFFFFF", "1A1A2E", "404040", "6B7280",
                      "F2F4F8", "E5E7EB"},
    "DK-6_max_title_words": 15,          # DR-2 assertion title ceiling (reword, never split)
    "DK-7_max_hues_per_slide": 4,        # DR-5 3-4 colors max, non-neutral
}


def _rgb(color):
    # python-pptx raises AttributeError/TypeError for non-RGB color types
    # (theme colors, inherited); those are "no explicit RGB" here, by design.
    try:
        if color and color.type is not None and color.rgb is not None:
            return str(color.rgb)
    except (AttributeError, TypeError):
        return None
    return None


def _is_connector(shape):
    # python-pptx reports a connector's shape_type as MSO_SHAPE_TYPE.LINE,
    # never a "CONNECTOR"-named value — match the actual type.
    return shape.shape_type == MSO_SHAPE_TYPE.LINE


def _rect(shape):
    return (shape.left, shape.top, shape.left + shape.width, shape.top + shape.height)


def _overlap_area(a, b):
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return w * h if (w > 0 and h > 0) else 0


def validate(path):
    prs = Presentation(path)
    sw, sh = prs.slide_width, prs.slide_height
    tol = RULES["DK-3_bounds_tolerance_emu"]
    violations = []

    for idx, slide in enumerate(prs.slides, 1):
        words = 0
        hues = set()
        text_rects = []
        for shape in slide.shapes:
            if shape.left is None:
                continue
            l, t, r, b = _rect(shape)
            if l < -tol or t < -tol or r > sw + tol or b > sh + tol:
                violations.append(
                    f"slide {idx}: DK-3 shape '{shape.name}' extends off-slide")
            if _is_connector(shape):
                continue
            fill_rgb = None
            try:
                # fill.type raises for shape kinds without a fill (e.g.
                # pictures); those simply have no fill hue to police.
                if shape.fill.type == 1:  # MSO_FILL.SOLID
                    fill_rgb = _rgb(shape.fill.fore_color)
            except (AttributeError, TypeError, NotImplementedError):
                fill_rgb = None
            if fill_rgb and fill_rgb not in RULES["DK-5_neutrals"]:
                hues.add(fill_rgb)
                if fill_rgb not in RULES["DK-5_palette"]:
                    violations.append(
                        f"slide {idx}: DK-5 fill #{fill_rgb} on '{shape.name}' not in palette")
            if not shape.has_text_frame:
                continue
            has_text = False
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    txt = run.text.strip()
                    if not txt:
                        continue
                    has_text = True
                    words += len(txt.split())
                    if run.font.size is None:
                        violations.append(
                            f"slide {idx}: DK-2 run without explicit font size in '{shape.name}'")
                    elif run.font.size.pt < RULES["DK-2_min_font_pt"]:
                        violations.append(
                            f"slide {idx}: DK-2 font {run.font.size.pt:.0f}pt < "
                            f"{RULES['DK-2_min_font_pt']}pt in '{shape.name}'")
                    run_rgb = _rgb(run.font.color)
                    if run_rgb is None:
                        # explicit color is part of "explicit type" — an
                        # inherited/theme color renders unpredictably (slop).
                        violations.append(
                            f"slide {idx}: DK-2 run without explicit font color in '{shape.name}'")
                    elif run_rgb not in RULES["DK-5_neutrals"]:
                        hues.add(run_rgb)
                        if run_rgb not in RULES["DK-5_palette"]:
                            violations.append(
                                f"slide {idx}: DK-5 font #{run_rgb} on '{shape.name}' not in palette")
            if has_text:
                text_rects.append((shape.name, _rect(shape)))
            if shape.name.lower().startswith("title"):
                title_words = len(shape.text_frame.text.split())
                if title_words > RULES["DK-6_max_title_words"]:
                    violations.append(
                        f"slide {idx}: DK-6 title has {title_words} words > "
                        f"{RULES['DK-6_max_title_words']}")
        if words > RULES["DK-1_max_words_per_slide"]:
            violations.append(
                f"slide {idx}: DK-1 {words} words > {RULES['DK-1_max_words_per_slide']}")
        if len(hues) > RULES["DK-7_max_hues_per_slide"]:
            violations.append(
                f"slide {idx}: DK-7 {len(hues)} non-neutral hues > "
                f"{RULES['DK-7_max_hues_per_slide']}")
        for i in range(len(text_rects)):
            for j in range(i + 1, len(text_rects)):
                if _overlap_area(text_rects[i][1], text_rects[j][1]) > RULES["DK-4_overlap_tolerance_emu2"]:
                    violations.append(
                        f"slide {idx}: DK-4 text shapes '{text_rects[i][0]}' and "
                        f"'{text_rects[j][0]}' overlap")
    return violations


def main():
    if len(sys.argv) != 2:
        print("usage: validate_deck.py <deck.pptx>", file=sys.stderr)
        return 2
    violations = validate(sys.argv[1])
    for v in violations:
        print(v)
    if violations:
        return 1
    print("DECK PASS — all DK rules green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
