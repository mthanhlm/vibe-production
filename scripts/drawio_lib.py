#!/usr/bin/env python3
"""drawio_lib.py — diagram model + dual serializer for /vibe:drawio.

Build one Diagram, then write it two ways from the SAME model:
  d.to_drawio()  -> editable mxGraphModel XML (opens in diagrams.net)
  d.to_svg()     -> faithful SVG for the render-review (soffice -> PNG)

Because both come from one model with identical geometry and tokens, the
PNG the model reviews faithfully represents the .drawio it ships (WA-16).
Visual tokens are the deck's (scripts/deck_lib.py) so the two suite skills
look like one system; the discipline is the deck research DR-8 + the
drawio specifics DG-17..21 (.vibe/research/2026-07-10-drawio-track-plan.md),
enforced as hard gates by scripts/validate_drawio.py (DL rules).

Positions come from scripts/drawio_layout.py (graphviz `dot`) or a hand
grid; this library is style-only and takes positions as given.
"""
import html
import xml.etree.ElementTree as ET

# One-accent palette — identical hexes to deck_lib.TOKENS (DR-5). Kept in
# sync with validate_drawio.RULES["DL-3_palette"].
TOKENS = {
    "ink": "#1A1A2E",      # node label text
    "muted": "#6B7280",    # edge labels, secondary
    "accent": "#2B59C3",   # the one accent — node stroke, primary-path edges
    "panel": "#F2F4F8",    # node fill
    "border": "#E5E7EB",   # zone container stroke
    "white": "#FFFFFF",
    "boundary": "#6B7280", # dashed logical/security boundary stroke
}

GRID = 8
FONT = "Helvetica"  # drawio's portable default; renders under soffice too


def _ortho_route(src, dst):
    """Border-to-border orthogonal polyline between two rects. Exits/enters
    on the side facing the other box and elbows at the midpoint, so the line
    never runs through either connected box. A preview approximation, not the
    diagrams.net router."""
    sx, sy, sw, sh = src
    tx, ty, tw, th = dst
    scx, scy, tcx, tcy = sx + sw / 2, sy + sh / 2, tx + tw / 2, ty + th / 2
    if abs(tcx - scx) >= abs(tcy - scy):  # mostly horizontal
        x1 = sx + sw if tcx >= scx else sx
        x2 = tx if tcx >= scx else tx + tw
        mid = (x1 + x2) / 2
        return [(x1, scy), (mid, scy), (mid, tcy), (x2, tcy)]
    y1 = sy + sh if tcy >= scy else sy       # mostly vertical
    y2 = ty if tcy >= scy else ty + th
    mid = (y1 + y2) / 2
    return [(scx, y1), (scx, mid), (tcx, mid), (tcx, y2)]

# Style strings — every value cites a rule. shadow=0 (DR-8/DG no shadows),
# rounded token cards, orthogonal jump edges (DG-19).
_NODE_STYLE = ("rounded=1;arcSize=8;whiteSpace=wrap;html=1;"
               "fillColor={fill};strokeColor={stroke};strokeWidth=1.5;"
               "fontFamily=" + FONT + ";fontSize=12;fontColor={ink};shadow=0;")
_ZONE_STYLE = ("rounded=1;arcSize=6;container=0;verticalAlign=top;align=left;"
               "spacingLeft=12;spacingTop=8;fontStyle=1;fontSize=12;"
               "fontFamily=" + FONT + ";fillColor=none;strokeColor={stroke};"
               "strokeWidth=1;fontColor={ink};dashed={dashed};"
               "whiteSpace=wrap;html=1;shadow=0;")
_EDGE_STYLE = ("edgeStyle=orthogonalEdgeStyle;rounded=1;jettySize=auto;"
               "orthogonalLoop=1;strokeWidth=1.5;strokeColor={stroke};"
               "endArrow=blockThin;endFill=1;startArrow=none;jumpStyle=gap;"
               "jumpSize=8;fontSize=11;fontColor={muted};"
               "labelBackgroundColor=" + TOKENS["white"] + ";shadow=0;")


