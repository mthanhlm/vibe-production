#!/usr/bin/env python3
"""Dev-time generator for template.pptx (stdlib only). Not used at runtime.

Regenerate with:  python3 skills/slide/assets/make_template.py
Writes template.pptx next to itself. The template holds one prototype slide
per deck slide type; scripts/build_pptx.py clones them and swaps the text,
so every generated deck inherits this design unchanged (SL-13, SL-14).
"""
import os
import zipfile

# EMU geometry: 16:9 deck, generous margins (SL-14 whitespace)
W, H = 12192000, 6858000
ML = 830000                 # left/right margin
CW = W - 2 * ML             # content width

NAVY = "163A5F"   # primary
GOLD = "C9A227"   # accent
INK = "20242C"    # body text
GRAY = "6B7280"   # secondary text
MIST = "B9C6D8"   # light text on navy
HAIR = "E3E7EE"   # hairline rules
RED = "DB444B"    # negative deltas only (SL-21 semantic color)
PANEL = "F2F4F7"  # de-emphasized panel fill (before side)
GOLD_TINT = "F6F0DC"  # accent-tinted panel fill (after side)
GRAD2 = "2E7DD1"  # second gradient stop for hero/divider fields
# Shadow hex is deliberately distinct from every text color so the dark-theme
# recolor pass in build_pptx.py can remap text without touching shadows.
SHADOW = "0F1B2A"
FONT = "Arial"

GRADIENT_FILL = (f'<a:gradFill flip="none" rotWithShape="1"><a:gsLst>'
                 f'<a:gs pos="0"><a:srgbClr val="{NAVY}"/></a:gs>'
                 f'<a:gs pos="100000"><a:srgbClr val="{GRAD2}"/></a:gs>'
                 f'</a:gsLst><a:lin ang="2700000" scaled="1"/></a:gradFill>')
CARD_SHADOW = (f'<a:effectLst><a:outerShdw blurRad="190500" dist="76200" '
               f'dir="5400000" rotWithShape="0"><a:srgbClr val="{SHADOW}">'
               '<a:alpha val="25000"/></a:srgbClr></a:outerShdw></a:effectLst>')

NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"')


def rpr(size, color, bold=False, spc=None):
    battr = ' b="1"' if bold else ""
    sattr = f' spc="{spc}"' if spc else ""
    return (f'<a:rPr lang="en-US" sz="{size}"{battr}{sattr} dirty="0">'
            f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
            f'<a:latin typeface="{FONT}"/><a:cs typeface="{FONT}"/></a:rPr>')


def para(text, size, color, bold=False, spc=None, ln_spc=None, spc_bef=None,
         bullet=None, level=0, algn=None):
    """One <a:p>. bullet: None | 'square' | 'dash' (level 1)."""
    props = []
    if ln_spc:
        props.append(f'<a:lnSpc><a:spcPct val="{ln_spc}"/></a:lnSpc>')
    if spc_bef:
        props.append(f'<a:spcBef><a:spcPts val="{spc_bef}"/></a:spcBef>')
    if bullet == "square":
        marl, ind = 342900, -342900
        props.append(f'<a:buClr><a:srgbClr val="{GOLD}"/></a:buClr>'
                     f'<a:buSzPct val="70000"/><a:buFont typeface="{FONT}"/>'
                     '<a:buChar char="■"/>')
    elif bullet == "dash":
        marl, ind = 685800, -274320
        props.append(f'<a:buClr><a:srgbClr val="{GRAY}"/></a:buClr>'
                     f'<a:buFont typeface="{FONT}"/><a:buChar char="–"/>')
    else:
        marl, ind = 0, 0
        props.append("<a:buNone/>")
    algn_attr = f' algn="{algn}"' if algn else ""
    ppr = (f'<a:pPr marL="{marl}" indent="{ind}" lvl="{level}"{algn_attr}>'
           + "".join(props) + "</a:pPr>")
    return f'<a:p>{ppr}<a:r>{rpr(size, color, bold, spc)}<a:t>{text}</a:t></a:r></a:p>'


