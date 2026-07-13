#!/usr/bin/env python3
"""validate_drawio.py — machine gate for generated .drawio diagrams (DL rules).

    python3 scripts/validate_drawio.py <diagram.drawio>

Reads the mxGraphModel XML (pure stdlib — no toolkit) and prints one line
per violation ("cell <id>: DL-x …"), exit 1 if any; else a single PASS line,
exit 0. Thresholds cite the deck research DR numbers and the drawio research
DG numbers; the qualitative rules (does the topology read, 15-second glance)
are the model's render review, not this gate.

Chrome uses the deck's "Ink & Signal" tokens; diagram nodes are typed by the
semantic swatch set (SEM) — both are allowed by DL-3. Deliberately NOT
enforced as hard fails (DR-8 refuted-overreach): edges may cross objects, and
non-right-angle bends are allowed — connector quality is a render-review
judgement. Legend cells (id "legend-*") are chrome, exempt from node limits.
"""
import math
import re
import sys
import xml.etree.ElementTree as ET

RULES = {
    "DL-1_max_nodes": 12,          # DR-1 one-idea: split a denser diagram
    "DL-2_max_label_words": 3,     # DR-8 label economy (2-3 words/node)
    "DL-3_palette": {              # Ink & Signal chrome + semantic swatches, lowercased
        # chrome (deck_lib.TOKENS)
        "#16283f", "#5c6675", "#1f5fa8", "#eef2f7", "#dce3ec",
        # semantic node swatches (deck_lib.SEM / drawio_lib.SEM)
        "#dae8fc", "#6c8ebf", "#d5e8d4", "#82b366", "#f8cecc", "#b85450",
        "#fff2cc", "#d6b656", "#e1d5e7", "#9673a6", "#f5f5f5", "#666666",
        # neutrals
        "#ffffff", "#000000", "none", "default",
    },
    "DL-6_default_grid": 8,        # DG-18 8px grid (falls back if unset)
    "DL-8_px_per_char": 6.5,       # ~Helvetica advance @12pt; DL-8 label fit
}
_HEX = re.compile(r"(?:fillColor|strokeColor|fontColor|gradientColor|"
                  r"labelBackgroundColor)=([^;]+)")
_STYLE_KV = lambda style, key: (
    dict(kv.split("=", 1) for kv in style.split(";") if "=" in kv).get(key))


def _num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def _main_label(value):
    """The visible first line of a node label — drop a <br> note sublabel and
    strip inline HTML, so DL-2/DL-8 measure the real label, not markup."""
    first = re.split(r"<br\s*/?>", value, maxsplit=1)[0]
    return re.sub(r"<[^>]+>", "", first).strip()


def _usable_factor(style):
    if "rhombus" in style:
        return 0.55          # diamond text area is narrow
    if "cylinder" in style:
        return 0.82
    if "ellipse" in style:
        return 0.70
    return 1.0               # rounded rect


def validate(path):
    root = ET.parse(path).getroot()
    model = root if root.tag == "mxGraphModel" else root.find(".//mxGraphModel")
    if model is None:
        return [f"{path}: not an mxGraphModel (.drawio) file"]
    grid = int(model.get("gridSize") or RULES["DL-6_default_grid"])
    pw, ph = _num(model.get("pageWidth")), _num(model.get("pageHeight"))
    ppc = RULES["DL-8_px_per_char"]

    violations = []
    node_rects = []   # (id, x, y, w, h) for solid-fill content nodes only
    node_count = 0

    for cell in model.iter("mxCell"):
        cid = cell.get("id", "?")
        style = cell.get("style") or ""
        raw = (cell.get("value") or "").strip()
        label = _main_label(raw)
        is_legend = cid.startswith("legend")

        # DL-3 palette — every color must be a token/semantic/neutral
        for hexv in _HEX.findall(style):
            if hexv.strip().lower() not in RULES["DL-3_palette"]:
                violations.append(
                    f"cell {cid}: DL-3 color {hexv} not in the token palette")
        # DL-4 no shadows
        if _STYLE_KV(style, "shadow") == "1" or "shadowBlur" in style:
            violations.append(f"cell {cid}: DL-4 shadow enabled (must be shadow=0)")

        if cell.get("edge") == "1":
            # DL-5 orthogonal edges with line-jumps at crossings (DG-19 MUST)
            if _STYLE_KV(style, "edgeStyle") != "orthogonalEdgeStyle":
                violations.append(
                    f"cell {cid}: DL-5 edge is not orthogonalEdgeStyle")
            if _STYLE_KV(style, "jumpStyle") != "gap":
                violations.append(
                    f"cell {cid}: DL-5 edge missing jumpStyle=gap")
            continue
        if cell.get("vertex") != "1":
            continue

        # DL-2 label economy (main label only; note sublabel exempt)
        if label and len(label.split()) > RULES["DL-2_max_label_words"]:
            violations.append(
                f"cell {cid}: DL-2 label has {len(label.split())} words > "
                f"{RULES['DL-2_max_label_words']}")

        geo = cell.find("mxGeometry")
        if geo is None:
            continue
        x, y = _num(geo.get("x")), _num(geo.get("y"))
        w, h = _num(geo.get("width")), _num(geo.get("height"))
        if None in (x, y, w, h):
            continue
        # DL-6 8px grid
        for name, v in (("x", x), ("y", y), ("width", w), ("height", h)):
            if v % grid != 0:
                violations.append(
                    f"cell {cid}: DL-6 {name}={v:g} not on the {grid}px grid")
        # DL-7 on-canvas bounds
        if x < 0 or y < 0 or (pw and x + w > pw) or (ph and y + h > ph):
            violations.append(f"cell {cid}: DL-7 extends off-canvas")

        is_zone = _STYLE_KV(style, "fillColor") in (None, "none")

        # DL-8 label fit — a label that needs more wrapped lines than the box
        # is tall spills out (drawio wraps but cannot grow the fixed box).
        if label and not is_zone and not is_legend:
            usable = max(w * _usable_factor(style) - 12, 8)
            lines = math.ceil(len(label) * ppc / usable)
            need_h = lines * 15 + 12
            if need_h > h + 1:
                violations.append(
                    f"cell {cid}: DL-8 label '{label[:20]}' needs {lines} lines "
                    f"({need_h:g}px) > box height {h:g} — widen or shorten")

        if not is_zone and not is_legend:
            node_count += 1
            node_rects.append((cid, x, y, w, h))

    # DL-1 node count
    if node_count > RULES["DL-1_max_nodes"]:
        violations.append(
            f"diagram: DL-1 {node_count} nodes > {RULES['DL-1_max_nodes']} "
            f"(split into linked diagrams)")
    # DL-7 node overlap (content nodes only; a node inside a zone is expected)
    for i in range(len(node_rects)):
        ai, ax, ay, aw, ah = node_rects[i]
        for j in range(i + 1, len(node_rects)):
            bi, bx, by, bw, bh = node_rects[j]
            if ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah:
                violations.append(
                    f"cell {ai}: DL-7 overlaps node '{bi}'")
    return violations


def main():
    if len(sys.argv) != 2:
        print("usage: validate_drawio.py <diagram.drawio>", file=sys.stderr)
        return 2
    violations = validate(sys.argv[1])
    for v in violations:
        print(v)
    if violations:
        return 1
    print("DIAGRAM PASS — all DL rules green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
