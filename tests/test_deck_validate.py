"""Tests for scripts/validate_deck.py — run through a pptx-capable python.

Resolution order for the interpreter: the vibe-pptx toolkit venv if
present, else the current python when it can import pptx (CI installs
python-pptx), else the whole module is skipped cleanly. The validator is
always exercised as a subprocess, never imported.
"""
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VALIDATOR = os.path.join(REPO, "scripts", "validate_deck.py")
VENV_PY = os.path.expanduser(
    os.path.join(os.environ.get("VIBE_PPTX_DIR", "~/.claude/vibe-pptx"),
                 "bin", "python"))


def _pptx_python():
    if os.path.exists(VENV_PY):
        return VENV_PY
    probe = subprocess.run([sys.executable, "-c", "import pptx"],
                           capture_output=True)
    return sys.executable if probe.returncode == 0 else None


PPTX_PY = _pptx_python()

GOOD_DECK = """
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
prs = Presentation()
prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)
s = prs.slides.add_slide(prs.slide_layouts[6])
tb = s.shapes.add_textbox(Inches(0.9), Inches(0.8), Inches(11), Inches(1.2))
tb.name = "title 1"
r = tb.text_frame.paragraphs[0].add_run(); r.text = "Revenue doubled in one quarter"
r.font.size = Pt(36); r.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)
b = s.shapes.add_textbox(Inches(0.9), Inches(2.4), Inches(11), Inches(2))
r = b.text_frame.paragraphs[0].add_run(); r.text = "Six words of supporting body text"
r.font.size = Pt(18); r.font.color.rgb = RGBColor(0x40, 0x40, 0x40)
prs.save(OUT)
"""

BAD_DECK = """
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
prs = Presentation()
prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)
s = prs.slides.add_slide(prs.slide_layouts[6])
# DK-2: tiny font; DK-5: off-palette color; DK-1: word wall
tb = s.shapes.add_textbox(Inches(0.9), Inches(0.8), Inches(11), Inches(4))
r = tb.text_frame.paragraphs[0].add_run()
r.text = " ".join(["filler"] * 200)
r.font.size = Pt(9); r.font.color.rgb = RGBColor(0xFF, 0x00, 0xFF)
# DK-3: off-slide shape
off = s.shapes.add_textbox(Inches(15), Inches(1), Inches(3), Inches(1))
r2 = off.text_frame.paragraphs[0].add_run(); r2.text = "off slide"
r2.font.size = Pt(18)
# DK-4: two overlapping text boxes
o1 = s.shapes.add_textbox(Inches(1), Inches(5), Inches(4), Inches(1))
r3 = o1.text_frame.paragraphs[0].add_run(); r3.text = "overlap one"
r3.font.size = Pt(18)
o2 = s.shapes.add_textbox(Inches(1.5), Inches(5.2), Inches(4), Inches(1))
r4 = o2.text_frame.paragraphs[0].add_run(); r4.text = "overlap two"
r4.font.size = Pt(18)
prs.save(OUT)
"""


# Exercises every deck_lib layout, incl. flow() at its documented n=5 max
# (regresses a real dogfood bug: hard-coded box width overflowed the content
# column at 5 steps → DK-4 overlap). Also asserts NO shape keeps a <p:style>
# (regresses the connector drop-shadow: theme effectRef must be flattened).
FULL_DECK = """
import sys
sys.path.insert(0, PLUGIN_SCRIPTS)
from deck_lib import Deck
from pptx.oxml.ns import qn
d = Deck()
d.title("Cover assertion here", subtitle="sub", eyebrow="Internal")
d.section("01", "Section label")
d.big_number("92%", "of revenue is repeat customers",
             title="Loyalty carries the business", source="Source: internal")
d.title_body("Three forces point the same way",
             ["Two of four sites hit capacity daily.",
              "Catering has a standing waitlist."], eyebrow="Demand")
d.cards("What changes", [("A", "one"), ("B", "two"), ("C", "three")])
d.flow("How a location opens",
       ["Scout", "Lease", "Fit-out", "Hire", "Launch"], eyebrow="Process")
d.statement("We can open three locations in 2026 from cash flow.")
d.closing("Questions?", contact="ops@example.com")
d.save(OUT)
# shadow regression: every deck_lib shape is flattened, so no slide keeps a style ref
styles = 0
for slide in d.prs.slides:
    styles += len(slide._element.findall('.//' + qn('p:style')))
if styles:
    sys.exit("REGRESSION: %d <p:style> survived (drop-shadow)" % styles)
"""