def sp(shape_id, name, x, y, cx, cy, fill=None, paras=None, anchor="t",
       geom=None, fill_xml=None, effect_xml=""):
    """One <p:sp>. geom: (preset, adj-xml) overriding the plain rect;
    fill_xml: full fill element overriding the solid/no-fill default;
    effect_xml: e.g. CARD_SHADOW. Defaults reproduce the legacy output."""
    if fill_xml is None:
        fill_xml = (f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>'
                    if fill else "<a:noFill/>")
    prst, av = geom if geom else ("rect", "<a:avLst/>")
    body = "".join(paras) if paras else '<a:p><a:endParaRPr lang="en-US"/></a:p>'
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name="{name}"/>'
            '<p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
            f'<a:prstGeom prst="{prst}">{av}</a:prstGeom>'
            f'{fill_xml}<a:ln><a:noFill/></a:ln>{effect_xml}</p:spPr>'
            f'<p:txBody><a:bodyPr wrap="square" anchor="{anchor}"><a:normAutofit/></a:bodyPr>'
            f'<a:lstStyle/>{body}</p:txBody></p:sp>')


def card(shape_id, name, x, y, cx, cy, fill="FFFFFF"):
    """White rounded card with the house soft shadow (probe-calibrated)."""
    return sp(shape_id, name, x, y, cx, cy, fill=fill,
              geom=("roundRect", '<a:avLst><a:gd name="adj" fmla="val 6000"/></a:avLst>'),
              effect_xml=CARD_SHADOW)


def slide(shapes):
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<p:sld {NS}>'
            '<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/>'
            '<p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
            '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
            '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
            + "".join(shapes) +
            '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>')


def kicker(shape_id, text):
    return sp(shape_id, "kicker", ML, 530000, CW, 360000,
              paras=[para(text, 1300, GOLD, bold=True, spc=300)])


def title_block(shape_id, text, size, color):
    return sp(shape_id, "title", ML, 940000, CW, 1150000,
              paras=[para(text, size, color, bold=True, ln_spc=105000)])


def rule(shape_id):
    return sp(shape_id, "rule", ML, 2170000, CW, 25400, fill=HAIR)


def body_block(shape_id, y, cy, sample, sub):
    return sp(shape_id, "body", ML, y, CW, cy, paras=[
        para(sample, 2000, INK, ln_spc=115000, spc_bef=1200, bullet="square"),
        para(sub, 1800, GRAY, ln_spc=115000, spc_bef=600, bullet="dash", level=1),
    ])


def footer(shape_id):
    return sp(shape_id, "footer", ML, 6350000, CW, 330000,
              paras=[para("Deck title · 1", 1100, GRAY)])


