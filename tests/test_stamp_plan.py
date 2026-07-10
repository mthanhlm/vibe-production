"""Subprocess tests for scripts/stamp_plan.py (PostToolUse: ExitPlanMode)."""
import json
import os
import tempfile
import unittest

from tests.hookrunner import APPROVED_PLAN, DRAFT_PLAN, make_project, run_hook

SCRIPT = "stamp_plan.py"
PLAN_BODY = "# My plan\n\n- step one\n- step two\n"


def payload(proj, plan=PLAN_BODY):
    return {"cwd": proj, "tool_input": {"plan": plan}}


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestStampPlan(unittest.TestCase):
    def test_happy_path_stamps_plan_and_state(self):
        with tempfile.TemporaryDirectory() as td:
            proj = make_project(td)
            code, out, err = run_hook(SCRIPT, payload(proj))
            self.assertEqual(code, 0)
            self.assertEqual(err, "")

            plan_text = read(os.path.join(proj, ".vibe", "plan.md"))
            self.assertTrue(plan_text.startswith("---\nstatus: approved\n"))
            self.assertIn("# My plan", plan_text)

            state_text = read(os.path.join(proj, ".vibe", "STATE.md"))
            self.assertIn("status: doing", state_text)
            self.assertIn("My plan", state_text)
            self.assertIn("next_action: /vibe:check", state_text)

            parsed = json.loads(out)
            self.assertIn("additionalContext",
                          parsed.get("hookSpecificOutput", {}))
            self.assertIn(".vibe/plan.md",
                          parsed["hookSpecificOutput"]["additionalContext"])

    def test_happy_path_leaves_no_temp_files(self):
        with tempfile.TemporaryDirectory() as td:
            proj = make_project(td)
            code, _, _ = run_hook(SCRIPT, payload(proj))
            self.assertEqual(code, 0)
            vibe = os.path.join(proj, ".vibe")
            leftovers = [n for n in os.listdir(vibe) if ".tmp" in n]
            self.assertEqual(leftovers, [])
            self.assertEqual(sorted(os.listdir(vibe)),
                             ["STATE.md", "plan.md"])

    def test_existing_approved_plan_left_byte_identical(self):
        with tempfile.TemporaryDirectory() as td:
            proj = make_project(td, plan=APPROVED_PLAN)
            plan_path = os.path.join(proj, ".vibe", "plan.md")
            with open(plan_path, "rb") as f:
                before = f.read()
            code, out, err = run_hook(SCRIPT, payload(proj))
            self.assertEqual(code, 0)
            self.assertEqual(out, "")
            self.assertEqual(err, "")
            with open(plan_path, "rb") as f:
                self.assertEqual(f.read(), before)
            self.assertFalse(
                os.path.exists(os.path.join(proj, ".vibe", "STATE.md")))

    def test_existing_draft_plan_is_replaced(self):
        with tempfile.TemporaryDirectory() as td:
            proj = make_project(td, plan=DRAFT_PLAN)
            code, out, _ = run_hook(SCRIPT, payload(proj))
            self.assertEqual(code, 0)
            plan_text = read(os.path.join(proj, ".vibe", "plan.md"))
            self.assertNotEqual(plan_text, DRAFT_PLAN)
            self.assertIn("status: approved", plan_text)
            self.assertIn("# My plan", plan_text)
            self.assertTrue(
                os.path.isfile(os.path.join(proj, ".vibe", "STATE.md")))
            self.assertIn("additionalContext", out)

    def test_whitespace_plan_writes_nothing(self):
        with tempfile.TemporaryDirectory() as td:
            proj = make_project(td)
            code, out, err = run_hook(SCRIPT, payload(proj, plan="   \n\t\n"))
            self.assertEqual((code, out, err), (0, "", ""))
            self.assertEqual(os.listdir(os.path.join(proj, ".vibe")), [])

    def test_plan_field_dict_writes_nothing(self):
        with tempfile.TemporaryDirectory() as td:
            proj = make_project(td)
            code, out, err = run_hook(
                SCRIPT, {"cwd": proj, "tool_input": {"plan": {"oops": 1}}})
            self.assertEqual((code, out, err), (0, "", ""))
            self.assertEqual(os.listdir(os.path.join(proj, ".vibe")), [])

    def test_malformed_stdin_exits_zero_silent(self):
        with tempfile.TemporaryDirectory() as td:
            proj = make_project(td)
            code, out, err = run_hook(SCRIPT, "this is {not json",
                                      env={"CLAUDE_PROJECT_DIR": proj})
            self.assertEqual((code, out, err), (0, "", ""))
            self.assertEqual(os.listdir(os.path.join(proj, ".vibe")), [])

    def test_malformed_stdin_breadcrumb_with_vibe_debug(self):
        with tempfile.TemporaryDirectory() as td:
            proj = make_project(td)
            code, out, err = run_hook(SCRIPT, "this is {not json",
                                      env={"VIBE_DEBUG": "1",
                                           "CLAUDE_PROJECT_DIR": proj})
            self.assertEqual(code, 0)
            self.assertEqual(out, "")
            self.assertIn("vibe-debug[stamp-plan]", err)
            self.assertEqual(os.listdir(os.path.join(proj, ".vibe")), [])

    def test_non_dict_payload_writes_nothing(self):
        with tempfile.TemporaryDirectory() as td:
            proj = make_project(td)
            code, out, err = run_hook(SCRIPT, json.dumps(["not", "a", "dict"]),
                                      env={"CLAUDE_PROJECT_DIR": proj})
            self.assertEqual((code, out, err), (0, "", ""))
            self.assertEqual(os.listdir(os.path.join(proj, ".vibe")), [])

    def test_no_vibe_dir_writes_nothing(self):
        with tempfile.TemporaryDirectory() as td:
            proj = make_project(td, vibe=False)
            code, out, err = run_hook(SCRIPT, payload(proj))
            self.assertEqual((code, out, err), (0, "", ""))
            self.assertEqual(os.listdir(proj), [])

    def test_plan_path_directory_no_traceback_and_breadcrumb(self):
        with tempfile.TemporaryDirectory() as td:
            proj = make_project(td)
            vibe = os.path.join(proj, ".vibe")
            # A directory where plan.md should be makes os.replace fail
            # deterministically, regardless of the invoking user.
            os.makedirs(os.path.join(vibe, "plan.md"))
            code, out, err = run_hook(SCRIPT, payload(proj),
                                      env={"VIBE_DEBUG": "1"})
            self.assertEqual(code, 0)
            self.assertEqual(out, "")
            self.assertNotIn("Traceback", err)
            self.assertIn("vibe-debug[stamp-plan]", err)
            self.assertTrue(os.path.isdir(os.path.join(vibe, "plan.md")))
            self.assertFalse(os.path.exists(os.path.join(vibe, "STATE.md")))
            leftovers = [n for n in os.listdir(vibe) if ".tmp" in n]
            self.assertEqual(leftovers, [])

    def test_symlinked_vibe_writes_into_real_target(self):
        with tempfile.TemporaryDirectory() as td:
            proj = make_project(td, vibe=False)
            real = os.path.join(td, "real-vibe")
            os.makedirs(real)
            os.symlink(real, os.path.join(proj, ".vibe"))
            code, out, _ = run_hook(SCRIPT, payload(proj))
            self.assertEqual(code, 0)
            self.assertIn("additionalContext", out)
            plan_text = read(os.path.join(real, "plan.md"))
            self.assertIn("status: approved", plan_text)
            state_text = read(os.path.join(real, "STATE.md"))
            self.assertIn("status: doing", state_text)
            leftovers = [n for n in os.listdir(real) if ".tmp" in n]
            self.assertEqual(leftovers, [])


if __name__ == "__main__":
    unittest.main()
