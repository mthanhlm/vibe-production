#!/usr/bin/env python3
"""drawio_lib.py — diagram model + dual serializer for /vibe:drawio.

Build one Diagram, then write it two ways from the SAME model:
  d.to_drawio()  -> editable mxGraphModel XML (opens in diagrams.net)
  d.to_svg()     -> faithful SVG for the render-review (soffice -> PNG)

Because both come from one model with identical geometry and tokens, the PNG
the model reviews faithfully represents the .drawio it ships (WA-16). Chrome
tokens are the deck's "Ink & Signal" (scripts/deck_lib.py) so the two suite
skills look like one system; diagram nodes are **typed** by a semantic
colour/shape swatch set (SEM) — the lever that makes a diagram readable at a
glance. Discipline: deck research DR-8 + drawio DG rules
(.vibe/research/2026-07-10-slide-drawio-rules.md), enforced as hard gates by
scripts/validate_drawio.py (DL rules).

Positions come from scripts/drawio_layout.py (graphviz `dot`) or a hand grid;
this library is style-only and takes positions as given.
"""
import html
import xml.etree.ElementTree as ET

# Chrome palette — Ink & Signal, identical to deck_lib.TOKENS (DR-5). Kept in
# sync with validate_drawio.RULES["DL-3_palette"].
TOKENS = {
    "ink": "#16283F",       # node label text, start/end fill, chrome dark
    "muted": "#5C6675",     # edge labels, note sublabels, secondary
    "accent": "#1F5FA8",    # the one accent — primary-path + loop edges
    "panel": "#EEF2F7",     # neutral panel fill
    "border": "#DCE3EC",    # hairline
    "white": "#FFFFFF",     # canvas / label backgrounds
    "boundary": "#5C6675",  # dashed logical/security boundary stroke
}

# Semantic node palette (DR-8) — colour-blind-safe draw.io swatches. Each type
# is (fill, stroke); shape comes from SHAPE. Allowed by validate_drawio DL-3.
SEM = {
    "action":   ("#DAE8FC", "#6C8EBF"),   # a work step
    "success":  ("#D5E8D4", "#82B366"),   # an exit / done
    "error":    ("#F8CECC", "#B85450"),   # a failure / blocked
    "decision": ("#FFF2CC", "#D6B656"),   # a check / gate
    "data":     ("#E1D5E7", "#9673A6"),   # a store
    "external": ("#F5F5F5", "#666666"),   # an actor / outside system
    "start":    ("#16283F", "#16283F"),   # filled terminal
    "end":      ("#FFFFFF", "#16283F"),   # ring terminal
}
SHAPE = {"decision": "rhombus", "data": "cylinder",
         "start": "ellipse", "end": "ellipse"}   # default: rounded rect

GRID = 8
FONT = "Helvetica"  # drawio's portable default; renders under soffice too


def _fill_stroke(kind):
    return SEM.get(kind, SEM["action"])


def _node_style(kind):
    fill, stroke = _fill_stroke(kind)
    shape = SHAPE.get(kind, "rect")
    label = TOKENS["white"] if kind == "start" else TOKENS["ink"]
    core = (f"whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};"
            f"strokeWidth=2;fontFamily={FONT};fontSize=12;fontColor={label};shadow=0;")
    if shape == "rhombus":
        return "rhombus;perimeter=rhombusPerimeter;" + core
    if shape == "cylinder":
        return "shape=cylinder3;boundedLbl=1;" + core
    if shape == "ellipse":
        return "ellipse;perimeter=ellipsePerimeter;" + core
    return "rounded=1;arcSize=8;" + core