SLIDES = {
    # 1: title
    "title": slide([
        sp(2, "bg", 0, 0, W, H, fill=NAVY),
        sp(3, "accent", ML, 2280000, 1600000, 76200, fill=GOLD),
        sp(4, "title", ML, 2480000, CW, 1500000,
           paras=[para("Deck title states the single recommendation", 4000,
                       "FFFFFF", bold=True, ln_spc=105000)]),
        sp(5, "subtitle", ML, 4060000, CW, 800000,
           paras=[para("Subtitle: why this matters to the business now", 2000,
                       MIST, ln_spc=115000)]),
        sp(6, "meta", ML, 6100000, CW, 400000,
           paras=[para("2026-01-01 · Prepared for the leadership team",
                       1400, MIST)]),
    ]),
    # 2: exec_summary
    "exec_summary": slide([
        kicker(2, "EXECUTIVE SUMMARY"),
        title_block(3, "Three moves capture the opportunity this quarter",
                    2800, NAVY),
        rule(4),
        body_block(5, 2400000, 3800000,
                   "Bold claim one, stated as a full sentence with a number",
                   "Optional supporting fact for the claim above"),
        footer(6),
    ]),
    # 3: section
    "section": slide([
        sp(2, "bg", 0, 0, W, H, fill=NAVY),
        sp(3, "accent", ML, 2830000, 1600000, 76200, fill=GOLD),
        sp(4, "kicker", ML, 2340000, CW, 400000,
           paras=[para("PART ONE", 1300, GOLD, bold=True, spc=300)]),
        sp(5, "title", ML, 3030000, CW, 1500000,
           paras=[para("Section statement in one confident sentence", 3200,
                       "FFFFFF", bold=True, ln_spc=105000)]),
    ]),
    # 4: content
    "content": slide([
        kicker(2, "TOPIC"),
        title_block(3, "Action title: the takeaway of this slide in one sentence",
                    2600, NAVY),
        rule(4),
        body_block(5, 2400000, 3700000,
                   "Supporting point that proves the title",
                   "Detail only if it earns its place"),
        footer(6),
    ]),
    # 5: closing
    "closing": slide([
        kicker(2, "THE ASK"),
        title_block(3, "Decision needed: approve the next step", 2800, NAVY),
        rule(4),
        body_block(5, 2400000, 3700000,
                   "What we need, from whom, by when",
                   "What happens once approved"),
        footer(6),
    ]),
    # 6: hero_statement — hook/close at billboard scale (layout catalog #1)
    "hero_statement": slide([
        sp(2, "bg", 0, 0, W, H, fill_xml=GRADIENT_FILL),
        sp(3, "statement", ML, 2300000, CW, 1800000, anchor="ctr",
           paras=[para("One idea, stated once, at billboard scale", 7200,
                       "FFFFFF", bold=True, ln_spc=100000, algn="ctr")]),
        sp(4, "support", ML, 4300000, CW, 700000,
           paras=[para("A single quiet line of support", 2000, MIST,
                       algn="ctr")]),
    ]),
    # 7: section_divider — chapter transition (layout catalog #2)
    "section_divider": slide([
        sp(2, "bg", 0, 0, W, H, fill_xml=GRADIENT_FILL),
        sp(3, "section_no", ML, 2340000, CW, 400000,
           paras=[para("01", 1300, GOLD, bold=True, spc=300)]),
        sp(4, "title", ML, 3030000, CW, 1500000,
           paras=[para("Chapter title in a few words", 4000, "FFFFFF",
                       bold=True, ln_spc=105000)]),
    ]),
    # 8: exec_summary_3col — answer-first summary (layout catalog #3)
    "exec_summary_3col": slide([
        kicker(2, "EXECUTIVE SUMMARY"),
        title_block(3, "The recommendation, the reasons, the ask", 2800, NAVY),
        rule(4),
        card(5, "col1_card", 830000, 2400000, 3310000, 3600000),
        card(6, "col2_card", 4441000, 2400000, 3310000, 3600000),
        card(7, "col3_card", 8052000, 2400000, 3310000, 3600000),
        sp(8, "col1_head", 1080000, 2650000, 2810000, 500000,
           paras=[para("Situation", 1800, GOLD, bold=True)]),
        sp(9, "col2_head", 4691000, 2650000, 2810000, 500000,
           paras=[para("Findings", 1800, GOLD, bold=True)]),
        sp(10, "col3_head", 8302000, 2650000, 2810000, 500000,
           paras=[para("Recommendation", 1800, GOLD, bold=True)]),
        sp(11, "col1_body", 1080000, 3250000, 2810000, 2600000,
           paras=[para("Up to five short lines", 1800, INK, ln_spc=115000,
                       spc_bef=600)]),
        sp(12, "col2_body", 4691000, 3250000, 2810000, 2600000,
           paras=[para("Up to five short lines", 1800, INK, ln_spc=115000,
                       spc_bef=600)]),
        sp(13, "col3_body", 8302000, 3250000, 2810000, 2600000,
           paras=[para("Up to five short lines", 1800, INK, ln_spc=115000,
                       spc_bef=600)]),
        footer(14),
    ]),
    # 9: big_number — one metric IS the story (layout catalog #4)
    "big_number": slide([
        kicker(2, "THE NUMBER"),
        sp(3, "metric", ML, 2050000, CW, 2300000, anchor="ctr",
           paras=[para("34,000", 12000, NAVY, bold=True, algn="ctr")]),
        sp(4, "context", ML, 4500000, CW, 800000,
           paras=[para("A line that makes the number human", 2000, GRAY,
                       algn="ctr")]),
        sp(5, "source", ML, 5950000, CW, 300000,
           paras=[para("Source: internal data (2026)", 1100, GRAY)]),
        footer(6),
    ]),
    # 10: before_after — transformation contrast (layout catalog #8)
    "before_after": slide([
        kicker(2, "THE CHANGE"),
        title_block(3, "What changes, side by side", 2600, NAVY),
        rule(4),
        sp(5, "left_panel", 830000, 2400000, 4866000, 3600000, fill=PANEL,
           geom=("roundRect", '<a:avLst><a:gd name="adj" fmla="val 6000"/></a:avLst>')),
        card(6, "right_panel", 6496000, 2400000, 4866000, 3600000,
             fill=GOLD_TINT),
        sp(7, "divider_arrow", 5796000, 4000000, 600000, 400000, fill=GOLD,
           geom=("rightArrow", "<a:avLst/>")),
        sp(8, "left_head", 1080000, 2650000, 4366000, 500000,
           paras=[para("Before", 1800, GRAY, bold=True)]),
        sp(9, "left_body", 1080000, 3250000, 4366000, 2600000,
           paras=[para("Mirrored attribute, plainly stated", 1800, GRAY,
                       ln_spc=115000, spc_bef=600)]),
        sp(10, "right_head", 6746000, 2650000, 4366000, 500000,
           paras=[para("After", 1800, NAVY, bold=True)]),
        sp(11, "right_body", 6746000, 3250000, 4366000, 2600000,
           paras=[para("Mirrored attribute, plainly stated", 1800, INK,
                       ln_spc=115000, spc_bef=600)]),
        sp(12, "source", ML, 6020000, CW, 280000,
           paras=[para("", 1100, GRAY)]),
        footer(13),
    ]),
    # 11: quote_evidence — qualitative proof (layout catalog #11)
    "quote_evidence": slide([
        sp(2, "quote_glyph", 780000, 1250000, 1800000, 1800000,
           paras=[para("“", 12000, GOLD, bold=True)]),
        sp(3, "quote", 1430000, 2500000, 9330000, 2300000,
           paras=[para("A short quotation that carries a number does the "
                       "arguing for you.", 3200, NAVY, ln_spc=110000)]),
        sp(4, "attribution", 1430000, 5000000, 9330000, 500000,
           paras=[para("— Customer name, role", 1600, GRAY)]),
        footer(5),
    ]),
    # 12: kpi_strip — status check-in tiles (layout catalog #5; tiles emitted)
    "kpi_strip": slide([
        kicker(2, "STATUS"),
        title_block(3, "The quarter at a glance, then the two things to fix",
                    2600, NAVY),
        rule(4),
        sp(5, "source", ML, 6020000, CW, 280000,
           paras=[para("", 1100, GRAY)]),
        footer(6),
    ]),
    # 13: chart_takeaway — one exhibit + insight callout (catalog #6;
    # the chart itself is emitted into the left two-thirds)
    "chart_takeaway": slide([
        kicker(2, "EVIDENCE"),
        title_block(3, "The takeaway stated as a sentence, proven at left",
                    2600, NAVY),
        rule(4),
        card(5, "callout_card", 7900000, 2400000, 3462000, 3500000),
        sp(6, "callout_head", 8150000, 2650000, 2962000, 500000,
           paras=[para("So what", 1800, GOLD, bold=True)]),
        sp(7, "callout_body", 8150000, 3250000, 2962000, 2400000,
           paras=[para("Three to five short lines", 1800, INK,
                       ln_spc=115000, spc_bef=600)]),
        sp(8, "source", ML, 6020000, CW, 280000,
           paras=[para("Source: internal data (2026)", 1100, GRAY)]),
        footer(9),
    ]),
    # 14: three_cards — solution pillars (catalog #7; icons emitted above heads)
    "three_cards": slide([
        kicker(2, "THE SOLUTION"),
        title_block(3, "Three moves deliver the outcome", 2600, NAVY),
        rule(4),
        card(5, "card1", 830000, 2400000, 3310000, 3600000),
        card(6, "card2", 4441000, 2400000, 3310000, 3600000),
        card(7, "card3", 8052000, 2400000, 3310000, 3600000),
        sp(8, "card1_head", 1080000, 3700000, 2810000, 500000,
           paras=[para("Pillar one", 2000, NAVY, bold=True)]),
        sp(9, "card2_head", 4691000, 3700000, 2810000, 500000,
           paras=[para("Pillar two", 2000, NAVY, bold=True)]),
        sp(10, "card3_head", 8302000, 3700000, 2810000, 500000,
           paras=[para("Pillar three", 2000, NAVY, bold=True)]),
        sp(11, "card1_line", 1080000, 4300000, 2810000, 1400000,
           paras=[para("One line that earns the pillar", 1800, GRAY,
                       ln_spc=115000)]),
        sp(12, "card2_line", 4691000, 4300000, 2810000, 1400000,
           paras=[para("One line that earns the pillar", 1800, GRAY,
                       ln_spc=115000)]),
        sp(13, "card3_line", 8302000, 4300000, 2810000, 1400000,
           paras=[para("One line that earns the pillar", 1800, GRAY,
                       ln_spc=115000)]),
        footer(14),
    ]),
    # 15: process_flow — how-it-works steps (catalog #9; steps emitted)
    "process_flow": slide([
        kicker(2, "HOW IT WORKS"),
        title_block(3, "Five steps or fewer, and where the magic happens",
                    2600, NAVY),
        rule(4),
        sp(5, "source", ML, 6020000, CW, 280000,
           paras=[para("", 1100, GRAY)]),
        footer(6),
    ]),
    # 16: timeline_roadmap — phases, milestones, today-line (catalog #10;
    # everything on the spine is emitted)
    "timeline_roadmap": slide([
        kicker(2, "ROADMAP"),
        title_block(3, "What ships when, and the decision points",
                    2600, NAVY),
        rule(4),
        sp(5, "source", ML, 6020000, CW, 280000,
           paras=[para("", 1100, GRAY)]),
        footer(6),
    ]),
    # 17: matrix_2x2 — positioning field (catalog #12; item bubbles emitted).
    # Plot: x=1830000 y=2400000 w=8500000 h=3200000, axes cross mid-plot.
    "matrix_2x2": slide([
        kicker(2, "THE TRADE-OFF"),
        title_block(3, "Where the options land on the two axes that matter",
                    2600, NAVY),
        rule(4),
        sp(5, "plot_field", 1830000, 2400000, 8500000, 3200000, fill=PANEL,
           geom=("roundRect", '<a:avLst><a:gd name="adj" fmla="val 3000"/></a:avLst>')),
        sp(6, "axis_v", 6073650, 2400000, 12700, 3200000, fill=GRAY),
        sp(7, "axis_h", 1830000, 3993650, 8500000, 12700, fill=GRAY),
        sp(8, "y_label", 1980000, 2480000, 4000000, 280000,
           paras=[para("Vertical axis: low to high", 1200, GRAY)]),
        sp(9, "x_label", 6130000, 5660000, 4050000, 240000,
           paras=[para("Horizontal axis: low to high", 1200, GRAY,
                       algn="r")]),
        sp(10, "q1_label", 1980000, 2800000, 3900000, 280000,
           paras=[para("", 1100, GRAY)]),
        sp(11, "q2_label", 6180000, 2800000, 3950000, 280000,
           paras=[para("", 1100, GRAY, algn="r")]),
        sp(12, "q3_label", 1980000, 5220000, 3900000, 280000,
           paras=[para("", 1100, GRAY)]),
        sp(13, "q4_label", 6180000, 5220000, 3950000, 280000,
           paras=[para("", 1100, GRAY, algn="r")]),
        footer(14),
    ]),
}

