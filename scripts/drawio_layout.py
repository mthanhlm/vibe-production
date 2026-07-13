#!/usr/bin/env python3
"""drawio_layout.py — position oracle for /vibe:drawio (graphviz `dot`).

Runs `dot -Tplain` on a .dot file (or parses recorded `-Tplain` output via
--plain) and prints JSON node positions + edges for drawio_lib to style.
Pure geometry — no style knowledge; dot's own edge splines are discarded
(the drawio router restyles edges orthogonally).

    drawio_layout.py FLOW.dot          # needs `dot` on PATH
    drawio_layout.py --plain FLOW.plain # recorded output, no `dot` (CI)

Output (stdout): {"nodes": {name: {x,y,w,h}}, "edges": [[tail,head],...]}
all in pixels, top-left origin, snapped to an 8px grid, +MARGIN.
Exit: 0 ok; 1 usage error OR `dot` not on PATH (→ use the hand grid);
2 `dot` ran but failed.

Mapping (proven against `dot -Tplain`): plain is inches, y-up,
center-anchored → px_x = round(DPI*(x - w/2)); px_y flips about graph
height → round(DPI*(gh - y - h/2)); DPI=72, +MARGIN, snap all to GRID.
"""
import json
import shutil
import subprocess
import sys

DPI = 72
MARGIN = 40
GRID = 8


def _snap(v):
    return int(round(v / GRID)) * GRID


def parse_plain(text):
    """Parse `dot -Tplain` text → (nodes dict, edges list). Raises
    ValueError on malformed input (no graph line / bad node arity)."""
    graph_h = None
    nodes = {}
    edges = []
    for line in text.splitlines():
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "graph":
            # graph <scale> <width_in> <height_in>
            if len(parts) < 4:
                raise ValueError("malformed graph line")
            graph_h = float(parts[3])
        elif parts[0] == "node":
            # node <name> <x> <y> <w> <h> <label> ...
            if graph_h is None or len(parts) < 6:
                raise ValueError("node before graph, or malformed node line")
            name, x, y, w, h = parts[1], *(float(p) for p in parts[2:6])
            px_x = _snap(DPI * (x - w / 2) + MARGIN)
            px_y = _snap(DPI * (graph_h - y - h / 2) + MARGIN)
            nodes[name] = {"x": px_x, "y": px_y,
                           "w": _snap(DPI * w), "h": _snap(DPI * h)}
        elif parts[0] == "edge":
            # edge <tail> <head> <n> <coords...> ...
            if len(parts) < 3:
                raise ValueError("malformed edge line")
            edges.append([parts[1], parts[2]])
    if graph_h is None:
        raise ValueError("no graph line in plain output")
    return nodes, edges


def main(argv):
    if len(argv) == 3 and argv[1] == "--plain":
        try:
            with open(argv[2], encoding="utf-8") as f:
                text = f.read()
        except OSError as exc:
            print(f"drawio_layout: cannot read {argv[2]}: {exc}", file=sys.stderr)
            return 1
    elif len(argv) == 2 and not argv[1].startswith("-"):
        if shutil.which("dot") is None:
            print("drawio_layout: `dot` not found on PATH — use the hand "
                  "grid (skill layouts.md) or install graphviz.", file=sys.stderr)
            return 1
        try:
            proc = subprocess.run(["dot", "-Tplain", argv[1]],
                                  capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.TimeoutExpired) as exc:
            print(f"drawio_layout: dot failed: {exc}", file=sys.stderr)
            return 2
        if proc.returncode != 0:
            print(f"drawio_layout: dot exited {proc.returncode}: "
                  f"{proc.stderr.strip()}", file=sys.stderr)
            return 2
        text = proc.stdout
    else:
        print("usage: drawio_layout.py FLOW.dot | --plain FLOW.plain",
              file=sys.stderr)
        return 1

    try:
        nodes, edges = parse_plain(text)
    except ValueError as exc:
        print(f"drawio_layout: {exc}", file=sys.stderr)
        return 2
    json.dump({"nodes": nodes, "edges": edges}, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
