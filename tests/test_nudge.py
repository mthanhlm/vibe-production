"""Subprocess tests for scripts/nudge.py (advisory deviation nudge).

Each test builds a throwaway project and a private TMPDIR so the child's
tempfile.gettempdir() — where the per-session seen-file lands — is fully
observable.
"""
import glob
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hookrunner import run_hook, make_project

SWALLOW_PY = "try:\n    x()\nexcept Exception:\n    pass\n"
SESSION = "sess1"
SEEN_NAME = f"vibe-nudge-{SESSION}.json"


class NudgeTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = os.path.realpath(tmp.name)
        self.proj = os.path.realpath(make_project(self.root))
        self.hooktmp = os.path.join(self.root, "hooktmp")
        os.makedirs(self.hooktmp)

    def run_nudge(self, payload, env=None):
        full_env = {"TMPDIR": self.hooktmp}
        if env:
            full_env.update(env)
        return run_hook("nudge.py", payload, env=full_env)

    def payload(self, path, session=SESSION, proj=None):
        return {"cwd": proj or self.proj, "session_id": session,
                "tool_input": {"file_path": path}}

    def write_target(self, relpath, content, proj=None):
        path = os.path.join(proj or self.proj, relpath)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        return path

    def context_of(self, stdout):
        data = json.loads(stdout)
        self.assertEqual(data["hookSpecificOutput"]["hookEventName"], "PostToolUse")
        return data["hookSpecificOutput"]["additionalContext"]

    # --- happy path: pattern hits ------------------------------------------

    def test_swallowed_exception_emits_note(self):
        path = self.write_target("app.py", SWALLOW_PY)
        code, out, err = self.run_nudge(self.payload(path))
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertIn("[swallowed-exception]", self.context_of(out))
        self.assertTrue(os.path.isfile(os.path.join(self.hooktmp, SEEN_NAME)))

    def test_requests_without_timeout_emits_note(self):
        path = self.write_target(
            "client.py",
            'import requests\nresp = requests.get("https://api.example.com/x")\n')
        code, out, _ = self.run_nudge(self.payload(path))
        self.assertEqual(code, 0)
        self.assertIn("[http-no-timeout]", self.context_of(out))

    def test_requests_with_timeout_is_silent(self):
        path = self.write_target(
            "client.py",
            'import requests\nresp = requests.get("https://api.example.com/x", timeout=5)\n')
        code, out, err = self.run_nudge(self.payload(path))
        self.assertEqual((code, out, err), (0, "", ""))

    # --- dedup --------------------------------------------------------------

    def test_second_run_same_session_is_deduped(self):
        path = self.write_target("app.py", SWALLOW_PY)
        code, out, _ = self.run_nudge(self.payload(path))
        self.assertEqual(code, 0)
        self.assertIn("[swallowed-exception]", self.context_of(out))
        code, out, err = self.run_nudge(self.payload(path))
        self.assertEqual((code, out, err), (0, "", ""))

    # --- exempt paths and extensions ----------------------------------------

    def test_file_under_tests_dir_is_skipped(self):
        path = self.write_target(os.path.join("tests", "helper.py"), SWALLOW_PY)
        code, out, err = self.run_nudge(self.payload(path))
        self.assertEqual((code, out, err), (0, "", ""))

    def test_test_prefixed_filename_is_skipped(self):
        path = self.write_target("test_app.py", SWALLOW_PY)
        code, out, err = self.run_nudge(self.payload(path))
        self.assertEqual((code, out, err), (0, "", ""))

    def test_markdown_file_is_skipped(self):
        path = self.write_target("notes.md", SWALLOW_PY)
        code, out, err = self.run_nudge(self.payload(path))
        self.assertEqual((code, out, err), (0, "", ""))

    def test_project_without_vibe_dir_is_silent(self):
        proj = os.path.realpath(
            make_project(os.path.join(self.root, "novibe"), vibe=False))
        path = self.write_target("app.py", SWALLOW_PY, proj=proj)
        code, out, err = self.run_nudge(self.payload(path, proj=proj))
        self.assertEqual((code, out, err), (0, "", ""))

    # --- malformed input (R-6) ----------------------------------------------

    def test_malformed_stdin_exits_zero_silently(self):
        code, out, err = self.run_nudge("{not json")
        self.assertEqual((code, out, err), (0, "", ""))

    def test_malformed_stdin_breadcrumb_with_debug(self):
        code, out, err = self.run_nudge("{not json", env={"VIBE_DEBUG": "1"})
        self.assertEqual((code, out), (0, ""))
        self.assertIn("vibe-debug[nudge] parsing stdin payload", err)

    def test_non_dict_payload_is_silent(self):
        code, out, err = self.run_nudge('["not", "a", "dict"]')
        self.assertEqual((code, out, err), (0, "", ""))

    def test_non_string_file_path_is_silent(self):
        payload = {"cwd": self.proj, "session_id": SESSION,
                   "tool_input": {"file_path": 42}}
        code, out, err = self.run_nudge(payload)
        self.assertEqual((code, out, err), (0, "", ""))

    def test_non_dict_tool_input_is_silent(self):
        payload = {"cwd": self.proj, "session_id": SESSION, "tool_input": "oops"}
        code, out, err = self.run_nudge(payload)
        self.assertEqual((code, out, err), (0, "", ""))

    # --- session_id sanitization (R-9) ---------------------------------------

    def test_traversal_session_id_stays_inside_tmpdir(self):
        deep = os.path.join(self.root, "a", "b", "c")
        os.makedirs(deep)
        path = self.write_target("app.py", SWALLOW_PY)
        payload = self.payload(path, session="../../../etc/passwd")
        code, out, _ = self.run_nudge(payload, env={"TMPDIR": deep})
        self.assertEqual(code, 0)
        self.assertIn("[swallowed-exception]", self.context_of(out))
        names = os.listdir(deep)
        self.assertEqual(names, ["vibe-nudge-etcpasswd.json"])
        self.assertNotIn(os.sep, names[0])
        self.assertNotIn("..", names[0])
        # Nothing escaped the temp dir: no seen-file anywhere else under root.
        strays = [os.path.join(d, n)
                  for d, _, files in os.walk(self.root) if d != deep
                  for n in files if "vibe-nudge" in n]
        self.assertEqual(strays, [])
        self.assertFalse(os.path.exists(os.path.join(self.root, "etc")))

    def test_non_string_session_id_falls_back_to_nosession(self):
        path = self.write_target("app.py", SWALLOW_PY)
        payload = {"cwd": self.proj, "session_id": {"x": 1},
                   "tool_input": {"file_path": path}}
        code, out, _ = self.run_nudge(payload)
        self.assertEqual(code, 0)
        self.assertIn("[swallowed-exception]", self.context_of(out))
        self.assertEqual(os.listdir(self.hooktmp), ["vibe-nudge-nosession.json"])

    # --- seen-file robustness (R-3, R-4) --------------------------------------

    def test_corrupt_seen_file_still_emits_with_breadcrumb(self):
        with open(os.path.join(self.hooktmp, SEEN_NAME), "w") as f:
            f.write("{corrupt json")
        path = self.write_target("app.py", SWALLOW_PY)
        code, out, err = self.run_nudge(self.payload(path), env={"VIBE_DEBUG": "1"})
        self.assertEqual(code, 0)
        self.assertIn("[swallowed-exception]", self.context_of(out))
        self.assertIn("vibe-debug[nudge] reading seen-file", err)
        with open(os.path.join(self.hooktmp, SEEN_NAME)) as f:
            self.assertIn("swallowed-exception", json.load(f))

    def test_write_leaves_only_seen_file_no_tmp_leftovers(self):
        path = self.write_target("app.py", SWALLOW_PY)
        code, out, _ = self.run_nudge(self.payload(path))
        self.assertEqual(code, 0)
        self.assertTrue(out.strip())
        self.assertEqual(glob.glob(os.path.join(self.hooktmp, "*.tmp*")), [])
        self.assertEqual(os.listdir(self.hooktmp), [SEEN_NAME])

    def test_seen_file_write_failure_still_emits_and_cleans_up(self):
        # A directory where the seen-file should be makes open() and
        # os.replace() fail deterministically for any user.
        os.makedirs(os.path.join(self.hooktmp, SEEN_NAME))
        path = self.write_target("app.py", SWALLOW_PY)
        code, out, err = self.run_nudge(self.payload(path), env={"VIBE_DEBUG": "1"})
        self.assertEqual(code, 0)
        self.assertIn("[swallowed-exception]", self.context_of(out))
        self.assertIn("vibe-debug[nudge] reading seen-file", err)
        self.assertIn("vibe-debug[nudge] writing seen-file", err)
        # The mkstemp temp file was cleaned up; only the blocking dir remains.
        self.assertEqual(os.listdir(self.hooktmp), [SEEN_NAME])


if __name__ == "__main__":
    unittest.main()
