#!/usr/bin/env python3
"""Validate a .pptx package for PowerPoint compatibility (stdlib only).

LibreOffice opening a deck does NOT prove PowerPoint will: PowerPoint enforces
OPC and DrawingML rules that LibreOffice forgives, and PowerPoint for the web
has no repair path at all. This validator asserts the rules hand-built
packages most often break, so no deck is delivered on hope (WA-2).

Usage:
  validate_pptx.py DECK.pptx

Exit codes: 0 clean (warnings allowed), 1 usage/IO error, 2 findings.
Findings print to stdout one per line as "check-id: message"; warnings print
to stderr as "warning: check-id: message".
"""
import posixpath
import sys
import xml.etree.ElementTree as ET
import zipfile

NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS_P = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_CT = "http://schemas.openxmlformats.org/package/2006/content-types"
NS_PR = "http://schemas.openxmlformats.org/package/2006/relationships"

EMU_MAX = 2147483647          # ST_Coordinate bound (signed 32-bit)
SLDSZ_MIN, SLDSZ_MAX = 914400, 51206400

# Relationship-reference attributes that must resolve in the part's rels.
R_ATTRS = {f"{{{NS_R}}}{local}" for local in
           ("id", "embed", "link", "pict", "dm", "lo", "qs", "cs")}

# ECMA-376 ST_ShapeType — the complete preset-geometry vocabulary. Anything
# else ("oval", "roundedRectangle", ...) triggers a PowerPoint repair prompt.
PRESET_SHAPES = frozenset("""
accentBorderCallout1 accentBorderCallout2 accentBorderCallout3 accentCallout1
accentCallout2 accentCallout3 actionButtonBackPrevious actionButtonBeginning
actionButtonBlank actionButtonDocument actionButtonEnd actionButtonForwardNext
actionButtonHelp actionButtonHome actionButtonInformation actionButtonMovie
actionButtonReturn actionButtonSound arc bentArrow bentConnector2
bentConnector3 bentConnector4 bentConnector5 bentUpArrow bevel blockArc
borderCallout1 borderCallout2 borderCallout3 bracePair bracketPair callout1
callout2 callout3 can chartPlus chartStar chartX chevron chord circularArrow
cloud cloudCallout corner cornerTabs cube curvedConnector2 curvedConnector3
curvedConnector4 curvedConnector5 curvedDownArrow curvedLeftArrow
curvedRightArrow curvedUpArrow decagon diagStripe diamond dodecagon donut
doubleWave downArrow downArrowCallout ellipse ellipseRibbon ellipseRibbon2
flowChartAlternateProcess flowChartCollate flowChartConnector flowChartDecision
flowChartDelay flowChartDisplay flowChartDocument flowChartExtract
flowChartInputOutput flowChartInternalStorage flowChartMagneticDisk
flowChartMagneticDrum flowChartMagneticTape flowChartManualInput
flowChartManualOperation flowChartMerge flowChartMultidocument
flowChartOfflineStorage flowChartOffpageConnector flowChartOnlineStorage
flowChartOr flowChartPredefinedProcess flowChartPreparation flowChartProcess
flowChartPunchedCard flowChartPunchedTape flowChartSort
flowChartSummingJunction flowChartTerminator foldedCorner frame funnel gear6
gear9 halfFrame heart heptagon hexagon homePlate horizontalScroll
irregularSeal1 irregularSeal2 leftArrow leftArrowCallout leftBrace leftBracket
leftCircularArrow leftRightArrow leftRightArrowCallout leftRightCircularArrow
leftRightRibbon leftRightUpArrow leftUpArrow lightningBolt line lineInv
mathDivide mathEqual mathMinus mathMultiply mathNotEqual mathPlus moon
nonIsoscelesTrapezoid noSmoking notchedRightArrow octagon parallelogram
pentagon pie pieWedge plaque plaqueTabs plus quadArrow quadArrowCallout rect
ribbon ribbon2 rightArrow rightArrowCallout rightBrace rightBracket round1Rect
round2DiagRect round2SameRect roundRect rtTriangle smileyFace snip1Rect
snip2DiagRect snip2SameRect snipRoundRect squareTabs star10 star12 star16
star24 star32 star4 star5 star6 star7 star8 straightConnector1
stripedRightArrow sun swooshArrow teardrop trapezoid triangle upArrow
upArrowCallout upDownArrow upDownArrowCallout uturnArrow verticalScroll wave
wedgeEllipseCallout wedgeRectCallout wedgeRoundRectCallout
""".split())

