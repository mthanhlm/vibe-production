#!/usr/bin/env python3
"""validate_drawio.py — machine gate for generated .drawio diagrams (DL rules).

    python3 scripts/validate_drawio.py <diagram.drawio>

Reads the mxGraphModel XML (pure stdlib — no toolkit) and prints one line
per violation ("cell <id>: DL-x …"), exit 1 if any; else a single PASS line,
exit 0. Thresholds cite the deck research DR numbers and the 2026-07-10
drawio research DG numbers; the qualitative rules (does the topology read,
15-second glance) are the model's render review, not this gate.

Deliberately NOT enforced as hard fails (DR-8 refuted-overreach): edges may
cross objects, and non-right-angle bends are allowed — connector quality is
a render-review judgement, not a rejection.
"""
import re
import sys
import xml.etree.ElementTree as ET

RULES = {
    "DL-1_max_nodes": 12,          # DR-1 one-idea: split a denser diagram
    "DL-2_max_label_words": 3,     # DR-8 label economy (2-3 words/node)
    "DL-3_palette": {              # DG-17 token palette (+ neutrals), lowercased
        "#1a1a2e", "#6b7280", "#2b59c3", "#f2f4f8", "#e5e7eb",
        "#ffffff", "#000000", "none", "default",
    },
    "DL-6_default_grid": 8,        # DG-18 8px grid (falls back if unset)
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


def validate(path):
    root = ET.parse(path).getroot()
    model = root if root.tag == "mxGraphModel" else root.find(".//mxGraphModel")
    if model is None:
        return [f"{path}: not an mxGraphModel (.drawio) file"]
    grid = int(model.get("gridSize") or RULES["DL-6_default_grid"])
    pw, ph = _num(model.get("pageWidth")), _num(model.get("pageHeight"))

    violations = []
    node_rects = []   # (id, x, y, w, h) for solid-fill nodes only
    node_count = 0

    for cell in model.iter("mxCell"):
        cid = cell.get("id", "?")
        style = cell.get("style") or ""
        label = (cell.get("value") or "").strip()

        # DL-3 palette — every color must be a token/neutral
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

        # DL-2 label economy (nodes and zones)
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
        if not is_zone:
            node_count += 1
            node_rects.append((cid, x, y, w, h))

    # DL-1 node count
    if node_count > RULES["DL-1_max_nodes"]:
        violations.append(
            f"diagram: DL-1 {node_count} nodes > {RULES['DL-1_max_nodes']} "
            f"(split into linked diagrams)")
    # DL-7 node overlap (nodes only; a node inside a zone is expected)
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