@unittest.skipUnless(PPTX_PY, "no python-pptx interpreter available")
class TestDeckLib(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="vibe-decklib-test.")
        self.addCleanup(lambda: subprocess.run(["rm", "-rf", self.tmp]))

    def test_full_deck_all_layouts_valid_and_shadowless(self):
        out = os.path.join(self.tmp, "full.pptx")
        script = (f"OUT = {out!r}\nPLUGIN_SCRIPTS = "
                  f"{os.path.join(REPO, 'scripts')!r}\n" + textwrap.dedent(FULL_DECK))
        built = subprocess.run([PPTX_PY, "-c", script],
                               capture_output=True, text=True, timeout=60)
        self.assertEqual(built.returncode, 0, built.stderr)  # incl. shadow regression
        validated = subprocess.run([PPTX_PY, VALIDATOR, out],
                                   capture_output=True, text=True, timeout=60)
        self.assertEqual(validated.returncode, 0,
                         "flow(n=5) overlap regressed?\n" + validated.stdout)
        self.assertIn("DECK PASS", validated.stdout)


@unittest.skipUnless(PPTX_PY, "no python-pptx interpreter available")
class TestValidateDeck(unittest.TestCase):
    def _build(self, body, name):
        path = os.path.join(self.tmp, name)
        script = f"OUT = {path!r}\n" + textwrap.dedent(body)
        proc = subprocess.run([PPTX_PY, "-c", script],
                              capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return path

    def _validate(self, deck):
        return subprocess.run([PPTX_PY, VALIDATOR, deck],
                              capture_output=True, text=True, timeout=60)

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="vibe-deck-test.")
        self.addCleanup(lambda: subprocess.run(["rm", "-rf", self.tmp]))

    def test_clean_deck_passes(self):
        proc = self._validate(self._build(GOOD_DECK, "good.pptx"))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("DECK PASS", proc.stdout)

    def test_broken_deck_fails_with_rule_ids(self):
        proc = self._validate(self._build(BAD_DECK, "bad.pptx"))
        self.assertEqual(proc.returncode, 1)
        for rule in ("DK-1", "DK-2", "DK-3", "DK-4", "DK-5"):
            self.assertIn(rule, proc.stdout, f"{rule} missing:\n{proc.stdout}")
        self.assertTrue(all("slide 1:" in l for l in
                            proc.stdout.splitlines() if l.startswith("slide")))

    def test_usage_error(self):
        proc = subprocess.run([PPTX_PY, VALIDATOR],
                              capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 2)

    def test_colored_connector_not_palette_flagged(self):
        # Regresses the _is_connector exemption: an accent-line connector
        # must be skipped by the palette/bounds checks, not flagged.
        deck = """
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
prs = Presentation()
prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)
s = prs.slides.add_slide(prs.slide_layouts[6])
a = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1), Inches(3), Inches(2), Inches(1))
a.fill.solid(); a.fill.fore_color.rgb = RGBColor(0xF2,0xF4,0xF8); a.line.color.rgb = RGBColor(0x2B,0x59,0xC3)
b = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6), Inches(3), Inches(2), Inches(1))
b.fill.solid(); b.fill.fore_color.rgb = RGBColor(0xF2,0xF4,0xF8); b.line.color.rgb = RGBColor(0x2B,0x59,0xC3)
c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, 0, 0, 0, 0)
c.begin_connect(a, 3); c.end_connect(b, 1); c.line.color.rgb = RGBColor(0x2B,0x59,0xC3)
prs.save(OUT)
"""
        proc = self._validate(self._build(deck, "conn.pptx"))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_tiny_overlap_within_tolerance_passes(self):
        # ~0.5% sq-in sliver overlap must pass DK-4 (regresses the old
        # 100x-too-strict tolerance that hard-failed sub-pixel touches).
        deck = """
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
prs = Presentation()
prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)
s = prs.slides.add_slide(prs.slide_layouts[6])
a = s.shapes.add_textbox(Inches(1), Inches(3), Inches(3), Inches(1))
r = a.text_frame.paragraphs[0].add_run(); r.text = "box a"; r.font.size = Pt(18); r.font.color.rgb = RGBColor(0x1A,0x1A,0x2E)
b = s.shapes.add_textbox(Inches(3.95), Inches(3.9), Inches(3), Inches(0.5))
r = b.text_frame.paragraphs[0].add_run(); r.text = "box b"; r.font.size = Pt(18); r.font.color.rgb = RGBColor(0x1A,0x1A,0x2E)
prs.save(OUT)
"""
        proc = self._validate(self._build(deck, "sliver.pptx"))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_missing_font_color_flagged_dk2(self):
        deck = """
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
prs = Presentation()
prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)
s = prs.slides.add_slide(prs.slide_layouts[6])
tb = s.shapes.add_textbox(Inches(1), Inches(1), Inches(6), Inches(1))
r = tb.text_frame.paragraphs[0].add_run(); r.text = "no explicit color"
r.font.size = Pt(20)  # size set, color left inherited
prs.save(OUT)
"""
        proc = self._validate(self._build(deck, "nocolor.pptx"))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("DK-2", proc.stdout)
        self.assertIn("font color", proc.stdout)


if __name__ == "__main__":
    unittest.main()