# Media magic bytes per extension (extensions we ever emit).
MEDIA_MAGIC = {
    "png": (b"\x89PNG\r\n\x1a\n",),
    "jpeg": (b"\xff\xd8\xff",),
    "jpg": (b"\xff\xd8\xff",),
    "gif": (b"GIF87a", b"GIF89a"),
}

# Element-order vocabularies (relative order of the children that appear).
SP_ORDER = [f"{{{NS_P}}}nvSpPr", f"{{{NS_P}}}spPr", f"{{{NS_P}}}style",
            f"{{{NS_P}}}txBody"]
PIC_ORDER = [f"{{{NS_P}}}nvPicPr", f"{{{NS_P}}}blipFill", f"{{{NS_P}}}spPr"]
SPPR_ORDER = [
    f"{{{NS_A}}}xfrm",
    f"{{{NS_A}}}custGeom", f"{{{NS_A}}}prstGeom",
    f"{{{NS_A}}}noFill", f"{{{NS_A}}}solidFill", f"{{{NS_A}}}gradFill",
    f"{{{NS_A}}}blipFill", f"{{{NS_A}}}pattFill", f"{{{NS_A}}}grpFill",
    f"{{{NS_A}}}ln", f"{{{NS_A}}}effectLst", f"{{{NS_A}}}effectDag",
    f"{{{NS_A}}}scene3d", f"{{{NS_A}}}sp3d", f"{{{NS_A}}}extLst",
]
CUSTGEOM_ORDER = [f"{{{NS_A}}}avLst", f"{{{NS_A}}}gdLst", f"{{{NS_A}}}ahLst",
                  f"{{{NS_A}}}cxnLst", f"{{{NS_A}}}rect", f"{{{NS_A}}}pathLst"]


class Findings:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, check, msg):
        self.errors.append(f"{check}: {msg}")

    def warn(self, check, msg):
        self.warnings.append(f"{check}: {msg}")


def _order_ok(children_tags, vocabulary):
    """True if the tags (filtered to the vocabulary) appear in vocabulary
    order. Tags outside the vocabulary are ignored."""
    indices = [vocabulary.index(t) for t in children_tags if t in vocabulary]
    return indices == sorted(indices)


def _rels_source_dir(rels_name):
    """Directory that Targets in this .rels file resolve against."""
    # "ppt/slides/_rels/slide1.xml.rels" -> "ppt/slides"
    #  "_rels/.rels" -> ""
    head = rels_name.split("_rels/")[0]
    return head.rstrip("/")


def check_package(parts, f):
    """OPC-level checks: names, content types, docProps, notes parts."""
    for name in parts:
        if "\\" in name or name.startswith("/"):
            f.error("opc-name", f"bad zip member name {name!r}")

    ct_xml = parts.get("[Content_Types].xml")
    if ct_xml is None:
        f.error("opc-untyped-part", "[Content_Types].xml missing")
        return {}, {}
    try:
        ct_root = ET.fromstring(ct_xml)
    except ET.ParseError as exc:
        f.error("xml-parse", f"[Content_Types].xml: {exc}")
        return {}, {}

    defaults, overrides = {}, {}
    for el in ct_root:
        if el.tag == f"{{{NS_CT}}}Default":
            defaults[el.get("Extension", "").lower()] = el.get("ContentType")
        elif el.tag == f"{{{NS_CT}}}Override":
            overrides[el.get("PartName", "")] = el.get("ContentType")

    for part in overrides:
        if part.lstrip("/") not in parts:
            f.error("opc-override-missing",
                    f"Override for missing part {part}")
    exts_in_zip = {name.rsplit(".", 1)[-1].lower()
                   for name in parts if "." in name}
    for ext in defaults:
        if ext not in exts_in_zip:
            f.error("opc-phantom-default",
                    f'Default for extension "{ext}" matches no part')
    for name in parts:
        if name == "[Content_Types].xml":
            continue
        ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
        if f"/{name}" not in overrides and ext not in defaults:
            f.error("opc-untyped-part", f"no content type for {name}")

    for required in ("docProps/core.xml", "docProps/app.xml"):
        if required not in parts:
            f.error("opc-docprops", f"{required} missing")
    for name in parts:
        if name.startswith("ppt/notesMasters/") or name.startswith("ppt/notesSlides/"):
            f.error("opc-notes", f"unexpected notes part {name} "
                    "(emitted without rels, PowerPoint repairs the deck)")
    return defaults, overrides


