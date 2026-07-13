#!/usr/bin/env python3
"""deck_lib.py — layout + token library for the /vibe:deck skill.

Import from a per-deck build script run with the vibe-pptx toolkit venv:
    from deck_lib import Deck, TOKENS

One accent hue, a small type scale with a single ~6x hero size, generous
margins, native-shape diagrams — the discipline distilled from the
deck-taste research (DR rules) and the reference decks (NVIDIA investor,
OpenAI whitepapers). Every value here is a design token, cited to a DR
number in references/design-system.md; change tokens there and here in
lockstep, never inline in a build script.

The companion scripts/validate_deck.py enforces the same numbers as hard
gates (DK rules) so a build that drifts off-system fails the check.
"""
from pptx import Presentation
from pptx.util import Emu, Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn


def _flatten(shape):
    """Drop the shape's <p:style> so no theme effectRef (drop shadow)
    survives — the reference decks are shadowless. fill/line are set
    explicitly by the caller, so the style ref is pure decoration."""
    style = shape._element.find(qn("p:style"))
    if style is not None:
        shape._element.remove(style)

# 16:9 at 13.333in x 7.5in (EMU). DR-0 canvas.
SLIDE_W = Emu(12192000)
SLIDE_H = Emu(6858000)

# One-accent palette (DR: palette discipline). Kept in sync with
# validate_deck.py RULES["DK-5_*"].
TOKENS = {
    "ink": RGBColor(0x1A, 0x1A, 0x2E),     # near-black, all body/titles
    "muted": RGBColor(0x6B, 0x72, 0x80),   # captions, eyebrows, sources
    "accent": RGBColor(0x2B, 0x59, 0xC3),  # the single accent hue
    "panel": RGBColor(0xF2, 0xF4, 0xF8),   # light card/panel fill
    "border": RGBColor(0xE5, 0xE7, 0xEB),  # hairline separators
    "white": RGBColor(0xFF, 0xFF, 0xFF),
}

# Type scale (DR: type scale). Body 18pt; H1:body ~= 1.9x; one hero ~= 6x.
TYPE = {
    "hero": Pt(104),    # one big number / cover payoff per slide
    "display": Pt(54),  # cover title
    "h1": Pt(34),       # assertion titles
    "eyebrow": Pt(16),  # accent so-what kicker above/below a title
    "body": Pt(18),
    "caption": Pt(14),  # floor; DK-2 min font
}

FONT = "Arial"  # neutral geometric sans; LibreOffice maps to Liberation Sans

# Layout grid (DR: margins/whitespace). Wide left margin, content column.
MARGIN = Inches(0.9)
CONTENT_W = Inches(13.333 - 1.8)  # slide width minus both margins
TITLE_Y = Inches(0.75)
BODY_Y = Inches(2.3)


