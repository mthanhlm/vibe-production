"""Subprocess-level tests for the slide v2 pipeline (stdlib only).

Covers scripts/validate_pptx.py (positive round-trips + zip mutations that
must be caught) and the legacy build path staying validator-clean. Extended
by later steps with spec-v2 layout, emitter-golden, and budget-lint tests.
Never imports the scripts as modules (WA-4 conventions).
"""
import json
import os
import tempfile
import unittest
import zipfile

from test_tools import REPO, run_tool

LEGACY_SPEC = {
    "title": "Legacy specs keep building after the v2 uplift",
    "subtitle": "Backward-compat fixture",
    "meta": "tests · vibe plugin",
    "slides": [
        {"type": "exec_summary", "title": "The old spec format still works",
         "bullets": ["Nothing about v1 decks changed",
                     {"text": "Same template, same text swap", "level": 1}]},
        {"type": "content", "kicker": "PROOF", "title": "This deck was built from a v1 spec",
         "bullets": ["And it passes the new package validator"]},
        {"type": "closing", "title": "Decision needed: none",
         "bullets": ["Fixture only"]},
    ],
}


def build_deck(tmpdir, spec=LEGACY_SPEC, *extra_args):
    """Build a deck from spec into tmpdir; return (code, out, err, path)."""
    spec_path = os.path.join(tmpdir, "spec.json")
    out_path = os.path.join(tmpdir, "deck.pptx")
    with open(spec_path, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    code, out, err = run_tool("build_pptx.py", spec_path, out_path, *extra_args)
    return code, out, err, out_path


def mutate_zip(src, dst, mutate):
    """Copy zip src->dst applying mutate(parts_dict) in between."""
    with zipfile.ZipFile(src) as zf:
        parts = {i.filename: zf.read(i.filename) for i in zf.infolist()}
    mutate(parts)
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in parts.items():
            zf.writestr(name, data)


class LegacyBuildTest(unittest.TestCase):
    def test_legacy_spec_builds_and_validates_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, err, path = build_deck(tmp)
            self.assertEqual(code, 0, f"stdout: {out}\nstderr: {err}")
            code, out, err = run_tool("validate_pptx.py", path)
            self.assertEqual(code, 0, f"stdout: {out}\nstderr: {err}")
            self.assertEqual(out, "")

    def test_template_validates_clean(self):
        template = os.path.join(REPO, "skills", "slide", "assets",
                                "template.pptx")
        code, out, err = run_tool("validate_pptx.py", template)
        self.assertEqual(code, 0, f"stdout: {out}\nstderr: {err}")


class ValidatePptxMutationTest(unittest.TestCase):
    """Each documented repair-trigger mutation must be caught (exit 2)."""

    def assert_finding(self, mutate, check_id):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, err, path = build_deck(tmp)
            self.assertEqual(code, 0, f"stderr: {err}")
            broken = os.path.join(tmp, "broken.pptx")
            mutate_zip(path, broken, mutate)
            code, out, err = run_tool("validate_pptx.py", broken)
            self.assertEqual(code, 2,
                             f"expected findings\nstdout: {out}\nstderr: {err}")
            self.assertIn(check_id, out)

    def test_unknown_preset_geometry(self):
        def mutate(parts):
            parts["ppt/slides/slide1.xml"] = parts["ppt/slides/slide1.xml"] \
                .replace(b'prst="rect"', b'prst="oval"', 1)
        self.assert_finding(mutate, "dml-prst-unknown")

    def test_phantom_content_type_default(self):
        def mutate(parts):
            parts["[Content_Types].xml"] = parts["[Content_Types].xml"].replace(
                b"</Types>",
                b'<Default Extension="png" ContentType="image/png"/></Types>')
        self.assert_finding(mutate, "opc-phantom-default")

    def test_missing_docprops_app(self):
        def mutate(parts):
            del parts["docProps/app.xml"]
        self.assert_finding(mutate, "opc-docprops")

    def test_duplicate_relationship_id(self):
        def mutate(parts):
            name = "ppt/slides/_rels/slide1.xml.rels"
            parts[name] = parts[name].replace(
                b"</Relationships>",
                b'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/></Relationships>')
        self.assert_finding(mutate, "rel-dup-id")

    def test_dropped_relationship_target(self):
        def mutate(parts):
            del parts["ppt/theme/theme1.xml"]
        self.assert_finding(mutate, "rel-target-missing")

    def test_unresolved_r_embed(self):
        def mutate(parts):
            parts["ppt/slides/slide2.xml"] = parts["ppt/slides/slide2.xml"] \
                .replace(b"</p:spTree>",
                         b'<p:pic xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                         b'<p:nvPicPr><p:cNvPr id="99" name="ghost"/>'
                         b"<p:cNvPicPr/><p:nvPr/></p:nvPicPr>"
                         b'<p:blipFill><a:blip r:embed="rId9"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>'
                         b'<p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="914400" cy="914400"/></a:xfrm>'
                         b'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic></p:spTree>')
        self.assert_finding(mutate, "rel-unresolved")


V2_SPEC = {
    "version": 2,
    "title": "One door now serves every chat, with memory",
    "subtitle": "Fixture deck",
    "meta": "tests · vibe plugin",
    "slides": [
        {"beat": "hook", "layout": "big_number", "kicker": "THE NUMBER",
         "value": "100%", "context": "of history was forgotten every message",
         "source": "Source: fixture (2026)"},
        {"beat": "transition", "kicker": "01", "title": "Why this was costly"},
        {"beat": "problem", "layout": "before_after", "title": "One door replaces two paths",
         "left": {"head": "Before", "lines": ["Re-planned from zero"]},
         "right": {"head": "After", "lines": ["One endpoint, three modes"]}},
        {"beat": "proof", "layout": "quote_evidence",
         "quote": "7/7 criteria PASS, 23/23 tests green.",
         "attribution": "— verify.sh"},
        {"beat": "ask", "layout": "exec_summary_3col", "title": "Approve the close-out commit",
         "columns": [{"head": "Situation", "lines": ["Shipped"]},
                     {"head": "Findings", "lines": ["All pass"]},
                     {"head": "Recommendation", "lines": ["Approve"]}]},
        {"beat": "ask", "layout": "hero_statement",
         "statement": "Approve the close-out today",
         "support": "Everything is green"},
    ],
}


class BuildV2Test(unittest.TestCase):
    def test_v2_builds_and_validates_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, err, path = build_deck(tmp, V2_SPEC)
            self.assertEqual(code, 0, f"stdout: {out}\nstderr: {err}")
            self.assertIn("7 slides", out)
            code, out, err = run_tool("validate_pptx.py", path)
            self.assertEqual(code, 0, f"stdout: {out}\nstderr: {err}")
            with zipfile.ZipFile(path) as zf:
                hero = zf.read("ppt/slides/slide7.xml").decode("utf-8")
                self.assertIn("Approve the close-out today", hero)
                self.assertIn("gradFill", hero)  # hero keeps its gradient field

    def test_dark_theme_recolors_content_not_heroes(self):
        spec = dict(V2_SPEC, theme="dark")
        with tempfile.TemporaryDirectory() as tmp:
            code, out, err, path = build_deck(tmp, spec)
            self.assertEqual(code, 0, f"stderr: {err}")
            with zipfile.ZipFile(path) as zf:
                master = zf.read("ppt/slideMasters/slideMaster1.xml").decode()
                self.assertIn('val="1E1E1E"', master)
                big = zf.read("ppt/slides/slide2.xml").decode()  # big_number
                self.assertIn('val="FFFFFF"', big)      # navy metric -> white
                self.assertNotIn('val="163A5F"', big)
                hero = zf.read("ppt/slides/slide7.xml").decode()  # exempt
                self.assertIn('val="163A5F"', hero)     # gradient untouched

    def test_budget_hard_fails_and_force_downgrades(self):
        spec = json.loads(json.dumps(V2_SPEC))
        spec["slides"][2]["title"] = ("This title is deliberately far too "
                                      "long to pass the fifteen word action "
                                      "title budget rule")
        with tempfile.TemporaryDirectory() as tmp:
            code, out, err, path = build_deck(tmp, spec)
            self.assertEqual(code, 1)
            self.assertIn("SL-", err)
            code, out, err, path = build_deck(tmp, spec, "--force")
            self.assertEqual(code, 0, f"stderr: {err}")
            self.assertIn("warning", err)

    def test_wrong_beat_layout_pairing_is_structural_error(self):
        spec = json.loads(json.dumps(V2_SPEC))
        spec["slides"][0]["layout"] = "quote_evidence"  # not allowed for hook
        with tempfile.TemporaryDirectory() as tmp:
            code, out, err, path = build_deck(tmp, spec)
            self.assertEqual(code, 1)
            self.assertIn("SL-17", err)
            # structural errors are never forceable
            code, out, err, path = build_deck(tmp, spec, "--force")
            self.assertEqual(code, 1)

    def test_build_is_deterministic(self):
        import hashlib
        digests = []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as tmp:
                code, out, err, path = build_deck(tmp, V2_SPEC)
                self.assertEqual(code, 0, f"stderr: {err}")
                with open(path, "rb") as fh:
                    digests.append(hashlib.sha256(fh.read()).hexdigest())
        self.assertEqual(digests[0], digests[1])


class ShowcaseTest(unittest.TestCase):
    def test_showcase_builds_validates_and_is_deterministic(self):
        import hashlib
        digests = []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as tmp:
                path = os.path.join(tmp, "showcase.pptx")
                code, out, err = run_tool("build_pptx.py", "--showcase", path)
                self.assertEqual(code, 0, f"stdout: {out}\nstderr: {err}")
                self.assertIn("showcase OK", out)
                code, vout, verr = run_tool("validate_pptx.py", path)
                self.assertEqual(code, 0, f"stdout: {vout}\nstderr: {verr}")
                with open(path, "rb") as fh:
                    digests.append(hashlib.sha256(fh.read()).hexdigest())
        self.assertEqual(digests[0], digests[1], "showcase not deterministic")

    def test_emitter_fragment_goldens(self):
        """Exact probe-derived XML survives the ET round trip (WA-2 goldens)."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "showcase.pptx")
            code, out, err = run_tool("build_pptx.py", "--showcase", path)
            self.assertEqual(code, 0, f"stderr: {err}")
            with zipfile.ZipFile(path) as zf:
                kpi = zf.read("ppt/slides/slide5.xml").decode()
                self.assertIn('blurRad="190500" dist="76200" dir="5400000"',
                              kpi)                       # probe-b shadow
                self.assertIn('fmla="val 6000"', kpi)    # card corner radius
                bars = zf.read("ppt/slides/slide6.xml").decode()
                self.assertEqual(bars.count("<p:sp>"),
                                 8 + 4 * 3)  # 8 chrome shapes + 4 bar triples
                self.assertIn('val="C9A227"', bars)      # one accent bar
                cols = zf.read("ppt/slides/slide7.xml").decode()
                self.assertIn('prst="line"', cols)       # zero-height baseline
                hero = zf.read("ppt/slides/slide3.xml").decode()
                self.assertIn('ang="2700000" scaled="1"', hero)  # probe-a

    def test_image_media_lands_in_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "showcase.pptx")
            code, out, err = run_tool("build_pptx.py", "--showcase", path)
            self.assertEqual(code, 0, f"stderr: {err}")
            with zipfile.ZipFile(path) as zf:
                names = set(zf.namelist())
                self.assertIn("ppt/media/image1.png", names)
                self.assertTrue(zf.read("ppt/media/image1.png")
                                .startswith(b"\x89PNG"))
                ct = zf.read("[Content_Types].xml").decode()
                self.assertIn('Extension="png"', ct)
                rels = zf.read("ppt/slides/_rels/slide11.xml.rels").decode()
                self.assertIn('Id="rId2"', rels)
                self.assertIn("image1.png", rels)

    def test_photo_without_path_falls_back_to_gradient(self):
        spec = json.loads(json.dumps(V2_SPEC))
        spec["slides"][3] = {
            "beat": "proof", "layout": "chart_takeaway",
            "title": "A missing photo degrades to the gradient field",
            "exhibit": {"type": "photo", "query": "team at work",
                        "alt": "team photo"},
            "source": "Source: fixture (2026)"}
        with tempfile.TemporaryDirectory() as tmp:
            code, out, err, path = build_deck(tmp, spec)
            self.assertEqual(code, 0, f"stderr: {err}")
            with zipfile.ZipFile(path) as zf:
                xml = zf.read("ppt/slides/slide5.xml").decode()
                self.assertIn("gradient_field", xml)
                self.assertNotIn("r:embed", xml)

    def test_missing_image_path_is_structural_error(self):
        spec = json.loads(json.dumps(V2_SPEC))
        spec["slides"][3] = {
            "beat": "proof", "layout": "chart_takeaway",
            "title": "A missing image path must fail the build",
            "exhibit": {"type": "image", "path": "/nonexistent/shot.png",
                        "alt": "screenshot"},
            "source": "Source: fixture (2026)"}
        with tempfile.TemporaryDirectory() as tmp:
            code, out, err, path = build_deck(tmp, spec)
            self.assertEqual(code, 1)
            self.assertIn("not found", err)

    def test_kpi_tile_count_enforced(self):
        spec = json.loads(json.dumps(V2_SPEC))
        spec["slides"][0] = {"beat": "status", "layout": "kpi_strip",
                             "title": "Too many tiles must fail the build",
                             "tiles": [{"label": f"m{i}", "value": i}
                                       for i in range(7)]}
        with tempfile.TemporaryDirectory() as tmp:
            code, out, err, path = build_deck(tmp, spec)
            self.assertEqual(code, 1)
            self.assertIn("2-6", err)


class IconsJsonTest(unittest.TestCase):
    """DM-5: the vendored icon set stays sane without re-running the vendor."""

    @classmethod
    def setUpClass(cls):
        path = os.path.join(REPO, "skills", "slide", "assets", "icons.json")
        with open(path, encoding="utf-8") as fh:
            cls.data = json.load(fh)

    def test_count_in_range(self):
        self.assertTrue(150 <= len(self.data["icons"]) <= 250,
                        f"got {len(self.data['icons'])} icons")

    def test_commands_and_coordinates(self):
        space = self.data["_meta"]["space"]
        self.assertEqual(space, 24000)
        for name, cmds in self.data["icons"].items():
            for cmd in cmds:
                self.assertIn(cmd[0], ("M", "L", "C", "Z"),
                              f"{name}: bad command {cmd[0]}")
                for v in cmd[1:]:
                    self.assertIsInstance(v, int, f"{name}: non-int coord")
                    self.assertTrue(0 <= v <= space,
                                    f"{name}: coord {v} out of range")

    def test_showcase_icons_present(self):
        for name in ("bot", "users", "gauge"):
            self.assertIn(name, self.data["icons"])


class FetchPhotoTest(unittest.TestCase):
    """Offline contract tests only — the network path is Tier 3."""

    def test_usage_error(self):
        code, out, err = run_tool("fetch_photo.py")
        self.assertEqual(code, 1)
        self.assertIn("Usage", err)

    def test_unreachable_api_exits_four(self):
        env_saved = os.environ.get("VIBE_OPENVERSE_API")
        os.environ["VIBE_OPENVERSE_API"] = "http://127.0.0.1:1/nope/"
        try:
            with tempfile.TemporaryDirectory() as tmp:
                code, out, err = run_tool("fetch_photo.py", "team", tmp)
            self.assertEqual(code, 4)
            self.assertIn("unreachable", err)
        finally:
            if env_saved is None:
                del os.environ["VIBE_OPENVERSE_API"]
            else:
                os.environ["VIBE_OPENVERSE_API"] = env_saved


class ValidatePptxCliTest(unittest.TestCase):
    def test_no_args_is_usage_error(self):
        code, out, err = run_tool("validate_pptx.py")
        self.assertEqual(code, 1)
        self.assertIn("Usage", err)

    def test_missing_file_is_io_error(self):
        code, out, err = run_tool("validate_pptx.py", "/nonexistent/deck.pptx")
        self.assertEqual(code, 1)
        self.assertIn("cannot read package", err)


if __name__ == "__main__":
    unittest.main()