def check_relationships(parts, f):
    """Every rels file parses; targets exist; ids unique; r:* attrs resolve."""
    rels_by_source = {}   # source part -> {rId: resolved target}
    for name, data in parts.items():
        if not name.endswith(".rels"):
            continue
        try:
            root = ET.fromstring(data)
        except ET.ParseError as exc:
            f.error("xml-parse", f"{name}: {exc}")
            continue
        src_dir = _rels_source_dir(name)
        seen = {}
        for rel in root.findall(f"{{{NS_PR}}}Relationship"):
            rid = rel.get("Id", "")
            if rid in seen:
                f.error("rel-dup-id", f"{name}: duplicate Id {rid}")
            target = rel.get("Target", "")
            if rel.get("TargetMode") == "External":
                seen[rid] = None
                continue
            resolved = (target.lstrip("/") if target.startswith("/")
                        else posixpath.normpath(posixpath.join(src_dir, target)))
            if resolved not in parts:
                f.error("rel-target-missing",
                        f"{name}: {rid} -> {target} (resolved {resolved}) not in package")
            seen[rid] = resolved
        # map back to the part this rels file describes
        base = name.split("_rels/")[0]
        described = base + name.split("_rels/")[1][:-len(".rels")]
        rels_by_source[described] = seen

    for name, data in parts.items():
        if not name.endswith(".xml") or name.endswith(".rels"):
            continue
        try:
            root = ET.fromstring(data)
        except ET.ParseError as exc:
            f.error("xml-parse", f"{name}: {exc}")
            continue
        rel_ids = rels_by_source.get(name, {})
        for el in root.iter():
            for attr, value in el.attrib.items():
                if attr in R_ATTRS and value not in rel_ids:
                    f.error("rel-unresolved",
                            f"{name}: {attr.split('}')[1]}=\"{value}\" has no relationship")
    return rels_by_source


def check_presentation(parts, rels_by_source, f):
    """sldIdLst <-> slide parts <-> rels agreement; sldSz; sldId ranges."""
    pres = parts.get("ppt/presentation.xml")
    if pres is None:
        f.error("pres-missing", "ppt/presentation.xml missing")
        return
    try:
        root = ET.fromstring(pres)
    except ET.ParseError:
        return  # already reported by check_relationships
    slide_parts = {n for n in parts
                   if n.startswith("ppt/slides/") and n.endswith(".xml")
                   and "_rels" not in n}
    rels = rels_by_source.get("ppt/presentation.xml", {})
    sld_ids = root.findall(f"{{{NS_P}}}sldIdLst/{{{NS_P}}}sldId")
    if len(sld_ids) != len(slide_parts):
        f.error("pres-slide-mismatch",
                f"sldIdLst has {len(sld_ids)} entries but package has "
                f"{len(slide_parts)} slide parts")
    seen_ids = set()
    for sld in sld_ids:
        sid = int(sld.get("id", "0"))
        if not 256 <= sid < 2147483648:
            f.error("pres-sldid-range", f"sldId {sid} outside [256, 2^31)")
        if sid in seen_ids:
            f.error("pres-sldid-range", f"duplicate sldId {sid}")
        seen_ids.add(sid)
        rid = sld.get(f"{{{NS_R}}}id")
        target = rels.get(rid)
        if target is not None and target not in slide_parts:
            f.error("pres-slide-mismatch",
                    f"sldId {sid} rel {rid} targets non-slide {target}")
    sldsz = root.find(f"{{{NS_P}}}sldSz")
    if sldsz is None:
        f.error("pres-sldsz", "sldSz missing")
    else:
        for axis in ("cx", "cy"):
            v = int(sldsz.get(axis, "0"))
            if not SLDSZ_MIN <= v <= SLDSZ_MAX:
                f.error("pres-sldsz", f"sldSz {axis}={v} outside "
                        f"[{SLDSZ_MIN}, {SLDSZ_MAX}]")


