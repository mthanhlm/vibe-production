"""Tests for scripts/drawio_layout.py (stdlib only, subprocess-level).

The oracle is pure geometry, so --plain against a recorded fixture is fully
CI-testable without graphviz; a dot-missing case proves the exit-1 hand-grid
fallback. dot-present end-to-end is guarded by shutil.which.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, "scripts", "drawio_layout.py")
FIXTURE = os.path.join(REPO, "tests", "fixtures", "flow.plain")


def run(args, path_override=None, timeout=30):
    env = dict(os.environ)
    if path_override is not None:
        env["PATH"] = path_override
    proc = subprocess.run([sys.executable, SCRIPT, *args],
                          capture_output=True, text=True, env=env, timeout=timeout)
    return proc.returncode, proc.stdout, proc.stderr


class TestDrawioLayout(unittest.TestCase):
    def test_plain_fixture_positions_exact_and_on_grid(self):
        rc, out, err = run(["--plain", FIXTURE])
        self.assertEqual(rc, 0, err)
        data = json.loads(out)
        # y-flipped, center→corner, snapped: ingest is the left/top-most box
        self.assertEqual(data["nodes"]["ingest"], {"x": 40, "y": 80, "w": 136, "h": 56})
        self.assertEqual(data["nodes"]["validate"]["x"], 216)
        # every coordinate is a multiple of the 8px grid
        for n in data["nodes"].values():
            for k in ("x", "y", "w", "h"):
                self.assertEqual(n[k] % 8, 0, f"{k}={n[k]} off-grid")
        self.assertIn(["ingest", "validate"], data["edges"])
        self.assertEqual(len(data["edges"]), 3)

    def test_dot_missing_exits_1_with_handgrid_hint(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        os.symlink(sys.executable, os.path.join(tmp, "python3"))
        # a .dot arg with no `dot` on PATH → exit 1, not a crash
        dot = os.path.join(tmp, "x.dot")
        with open(dot, "w", encoding="utf-8") as f:
            f.write("digraph{a->b}")
        rc, _, err = run([dot], path_override=tmp)
        self.assertEqual(rc, 1)
        self.assertIn("hand grid", err)

    def test_usage_error(self):
        rc, _, err = run([])
        self.assertEqual(rc, 1)
        self.assertIn("usage", err)

    def test_malformed_plain_exits_2(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        bad = os.path.join(tmp, "bad.plain")
        with open(bad, "w", encoding="utf-8") as f:
            f.write("node a 1 2\n")  # node before any graph line
        rc, _, err = run(["--plain", bad])
        self.assertEqual(rc, 2)

    @unittest.skipUnless(shutil.which("dot"), "graphviz `dot` not installed")
    def test_live_dot_matches_recorded_plain(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        dot = os.path.join(tmp, "flow.dot")
        with open(dot, "w", encoding="utf-8") as f:
            f.write("digraph { rankdir=LR; "
                    "node[shape=box, fixedsize=true, width=1.9444, height=0.8333]; "
                    "ingest -> validate; validate -> store; validate -> alert; }")
        rc_live, out_live, _ = run([dot])
        rc_rec, out_rec, _ = run(["--plain", FIXTURE])
        self.assertEqual(rc_live, 0)
        self.assertEqual(json.loads(out_live), json.loads(out_rec))


if __name__ == "__main__":
    unittest.main()
