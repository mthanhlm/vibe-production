#!/usr/bin/env python3
"""Dev-time vendoring of Lucide icons into icons.json (stdlib only).

Not used at runtime. Regenerate with:
  python3 skills/slide/assets/vendor_icons.py [icon-nodes.json]

Fetches https://lucide.dev/api/icon-nodes (or reads a local copy), keeps the
curated business set below, expands SVG primitives, converts every path to
absolute M/L/C/Z commands (arcs become cubics via the W3C B.2.4 algorithm,
quadratics become cubics), and writes integer coordinates in a 24000-unit
custGeom path space. Lucide draws on a 24-unit grid but cubic CONTROL points
may overshoot it, so the grid is mapped with a 2-unit margin on each side:
  emu = round((v + 2) * 24000 / 28)
The visual icon therefore spans 24/28 of the box; emitters compensate when
sizing strokes. Icons whose converted coordinates still fall outside
[0, 24000] are dropped and reported — the package validator enforces
in-bounds points on every deck.

Licenses: Lucide is ISC (© Lucide Contributors), derived from Feather
(MIT, © Cole Bemis) — both recorded in NOTICES.md.
"""
import json
import math
import os
import re
import sys
import urllib.request

API = "https://lucide.dev/api/icon-nodes"
SPACE = 24000
SCALE = SPACE / 28.0
MARGIN = 2.0
KAPPA = 0.5522847498307936

CURATED = """
activity alarm-clock archive arrow-down arrow-down-right arrow-left
arrow-right arrow-up arrow-up-right award badge-check ban banknote
battery-charging bell bell-ring bolt book-open bookmark bot box boxes brain
briefcase bug building building-2 bus calculator calendar calendar-check
calendar-clock camera chart-area chart-bar chart-column chart-line
chart-no-axes-combined chart-pie check check-check circle-alert circle-check
circle-dollar-sign circle-minus circle-pause circle-play
circle-plus circle-x clipboard clipboard-check clipboard-list clock cloud
cloud-upload code cog coins compass construction container cpu credit-card
crown database dollar-sign door-open download earth eye eye-off factory file
file-check file-text fingerprint-pattern flag flame flask-conical folder
folder-open funnel gauge gem gift git-branch git-merge globe goal
graduation-cap
grid-2x2 hammer hand-coins handshake hard-drive headphones heart
heart-handshake hourglass house id-card image inbox infinity info key
key-round landmark laptop layers layout-dashboard leaf lightbulb link list
list-checks lock log-in log-out luggage magnet mail map map-pin medal
megaphone message-circle message-square messages-square mic milestone monitor
moon mouse-pointer network newspaper notebook package package-check palette
paperclip pause pen pencil percent phone piggy-bank pin plane play plug plus
presentation printer puzzle radar radio receipt recycle refresh-ccw
refresh-cw rocket route ruler scale scan school scissors search send server
settings share-2 shield shield-alert shield-check ship shopping-bag
shopping-cart shuffle signal smartphone smile sparkles speech split star
store sun tablet tag target terminal thermometer thumbs-down thumbs-up ticket
timer trash-2 trending-down trending-up triangle-alert trophy truck umbrella
undo lock-open upload user user-check user-plus users video wallet
wand-sparkles warehouse watch waves-horizontal webhook wifi workflow wrench x
zap zoom-in
""".split()

NUM = r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?"
TOKEN = re.compile(rf"([MmLlHhVvCcSsQqTtAaZz])|({NUM})")


def tokenize(d):
    for cmd, num in TOKEN.findall(d):
        yield (cmd, None) if cmd else (None, float(num))