def _check_sppr(name, where, sppr, f):
    tags = [child.tag for child in sppr]
    if not _order_ok(tags, SPPR_ORDER):
        f.error("dml-order-sppr", f"{name}: {where}: spPr children out of "
                "schema order (xfrm, geom, fill, ln, effectLst)")
    prst = sppr.find(f"{{{NS_A}}}prstGeom")
    if prst is not None and prst.get("prst") not in PRESET_SHAPES:
        f.error("dml-prst-unknown",
                f"{name}: {where}: unknown preset geometry "
                f"{prst.get('prst')!r}")
    cust = sppr.find(f"{{{NS_A}}}custGeom")
    if cust is not None:
        ctags = [child.tag for child in cust]
        if not _order_ok(ctags, CUSTGEOM_ORDER):
            f.error("dml-order-custgeom",
                    f"{name}: {where}: custGeom children out of schema order")
        pathlst = cust.find(f"{{{NS_A}}}pathLst")
        if pathlst is None:
            f.error("dml-custgeom-path", f"{name}: {where}: custGeom without pathLst")
        else:
            for path in pathlst.findall(f"{{{NS_A}}}path"):
                w, h = path.get("w"), path.get("h")
                if w is None or h is None:
                    f.error("dml-custgeom-path",
                            f"{name}: {where}: path without explicit w/h")
                    continue
                w, h = int(w), int(h)
                for pt in path.iter(f"{{{NS_A}}}pt"):
                    px, py = int(pt.get("x", "0")), int(pt.get("y", "0"))
                    if not (0 <= px <= w and 0 <= py <= h):
                        f.error("dml-custgeom-path",
                                f"{name}: {where}: point ({px},{py}) outside "
                                f"path space {w}x{h}")
    xfrm = sppr.find(f"{{{NS_A}}}xfrm")
    if xfrm is not None:
        ext = xfrm.find(f"{{{NS_A}}}ext")
        if ext is not None:
            cx, cy = int(ext.get("cx", "0")), int(ext.get("cy", "0"))
            # line presets are legitimately flat on one axis
            flat_ok = prst is not None and prst.get("prst") in (
                "line", "straightConnector1")
            if (cx <= 0 or cy <= 0) if not flat_ok else (cx <= 0 and cy <= 0):
                f.error("emu-bounds", f"{name}: {where}: non-positive extent")