class Diagram:
    """A styled node/edge/zone model. Positions (x,y,w,h in px, 8-grid) are
    supplied by the caller (drawio_layout or a hand grid); this class owns
    only styling and serialization."""

    def __init__(self, name="diagram"):
        self.name = name
        self._nodes = []   # (id, label, x, y, w, h, accent_stroke)
        self._zones = []   # (id, label, x, y, w, h, dashed)
        self._edges = []   # (src_id, dst_id, label, primary)
        self._ids = set()

    def _reserve(self, cid):
        if cid in self._ids:
            raise ValueError(f"duplicate cell id: {cid}")
        self._ids.add(cid)

    def node(self, cid, label, x, y, w=136, h=56, accent=True):
        """A token card. accent=True strokes it with the accent hue."""
        self._reserve(cid)
        self._nodes.append((cid, label, int(x), int(y), int(w), int(h), accent))
        return cid

    def zone(self, cid, label, x, y, w, h, dashed=True):
        """A labelled boundary container (dashed = logical/security, DG-19)."""
        self._reserve(cid)
        self._zones.append((cid, label, int(x), int(y), int(w), int(h), dashed))
        return cid

    def zone_around(self, cid, label, node_ids, pad=24, pad_top=40, dashed=True):
        """Frame already-placed nodes with a boundary zone whose bounds are
        computed from them — the documented way to add a boundary to a
        dot-laid-out diagram. Extra top padding leaves room for the label."""
        boxes = [n for n in self._nodes if n[0] in set(node_ids)]
        if not boxes:
            raise ValueError("zone_around: no matching placed nodes")
        x0 = min(b[2] for b in boxes) - pad
        y0 = min(b[3] for b in boxes) - pad_top
        x1 = max(b[2] + b[4] for b in boxes) + pad
        y1 = max(b[3] + b[5] for b in boxes) + pad
        return self.zone(cid, label, x0, y0, x1 - x0, y1 - y0, dashed=dashed)

    def edge(self, src, dst, label="", primary=False):
        """An orthogonal edge; primary=True colors it accent (the main path)."""
        self._edges.append((src, dst, label, primary))

    def _extent(self):
        w = h = 0
        for _, _, x, y, nw, nh, _ in self._nodes:
            w, h = max(w, x + nw), max(h, y + nh)
        for _, _, x, y, zw, zh, _ in self._zones:
            w, h = max(w, x + zw), max(h, y + zh)
        return w + GRID * 5, h + GRID * 5

    # --- serializers -----------------------------------------------------

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
        # zones first so nodes render on top
        for cid, label, x, y, zw, zh, dashed in self._zones:
            style = _ZONE_STYLE.format(stroke=TOKENS["boundary"], ink=TOKENS["ink"],
                                       dashed=1 if dashed else 0)
            self._vertex(root, cid, label, x, y, zw, zh, style)
        for cid, label, x, y, nw, nh, accent in self._nodes:
            stroke = TOKENS["accent"] if accent else TOKENS["border"]
            style = _NODE_STYLE.format(fill=TOKENS["panel"], stroke=stroke,
                                       ink=TOKENS["ink"])
            self._vertex(root, cid, label, x, y, nw, nh, style)
        for i, (src, dst, label, primary) in enumerate(self._edges):
            stroke = TOKENS["accent"] if primary else TOKENS["muted"]
            style = _EDGE_STYLE.format(stroke=stroke, muted=TOKENS["muted"])
            cell = ET.SubElement(root, "mxCell", {
                "id": f"e{i}", "style": style, "edge": "1", "parent": "1",
                "source": src, "target": dst, "value": label})
            geo = ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
            geo.set("relative", "1")
        return ('<?xml version="1.0" encoding="UTF-8"?>\n'
                + ET.tostring(mx, encoding="unicode"))

    def _vertex(self, root, cid, label, x, y, w, h, style):
        cell = ET.SubElement(root, "mxCell", {
            "id": cid, "value": label, "style": style, "vertex": "1", "parent": "1"})
        ET.SubElement(cell, "mxGeometry", {
            "x": str(x), "y": str(y), "width": str(w), "height": str(h),
            "as": "geometry"})

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
        # edges under nodes. Approximate orthogonal routing from border to
        # border (not through centers) so the preview doesn't draw lines
        # straight through the connected boxes. This is a REVIEW preview; the
        # real diagrams.net orthogonal router (orthogonalEdgeStyle in the
        # .drawio) is cleaner — judge topology and reading, not pixel routing.
        rects = {cid: (x, y, nw, nh) for cid, _, x, y, nw, nh, _ in self._nodes}
        for src, dst, label, primary in self._edges:
            if src not in rects or dst not in rects:
                continue
            pts = _ortho_route(rects[src], rects[dst])
            stroke = TOKENS["accent"] if primary else TOKENS["muted"]
            pstr = " ".join(f"{px:.0f},{py:.0f}" for px, py in pts)
            out.append(f'<polyline points="{pstr}" fill="none" '
                       f'stroke="{stroke}" stroke-width="1.5"/>')
            if label:
                mx, my = pts[len(pts) // 2]
                out.append(f'<text x="{mx:.0f}" y="{my - 4:.0f}" '
                           f'font-family="{FONT}" font-size="11" '
                           f'text-anchor="middle" fill="{TOKENS["muted"]}">'
                           f'{html.escape(label)}</text>')
        for cid, label, x, y, nw, nh, accent in self._nodes:
            stroke = TOKENS["accent"] if accent else TOKENS["border"]
            out.append(f'<rect x="{x}" y="{y}" width="{nw}" height="{nh}" rx="8" '
                       f'fill="{TOKENS["panel"]}" stroke="{stroke}" '
                       f'stroke-width="1.5"/>')
            out.append(f'<text x="{x + nw / 2:.0f}" y="{y + nh / 2 + 4:.0f}" '
                       f'font-family="{FONT}" font-size="12" text-anchor="middle" '
                       f'fill="{TOKENS["ink"]}">{html.escape(label)}</text>')
        out.append("</svg>")
        return "\n".join(out)

    def save(self, drawio_path, svg_path):
        with open(drawio_path, "w", encoding="utf-8") as f:
            f.write(self.to_drawio())
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(self.to_svg())


def from_layout(layout, labels, diagram=None, primary_src=None):
    """Build a Diagram from drawio_layout JSON (dict) + a {node_id: label}
    map. Edges from the layout are drawn; the root's out-edges are the accent
    primary path. `primary_src` overrides the root; otherwise the root is a
    node that is an edge source but never a target (falling back to the first
    edge's source) — NOT dict order, which the sorted layout JSON scrambles.
    Positions are already 8-grid px."""
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
