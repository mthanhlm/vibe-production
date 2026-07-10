#!/usr/bin/env python3
"""Graphviz layout oracle for .drawio generation (stdlib only).

Runs `dot -Tplain` on a .dot flow description and prints JSON positions
only — {"nodes": {name: {x, y, w, h}}, "edges": [[tail, head, label], ...]}
— mapped to draw.io mxGeometry pixels: `dot -Tplain` emits inches with the
origin bottom-left (y grows up) and node (x, y) at the CENTER, while
mxGeometry is pixels (1px == 1pt at 72 DPI) with the origin top-left
(y grows down) and (x, y) at the top-left corner. So with the graph height
H (inches) from the `graph` line:

    px_x = round(72 * (x - w / 2)) + MARGIN
    px_y = round(72 * (H - y - h / 2)) + MARGIN   # flip y, center -> corner

Every emitted number is then snapped to the 8px grid (DG-18). dot's edge
splines are discarded — draw.io's orthogonal router restyles edges (DG-15).
Pure layout oracle: no style knowledge.

Usage:
  drawio_layout.py FLOW.dot           # requires graphviz dot on PATH
  drawio_layout.py --plain PLAIN.txt  # parse recorded `dot -Tplain` output

Exit codes: 0 = ok, 1 = usage error or dot missing, 2 = dot failed.
"""
import json
import shlex
import shutil
import subprocess
import sys

DPI = 72     # dot -Tplain inches -> drawio px (1px == 1pt at 100% zoom)
MARGIN = 40  # DG-14 page gutter, itself a multiple of the grid
GRID = 8     # DG-18 base grid


def snap(value):
    """Snap a pixel value to the nearest multiple of the 8px grid."""
    return round(value / GRID) * GRID


def parse_plain(plain):
    """Parse `dot -Tplain` text into ({name: {x,y,w,h}}, [[tail,head,label]])."""
    nodes, edges, height_in = {}, [], 0.0
    for line in plain.splitlines():
        parts = shlex.split(line)  # node names and labels may be quoted
        if not parts:
            continue
        if parts[0] == "graph":    # graph <scale> <width> <height>
            height_in = float(parts[3])
        elif parts[0] == "node":   # node <name> <x> <y> <w> <h> <label> ...
            name = parts[1]
            x, y, w, h = map(float, parts[2:6])
            nodes[name] = {
                "x": snap(round(DPI * (x - w / 2)) + MARGIN),
                "y": snap(round(DPI * (height_in - y - h / 2)) + MARGIN),
                "w": snap(round(DPI * w)),
                "h": snap(round(DPI * h)),
            }
        elif parts[0] == "edge":   # edge <tail> <head> <n> x1 y1 ... [label lx ly] style color
            tail, head, npts = parts[1], parts[2], int(parts[3])
            rest = parts[4 + 2 * npts:]
            label = rest[0] if len(rest) > 2 else ""  # trailing style+color only
            edges.append([tail, head, label])
    return nodes, edges


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--plain":
        try:
            with open(sys.argv[2], encoding="utf-8") as f:
                plain = f.read()
        except OSError as exc:
            print(f"cannot read {sys.argv[2]}: {exc}", file=sys.stderr)
            return 1
    elif len(sys.argv) == 2 and not sys.argv[1].startswith("-"):
        if shutil.which("dot") is None:
            print("dot not found — use the DG-14 hand grid", file=sys.stderr)
            return 1
        try:
            proc = subprocess.run(
                ["dot", "-Tplain", sys.argv[1]], capture_output=True,
                text=True, timeout=30,
            )
        except subprocess.TimeoutExpired:
            print("dot timed out after 30s — use the DG-14 hand grid",
                  file=sys.stderr)
            return 2
        if proc.returncode != 0:
            print(f"dot failed ({proc.returncode}): {proc.stderr.strip()}",
                  file=sys.stderr)
            return 2
        plain = proc.stdout
    else:
        print(__doc__.strip(), file=sys.stderr)
        return 1

    try:
        nodes, edges = parse_plain(plain)
    except (ValueError, IndexError) as exc:
        print(f"malformed dot -Tplain input: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"nodes": nodes, "edges": edges}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