def check_drawingml(parts, f):
    """Shape schemas + EMU bounds + off-canvas, on every slide part."""
    pres = parts.get("ppt/presentation.xml")
    canvas = None
    if pres is not None:
        try:
            sldsz = ET.fromstring(pres).find(f"{{{NS_P}}}sldSz")
            if sldsz is not None:
                canvas = (int(sldsz.get("cx", "0")), int(sldsz.get("cy", "0")))
        except ET.ParseError:
            pass  # parse failure already reported by check_relationships
    slide_names = sorted(n for n in parts
                         if n.startswith("ppt/slides/") and n.endswith(".xml")
                         and "_rels" not in n)
    for name in slide_names:
        try:
            root = ET.fromstring(parts[name])
        except ET.ParseError:
            continue  # reported elsewhere
        # EMU bounds everywhere in the slide
        for el in root.iter():
            if el.tag in (f"{{{NS_A}}}off", f"{{{NS_A}}}ext",
                          f"{{{NS_A}}}chOff", f"{{{NS_A}}}chExt"):
                for attr in ("x", "y", "cx", "cy"):
                    raw = el.get(attr)
                    if raw is None:
                        continue
                    try:
                        v = int(raw)
                    except ValueError:
                        f.error("emu-bounds", f"{name}: non-integer {attr}={raw!r}")
                        continue
                    if abs(v) > EMU_MAX:
                        f.error("emu-bounds",
                                f"{name}: {attr}={v} exceeds signed 32-bit EMU")
        for sp in root.iter(f"{{{NS_P}}}sp"):
            cnvpr = sp.find(f"{{{NS_P}}}nvSpPr/{{{NS_P}}}cNvPr")
            where = f'sp "{cnvpr.get("name", "?") if cnvpr is not None else "?"}"'
            if not _order_ok([c.tag for c in sp], SP_ORDER):
                f.error("dml-order-sp",
                        f"{name}: {where}: children out of schema order "
                        "(nvSpPr, spPr, style, txBody)")
            sppr = sp.find(f"{{{NS_P}}}spPr")
            if sppr is None:
                f.error("dml-order-sp", f"{name}: {where}: missing spPr")
            else:
                _check_sppr(name, where, sppr, f)
        for pic in root.iter(f"{{{NS_P}}}pic"):
            cnvpr = pic.find(f"{{{NS_P}}}nvPicPr/{{{NS_P}}}cNvPr")
            where = f'pic "{cnvpr.get("name", "?") if cnvpr is not None else "?"}"'
            if not _order_ok([c.tag for c in pic], PIC_ORDER):
                f.error("dml-order-pic",
                        f"{name}: {where}: children out of schema order "
                        "(nvPicPr, blipFill, spPr)")
            blip = pic.find(f"{{{NS_P}}}blipFill/{{{NS_A}}}blip")
            if blip is None or not blip.get(f"{{{NS_R}}}embed"):
                f.error("dml-pic-blip", f"{name}: {where}: no blip r:embed")
            sppr = pic.find(f"{{{NS_P}}}spPr")
            if sppr is not None:
                _check_sppr(name, where, sppr, f)
        # off-canvas warning for top-level shapes only (group children use
        # child coordinate spaces)
        if canvas:
            sptree = root.find(f"{{{NS_P}}}cSld/{{{NS_P}}}spTree")
            for child in (sptree if sptree is not None else ()):
                if child.tag not in (f"{{{NS_P}}}sp", f"{{{NS_P}}}pic",
                                     f"{{{NS_P}}}grpSp"):
                    continue
                # explicit None checks: ET elements are falsy when childless
                sppr = child.find(f"{{{NS_P}}}spPr")
                if sppr is None:
                    sppr = child.find(f"{{{NS_P}}}grpSpPr")
                xfrm = sppr.find(f"{{{NS_A}}}xfrm") if sppr is not None else None
                off = xfrm.find(f"{{{NS_A}}}off") if xfrm is not None else None
                ext = xfrm.find(f"{{{NS_A}}}ext") if xfrm is not None else None
                if off is None or ext is None:
                    continue
                x, y = int(off.get("x", "0")), int(off.get("y", "0"))
                cx, cy = int(ext.get("cx", "0")), int(ext.get("cy", "0"))
                if x < 0 or y < 0 or x + cx > canvas[0] or y + cy > canvas[1]:
                    f.warn("emu-offcanvas",
                           f"{name}: shape extends beyond the slide canvas")


def check_media(parts, rels_by_source, defaults, f):
    referenced = set()
    for targets in rels_by_source.values():
        referenced.update(t for t in targets.values() if t)
    for name, data in parts.items():
        if not name.startswith("ppt/media/"):
            continue
        if name not in referenced:
            f.error("media-orphan", f"{name} not referenced by any relationship")
        ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
        if ext not in defaults:
            f.error("media-no-default",
                    f'{name}: no Default content type for extension "{ext}"')
        magics = MEDIA_MAGIC.get(ext)
        if magics and not any(data.startswith(m) for m in magics):
            f.error("media-magic",
                    f"{name}: bytes do not match .{ext} signature")


def validate(path):
    """Validate the package at path. Returns (errors, warnings) lists."""
    f = Findings()
    try:
        with zipfile.ZipFile(path) as zf:
            bad = zf.testzip()
            if bad:
                f.error("opc-zip", f"corrupt zip member {bad}")
                return f.errors, f.warnings
            parts = {i.filename: zf.read(i.filename) for i in zf.infolist()
                     if not i.is_dir()}
    except (OSError, zipfile.BadZipFile) as exc:
        raise IOError(f"cannot read package: {exc}") from exc

    defaults, _overrides = check_package(parts, f)
    rels_by_source = check_relationships(parts, f)
    check_presentation(parts, rels_by_source, f)
    check_drawingml(parts, f)
    check_media(parts, rels_by_source, defaults, f)
    return f.errors, f.warnings


def main(argv):
    if len(argv) != 1:
        print(__doc__.strip(), file=sys.stderr)
        return 1
    try:
        errors, warnings = validate(argv[0])
    except IOError as exc:
        print(f"validate_pptx: {exc}", file=sys.stderr)
        return 1
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    for e in errors:
        print(e)
    return 2 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