class Deck:
    """Thin wrapper over a blank-layout Presentation with named helpers.

    Every helper returns the shape it created so a build script can nudge
    one thing without reaching into python-pptx internals. Text runs always
    carry an explicit font size and color (DK-2 requires both — an inherited
    theme color renders unpredictably).
    """

    def __init__(self):
        self.prs = Presentation()
        self.prs.slide_width = SLIDE_W
        self.prs.slide_height = SLIDE_H
        self._blank = self.prs.slide_layouts[6]

    def save(self, path):
        self.prs.save(path)

    def _slide(self):
        return self.prs.slides.add_slide(self._blank)

    def _text(self, slide, x, y, w, h, name, runs, align=PP_ALIGN.LEFT,
              anchor=MSO_ANCHOR.TOP):
        """runs: list of (text, size, color, bold, italic) tuples."""
        box = slide.shapes.add_textbox(x, y, w, h)
        box.name = name
        tf = box.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = anchor
        first = True
        for text, size, color, bold, italic in runs:
            para = tf.paragraphs[0] if first else tf.add_paragraph()
            para.alignment = align
            first = False
            run = para.add_run()
            run.text = text
            run.font.size = size
            run.font.name = FONT
            run.font.bold = bold
            run.font.italic = italic
            run.font.color.rgb = color
        return box

    # --- layouts ---------------------------------------------------------

    def title(self, title, subtitle=None, eyebrow=None):
        """Cover: big display title, optional accent eyebrow + subtitle."""
        s = self._slide()
        y = Inches(2.6)
        if eyebrow:
            self._text(s, MARGIN, Inches(2.0), CONTENT_W, Inches(0.5),
                       "eyebrow", [(eyebrow.upper(), TYPE["eyebrow"],
                                    TOKENS["accent"], True, False)])
        self._text(s, MARGIN, y, CONTENT_W, Inches(2.0), "title 1",
                   [(title, TYPE["display"], TOKENS["ink"], True, False)])
        if subtitle:
            self._text(s, MARGIN, Inches(4.7), CONTENT_W, Inches(0.8),
                       "subtitle", [(subtitle, TYPE["body"],
                                     TOKENS["muted"], False, False)])
        return s

    def section(self, number, title):
        """Section divider: small accent number tag + section title."""
        s = self._slide()
        self._text(s, MARGIN, Inches(2.4), CONTENT_W, Inches(0.6),
                   "eyebrow", [(number, TYPE["eyebrow"], TOKENS["accent"],
                               True, False)])
        self._text(s, MARGIN, Inches(3.0), CONTENT_W, Inches(1.6),
                   "title 1", [(title, TYPE["display"], TOKENS["ink"],
                              True, False)])
        return s

    def statement(self, text, attribution=None):
        """One large payoff line, vertically centered. The slide's anchor."""
        s = self._slide()
        self._text(s, MARGIN, Inches(1.8), CONTENT_W, Inches(3.4),
                   "statement", [(text, TYPE["h1"], TOKENS["ink"],
                                  True, False)], anchor=MSO_ANCHOR.MIDDLE)
        if attribution:
            self._text(s, MARGIN, Inches(5.6), CONTENT_W, Inches(0.6),
                       "attribution", [(attribution, TYPE["body"],
                                        TOKENS["muted"], False, True)])
        return s

    def title_body(self, title, body_lines, eyebrow=None):
        """Assertion title + up to ~4 short body lines (no bullet walls)."""
        s = self._slide()
        self._title_block(s, title, eyebrow)
        runs = []
        for line in body_lines:
            runs.append((line, TYPE["body"], TOKENS["ink"], False, False))
        self._text(s, MARGIN, BODY_Y, CONTENT_W, Inches(3.8),
                   "body", runs)
        return s

    def big_number(self, value, context, title=None, source=None):
        """One hero metric + one context line (DR: one hero per slide)."""
        s = self._slide()
        if title:
            self._title_block(s, title, None)
        self._text(s, MARGIN, Inches(2.4), CONTENT_W, Inches(2.2),
                   "hero", [(value, TYPE["hero"], TOKENS["accent"],
                            True, False)])
        self._text(s, MARGIN, Inches(4.9), CONTENT_W, Inches(1.0),
                   "context", [(context, TYPE["body"], TOKENS["ink"],
                               False, False)])
        if source:
            self._source(s, source)
        return s

    def cards(self, title, items, eyebrow=None):
        """2-4 panel cards, each a bold head + one supporting line."""
        s = self._slide()
        self._title_block(s, title, eyebrow)
        n = len(items)
        if not 2 <= n <= 4:
            raise ValueError("cards() takes 2-4 items (DR: card grid limit)")
        gap = Inches(0.4)
        total_gap = Emu(int(gap) * (n - 1))
        card_w = Emu(int((int(CONTENT_W) - int(total_gap)) / n))
        x = MARGIN
        for head, sub in items:
            card = s.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE, x, BODY_Y, card_w, Inches(2.8))
            card.name = f"card {head[:12]}"
            card.fill.solid()
            card.fill.fore_color.rgb = TOKENS["panel"]
            card.line.color.rgb = TOKENS["border"]
            card.line.width = Pt(1)
            _flatten(card)
            tf = card.text_frame
            tf.word_wrap = True
            tf.margin_left = Inches(0.3)
            tf.margin_right = Inches(0.3)
            tf.margin_top = Inches(0.3)
            p0 = tf.paragraphs[0]
            r = p0.add_run()
            r.text = head
            r.font.size = TYPE["h1"]
            r.font.name = FONT
            r.font.bold = True
            r.font.color.rgb = TOKENS["ink"]
            p1 = tf.add_paragraph()
            r = p1.add_run()
            r.text = sub
            r.font.size = TYPE["body"]
            r.font.name = FONT
            r.font.color.rgb = TOKENS["muted"]
            x = Emu(int(x) + int(card_w) + int(gap))
        return s

    def flow(self, title, steps, eyebrow=None):
        """Native-shape process diagram: 3-5 boxes joined by connectors."""
        s = self._slide()
        self._title_block(s, title, eyebrow)
        n = len(steps)
        if not 3 <= n <= 5:
            raise ValueError("flow() takes 3-5 steps (DR: connector economy)")
        box_h = Inches(1.2)
        gap = Inches(0.4)
        box_w = Emu(int((int(CONTENT_W) - int(gap) * (n - 1)) / n))
        y = Inches(3.2)
        boxes = []
        x = MARGIN
        for label in steps:
            b = s.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE, x, y, box_w, box_h)
            b.name = f"step {label[:12]}"
            b.fill.solid()
            b.fill.fore_color.rgb = TOKENS["panel"]
            b.line.color.rgb = TOKENS["accent"]
            b.line.width = Pt(1.25)
            _flatten(b)
            tf = b.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            r = p.add_run()
            r.text = label
            r.font.size = TYPE["body"]
            r.font.name = FONT
            r.font.color.rgb = TOKENS["ink"]
            boxes.append(b)
            x = Emu(int(x) + int(box_w) + int(gap))
        for a, b in zip(boxes, boxes[1:]):
            c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, 0, 0, 0, 0)
            c.begin_connect(a, 3)
            c.end_connect(b, 1)
            c.line.color.rgb = TOKENS["accent"]
            c.line.width = Pt(1.5)
            _flatten(c)  # connectors also carry a theme effectRef; kill it
        return s

    def closing(self, text, contact=None):
        """Bookend slide: short closing line, optional contact."""
        s = self._slide()
        self._text(s, MARGIN, Inches(2.8), CONTENT_W, Inches(1.6),
                   "statement", [(text, TYPE["display"], TOKENS["ink"],
                                  True, False)], anchor=MSO_ANCHOR.MIDDLE)
        if contact:
            self._text(s, MARGIN, Inches(4.6), CONTENT_W, Inches(0.6),
                       "contact", [(contact, TYPE["body"], TOKENS["accent"],
                                    False, False)])
        return s

    # --- shared chrome ---------------------------------------------------

    def _title_block(self, slide, title, eyebrow):
        if eyebrow:
            self._text(slide, MARGIN, Inches(0.75), CONTENT_W, Inches(0.45),
                       "eyebrow", [(eyebrow.upper(), TYPE["eyebrow"],
                                    TOKENS["accent"], True, False)])
            ty = Inches(1.25)
        else:
            ty = TITLE_Y
        self._text(slide, MARGIN, ty, CONTENT_W, Inches(1.0), "title 1",
                   [(title, TYPE["h1"], TOKENS["ink"], True, False)])

    def _source(self, slide, source):
        self._text(slide, MARGIN, Inches(6.7), CONTENT_W, Inches(0.4),
                   "source", [(source, TYPE["caption"], TOKENS["muted"],
                               False, True)])
