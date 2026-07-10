#!/usr/bin/env python3
"""Structural linter for generated .drawio files (stdlib only).

Checks the invariants from skills/drawio/references/drawio-diagrams.md
("XML authoring essentials"). Exit codes: 0 = clean (warnings allowed on
stderr), 1 = usage error, 2 = lint failures (one per line on stdout).

Usage: lint_drawio.py FILE.drawio
"""
import os
import sys
import xml.etree.ElementTree as ET

VERTEX_BUDGET = 9  # DG-4: advisory cap per page

# DG-17 frozen palette (lowercase): the style-token colors plus draw.io's
# default palette, both listed verbatim in the reference doc ("Style tokens"
# section and pitfall 9). `none`/`default` are always legal.
ALLOWED_COLORS = {
    # token palette
    "#ffffff", "#000000", "#1e1e1e", "#1f2937", "#2a3618", "#76b900",
    "#8a8f98", "#dde3ea", "#ed7100",
    # draw.io default palette (pitfall 9)
    "#dae8fc", "#d5e8d4", "#fff2cc", "#f8cecc",
    "#6c8ebf", "#82b366", "#d6b656", "#b85450",
    # keywords
    "none", "default",
}
COLOR_KEYS = ("fillColor", "strokeColor", "fontColor", "gradientColor",
              "labelBackgroundColor")
NUMERIC_KEYS = ("arcSize", "strokeWidth", "jumpSize")


def _debug(context, exc):
    # Swallowed failures leave a breadcrumb when VIBE_DEBUG is set.
    if os.environ.get("VIBE_DEBUG"):
        print(f"vibe-debug[lint_drawio] {context}: {type(exc).__name__}: {exc}",
              file=sys.stderr)


def fail(errors, page, cell_id, msg):
    errors.append(f"{page}:{cell_id or '-'}: {msg}")


def style_dict(style):
    """Split a drawio style string into {key: value}; bare flags are skipped."""
    tokens = {}
    for token in (style or "").split(";"):
        if "=" in token:
            key, value = token.split("=", 1)
            tokens[key] = value
    return tokens


def lint_style(page_name, cid, style, is_edge, errors, warnings):
    """Style-token checks E1/E2 and W2/W3/W6/W7 for one cell."""
    if "data:" in style and ";base64" in style:
        fail(errors, page_name, cid,
             "style embeds a base64 data-URI — use URL-encoded SVG (DG-20)")
    tokens = style_dict(style)
    numeric = {}
    for key in NUMERIC_KEYS:
        if key in tokens:
            try:
                numeric[key] = float(tokens[key])
            except ValueError:
                fail(errors, page_name, cid,
                     f'style {key}="{tokens[key]}" is not numeric')
    if "arcSize" in numeric and not 2 <= numeric["arcSize"] <= 24:
        warnings.append(
            f"{page_name}: {cid} arcSize={tokens['arcSize']} is outside 2-24 (DG-21)")
    for key in COLOR_KEYS:
        value = tokens.get(key)
        if value and value.lower() not in ALLOWED_COLORS:
            warnings.append(
                f"{page_name}: {cid} {key}={value} is outside the token palette (DG-17)")
    if is_edge:
        if tokens.get("edgeStyle") != "orthogonalEdgeStyle":
            warnings.append(
                f"{page_name}: edge {cid} missing edgeStyle=orthogonalEdgeStyle (DG-15, DG-19)")
        if tokens.get("dashed") == "1":
            warnings.append(
                f"{page_name}: edge {cid} is dashed — dashed=1 is reserved for "
                f"boundary containers (DG-19)")
    elif tokens.get("dashed") == "1" and tokens.get("container") != "1":
        warnings.append(
            f"{page_name}: vertex {cid} is dashed but not a container — dashed=1 "
            f"is reserved for boundary containers (DG-19)")


