#!/usr/bin/env python3
"""Parametric DrawingML component emitters for build_pptx.py (stdlib only).

WA-2: this module IS the enumerated emitter list — every visual component a
deck may contain beyond template chrome lives here as a pure function of
(zone rect, spec block, theme), covered by golden-fragment tests and gated
by validate_pptx.py. Emitters never do I/O and never touch the template.

Each emit_* returns (xml_str, media, rels):
  xml_str — one or more DrawingML fragments to append into the slide spTree
  media   — list of (part_name, bytes) for ppt/media/
  rels    — list of (rel_id, target) for the slide's .rels

Emitters are pure: file I/O (reading image bytes) happens in build_pptx.py,
which passes bytes in via the block's private "_" keys.
"""
import json
import os
import struct
import zlib

# Palette per theme. Keep in sync with the chrome colors in
# skills/slide/assets/make_template.py (single-file dev-time generator).
THEMES = {
    "light": {"strong": "163A5F", "ink": "20242C", "grey": "6B7280",
              "faint": "D8DCE3", "hair": "E3E7EE", "accent": "C9A227",
              "card": "FFFFFF", "green": "2E7D4F", "red": "DB444B"},
    "dark":  {"strong": "FFFFFF", "ink": "E8EAED", "grey": "9AA3AE",
              "faint": "3F4650", "hair": "3A3F47", "accent": "C9A227",
              "card": "262E36", "green": "58B788", "red": "E0666E"},
}
SHADOW = "0F1B2A"  # distinct from all text hexes (dark recolor safety)

CARD_SHADOW = (f'<a:effectLst><a:outerShdw blurRad="190500" dist="76200" '
               f'dir="5400000" rotWithShape="0"><a:srgbClr val="{SHADOW}">'
               '<a:alpha val="25000"/></a:srgbClr></a:outerShdw></a:effectLst>')

# Exhibit kinds chart_takeaway accepts.
EXHIBIT_TYPES = {"bars", "column", "waterfall", "line", "ring", "harvey",
                 "image", "photo"}


def _txt(shape_id, name, x, y, cx, cy, runs, anchor="t"):
    """Text shape. runs: list of (text, size, color, bold, algn)."""
    paras = []
    for text, size, color, bold, algn in runs:
        battr = ' b="1"' if bold else ""
        aattr = f' algn="{algn}"' if algn else ""
        paras.append(
            f'<a:p><a:pPr marL="0" indent="0"{aattr}><a:buNone/></a:pPr>'
            f'<a:r><a:rPr lang="en-US" sz="{size}"{battr} dirty="0">'
            f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
            '<a:latin typeface="Arial"/><a:cs typeface="Arial"/></a:rPr>'
            f'<a:t>{_esc(text)}</a:t></a:r></a:p>')
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name="{name}"/>'
            '<p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/>'
            f'<a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            '<a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>'
            f'<p:txBody><a:bodyPr wrap="square" anchor="{anchor}">'
            '<a:normAutofit/></a:bodyPr><a:lstStyle/>'
            + "".join(paras) + "</p:txBody></p:sp>")


def _rect(shape_id, name, x, y, cx, cy, fill, geom="rect", adj=None,
          effect="", rot=None):
    av = (f'<a:avLst><a:gd name="adj" fmla="val {adj}"/></a:avLst>'
          if adj is not None else "<a:avLst/>")
    rattr = f' rot="{rot}"' if rot else ""
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name="{name}"/>'
            '<p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm{rattr}><a:off x="{x}" y="{y}"/>'
            f'<a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
            f'<a:prstGeom prst="{geom}">{av}</a:prstGeom>'
            f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>'
            f'<a:ln><a:noFill/></a:ln>{effect}</p:spPr>'
            '<p:txBody><a:bodyPr/><a:lstStyle/>'
            '<a:p><a:endParaRPr lang="en-US"/></a:p></p:txBody></p:sp>')


def _line(shape_id, name, x, y, cx, cy, color, width=9525):
    """Thin rule drawn as a straight connector-style line shape."""
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name="{name}"/>'
            '<p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/>'
            f'<a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
            '<a:prstGeom prst="line"><a:avLst/></a:prstGeom>'
            f'<a:ln w="{width}"><a:solidFill><a:srgbClr val="{color}"/>'
            '</a:solidFill></a:ln></p:spPr>'
            '<p:txBody><a:bodyPr/><a:lstStyle/>'
            '<a:p><a:endParaRPr lang="en-US"/></a:p></p:txBody></p:sp>')