def arc_to_cubics(x1, y1, rx, ry, phi_deg, large, sweep, x2, y2):
    """SVG endpoint arc -> list of cubic segments (W3C implnote B.2.4/F.6.5)."""
    if rx == 0 or ry == 0:
        return [("L", x2, y2)]
    phi = math.radians(phi_deg % 360)
    cosp, sinp = math.cos(phi), math.sin(phi)
    dx, dy = (x1 - x2) / 2.0, (y1 - y2) / 2.0
    x1p = cosp * dx + sinp * dy
    y1p = -sinp * dx + cosp * dy
    rx, ry = abs(rx), abs(ry)
    lam = (x1p / rx) ** 2 + (y1p / ry) ** 2
    if lam > 1:
        s = math.sqrt(lam)
        rx, ry = rx * s, ry * s
    num = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p
    den = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    co = math.sqrt(max(num, 0) / den) if den else 0.0
    if large == sweep:
        co = -co
    cxp = co * rx * y1p / ry
    cyp = -co * ry * x1p / rx
    cx = cosp * cxp - sinp * cyp + (x1 + x2) / 2.0
    cy = sinp * cxp + cosp * cyp + (y1 + y2) / 2.0

    def ang(ux, uy, vx, vy):
        dot = ux * vx + uy * vy
        norm = math.hypot(ux, uy) * math.hypot(vx, vy)
        a = math.acos(max(-1.0, min(1.0, dot / norm)))
        return -a if ux * vy - uy * vx < 0 else a

    t1 = ang(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dt = ang((x1p - cxp) / rx, (y1p - cyp) / ry,
             (-x1p - cxp) / rx, (-y1p - cyp) / ry) % (2 * math.pi)
    if not sweep and dt > 0:
        dt -= 2 * math.pi
    if sweep and dt < 0:
        dt += 2 * math.pi

    segs = []
    n = max(1, math.ceil(abs(dt) / (math.pi / 2)))
    delta = dt / n
    alpha = 4.0 / 3.0 * math.tan(delta / 4.0)

    def point(t):
        px = rx * math.cos(t)
        py = ry * math.sin(t)
        return (cosp * px - sinp * py + cx, sinp * px + cosp * py + cy)

    def deriv(t):
        px = -rx * math.sin(t)
        py = ry * math.cos(t)
        return (cosp * px - sinp * py, sinp * px + cosp * py)

    t = t1
    for _ in range(n):
        t_next = t + delta
        p0, p3 = point(t), point(t_next)
        d0, d3 = deriv(t), deriv(t_next)
        segs.append(("C",
                     p0[0] + alpha * d0[0], p0[1] + alpha * d0[1],
                     p3[0] - alpha * d3[0], p3[1] - alpha * d3[1],
                     p3[0], p3[1]))
        t = t_next
    return segs


def parse_path(d):
    """Absolute M/L/C/Z command list from an SVG path d string."""
    out = []
    nums = []
    cmd = None
    cx = cy = sx = sy = 0.0
    prev_cubic_ctrl = prev_quad_ctrl = None
    tokens = list(tokenize(d))
    i = 0

    def take(n):
        nonlocal i
        vals = []
        while len(vals) < n:
            c, v = tokens[i]
            i += 1
            if c is not None:
                raise ValueError(f"expected number, got command {c}")
            vals.append(v)
        return vals

    while i < len(tokens):
        c, v = tokens[i]
        if c is not None:
            cmd = c
            i += 1
        elif cmd is None:
            raise ValueError("path starts with a number")
        rel = cmd.islower()
        C = cmd.upper()
        if C == "Z":
            out.append(("Z",))
            cx, cy = sx, sy
            prev_cubic_ctrl = prev_quad_ctrl = None
            continue
        if C == "M":
            x, y = take(2)
            if rel:
                x, y = cx + x, cy + y
            out.append(("M", x, y))
            cx, cy, sx, sy = x, y, x, y
            cmd = "l" if rel else "L"   # subsequent pairs are implicit lineto
            prev_cubic_ctrl = prev_quad_ctrl = None
        elif C == "L":
            x, y = take(2)
            if rel:
                x, y = cx + x, cy + y
            out.append(("L", x, y))
            cx, cy = x, y
            prev_cubic_ctrl = prev_quad_ctrl = None
        elif C == "H":
            (x,) = take(1)
            x = cx + x if rel else x
            out.append(("L", x, cy))
            cx = x
            prev_cubic_ctrl = prev_quad_ctrl = None
        elif C == "V":
            (y,) = take(1)
            y = cy + y if rel else y
            out.append(("L", cx, y))
            cy = y
            prev_cubic_ctrl = prev_quad_ctrl = None
        elif C in ("C", "S"):
            if C == "C":
                x1, y1, x2, y2, x, y = take(6)
                if rel:
                    x1, y1, x2, y2, x, y = (cx + x1, cy + y1, cx + x2,
                                            cy + y2, cx + x, cy + y)
            else:
                x2, y2, x, y = take(4)
                if rel:
                    x2, y2, x, y = cx + x2, cy + y2, cx + x, cy + y
                if prev_cubic_ctrl:
                    x1, y1 = 2 * cx - prev_cubic_ctrl[0], 2 * cy - prev_cubic_ctrl[1]
                else:
                    x1, y1 = cx, cy
            out.append(("C", x1, y1, x2, y2, x, y))
            prev_cubic_ctrl = (x2, y2)
            prev_quad_ctrl = None
            cx, cy = x, y
        elif C in ("Q", "T"):
            if C == "Q":
                qx, qy, x, y = take(4)
                if rel:
                    qx, qy, x, y = cx + qx, cy + qy, cx + x, cy + y
            else:
                x, y = take(2)
                if rel:
                    x, y = cx + x, cy + y
                if prev_quad_ctrl:
                    qx, qy = 2 * cx - prev_quad_ctrl[0], 2 * cy - prev_quad_ctrl[1]
                else:
                    qx, qy = cx, cy
            # quadratic -> cubic
            x1, y1 = cx + 2.0 / 3.0 * (qx - cx), cy + 2.0 / 3.0 * (qy - cy)
            x2, y2 = x + 2.0 / 3.0 * (qx - x), y + 2.0 / 3.0 * (qy - y)
            out.append(("C", x1, y1, x2, y2, x, y))
            prev_quad_ctrl = (qx, qy)
            prev_cubic_ctrl = None
            cx, cy = x, y
        elif C == "A":
            rx, ry, rot, large, sweep, x, y = take(7)
            if rel:
                x, y = cx + x, cy + y
            out.extend(arc_to_cubics(cx, cy, rx, ry, rot,
                                     int(large), int(sweep), x, y))
            cx, cy = x, y
            prev_cubic_ctrl = prev_quad_ctrl = None
        else:
            raise ValueError(f"unsupported command {cmd}")
    return out


def expand_node(tag, attrs):
    """One SVG primitive -> absolute M/L/C/Z command list."""
    g = lambda k, d=0.0: float(attrs.get(k, d))
    if tag == "path":
        return parse_path(attrs["d"])
    if tag == "circle":
        cx, cy, r = g("cx"), g("cy"), g("r")
        return _ellipse_cmds(cx, cy, r, r)
    if tag == "ellipse":
        return _ellipse_cmds(g("cx"), g("cy"), g("rx"), g("ry"))
    if tag == "line":
        return [("M", g("x1"), g("y1")), ("L", g("x2"), g("y2"))]
    if tag == "polyline" or tag == "polygon":
        pts = [float(p) for p in re.split(r"[\s,]+", attrs["points"].strip())]
        pairs = list(zip(pts[0::2], pts[1::2]))
        cmds = [("M", *pairs[0])] + [("L", x, y) for x, y in pairs[1:]]
        if tag == "polygon":
            cmds.append(("Z",))
        return cmds
    if tag == "rect":
        x, y, w, h = g("x"), g("y"), g("width"), g("height")
        rx = g("rx", 0.0) or g("ry", 0.0)
        if rx <= 0:
            return [("M", x, y), ("L", x + w, y), ("L", x + w, y + h),
                    ("L", x, y + h), ("Z",)]
        rx = min(rx, w / 2, h / 2)
        k = KAPPA * rx
        return [
            ("M", x + rx, y), ("L", x + w - rx, y),
            ("C", x + w - rx + k, y, x + w, y + rx - k, x + w, y + rx),
            ("L", x + w, y + h - rx),
            ("C", x + w, y + h - rx + k, x + w - rx + k, y + h,
             x + w - rx, y + h),
            ("L", x + rx, y + h),
            ("C", x + rx - k, y + h, x, y + h - rx + k, x, y + h - rx),
            ("L", x, y + rx),
            ("C", x, y + rx - k, x + rx - k, y, x + rx, y), ("Z",),
        ]
    raise ValueError(f"unsupported node <{tag}>")


def _ellipse_cmds(cx, cy, rx, ry):
    kx, ky = KAPPA * rx, KAPPA * ry
    return [
        ("M", cx + rx, cy),
        ("C", cx + rx, cy + ky, cx + kx, cy + ry, cx, cy + ry),
        ("C", cx - kx, cy + ry, cx - rx, cy + ky, cx - rx, cy),
        ("C", cx - rx, cy - ky, cx - kx, cy - ry, cx, cy - ry),
        ("C", cx + kx, cy - ry, cx + rx, cy - ky, cx + rx, cy),
        ("Z",),
    ]


def to_grid(cmds):
    """Float 24-grid commands -> int coords in the 24000 space (2-unit
    margin folded in). Raises ValueError if anything lands out of bounds."""
    out = []
    for cmd in cmds:
        if cmd[0] == "Z":
            out.append(["Z"])
            continue
        vals = []
        for v in cmd[1:]:
            iv = round((v + MARGIN) * SCALE)
            if not 0 <= iv <= SPACE:
                raise ValueError(f"coordinate {v} outside the padded grid")
            vals.append(iv)
        out.append([cmd[0], *vals])
    return out


def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as fh:
            nodes = json.load(fh)
    else:
        with urllib.request.urlopen(API, timeout=30) as resp:
            nodes = json.load(resp)

    icons, missing, dropped = {}, [], []
    for name in CURATED:
        node = nodes.get(name)
        if node is None:
            missing.append(name)
            continue
        try:
            cmds = []
            for tag, attrs in node:
                cmds.extend(expand_node(tag, attrs))
            grid = to_grid(cmds)
            assert all(c[0] in ("M", "L", "C", "Z") for c in grid)
            icons[name] = grid
        except (ValueError, KeyError, AssertionError) as exc:
            dropped.append(f"{name}: {exc}")

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "icons.json")
    payload = {
        "_meta": {"source": API, "license": "ISC (Lucide), MIT (Feather)",
                  "space": SPACE, "grid": 24, "margin": MARGIN,
                  "count": len(icons)},
        "icons": icons,
    }
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, separators=(",", ":"), sort_keys=True)
    print(f"wrote {out_path}: {len(icons)} icons "
          f"({os.path.getsize(out_path) // 1024} KB)")
    if missing:
        print(f"missing from upstream ({len(missing)}): {' '.join(missing)}",
              file=sys.stderr)
    if dropped:
        print(f"dropped ({len(dropped)}):", file=sys.stderr)
        for line in dropped:
            print(f"  {line}", file=sys.stderr)
    return 0 if len(icons) >= 150 else 1


if __name__ == "__main__":
    sys.exit(main())
