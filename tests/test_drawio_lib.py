"""Tests for scripts/drawio_lib.py (stdlib only — pure XML, no toolkit)."""
import os
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import drawio_lib as dl  # noqa: E402

VALIDATOR = os.path.join(REPO, "scripts", "validate_drawio.py")


def sample():
    d = dl.Diagram("t")
    d.node("a", "Ingest", 40, 80)
    d.node("b", "Validate", 216, 80)
    d.node("c", "Store", 392, 40)
    d.zone("z", "Persistence", 360, 8, 200, 176, dashed=True)
    d.edge("a", "b", primary=True)
    d.edge("b", "c")
    return d


class TestDrawioLib(unittest.TestCase):
    def test_to_drawio_is_mxgraphmodel(self):
        root = ET.fromstring(sample().to_drawio())
        self.assertEqual(root.tag, "mxGraphModel")
        self.assertEqual(root.get("gridSize"), "8")
        ids = {c.get("id") for c in root.iter("mxCell")}
        self.assertTrue({"a", "b", "c", "z"} <= ids)
        edges = [c for c in root.iter("mxCell") if c.get("edge") == "1"]
        self.assertEqual(len(edges), 2)

    def test_to_svg_is_wellformed_and_labelled(self):
        svg = sample().to_svg()
        root = ET.fromstring(svg)  # raises if malformed
        self.assertTrue(root.tag.endswith("svg"))
        self.assertIn("Ingest", svg)
        self.assertIn("Persistence", svg)

    def test_duplicate_id_raises(self):
        d = dl.Diagram()
        d.node("a", "A", 0, 0)
        with self.assertRaises(ValueError):
            d.node("a", "B", 200, 0)

    def test_from_layout_builds_nodes_and_edges(self):
        layout = {"nodes": {"a": {"x": 40, "y": 80, "w": 136, "h": 56},
                            "b": {"x": 216, "y": 80, "w": 136, "h": 56}},
                  "edges": [["a", "b"]]}
        d = dl.from_layout(layout, {"a": "A", "b": "B"})
        root = ET.fromstring(d.to_drawio())
        self.assertEqual(len([c for c in root.iter("mxCell")
                              if c.get("vertex") == "1"]), 2)

    def test_from_layout_accent_path_is_root_not_alpha(self):
        # sorted layout JSON puts 'auth' (a leaf) first; the accent path must
        # still originate at the root 'gateway', not the alphabetic first node.
        layout = {"nodes": {k: {"x": 0, "y": i * 80, "w": 136, "h": 56}
                            for i, k in enumerate(["auth", "gateway", "orders"])},
                  "edges": [["gateway", "auth"], ["gateway", "orders"]]}
        d = dl.from_layout(layout, {})
        primary = [(s, t) for (s, t, _l, p, _loop) in d._edges if p]
        self.assertEqual(len(primary), 2)
        self.assertTrue(all(s == "gateway" for s, _ in primary))

    def test_zone_around_frames_placed_nodes(self):
        d = dl.Diagram()
        d.node("a", "A", 40, 80, 136, 56)
        d.node("b", "B", 240, 160, 136, 56)
        zid = d.zone_around("z", "Group", ["a", "b"])
        z = next(zz for zz in d._zones if zz[0] == zid)
        _, _, zx, zy, zw, zh, _ = z
        self.assertLessEqual(zx, 40)          # frames the left-most node
        self.assertGreaterEqual(zx + zw, 240 + 136)  # and the right-most
        self.assertLess(zy, 80)               # top padding leaves room for label

    def test_label_escaping(self):
        d = dl.Diagram()
        d.node("a", "A & B", 0, 0)
        # ampersand must be XML-safe in both serializers
        ET.fromstring(d.to_drawio())
        ET.fromstring(d.to_svg())

    def test_ortho_route_anchors_on_borders_not_through_boxes(self):
        # regresses the router fix: the polyline must start on the source
        # border and end on the target border, never route through a box.
        src, dst = (0, 0, 100, 50), (300, 0, 100, 50)  # horizontal pair
        pts = dl._ortho_route(src, dst)
        (fx, fy), (lx, ly) = pts[0], pts[-1]

        def on_border(px, py, r):
            x, y, w, h = r
            inside = x <= px <= x + w and y <= py <= y + h
            on = (px in (x, x + w)) or (py in (y, y + h))
            return inside and on

        self.assertTrue(on_border(fx, fy, src), f"start {pts[0]} not on source border")
        self.assertTrue(on_border(lx, ly, dst), f"end {pts[-1]} not on target border")
        self.assertEqual(fx, 100)  # exits source's right edge toward target
        self.assertEqual(lx, 300)  # enters target's left edge

    def test_built_diagram_passes_validator(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(lambda: subprocess.run(["rm", "-rf", tmp]))
        drawio = os.path.join(tmp, "d.drawio")
        sample().save(drawio, os.path.join(tmp, "d.svg"))
        proc = subprocess.run([sys.executable, VALIDATOR, drawio],
                              capture_output=True, text=True, timeout=30)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("DIAGRAM PASS", proc.stdout)

    def test_typed_node_shapes_and_semantic_palette(self):
        d = dl.Diagram()
        d.node("s", "", 0, 0, 40, 40, kind="start")
        d.node("a", "Do it", 80, 0, kind="action")
        d.node("g", "Met?", 280, 0, 136, 72, kind="decision")
        d.node("db", "Store", 480, 0, kind="data")
        d.node("ok", "Done", 680, 0, 120, 56, kind="success")
        xml = d.to_drawio()
        self.assertIn("rhombus", xml)
        self.assertIn("cylinder", xml)
        self.assertIn("ellipse", xml)
        self.assertIn(dl.SEM["action"][0], xml)   # blue fill
        self.assertIn(dl.SEM["success"][1], xml)  # green stroke
        svg = d.to_svg()
        self.assertIn("<polygon", svg)            # rhombus preview
        self.assertIn("<ellipse", svg)

    def test_unknown_kind_raises(self):
        with self.assertRaises(ValueError):
            dl.Diagram().node("x", "X", 0, 0, kind="bogus")

    def test_note_sublabel_in_both_serializers(self):
        d = dl.Diagram()
        d.node("a", "Api", 0, 0, kind="action", note="FastAPI")
        self.assertIn("FastAPI", d.to_drawio())
        self.assertIn("FastAPI", d.to_svg())

    def test_loop_edge_is_dashed_accent(self):
        d = dl.Diagram()
        d.node("a", "A", 0, 0)
        d.node("b", "B", 300, 0)
        d.edge("b", "a", "retry", loop=True)
        root = ET.fromstring(d.to_drawio())
        estyle = next(c.get("style") for c in root.iter("mxCell")
                      if c.get("edge") == "1")
        self.assertIn("dashed=1", estyle)
        self.assertIn(dl.TOKENS["accent"], estyle)

    def test_legend_cells_emitted(self):
        d = dl.Diagram()
        d.node("a", "A", 0, 0)
        d.legend([("action", "work step"), ("decision", "check")], 0, 200)
        xml = d.to_drawio()
        self.assertIn("legend-sw0", xml)
        self.assertIn("legend-tx1", xml)
        self.assertIn("check", d.to_svg())


if __name__ == "__main__":
    unittest.main()
