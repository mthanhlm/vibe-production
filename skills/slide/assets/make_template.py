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
FONT = "Arial"

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
         bullet=None, level=0):
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
    ppr = (f'<a:pPr marL="{marl}" indent="{ind}" lvl="{level}">'
           + "".join(props) + "</a:pPr>")
    return f'<a:p>{ppr}<a:r>{rpr(size, color, bold, spc)}<a:t>{text}</a:t></a:r></a:p>'


def sp(shape_id, name, x, y, cx, cy, fill=None, paras=None, anchor="t"):
    fill_xml = (f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>'
                if fill else "<a:noFill/>")
    body = "".join(paras) if paras else '<a:p><a:endParaRPr lang="en-US"/></a:p>'
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name="{name}"/>'
            '<p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            f'{fill_xml}<a:ln><a:noFill/></a:ln></p:spPr>'
            f'<p:txBody><a:bodyPr wrap="square" anchor="{anchor}"><a:normAutofit/></a:bodyPr>'
            f'<a:lstStyle/>{body}</p:txBody></p:sp>')


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
}

SLIDE_ORDER = ["title", "exec_summary", "section", "content", "closing"]

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
    ]
    for i in range(n_slides):
        overrides.append(f'<Override PartName="/ppt/slides/slide{i + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>')
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            + "".join(overrides) + "</Types>")


ROOT_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/></Relationships>'''

CORE = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>vibe deck template</dc:title><dc:creator>vibe plugin</dc:creator></cp:coreProperties>'''

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
