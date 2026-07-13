"""Tests for scripts/validate_drawio.py (stdlib only, subprocess-level)."""
import os
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import drawio_lib as dl  # noqa: E402

VALIDATOR = os.path.join(REPO, "scripts", "validate_drawio.py")

BROKEN = """<?xml version="1.0" encoding="UTF-8"?>
<mxGraphModel gridSize="8" pageWidth="800" pageHeight="400" shadow="0">
<root>
<mxCell id="0"/>
<mxCell id="1" parent="0"/>
<mxCell id="n1" value="This label has far too many words"
 style="rounded=1;fillColor=#FF00FF;strokeColor=#1F5FA8;shadow=1;fontColor=#16283F;"
 vertex="1" parent="1"><mxGeometry x="41" y="10" width="140" height="60" as="geometry"/></mxCell>
<mxCell id="n2" value="OK"
 style="rounded=1;fillColor=#EEF2F7;strokeColor=#1F5FA8;shadow=0;fontColor=#16283F;"
 vertex="1" parent="1"><mxGeometry x="300" y="8" width="136" height="56" as="geometry"/></mxCell>
<mxCell id="e0" style="rounded=1;strokeColor=#5C6675;" edge="1" parent="1"
 source="n1" target="n2"><mxGeometry relative="1" as="geometry"/></mxCell>
</root>
</mxGraphModel>
"""


class TestValidateDrawio(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(lambda: subprocess.run(["rm", "-rf", self.tmp]))

    def _run(self, path):
        return subprocess.run([sys.executable, VALIDATOR, path],
                              capture_output=True, text=True, timeout=30)

    def _write(self, name, text):
        p = os.path.join(self.tmp, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        return p

    def test_clean_lib_diagram_passes(self):
        d = dl.Diagram()
        d.node("a", "Ingest", 40, 80)
        d.node("b", "Process", 216, 80)
        d.edge("a", "b", primary=True)
        p = os.path.join(self.tmp, "clean.drawio")
        d.save(p, os.path.join(self.tmp, "clean.svg"))
        proc = self._run(p)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("DIAGRAM PASS", proc.stdout)

    def test_broken_fails_with_expected_dl_ids(self):
        proc = self._run(self._write("bad.drawio", BROKEN))
        self.assertEqual(proc.returncode, 1)
        for rule in ("DL-2", "DL-3", "DL-4", "DL-5", "DL-6"):
            self.assertIn(rule, proc.stdout, f"{rule} missing:\n{proc.stdout}")
        # each violation names a cell id
        for line in proc.stdout.splitlines():
            self.assertTrue(line.startswith(("cell ", "diagram")), line)

    def test_too_many_nodes_flags_dl1(self):
        d = dl.Diagram()
        for i in range(13):
            d.node(f"n{i}", f"N{i}", (i % 4) * 160, (i // 4) * 80)
        p = os.path.join(self.tmp, "dense.drawio")
        d.save(p, os.path.join(self.tmp, "dense.svg"))
        proc = self._run(p)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("DL-1", proc.stdout)

    def test_overlapping_nodes_flag_dl7(self):
        d = dl.Diagram()
        d.node("a", "A", 40, 40, 136, 56)
        d.node("b", "B", 48, 48, 136, 56)  # overlaps a
        p = os.path.join(self.tmp, "ov.drawio")
        d.save(p, os.path.join(self.tmp, "ov.svg"))
        proc = self._run(p)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("DL-7", proc.stdout)

    def test_semantic_diagram_passes(self):
        # typed nodes (blue/yellow/green + start/end), a guarded loop back-edge,
        # and a legend must all validate — the semantic palette is allowed and
        # legend swatches don't count toward DL-1.
        d = dl.Diagram()
        d.node("s", "", 40, 136, 40, 40, kind="start")
        d.node("p", "Plan", 120, 128, kind="action")
        d.node("g", "Met?", 320, 120, 136, 72, kind="decision")
        d.node("ok", "Done", 560, 128, 120, 56, kind="success")
        d.edge("s", "p", primary=True)
        d.edge("p", "g", primary=True)
        d.edge("g", "ok", "yes", primary=True)
        d.edge("g", "p", "no", loop=True)
        d.legend([("action", "step"), ("decision", "check"), ("success", "done")], 40, 280)
        p = os.path.join(self.tmp, "sem.drawio")
        d.save(p, os.path.join(self.tmp, "sem.svg"))
        proc = self._run(p)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("DIAGRAM PASS", proc.stdout)

    def test_label_overflow_flags_dl8(self):
        d = dl.Diagram()
        d.node("a", "Verification", 40, 40, 64, 32, kind="action")  # too long for box
        p = os.path.join(self.tmp, "of.drawio")
        d.save(p, os.path.join(self.tmp, "of.svg"))
        proc = self._run(p)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("DL-8", proc.stdout)

    def test_legend_not_counted_toward_dl1(self):
        d = dl.Diagram()
        for i in range(12):  # exactly the DL-1 ceiling of content nodes
            d.node(f"n{i}", f"N{i}", (i % 4) * 160, (i // 4) * 80)
        d.legend([("action", "a"), ("decision", "b"), ("success", "c")], 0, 320)
        p = os.path.join(self.tmp, "leg.drawio")
        d.save(p, os.path.join(self.tmp, "leg.svg"))
        proc = self._run(p)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("DIAGRAM PASS", proc.stdout)

    def test_usage_error(self):
        proc = subprocess.run([sys.executable, VALIDATOR],
                              capture_output=True, text=True, timeout=30)
        self.assertEqual(proc.returncode, 2)


if __name__ == "__main__":
    unittest.main()