def _ortho_route(src, dst, loop=False):
    """Border-to-border orthogonal polyline between two rects. A back-edge
    (loop) drops into a return lane below both boxes so it never overlaps the
    forward path. Preview approximation, not the diagrams.net router."""
    sx, sy, sw, sh = src
    tx, ty, tw, th = dst
    scx, scy, tcx, tcy = sx + sw / 2, sy + sh / 2, tx + tw / 2, ty + th / 2
    if loop:
        lane = max(sy + sh, ty + th) + GRID * 3
        return [(scx, sy + sh), (scx, lane), (tcx, lane), (tcx, ty + th)]
    if abs(tcx - scx) >= abs(tcy - scy):  # mostly horizontal
        x1 = sx + sw if tcx >= scx else sx
        x2 = tx if tcx >= scx else tx + tw
        mid = (x1 + x2) / 2
        return [(x1, scy), (mid, scy), (mid, tcy), (x2, tcy)]
    y1 = sy + sh if tcy >= scy else sy       # mostly vertical
    y2 = ty if tcy >= scy else ty + th
    mid = (y1 + y2) / 2
    return [(scx, y1), (scx, mid), (tcx, mid), (tcx, y2)]


_ZONE_STYLE = ("rounded=1;arcSize=6;container=0;verticalAlign=top;align=left;"
               "spacingLeft=12;spacingTop=8;fontStyle=1;fontSize=12;"
               "fontFamily=" + FONT + ";fillColor=none;strokeColor={stroke};"
               "strokeWidth=1;fontColor={ink};dashed={dashed};"
               "whiteSpace=wrap;html=1;shadow=0;")


def _edge_style(primary, loop):
    stroke = TOKENS["accent"] if (primary or loop) else TOKENS["muted"]
    dash = "dashed=1;" if loop else ""
    # a back-edge exits and re-enters at the BOTTOM so diagrams.net drops it
    # into the return lane below the row (with the explicit waypoints in
    # to_drawio) instead of drawing a straight line through the middle.
    ee = "exitX=0.5;exitY=1;entryX=0.5;entryY=1;" if loop else ""
    return ("edgeStyle=orthogonalEdgeStyle;rounded=1;jettySize=auto;"
            f"orthogonalLoop=1;strokeWidth=2;strokeColor={stroke};{dash}{ee}"
            "endArrow=blockThin;endFill=1;startArrow=none;jumpStyle=gap;"
            f"jumpSize=8;fontSize=11;fontColor={TOKENS['muted']};"
            f"labelBackgroundColor={TOKENS['white']};shadow=0;")