SLIDE_ORDER = ["title", "exec_summary", "section", "content", "closing",
               # v2 archetypes — append-only: legacy indices 1-5 never move
               "hero_statement", "section_divider", "exec_summary_3col",
               "big_number", "before_after", "quote_evidence",
               "kpi_strip", "chart_takeaway", "three_cards",
               "process_flow", "timeline_roadmap", "matrix_2x2"]

THEME = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Vibe">
<a:themeElements>
<a:clrScheme name="Vibe"><a:dk1><a:srgbClr val="{INK}"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="{NAVY}"/></a:dk2><a:lt2><a:srgbClr val="F2F4F7"/></a:lt2><a:accent1><a:srgbClr val="{GOLD}"/></a:accent1><a:accent2><a:srgbClr val="2C7A7B"/></a:accent2><a:accent3><a:srgbClr val="{GRAY}"/></a:accent3><a:accent4><a:srgbClr val="B85450"/></a:accent4><a:accent5><a:srgbClr val="82B366"/></a:accent5><a:accent6><a:srgbClr val="6C8EBF"/></a:accent6><a:hlink><a:srgbClr val="2C7A7B"/></a:hlink><a:folHlink><a:srgbClr val="{GRAY}"/></a:folHlink></a:clrScheme>
<a:fontScheme name="Vibe"><a:majorFont><a:latin typeface="{FONT}"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont><a:minorFont><a:latin typeface="{FONT}"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont></a:fontScheme>
<a:fmtScheme name="Office"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln><a:ln w="19050"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln><a:ln w="28575"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme>
</a:themeElements></a:theme>'''

MASTER = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster {NS}>
<p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill><a:effectLst/></p:bgPr></p:bg>
<p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
</p:spTree></p:cSld>
<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
<p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles>
</p:sldMaster>'''