def lint_page(page_name, model, errors, warnings):
    root = model.find("root")
    if root is None:
        fail(errors, page_name, None, "mxGraphModel has no <root>")
        return

    cells = root.findall("mxCell")
    ids = [c.get("id") for c in cells]
    if len(ids) != len(set(ids)):
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        fail(errors, page_name, ",".join(dupes), "duplicate cell ids")
    id_set = set(ids)
    if "0" not in id_set or "1" not in id_set:
        fail(errors, page_name, None, 'missing structural cells id="0" and id="1"')

    vertices = set()
    for cell in cells:
        cid = cell.get("id")
        if cid in ("0", "1"):
            continue
        is_vertex = cell.get("vertex") == "1"
        is_edge = cell.get("edge") == "1"
        if is_vertex == is_edge:
            fail(errors, page_name, cid, 'need exactly one of vertex="1" or edge="1"')
        lint_style(page_name, cid, cell.get("style") or "", is_edge, errors, warnings)
        parent = cell.get("parent")
        if parent not in id_set:
            fail(errors, page_name, cid, f'parent "{parent}" does not exist')
        geom = cell.find("mxGeometry")
        if geom is None:
            fail(errors, page_name, cid, "missing <mxGeometry> child")
        if is_vertex:
            vertices.add(cid)
            if geom is not None and geom.get("as") != "geometry":
                fail(errors, page_name, cid, 'mxGeometry needs as="geometry"')
        if is_edge:
            if geom is not None and geom.get("relative") != "1":
                fail(errors, page_name, cid, 'edge geometry needs relative="1"')
            for ref_attr in ("source", "target"):
                ref = cell.get(ref_attr)
                if not ref:
                    fail(errors, page_name, cid, f"edge has no {ref_attr}")
                elif ref not in id_set:
                    fail(errors, page_name, cid, f'{ref_attr} "{ref}" does not exist')

    # DG-18: off-grid vertices, judged against the DECLARED grid only
    # (legacy files declare or default gridSize 10 and stay warning-free)
    grid_size = None
    if model.get("grid") == "1":
        try:
            grid_size = float(model.get("gridSize", "10"))
        except ValueError as exc:
            _debug(f"page {page_name}: non-numeric gridSize", exc)
        if grid_size is not None and grid_size <= 0:
            grid_size = None

    # DG-14: overlapping sibling boxes render broken and draw.io won't fix them
    boxes = []
    for cell in cells:
        if cell.get("vertex") != "1" or cell.get("id") in ("0", "1"):
            continue
        geom = cell.find("mxGeometry")
        if geom is None:
            continue
        try:
            x, y = float(geom.get("x", 0)), float(geom.get("y", 0))
            w, h = float(geom.get("width", 0)), float(geom.get("height", 0))
        except ValueError:
            fail(errors, page_name, cell.get("id"), "non-numeric geometry")
            continue
        if grid_size:
            off = [f"{attr}={value:g}" for attr, value in
                   (("x", x), ("y", y), ("width", w), ("height", h))
                   if value % grid_size != 0]
            if off:
                warnings.append(
                    f"{page_name}: vertex {cell.get('id')} is off the declared "
                    f"{grid_size:g}px grid: {', '.join(off)} (DG-18)")
        boxes.append((cell.get("id"), cell.get("parent"), x, y, x + w, y + h))
    for i, (id_a, par_a, ax1, ay1, ax2, ay2) in enumerate(boxes):
        for id_b, par_b, bx1, by1, bx2, by2 in boxes[i + 1:]:
            if par_a != par_b:
                continue
            x_overlap = ax1 < bx2 and bx1 < ax2
            y_overlap = ay1 < by2 and by1 < ay2
            if x_overlap and y_overlap:
                warnings.append(f"{page_name}: boxes {id_a} and {id_b} overlap (DG-14)")
            elif x_overlap or y_overlap:
                # DG-18: siblings aligned on one axis need breathing room on the other
                if x_overlap:
                    gap = max(ay1 - by2, by1 - ay2)
                else:
                    gap = max(ax1 - bx2, bx1 - ax2)
                if gap < 24:
                    warnings.append(
                        f"{page_name}: boxes {id_a} and {id_b} are only {gap:g}px "
                        f"apart — keep siblings >=24px apart (DG-18)")

    # DG-18: container nesting depth (parent chain, excluding cells 0/1)
    parent_of = {c.get("id"): c.get("parent") for c in cells}
    for cell in cells:
        cid = cell.get("id")
        if cid in ("0", "1") or cell.get("vertex") != "1":
            continue
        depth, seen, parent = 1, {cid}, cell.get("parent")
        while parent not in (None, "0", "1") and parent in parent_of and parent not in seen:
            seen.add(parent)
            depth += 1
            parent = parent_of.get(parent)
        if depth > 3:
            warnings.append(
                f"{page_name}: {cid} is nested {depth} levels deep — max 3 (DG-18)")

    if len(vertices) > VERTEX_BUDGET:
        warnings.append(
            f"{page_name}: {len(vertices)} boxes exceeds the ~{VERTEX_BUDGET}-box "
            f"executive budget (DG-4) — consider clustering"
        )


def main():
    if len(sys.argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 1
    path = sys.argv[1]
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as exc:
        print(f"cannot read {path}: {exc}", file=sys.stderr)
        return 1

    errors, warnings = [], []
    if "<!--" in text:
        errors.append("-:-: XML comments present — emit none (DG-16)")
    try:
        tree = ET.fromstring(text)
    except ET.ParseError as exc:
        print(f"{path}: not well-formed XML: {exc}")
        return 2

    if tree.tag == "mxfile":
        pages = tree.findall("diagram")
        if not pages:
            errors.append("-:-: <mxfile> contains no <diagram> pages")
        for page in pages:
            name = page.get("name") or page.get("id") or "?"
            model = page.find("mxGraphModel")
            if model is None:
                # compressed payloads are text content, not child elements
                errors.append(f"{name}:-: no <mxGraphModel> — emit uncompressed XML (DG-16)")
                continue
            lint_page(name, model, errors, warnings)
    elif tree.tag == "mxGraphModel":
        lint_page("Page-1", tree, errors, warnings)
    else:
        errors.append(f"-:-: root element <{tree.tag}> is not <mxfile>/<mxGraphModel>")

    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    if errors:
        for error in errors:
            print(f"{path}:{error}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