class Diagram:
    """A styled node/edge/zone model. Positions (x,y,w,h in px, 8-grid) are
    supplied by the caller (drawio_layout or a hand grid); this class owns
    only styling and serialization."""

    def __init__(self, name="diagram"):
        self.name = name
        self._nodes = []   # (id, label, x, y, w, h, kind, note)
        self._zones = []   # (id, label, x, y, w, h, dashed)
        self._edges = []   # (src, dst, label, primary, loop)
        self._legend = []  # (kind, label, x, y)
        self._ids = set()

    def _reserve(self, cid):
        if cid in self._ids:
            raise ValueError(f"duplicate cell id: {cid}")
        self._ids.add(cid)

    def node(self, cid, label, x, y, w=136, h=56, kind="action", note=None):
        """A typed node. kind ∈ SEM sets its colour + shape (decision=rhombus,
        data=cylinder, start/end=ellipse, else rounded rect). note = an
        optional grey second line (e.g. "[FastAPI]")."""
        if kind not in SEM:
            raise ValueError(f"unknown node kind: {kind}")
        self._reserve(cid)
        self._nodes.append((cid, label, int(x), int(y), int(w), int(h), kind, note))
        return cid

    def zone(self, cid, label, x, y, w, h, dashed=True):
        """A labelled boundary container (dashed = logical/security, DG-19)."""
        self._reserve(cid)
        self._zones.append((cid, label, int(x), int(y), int(w), int(h), dashed))
        return cid

    def zone_around(self, cid, label, node_ids, pad=24, pad_top=40, dashed=True):
        """Frame already-placed nodes with a boundary zone whose bounds are
        computed from them. Extra top padding leaves room for the label."""
        boxes = [n for n in self._nodes if n[0] in set(node_ids)]
        if not boxes:
            raise ValueError("zone_around: no matching placed nodes")
        x0 = min(b[2] for b in boxes) - pad
        y0 = min(b[3] for b in boxes) - pad_top
        x1 = max(b[2] + b[4] for b in boxes) + pad
        y1 = max(b[3] + b[5] for b in boxes) + pad
        return self.zone(cid, label, x0, y0, x1 - x0, y1 - y0, dashed=dashed)

    def edge(self, src, dst, label="", primary=False, loop=False):
        """An orthogonal edge. primary=True colours it accent (the main path);
        loop=True is a dashed accent back-edge routed through a return lane.
        `label` carries a decision guard, e.g. "yes" / "no"."""
        self._edges.append((src, dst, label, primary, loop))

    def legend(self, items, x, y, gap=120):
        """Auto key: items=[(kind, label), …] laid left-to-right from (x,y)."""
        for i, (kind, label) in enumerate(items):
            if kind not in SEM:
                raise ValueError(f"unknown legend kind: {kind}")
            self._legend.append((kind, label, int(x) + i * gap, int(y)))

    def _extent(self):
        w = h = 0
        for _, _, x, y, nw, nh, _, _ in self._nodes:
            w, h = max(w, x + nw), max(h, y + nh)
        for _, _, x, y, zw, zh, _ in self._zones:
            w, h = max(w, x + zw), max(h, y + zh)
        for _, _, lx, ly in self._legend:
            w, h = max(w, lx + 132), max(h, ly + 16)
        return w + GRID * 5, h + GRID * 5

    # --- serializers -----------------------------------------------------

    def _value(self, label, note):
        if note:
            return (f'{label}<br><font color="{TOKENS["muted"]}" '
                    f'style="font-size:10px">{note}</font>')
        return label

    def to_drawio(self):
        """mxGraphModel XML string (editable in diagrams.net)."""
        w, h = self._extent()
        mx = ET.Element("mxGraphModel", {
            "dx": "800", "dy": "600", "grid": "1", "gridSize": str(GRID),
            "guides": "1", "tooltips": "1", "connect": "1", "arrows": "1",
            "fold": "1", "page": "1", "pageScale": "1",
            "pageWidth": str(w), "pageHeight": str(h), "math": "0", "shadow": "0",
        })
        root = ET.SubElement(mx, "root")
        ET.SubElement(root, "mxCell", {"id": "0"})
        ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})
        for cid, label, x, y, zw, zh, dashed in self._zones:
            style = _ZONE_STYLE.format(stroke=TOKENS["boundary"], ink=TOKENS["ink"],
                                       dashed=1 if dashed else 0)
            self._vertex(root, cid, label, x, y, zw, zh, style)
        for cid, label, x, y, nw, nh, kind, note in self._nodes:
            self._vertex(root, cid, self._value(label, note), x, y, nw, nh,
                         _node_style(kind))
        rects = {c: (x, y, nw, nh) for c, _, x, y, nw, nh, _, _ in self._nodes}
        for i, (src, dst, label, primary, loop) in enumerate(self._edges):
            cell = ET.SubElement(root, "mxCell", {
                "id": f"e{i}", "style": _edge_style(primary, loop), "edge": "1",
                "parent": "1", "source": src, "target": dst, "value": label})
            geo = ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
            if loop and src in rects and dst in rects:
                sx, sy, sw, sh = rects[src]
                tx, ty, tw, th = rects[dst]
                lane = max(sy + sh, ty + th) + GRID * 3
                arr = ET.SubElement(geo, "Array", {"as": "points"})
                ET.SubElement(arr, "mxPoint",
                              {"x": str(int(sx + sw / 2)), "y": str(int(lane))})
                ET.SubElement(arr, "mxPoint",
                              {"x": str(int(tx + tw / 2)), "y": str(int(lane))})
        for i, (kind, label, lx, ly) in enumerate(self._legend):
            fill, stroke = _fill_stroke(kind)
            sw = (f"rounded=1;arcSize=20;whiteSpace=wrap;html=1;fillColor={fill};"
                  f"strokeColor={stroke};strokeWidth=1.5;shadow=0;")
            self._vertex(root, f"legend-sw{i}", "", lx, ly, 16, 16, sw)
            tx = (f"text;html=1;align=left;verticalAlign=middle;fillColor=none;"
                  f"fontFamily={FONT};fontSize=11;fontColor={TOKENS['ink']};")
            self._vertex(root, f"legend-tx{i}", label, lx + 24, ly, 96, 16, tx)
        return ('<?xml version="1.0" encoding="UTF-8"?>\n'
                + ET.tostring(mx, encoding="unicode"))

    def _vertex(self, root, cid, label, x, y, w, h, style):
        cell = ET.SubElement(root, "mxCell", {
            "id": cid, "value": label, "style": style, "vertex": "1", "parent": "1"})
        ET.SubElement(cell, "mxGeometry", {
            "x": str(x), "y": str(y), "width": str(w), "height": str(h),
            "as": "geometry"})

    def _svg_node(self, out, x, y, nw, nh, kind):
        fill, stroke = _fill_stroke(kind)
        shape = SHAPE.get(kind, "rect")
        cx, cy = x + nw / 2, y + nh / 2
        if shape == "rhombus":
            pts = f"{cx:.0f},{y} {x + nw},{cy:.0f} {cx:.0f},{y + nh} {x},{cy:.0f}"
            out.append(f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" '
                       f'stroke-width="2"/>')
        elif shape == "cylinder":
            ry = 10
            out.append(f'<path d="M {x},{y + ry} A {nw / 2:.0f},{ry} 0 0 1 '
                       f'{x + nw},{y + ry} L {x + nw},{y + nh - ry} A {nw / 2:.0f},'
                       f'{ry} 0 0 1 {x},{y + nh - ry} Z" fill="{fill}" '
                       f'stroke="{stroke}" stroke-width="2"/>')
            out.append(f'<ellipse cx="{cx:.0f}" cy="{y + ry}" rx="{nw / 2:.0f}" '
                       f'ry="{ry}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        elif shape == "ellipse":
            out.append(f'<ellipse cx="{cx:.0f}" cy="{cy:.0f}" rx="{nw / 2:.0f}" '
                       f'ry="{nh / 2:.0f}" fill="{fill}" stroke="{stroke}" '
                       f'stroke-width="2"/>')
        else:
            out.append(f'<rect x="{x}" y="{y}" width="{nw}" height="{nh}" rx="8" '
                       f'fill="{fill}" stroke="{stroke}" stroke-width="2"/>')

    def to_svg(self):
        """Faithful preview SVG (same geometry + tokens as to_drawio)."""
        w, h = self._extent()
        out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" '
               f'height="{h}" viewBox="0 0 {w} {h}">',
               f'<rect width="{w}" height="{h}" fill="{TOKENS["white"]}"/>']
        for cid, label, x, y, zw, zh, dashed in self._zones:
            dash = ' stroke-dasharray="6 4"' if dashed else ""
            out.append(f'<rect x="{x}" y="{y}" width="{zw}" height="{zh}" rx="6" '
                       f'fill="none" stroke="{TOKENS["boundary"]}" '
                       f'stroke-width="1"{dash}/>')
            out.append(f'<text x="{x + 12}" y="{y + 20}" font-family="{FONT}" '
                       f'font-size="12" font-weight="bold" '
                       f'fill="{TOKENS["ink"]}">{html.escape(label)}</text>')
        # edges under nodes (border-to-border; back-edges use a return lane)
        rects = {c: (x, y, nw, nh) for c, _, x, y, nw, nh, _, _ in self._nodes}
        for src, dst, label, primary, loop in self._edges:
            if src not in rects or dst not in rects:
                continue
            pts = _ortho_route(rects[src], rects[dst], loop=loop)
            stroke = TOKENS["accent"] if (primary or loop) else TOKENS["muted"]
            dash = ' stroke-dasharray="6 4"' if loop else ""
            pstr = " ".join(f"{px:.0f},{py:.0f}" for px, py in pts)
            out.append(f'<polyline points="{pstr}" fill="none" stroke="{stroke}" '
                       f'stroke-width="2"{dash}/>')
            if label:
                mx, my = pts[len(pts) // 2]
                lw = len(label) * 6 + 8   # mimic drawio labelBackgroundColor
                out.append(f'<rect x="{mx - lw / 2:.0f}" y="{my - 15:.0f}" '
                           f'width="{lw}" height="15" fill="{TOKENS["white"]}"/>')
                out.append(f'<text x="{mx:.0f}" y="{my - 4:.0f}" '
                           f'font-family="{FONT}" font-size="11" '
                           f'text-anchor="middle" fill="{TOKENS["muted"]}">'
                           f'{html.escape(label)}</text>')
        for cid, label, x, y, nw, nh, kind, note in self._nodes:
            self._svg_node(out, x, y, nw, nh, kind)
            cx, cy = x + nw / 2, y + nh / 2
            tcol = TOKENS["white"] if kind == "start" else TOKENS["ink"]
            if note:
                out.append(f'<text x="{cx:.0f}" y="{cy - 3:.0f}" font-family="{FONT}" '
                           f'font-size="12" font-weight="bold" text-anchor="middle" '
                           f'fill="{tcol}">{html.escape(label)}</text>')
                out.append(f'<text x="{cx:.0f}" y="{cy + 13:.0f}" font-family="{FONT}" '
                           f'font-size="10" text-anchor="middle" '
                           f'fill="{TOKENS["muted"]}">{html.escape(note)}</text>')
            else:
                out.append(f'<text x="{cx:.0f}" y="{cy + 4:.0f}" font-family="{FONT}" '
                           f'font-size="12" text-anchor="middle" fill="{tcol}">'
                           f'{html.escape(label)}</text>')
        for kind, label, lx, ly in self._legend:
            fill, stroke = _fill_stroke(kind)
            out.append(f'<rect x="{lx}" y="{ly}" width="16" height="16" rx="3" '
                       f'fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
            out.append(f'<text x="{lx + 24}" y="{ly + 12}" font-family="{FONT}" '
                       f'font-size="11" fill="{TOKENS["ink"]}">{html.escape(label)}</text>')
        out.append("</svg>")
        return "\n".join(out)

    def save(self, drawio_path, svg_path):
        with open(drawio_path, "w", encoding="utf-8") as f:
            f.write(self.to_drawio())
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(self.to_svg())


def from_layout(layout, labels, diagram=None, primary_src=None):
    """Build a Diagram from drawio_layout JSON (dict) + a {node_id: label}
    map. Nodes default to kind="action"; the root's out-edges are the accent
    primary path. `primary_src` overrides the root; otherwise the root is a
    node that is an edge source but never a target (falling back to the first
    edge's source). Positions are already 8-grid px."""
    d = diagram or Diagram()
    nodes = layout["nodes"]
    for nid, box in nodes.items():
        d.node(nid, labels.get(nid, nid), box["x"], box["y"], box["w"], box["h"])
    edges = layout.get("edges", [])
    if primary_src is None and edges:
        targets = {dst for _, dst in edges}
        roots = [src for src, _ in edges if src not in targets]
        primary_src = roots[0] if roots else edges[0][0]
    for src, dst in edges:
        d.edge(src, dst, primary=(src == primary_src))
    return d
