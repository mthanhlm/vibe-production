"""Subprocess-level tests for scripts/gate.py (the plan gate hook).

Each test spawns gate.py exactly as the harness does: JSON on stdin,
assertions on exit code, stderr, and files on disk.
"""
import os
import tempfile
import unittest

try:
    from tests.hookrunner import APPROVED_PLAN, DRAFT_PLAN, make_project, run_hook
except ImportError:  # discovery started inside tests/
    from hookrunner import APPROVED_PLAN, DRAFT_PLAN, make_project, run_hook

GATE = "gate.py"


def payload(proj, file_path, mode="default"):
    return {"cwd": proj, "tool_input": {"file_path": file_path},
            "permission_mode": mode}


class TestGateOptIn(unittest.TestCase):
    def test_no_vibe_dir_allows(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = make_project(tmp, vibe=False)
            code, _, err = run_hook(GATE, payload(proj, os.path.join(proj, "a.py")))
            self.assertEqual(code, 0, err)


class TestGateMalformedInput(unittest.TestCase):
    def test_malformed_stdin_allows_silently(self):
        code, _, err = run_hook(GATE, "{this is not json")
        self.assertEqual(code, 0, err)
        self.assertNotIn("vibe-debug", err)

    def test_malformed_stdin_breadcrumb_with_debug(self):
        code, _, err = run_hook(GATE, "{this is not json",
                                env={"VIBE_DEBUG": "1"})
        self.assertEqual(code, 0, err)
        self.assertIn("vibe-debug[gate]", err)

    def test_list_payload_allows(self):
        code, _, err = run_hook(GATE, ["not", "a", "dict"],
                                env={"VIBE_DEBUG": "1"})
        self.assertEqual(code, 0, err)
        self.assertIn("vibe-debug[gate]", err)


class TestGateKillSwitches(unittest.TestCase):
    def test_env_kill_switch_allows(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = make_project(tmp)  # .vibe/ but no plan: gate would block
            code, _, err = run_hook(GATE, payload(proj, os.path.join(proj, "a.py")),
                                    env={"VIBE_GATE": "off"})
            self.assertEqual(code, 0, err)

    def test_config_kill_switch_allows(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = make_project(tmp, config={"gate": "off"})
            code, _, err = run_hook(GATE, payload(proj, os.path.join(proj, "a.py")))
            self.assertEqual(code, 0, err)

    def test_malformed_config_keeps_gate_active(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = make_project(tmp, config="{definitely not json")
            code, _, err = run_hook(GATE, payload(proj, os.path.join(proj, "a.py")),
                                    env={"VIBE_DEBUG": "1"})
            self.assertEqual(code, 2, err)
            self.assertIn("PLAN GATE", err)
            self.assertIn("vibe-debug[gate]", err)


class TestGateScope(unittest.TestCase):
    def test_plan_mode_allows(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = make_project(tmp)
            code, _, err = run_hook(GATE, payload(proj, os.path.join(proj, "a.py"),
                                                  mode="plan"))
            self.assertEqual(code, 0, err)

    def test_missing_or_invalid_file_path_allows(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = make_project(tmp)
            for tool_input in ({}, {"file_path": ""}, {"file_path": 42}):
                with self.subTest(tool_input=tool_input):
                    code, _, err = run_hook(GATE, {
                        "cwd": proj, "tool_input": tool_input,
                        "permission_mode": "default",
                    })
                    self.assertEqual(code, 0, err)

    def test_tool_input_not_a_dict_allows(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = make_project(tmp)
            code, _, err = run_hook(GATE, {
                "cwd": proj, "tool_input": "rm -rf /",
                "permission_mode": "default",
            })
            self.assertEqual(code, 0, err)

    def test_nonstring_cwd_falls_back_to_project_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = make_project(tmp)  # no plan: gate blocks if project resolves
            code, _, err = run_hook(
                GATE, {"cwd": 123,
                       "tool_input": {"file_path": os.path.join(proj, "a.py")},
                       "permission_mode": "default"},
                env={"CLAUDE_PROJECT_DIR": proj})
            self.assertEqual(code, 2, err)
            self.assertIn("PLAN GATE", err)

    def test_file_outside_project_allows(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = make_project(tmp)
            outside = os.path.join(tmp, "outside.py")
            code, _, err = run_hook(GATE, payload(proj, outside))
            self.assertEqual(code, 0, err)

    def test_exempt_paths_allow(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = make_project(tmp)  # no plan: only the exemption can allow
            for rel in (".vibe/x", ".claude/x", "docs/solutions/x", "CLAUDE.md"):
                with self.subTest(rel=rel):
                    code, _, err = run_hook(
                        GATE, payload(proj, os.path.join(proj, rel)))
                    self.assertEqual(code, 0, err)


class TestGateDecision(unittest.TestCase):
    def test_approved_plan_allows(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = make_project(tmp, plan=APPROVED_PLAN)
            code, _, err = run_hook(
                GATE, payload(proj, os.path.join(proj, "src", "main.py")))
            self.assertEqual(code, 0, err)

    def test_draft_plan_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = make_project(tmp, plan=DRAFT_PLAN)
            code, _, err = run_hook(
                GATE, payload(proj, os.path.join(proj, "src", "main.py")))
            self.assertEqual(code, 2)
            self.assertIn("PLAN GATE", err)
            self.assertIn("not approved", err)

    def test_no_plan_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = make_project(tmp)
            code, _, err = run_hook(
                GATE, payload(proj, os.path.join(proj, "src", "main.py")))
            self.assertEqual(code, 2)
            self.assertIn("PLAN GATE", err)

    def test_unreadable_plan_fails_open(self):
        # A directory where plan.md should be makes open() fail for any
        # user (chmod tricks are ignored by root).
        with tempfile.TemporaryDirectory() as tmp:
            proj = make_project(tmp)
            os.makedirs(os.path.join(proj, ".vibe", "plan.md"))
            target = payload(proj, os.path.join(proj, "src", "main.py"))

            code, _, err = run_hook(GATE, target)
            self.assertEqual(code, 0, err)
            self.assertNotIn("vibe-debug", err)

            code, _, err = run_hook(GATE, target, env={"VIBE_DEBUG": "1"})
            self.assertEqual(code, 0, err)
            self.assertIn("vibe-debug[gate]", err)


if __name__ == "__main__":
    unittest.main()