LAYOUT = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout {NS} type="blank">
<p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>'''


def presentation(n_slides):
    sld_ids = "".join(
        f'<p:sldId id="{256 + i}" r:id="rId{2 + i}"/>' for i in range(n_slides))
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<p:presentation {NS}>'
            '<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>'
            f'<p:sldIdLst>{sld_ids}</p:sldIdLst>'
            f'<p:sldSz cx="{W}" cy="{H}"/><p:notesSz cx="6858000" cy="9144000"/>'
            '</p:presentation>')


def presentation_rels(n_slides):
    rels = ['<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>']
    for i in range(n_slides):
        rels.append(f'<Relationship Id="rId{2 + i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i + 1}.xml"/>')
    rels.append(f'<Relationship Id="rId{2 + n_slides}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>')
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            + "".join(rels) + "</Relationships>")


def content_types(n_slides):
    overrides = [
        '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>',
        '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>',
        '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>',
        '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>',
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>',
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>',
    ]
    for i in range(n_slides):
        overrides.append(f'<Override PartName="/ppt/slides/slide{i + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>')
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            + "".join(overrides) + "</Types>")


ROOT_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/></Relationships>'''

CORE = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>vibe deck template</dc:title><dc:creator>vibe plugin</dc:creator></cp:coreProperties>'''

APP = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"><Application>vibe plugin</Application></Properties>'''