def _esc(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def _fmt(value, unit=""):
    if isinstance(value, (int, float)):
        s = f"{value:,.10g}"
    else:
        s = str(value)
    return f"{s}{unit}"


_ICONS = None
ICON_SPACE = 24000   # must match icons.json _meta.space
ICON_VISUAL = 24 / 28.0  # the 24-grid spans 24/28 of the padded path space


def _icons():
    global _ICONS
    if _ICONS is None:
        root = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..")
        path = os.path.join(root, "skills", "slide", "assets", "icons.json")
        with open(path, encoding="utf-8") as fh:
            _ICONS = json.load(fh)
    return _ICONS


def icon_exists(name):
    return name in _icons()["icons"]


def nice_max(vmax):
    """Smallest 1/2/5 ladder value >= vmax (chart scaling)."""
    if vmax <= 0:
        return 1
    mag = 1
    while mag * 10 <= vmax:
        mag *= 10
    for step in (1, 2, 5, 10):
        if mag * step >= vmax:
            return mag * step
    return mag * 10


# --- emitters ---------------------------------------------------------------

def emit_kpi_row(zone, block, theme):
    """4-6 metric tiles: value, label, delta chip (SL-21 semantic color)."""
    x0, y0, w, _h = zone
    tiles = block["tiles"]
    n = len(tiles)
    gap = 250000
    tw = (w - (n - 1) * gap) // n
    th = 2000000
    out, sid = [], 100
    for i, t in enumerate(tiles):
        tx = x0 + i * (tw + gap)
        out.append(_rect(sid, f"kpi_tile_{i + 1}", tx, y0, tw, th,
                         theme["card"], geom="roundRect", adj=6000,
                         effect=CARD_SHADOW))
        sid += 1
        out.append(_txt(sid, f"kpi_value_{i + 1}", tx + 150000, y0 + 250000,
                        tw - 300000, 900000,
                        [(_fmt(t.get("value", "")), 6000, theme["strong"],
                          True, None)]))
        sid += 1
        out.append(_txt(sid, f"kpi_label_{i + 1}", tx + 150000, y0 + 1200000,
                        tw - 300000, 350000,
                        [(t.get("label", ""), 1300, theme["grey"], False,
                          None)]))
        sid += 1
        delta = t.get("delta")
        if delta:
            direction = t.get("direction", "flat")
            sentiment = t.get("sentiment",
                              {"up": "good", "down": "bad"}.get(direction,
                                                                "neutral"))
            color = {"good": theme["green"], "bad": theme["red"],
                     "neutral": theme["grey"]}[sentiment]
            cy = y0 + 1600000
            if direction in ("up", "down"):
                rot = None if direction == "up" else 10800000
                out.append(_rect(sid, f"kpi_delta_glyph_{i + 1}",
                                 tx + 150000, cy + 40000, 140000, 120000,
                                 color, geom="triangle", rot=rot))
                sid += 1
            out.append(_txt(sid, f"kpi_delta_{i + 1}", tx + 340000, cy - 60000,
                            tw - 500000, 320000,
                            [(str(delta), 1300, color, True, None)]))
            sid += 1
    return "".join(out), [], []


def emit_bars(zone, block, theme):
    """Horizontal bars, sorted desc, direct value labels, one accent bar."""
    x0, y0, w, h = zone
    items = list(block["items"])
    if block.get("sort", "desc") == "desc":
        items.sort(key=lambda it: it["value"], reverse=True)
    unit = block.get("unit", "")
    highlight = block.get("highlight")
    n = len(items)
    label_w = 2600000
    value_w = 1100000
    bar_area = w - label_w - value_w
    row_h = h // n
    bar_h = int(row_h / 1.3)          # gap ratio 0.3
    vmax = nice_max(max(it["value"] for it in items))
    out, sid = [], 140
    for i, it in enumerate(items):
        ry = y0 + i * row_h
        by = ry + (row_h - bar_h) // 2
        hot = (it["label"] == highlight) or (highlight is None and i == 0)
        fill = theme["accent"] if hot else theme["faint"]
        blen = max(int(bar_area * it["value"] / vmax), 20000)
        out.append(_txt(sid, f"bar_label_{i + 1}", x0, by,
                        label_w - 150000, bar_h,
                        [(it["label"], 1200, theme["ink"], hot, "r")],
                        anchor="ctr"))
        sid += 1
        out.append(_rect(sid, f"bar_{i + 1}", x0 + label_w, by, blen, bar_h,
                         fill))
        sid += 1
        out.append(_txt(sid, f"bar_value_{i + 1}",
                        x0 + label_w + blen + 60000, by, value_w, bar_h,
                        [(_fmt(it["value"], unit), 1200,
                          theme["ink"] if hot else theme["grey"], hot, None)],
                        anchor="ctr"))
        sid += 1
    return "".join(out), [], []


def emit_column(zone, block, theme):
    """Vertical columns for time series; zero baseline; direct labels."""
    x0, y0, w, h = zone
    items = list(block["items"])  # keep given (time) order
    unit = block.get("unit", "")
    highlight = block.get("highlight")
    n = len(items)
    label_h = 400000
    value_h = 350000
    plot_h = h - label_h - value_h
    col_slot = w // n
    col_w = int(col_slot / 1.3)
    vmax = nice_max(max(it["value"] for it in items))
    baseline_y = y0 + value_h + plot_h
    out, sid = [], 180
    for i, it in enumerate(items):
        cx = x0 + i * col_slot + (col_slot - col_w) // 2
        hot = (it["label"] == highlight) or (highlight is None and i == n - 1)
        fill = theme["accent"] if hot else theme["faint"]
        ch = max(int(plot_h * it["value"] / vmax), 20000)
        cy = baseline_y - ch
        out.append(_rect(sid, f"col_{i + 1}", cx, cy, col_w, ch, fill))
        sid += 1
        out.append(_txt(sid, f"col_value_{i + 1}", cx - 100000, cy - value_h,
                        col_w + 200000, value_h,
                        [(_fmt(it["value"], unit), 1200,
                          theme["ink"] if hot else theme["grey"], hot,
                          "ctr")]))
        sid += 1
        out.append(_txt(sid, f"col_label_{i + 1}", cx - 100000,
                        baseline_y + 60000, col_w + 200000, label_h - 60000,
                        [(it["label"], 1200, theme["grey"], False, "ctr")]))
        sid += 1
    out.append(_line(sid, "col_baseline", x0, baseline_y, w, 0,
                     theme["grey"]))
    return "".join(out), [], []


def emit_icon(zone, block, theme):
    """Vendored Lucide icon as a stroked open custGeom path (probe-proven).
    Crisp at any size, recolorable, fully vector — never a raster."""
    x, y, cx, cy = zone
    data = _icons()["icons"][block["name"]]
    color = theme.get(block.get("color", "accent"), theme["accent"])
    parts = []
    for cmd in data:
        if cmd[0] == "M":
            parts.append(f'<a:moveTo><a:pt x="{cmd[1]}" y="{cmd[2]}"/></a:moveTo>')
        elif cmd[0] == "L":
            parts.append(f'<a:lnTo><a:pt x="{cmd[1]}" y="{cmd[2]}"/></a:lnTo>')
        elif cmd[0] == "C":
            pts = "".join(f'<a:pt x="{cmd[i]}" y="{cmd[i + 1]}"/>'
                          for i in (1, 3, 5))
            parts.append(f"<a:cubicBezTo>{pts}</a:cubicBezTo>")
        elif cmd[0] == "Z":
            parts.append("<a:close/>")
    # Lucide stroke is 2/24 of the visual grid; the grid spans ICON_VISUAL
    # of the box, so stroke EMU = box * 2/24 * ICON_VISUAL = box / 14.
    stroke = max(int(cx // 14), 12700)
    shape_id = block.get("_id", 90)  # caller keeps ids unique per slide
    return ((f'<p:sp><p:nvSpPr>'
             f'<p:cNvPr id="{shape_id}" name="icon_{block["name"]}"/>'
             '<p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
             f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/>'
             f'<a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
             '<a:custGeom><a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/>'
             f'<a:rect l="0" t="0" r="{ICON_SPACE}" b="{ICON_SPACE}"/>'
             f'<a:pathLst><a:path w="{ICON_SPACE}" h="{ICON_SPACE}" '
             f'fill="none">{"".join(parts)}</a:path></a:pathLst></a:custGeom>'
             f'<a:noFill/><a:ln w="{stroke}" cap="rnd">'
             f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
             '<a:round/></a:ln></p:spPr>'
             '<p:txBody><a:bodyPr/><a:lstStyle/>'
             '<a:p><a:endParaRPr lang="en-US"/></a:p></p:txBody></p:sp>'),
            [], [])


def emit_waterfall(zone, block, theme):
    """Bridge between two totals; every bar labelled (McKinsey rule)."""
    x0, y0, w, h = zone
    unit = block.get("unit", "")
    start = block["start"]
    deltas = list(block["deltas"])
    cum = float(start["value"])
    bars = [(start["label"], 0.0, cum, "total")]
    for d in deltas:
        v = float(d["value"])
        lo, hi = sorted((cum, cum + v))
        bars.append((d["label"], lo, hi, "up" if v >= 0 else "down"))
        cum += v
    bars.append((block.get("end_label", "End"), 0.0, cum, "total"))

    label_h, value_h = 400000, 320000
    plot_h = h - label_h - value_h
    vmax = nice_max(max(hi for _, _, hi, _ in bars))
    base_y = y0 + value_h + plot_h

    def vy(v):
        return int(base_y - plot_h * v / vmax)

    n = len(bars)
    slot = w // n
    bw = int(slot / 1.3)
    colors = {"total": theme["strong"], "up": theme["green"],
              "down": theme["red"]}
    out, sid = [], 220
    prev_edge = None
    running = 0.0
    for i, (label, lo, hi, kind) in enumerate(bars):
        bx = x0 + i * slot + (slot - bw) // 2
        top, bot = vy(hi), vy(lo)
        out.append(_rect(sid, f"wf_bar_{i + 1}", bx, top,
                         bw, max(bot - top, 20000), colors[kind]))
        sid += 1
        if kind == "total":
            running = hi
            text = _fmt(hi, unit)
        else:
            d = hi - lo if kind == "up" else lo - hi
            running = running + d
            text = ("+" if kind == "up" else "−") + _fmt(abs(d), unit)
        out.append(_txt(sid, f"wf_value_{i + 1}", bx - 150000,
                        top - value_h, bw + 300000, value_h,
                        [(text, 1200, colors[kind], True, "ctr")]))
        sid += 1
        out.append(_txt(sid, f"wf_label_{i + 1}", bx - 150000,
                        base_y + 40000, bw + 300000, label_h - 40000,
                        [(label, 1200, theme["grey"], False, "ctr")]))
        sid += 1
        conn_y = vy(running if kind != "total" else hi)
        if prev_edge is not None:
            out.append(_line(sid, f"wf_conn_{i}", prev_edge, vy(lo if kind == "up" else hi) if kind != "total" else conn_y,
                             bx - prev_edge, 0, theme["grey"]))
            sid += 1
        prev_edge = bx + bw
    out.append(_line(sid, "wf_baseline", x0, base_y, w, 0, theme["grey"]))
    return "".join(out), [], []


def emit_line_chart(zone, block, theme):
    """<=4 series as stroked polylines with direct end labels, no legend."""
    x0, y0, w, h = zone
    series = block["series"]
    unit = block.get("unit", "")
    highlight = block.get("highlight") or series[0]["name"]
    label_w = 1900000                      # room for direct end labels
    xaxis_h = 400000
    plot_w, plot_h = w - label_w, h - xaxis_h
    vmax = nice_max(max(v for s in series for _, v in s["points"]))
    out, sid = [], 260
    for s in series:
        pts = s["points"]
        n = len(pts)
        hot = s["name"] == highlight
        color = theme["accent"] if hot else theme["faint"]
        coords = [(int(i * plot_w / (n - 1)),
                   int(plot_h - plot_h * v / vmax))
                  for i, (_x, v) in enumerate(pts)]
        path = f'<a:moveTo><a:pt x="{coords[0][0]}" y="{coords[0][1]}"/></a:moveTo>'
        path += "".join(f'<a:lnTo><a:pt x="{px}" y="{py}"/></a:lnTo>'
                        for px, py in coords[1:])
        width = 28575 if hot else 19050
        out.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="line_{_esc(s["name"])}"/>'
            '<p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{x0}" y="{y0}"/>'
            f'<a:ext cx="{plot_w}" cy="{plot_h}"/></a:xfrm>'
            '<a:custGeom><a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/>'
            f'<a:rect l="0" t="0" r="{plot_w}" b="{plot_h}"/>'
            f'<a:pathLst><a:path w="{plot_w}" h="{plot_h}" fill="none">{path}'
            '</a:path></a:pathLst></a:custGeom>'
            f'<a:noFill/><a:ln w="{width}" cap="rnd">'
            f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
            '<a:round/></a:ln></p:spPr>'
            '<p:txBody><a:bodyPr/><a:lstStyle/>'
            '<a:p><a:endParaRPr lang="en-US"/></a:p></p:txBody></p:sp>')
        sid += 1
        ex, ey = coords[-1]
        dot = 90000
        out.append(_rect(sid, f"line_dot_{_esc(s['name'])}",
                         x0 + ex - dot // 2, y0 + ey - dot // 2, dot, dot,
                         color, geom="ellipse"))
        sid += 1
        last_v = pts[-1][1]
        out.append(_txt(sid, f"line_end_{_esc(s['name'])}",
                        x0 + plot_w + 80000,
                        y0 + ey - 160000, label_w - 80000, 340000,
                        [(f"{s['name']}  {_fmt(last_v, unit)}", 1200,
                          theme["ink"] if hot else theme["grey"], hot,
                          None)]))
        sid += 1
    # x category labels from the first series
    first = series[0]["points"]
    n = len(first)
    for i, (xlab, _v) in enumerate(first):
        cxp = x0 + int(i * plot_w / (n - 1))
        out.append(_txt(sid, f"line_x_{i + 1}", cxp - 500000,
                        y0 + plot_h + 60000, 1000000, xaxis_h - 60000,
                        [(str(xlab), 1200, theme["grey"], False, "ctr")]))
        sid += 1
    out.append(_line(sid, "line_baseline", x0, y0 + plot_h, plot_w, 0,
                     theme["grey"]))
    return "".join(out), [], []


def emit_ring(zone, block, theme):
    """Progress ring: grey track + accent arc with round caps (probe e2)."""
    x0, y0, w, h = zone
    size = min(w, h)
    cx = x0 + (w - size) // 2
    cy = y0 + (h - size) // 2
    pct = max(0, min(100, int(block["pct"])))
    stroke = int(size * 0.125)
    inset = stroke // 2
    track = (f'<p:sp><p:nvSpPr><p:cNvPr id="300" name="ring_track"/>'
             '<p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
             f'<p:spPr><a:xfrm><a:off x="{cx + inset}" y="{cy + inset}"/>'
             f'<a:ext cx="{size - stroke}" cy="{size - stroke}"/></a:xfrm>'
             '<a:prstGeom prst="ellipse"><a:avLst/></a:prstGeom>'
             f'<a:noFill/><a:ln w="{stroke}">'
             f'<a:solidFill><a:srgbClr val="{theme["hair"]}"/></a:solidFill>'
             '</a:ln></p:spPr><p:txBody><a:bodyPr/><a:lstStyle/>'
             '<a:p><a:endParaRPr lang="en-US"/></a:p></p:txBody></p:sp>')
    sw_ang = int(21600000 * pct / 100)
    arc = ""
    if pct > 0:
        arc = (f'<p:sp><p:nvSpPr><p:cNvPr id="301" name="ring_arc"/>'
               '<p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
               f'<p:spPr><a:xfrm><a:off x="{cx + inset}" y="{cy + inset}"/>'
               f'<a:ext cx="{size - stroke}" cy="{size - stroke}"/></a:xfrm>'
               '<a:custGeom><a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/>'
               '<a:rect l="0" t="0" r="100000" b="100000"/>'
               '<a:pathLst><a:path w="100000" h="100000" fill="none">'
               '<a:moveTo><a:pt x="50000" y="0"/></a:moveTo>'
               f'<a:arcTo wR="50000" hR="50000" stAng="16200000" '
               f'swAng="{sw_ang}"/></a:path></a:pathLst></a:custGeom>'
               f'<a:noFill/><a:ln w="{stroke}" cap="rnd">'
               f'<a:solidFill><a:srgbClr val="{theme["accent"]}"/></a:solidFill>'
               '<a:round/></a:ln></p:spPr>'
               '<p:txBody><a:bodyPr/><a:lstStyle/>'
               '<a:p><a:endParaRPr lang="en-US"/></a:p></p:txBody></p:sp>')
    pct_txt = _txt(302, "ring_pct", cx, cy + size // 2 - 500000, size,
                   700000, [(f"{pct}%", 4400, theme["strong"], True, "ctr")])
    label = _txt(303, "ring_label", cx, cy + size // 2 + 200000, size,
                 400000, [(block.get("label", ""), 1400, theme["grey"],
                           False, "ctr")])
    return track + arc + pct_txt + label, [], []


def emit_harvey(zone, block, theme):
    """Scorecard rows with quarter-quantized harvey balls."""
    x0, y0, w, h = zone
    items = block["items"]
    n = len(items)
    row_h = min(h // n, 700000)
    ball = int(row_h * 0.62)
    out, sid = [], 320
    for i, it in enumerate(items):
        ry = y0 + i * row_h
        pct = max(0, min(100, int(round(float(it["pct"]) / 25) * 25)))
        bx, by = x0, ry + (row_h - ball) // 2
        out.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="harvey_ring_{i + 1}"/>'
            '<p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{bx}" y="{by}"/>'
            f'<a:ext cx="{ball}" cy="{ball}"/></a:xfrm>'
            '<a:prstGeom prst="ellipse"><a:avLst/></a:prstGeom>'
            '<a:noFill/><a:ln w="9525">'
            f'<a:solidFill><a:srgbClr val="{theme["grey"]}"/></a:solidFill>'
            '</a:ln></p:spPr><p:txBody><a:bodyPr/><a:lstStyle/>'
            '<a:p><a:endParaRPr lang="en-US"/></a:p></p:txBody></p:sp>')
        sid += 1
        if pct == 100:
            out.append(_rect(sid, f"harvey_fill_{i + 1}", bx, by, ball, ball,
                             theme["accent"], geom="ellipse"))
            sid += 1
        elif pct > 0:
            end = (16200000 + int(21600000 * pct / 100)) % 21600000
            out.append(
                f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="harvey_fill_{i + 1}"/>'
                '<p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
                f'<p:spPr><a:xfrm><a:off x="{bx}" y="{by}"/>'
                f'<a:ext cx="{ball}" cy="{ball}"/></a:xfrm>'
                '<a:prstGeom prst="pie"><a:avLst>'
                '<a:gd name="adj1" fmla="val 16200000"/>'
                f'<a:gd name="adj2" fmla="val {end}"/></a:avLst></a:prstGeom>'
                f'<a:solidFill><a:srgbClr val="{theme["accent"]}"/></a:solidFill>'
                '<a:ln><a:noFill/></a:ln></p:spPr>'
                '<p:txBody><a:bodyPr/><a:lstStyle/>'
                '<a:p><a:endParaRPr lang="en-US"/></a:p></p:txBody></p:sp>')
            sid += 1
        out.append(_txt(sid, f"harvey_label_{i + 1}", bx + ball + 250000,
                        ry, w - ball - 250000, row_h,
                        [(it["label"], 1400, theme["ink"], False, None)],
                        anchor="ctr"))
        sid += 1
    return "".join(out), [], []


def emit_flow(zone, block, theme):
    """4-5 step horizontal process; accent on the step that matters."""
    x0, y0, w, h = zone
    steps = block["steps"]
    highlight = block.get("highlight")
    n = len(steps)
    arrow_w = 420000
    box_w = (w - (n - 1) * arrow_w) // n
    box_h = 1700000
    by = y0 + (h - box_h) // 2
    out, sid = [], 360
    for i, s in enumerate(steps):
        bx = x0 + i * (box_w + arrow_w)
        hot = s["label"] == highlight
        fill = theme["accent"] if hot else theme["card"]
        out.append(_rect(sid, f"flow_box_{i + 1}", bx, by, box_w, box_h,
                         fill, geom="roundRect", adj=8000,
                         effect=CARD_SHADOW))
        sid += 1
        label_color = "FFFFFF" if hot else theme["strong"]
        detail_color = "FFFFFF" if hot else theme["grey"]
        out.append(_txt(sid, f"flow_label_{i + 1}", bx + 150000, by + 250000,
                        box_w - 300000, 450000,
                        [(s["label"], 1600, label_color, True, None)]))
        sid += 1
        if s.get("detail"):
            out.append(_txt(sid, f"flow_detail_{i + 1}", bx + 150000,
                            by + 780000, box_w - 300000, box_h - 900000,
                            [(s["detail"], 1300, detail_color, False, None)]))
            sid += 1
        if i < n - 1:
            out.append(_rect(sid, f"flow_arrow_{i + 1}",
                             bx + box_w + 90000, by + box_h // 2 - 110000,
                             arrow_w - 180000, 220000, theme["faint"],
                             geom="rightArrow"))
            sid += 1
    return "".join(out), [], []


def emit_timeline(zone, block, theme):
    """Phase bars above a spine, diamond milestones on it, optional today."""
    x0, y0, w, h = zone
    phases = block.get("phases") or []
    milestones = block.get("milestones") or []
    today = block.get("today")
    times = ([p["start"] for p in phases] + [p["end"] for p in phases]
             + [m["at"] for m in milestones]
             + ([today] if today is not None else []))
    t0, t1 = min(times), max(times)
    span = (t1 - t0) or 1

    def tx(t):
        return x0 + int(w * (t - t0) / span)

    spine_y = y0 + int(h * 0.62)
    out, sid = [], 400
    # phase bars in up to 3 greedy rows above the spine
    row_ends = []
    bar_h, row_gap = 470000, 90000
    for i, p in enumerate(phases):
        row = next((r for r, end in enumerate(row_ends)
                    if p["start"] >= end), None)
        if row is None:
            row = len(row_ends)
            row_ends.append(p["end"])
        else:
            row_ends[row] = p["end"]
        row = min(row, 2)
        py = spine_y - 350000 - (row + 1) * (bar_h + row_gap)
        px, pw = tx(p["start"]), max(tx(p["end"]) - tx(p["start"]), 200000)
        out.append(_rect(sid, f"tl_phase_{i + 1}", px, py, pw, bar_h,
                         theme["faint"], geom="roundRect", adj=16667))
        sid += 1
        out.append(_txt(sid, f"tl_phase_label_{i + 1}", px + 120000, py,
                        max(pw - 240000, 400000), bar_h,
                        [(p["label"], 1300, theme["strong"], True, None)],
                        anchor="ctr"))
        sid += 1
    out.append(_line(sid, "tl_spine", x0, spine_y, w, 0, theme["grey"],
                     width=19050))
    sid += 1
    if today is not None:
        out.append(_line(sid, "tl_today", tx(today), y0 + 200000, 0,
                         spine_y - y0 + 300000, theme["red"], width=12700))
        sid += 1
    dia = 220000
    for i, m in enumerate(milestones):
        final = bool(m.get("final"))
        mx = tx(m["at"])
        size = int(dia * 1.35) if final else dia
        out.append(_rect(sid, f"tl_ms_{i + 1}", mx - size // 2,
                         spine_y - size // 2, size, size,
                         theme["accent"] if final else theme["strong"],
                         geom="diamond"))
        sid += 1
        out.append(_txt(sid, f"tl_ms_label_{i + 1}", mx - 800000,
                        spine_y + 200000, 1600000, 600000,
                        [(m["label"], 1200, theme["ink"], final, "ctr")]))
        sid += 1
    return "".join(out), [], []


def emit_matrix(zone, block, theme):
    """2x2 positioning bubbles; accent marks the winning item(s)."""
    x0, y0, w, h = zone
    out, sid = [], 440
    for it in block["items"]:
        accent = bool(it.get("accent"))
        bw, bh = 1900000, 480000
        bx = x0 + int(w * float(it["x"])) - bw // 2
        by = y0 + int(h * (1 - float(it["y"]))) - bh // 2
        bx = max(x0, min(bx, x0 + w - bw))
        by = max(y0, min(by, y0 + h - bh))
        out.append(_rect(sid, f"mx_item_{_esc(it['label'])}", bx, by, bw, bh,
                         theme["accent"] if accent else theme["card"],
                         geom="roundRect", adj=50000,
                         effect="" if accent else CARD_SHADOW))
        sid += 1
        out.append(_txt(sid, f"mx_label_{_esc(it['label'])}", bx, by, bw, bh,
                        [(it["label"], 1300,
                          "FFFFFF" if accent else theme["ink"], accent,
                          "ctr")], anchor="ctr"))
        sid += 1
    return "".join(out), [], []


def png_size(data):
    """(w, h) from PNG IHDR or JPEG SOF; None if not recognized."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = struct.unpack(">II", data[16:24])
        return w, h
    if data[:3] == b"\xff\xd8\xff":       # JPEG: scan for a SOF marker
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return w, h
            i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    return None


def emit_image(zone, block, theme):
    """Embedded picture, aspect-fit and centered in the zone (probe-image).
    build_pptx supplies _bytes/_ext/_rid/_part; falls back to a gradient
    field when a photo has no usable bytes."""
    if not block.get("_bytes"):
        return emit_gradient_field(zone, block, theme)
    x0, y0, w, h = zone
    dims = png_size(block["_bytes"])
    if dims:
        iw, ih = dims
        scale = min(w / iw, h / ih)
        pw, ph = int(iw * scale), int(ih * scale)
    else:
        pw, ph = w, h
    px = x0 + (w - pw) // 2
    py = y0 + (h - ph) // 2
    xml = (f'<p:pic><p:nvPicPr><p:cNvPr id="500" '
           f'name="image_{_esc(block.get("alt", "exhibit"))}"/>'
           '<p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr>'
           '<p:nvPr/></p:nvPicPr>'
           f'<p:blipFill><a:blip r:embed="{block["_rid"]}"/>'
           '<a:stretch><a:fillRect/></a:stretch></p:blipFill>'
           f'<p:spPr><a:xfrm><a:off x="{px}" y="{py}"/>'
           f'<a:ext cx="{pw}" cy="{ph}"/></a:xfrm>'
           '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>')
    attribution = block.get("attribution")
    if attribution:
        xml += _txt(501, "image_attribution", px, py + ph - 300000,
                    pw - 60000, 280000,
                    [(attribution, 900, "FFFFFF", False, "r")])
    media = [(block["_part"], block["_bytes"])]
    rels = [(block["_rid"],
             f"../media/{block['_part'].rsplit('/', 1)[1]}")]
    return xml, media, rels


def emit_gradient_field(zone, block, theme):
    """Vector stand-in for a missing photo — the house gradient (probe-a)."""
    x0, y0, w, h = zone
    grad = ('<a:gradFill flip="none" rotWithShape="1"><a:gsLst>'
            f'<a:gs pos="0"><a:srgbClr val="163A5F"/></a:gs>'
            '<a:gs pos="100000"><a:srgbClr val="2E7DD1"/></a:gs>'
            '</a:gsLst><a:lin ang="2700000" scaled="1"/></a:gradFill>')
    xml = (f'<p:sp><p:nvSpPr><p:cNvPr id="500" name="gradient_field"/>'
           '<p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
           f'<p:spPr><a:xfrm><a:off x="{x0}" y="{y0}"/>'
           f'<a:ext cx="{w}" cy="{h}"/></a:xfrm>'
           '<a:prstGeom prst="roundRect"><a:avLst>'
           '<a:gd name="adj" fmla="val 4000"/></a:avLst></a:prstGeom>'
           f'{grad}<a:ln><a:noFill/></a:ln></p:spPr>'
           '<p:txBody><a:bodyPr/><a:lstStyle/>'
           '<a:p><a:endParaRPr lang="en-US"/></a:p></p:txBody></p:sp>')
    alt = block.get("alt") or block.get("query")
    if alt:
        xml += _txt(501, "gradient_field_alt", x0 + 200000,
                    y0 + h - 500000, w - 400000, 400000,
                    [(alt, 1300, "FFFFFF", False, None)])
    return xml, [], []


def make_test_png(w=320, h=240):
    """Deterministic stdlib PNG (showcase/tests only — never design output)."""
    rows = b""
    for y in range(h):
        row = b"\x00"
        for x in range(w):
            if (x // 40 + y // 40) % 2 == 0:
                row += bytes((22, 58, 95))       # navy
            else:
                row += bytes((201, 162, 39))     # gold
        rows += row

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b""))


EMITTERS = {
    "kpi_row": emit_kpi_row,
    "bars": emit_bars,
    "column": emit_column,
    "icon": emit_icon,
    "waterfall": emit_waterfall,
    "line": emit_line_chart,
    "ring": emit_ring,
    "harvey": emit_harvey,
    "flow": emit_flow,
    "timeline": emit_timeline,
    "matrix": emit_matrix,
    "image": emit_image,
    "photo": emit_image,
    "gradient_field": emit_gradient_field,
}


def emit(kind, zone, block, theme_name):
    theme = THEMES[theme_name]
    return EMITTERS[kind](zone, block, theme)
