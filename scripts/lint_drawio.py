#!/usr/bin/env python3
"""Structural linter for generated .drawio files (stdlib only).

Checks the invariants from skills/drawio/references/drawio-diagrams.md
("XML authoring essentials"). Exit codes: 0 = clean (warnings allowed on
stderr), 1 = usage error, 2 = lint failures (one per line on stdout).

Usage: lint_drawio.py FILE.drawio
"""
import sys
import xml.etree.ElementTree as ET

VERTEX_BUDGET = 9  # DG-4: advisory cap per page


def fail(errors, page, cell_id, msg):
    errors.append(f"{page}:{cell_id or '-'}: {msg}")


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
        boxes.append((cell.get("id"), cell.get("parent"), x, y, x + w, y + h))
    for i, (id_a, par_a, ax1, ay1, ax2, ay2) in enumerate(boxes):
        for id_b, par_b, bx1, by1, bx2, by2 in boxes[i + 1:]:
            if par_a == par_b and ax1 < bx2 and bx1 < ax2 and ay1 < by2 and by1 < ay2:
                warnings.append(f"{page_name}: boxes {id_a} and {id_b} overlap (DG-14)")

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