SLIDE_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/></Relationships>'''

MASTER_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/></Relationships>'''

LAYOUT_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/></Relationships>'''


def main():
    n = len(SLIDE_ORDER)
    parts = {
        "[Content_Types].xml": content_types(n),
        "_rels/.rels": ROOT_RELS,
        "docProps/core.xml": CORE,
        "docProps/app.xml": APP,
        "ppt/presentation.xml": presentation(n),
        "ppt/_rels/presentation.xml.rels": presentation_rels(n),
        "ppt/theme/theme1.xml": THEME,
        "ppt/slideMasters/slideMaster1.xml": MASTER,
        "ppt/slideMasters/_rels/slideMaster1.xml.rels": MASTER_RELS,
        "ppt/slideLayouts/slideLayout1.xml": LAYOUT,
        "ppt/slideLayouts/_rels/slideLayout1.xml.rels": LAYOUT_RELS,
    }
    for i, key in enumerate(SLIDE_ORDER):
        parts[f"ppt/slides/slide{i + 1}.xml"] = SLIDES[key]
        parts[f"ppt/slides/_rels/slide{i + 1}.xml.rels"] = SLIDE_RELS

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.pptx")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in parts.items():
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, data)
    print(f"wrote {out} ({n} prototype slides: {', '.join(SLIDE_ORDER)})")


if __name__ == "__main__":
    main()
