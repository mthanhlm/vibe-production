"""Behavior-table tests for scripts/git_guard.py.

Subprocess-level via hookrunner: each case runs the script exactly as the
Claude Code harness does (JSON payload on stdin) and asserts outcomes —
exit code, stderr text, and bypass behavior.
"""
import os
import tempfile
import unittest

try:
    from tests.hookrunner import run_hook, make_project
except ImportError:  # `unittest discover -s tests` imports us top-level
    from hookrunner import run_hook, make_project

SCRIPT = "git_guard.py"
BLOCK_MARKER = "VIBE GIT GUARD: blocked"
APPROVAL_MARKER = "explicit go-ahead"


def bash_payload(command, cwd):
    return {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": cwd}


class GitGuardTest(unittest.TestCase):
    def run_cmd(self, command, config=None, env=None):
        """Run the guard on `command` in a fresh throwaway project."""
        with tempfile.TemporaryDirectory() as td:
            proj = make_project(td, config=config)
            return run_hook(SCRIPT, bash_payload(command, proj), env=env)

    # --- tool/command shape: nothing git-visible -> allow -------------

    def test_non_bash_tool_allowed(self):
        with tempfile.TemporaryDirectory() as td:
            proj = make_project(td)
            rc, out, err = run_hook(SCRIPT, {
                "tool_name": "Read",
                "tool_input": {"command": "git push --force"},
                "cwd": proj,
            })
        self.assertEqual(rc, 0)
        self.assertEqual(err, "")

    def test_command_without_git_allowed(self):
        rc, out, err = self.run_cmd("ls -la && make test")
        self.assertEqual(rc, 0)
        self.assertEqual(err, "")

    def test_tool_input_not_dict_allowed(self):
        with tempfile.TemporaryDirectory() as td:
            proj = make_project(td)
            rc, out, err = run_hook(SCRIPT, {
                "tool_name": "Bash",
                "tool_input": "git push --force",
                "cwd": proj,
            })
        self.assertEqual(rc, 0)
        self.assertEqual(err, "")

    def test_command_not_str_allowed(self):
        with tempfile.TemporaryDirectory() as td:
            proj = make_project(td)
            rc, out, err = run_hook(SCRIPT, {
                "tool_name": "Bash",
                "tool_input": {"command": ["git", "push", "--force"]},
                "cwd": proj,
            })
        self.assertEqual(rc, 0)
        self.assertEqual(err, "")

    def test_tool_name_not_str_allowed(self):
        with tempfile.TemporaryDirectory() as td:
            proj = make_project(td)
            rc, out, err = run_hook(SCRIPT, {
                "tool_name": ["Bash"],
                "tool_input": {"command": "git push --force"},
                "cwd": proj,
            })
        self.assertEqual(rc, 0)
        self.assertEqual(err, "")

    def test_cwd_not_str_still_guards(self):
        with tempfile.TemporaryDirectory() as td:
            make_project(td)
            rc, out, err = run_hook(SCRIPT, {
                "tool_name": "Bash",
                "tool_input": {"command": "git push --force"},
                "cwd": 42,
            })
        self.assertEqual(rc, 2)
        self.assertIn(BLOCK_MARKER, err)

    # --- destructive rules -> block (exit 2) --------------------------

    def test_force_push_blocked(self):
        rc, out, err = self.run_cmd("git push --force")
        self.assertEqual(rc, 2)
        self.assertIn(BLOCK_MARKER, err)
        self.assertIn("force-push", err)

    def test_force_with_lease_not_destructive_but_needs_approval(self):
        # Exempt from the force-push DESTRUCTIVE rule, still a push: the
        # approval gate applies until the user says go.
        rc, out, err = self.run_cmd("git push --force-with-lease")
        self.assertEqual(rc, 2)
        self.assertNotIn("force-push", err)
        self.assertIn("go-ahead", err)

    def test_force_with_lease_with_allow_prefix_passes(self):
        rc, out, err = self.run_cmd("VIBE_GIT=allow git push --force-with-lease")
        self.assertEqual(rc, 0)
        self.assertEqual(err, "")

    def test_push_delete_flag_blocked(self):
        rc, out, err = self.run_cmd("git push origin --delete b")
        self.assertEqual(rc, 2)
        self.assertIn("remote branch", err)

    def test_push_colon_refspec_blocked(self):
        rc, out, err = self.run_cmd("git push origin :b")
        self.assertEqual(rc, 2)
        self.assertIn("remote branch", err)

    def test_reset_hard_blocked(self):
        rc, out, err = self.run_cmd("git reset --hard HEAD~1")
        self.assertEqual(rc, 2)
        self.assertIn(BLOCK_MARKER, err)

    def test_clean_force_blocked(self):
        rc, out, err = self.run_cmd("git clean -fd")
        self.assertEqual(rc, 2)
        self.assertIn("untracked files", err)

    def test_clean_dry_run_allowed(self):
        rc, out, err = self.run_cmd("git clean -n")
        self.assertEqual(rc, 0)
        self.assertEqual(err, "")

    def test_checkout_dot_blocked(self):
        rc, out, err = self.run_cmd("git checkout .")
        self.assertEqual(rc, 2)
        self.assertIn("uncommitted changes", err)

    def test_checkout_branch_allowed(self):
        rc, out, err = self.run_cmd("git checkout main")
        self.assertEqual(rc, 0)
        self.assertEqual(err, "")

    def test_restore_dot_blocked(self):
        rc, out, err = self.run_cmd("git restore .")
        self.assertEqual(rc, 2)
        self.assertIn("uncommitted changes", err)

    def test_branch_force_delete_blocked(self):
        rc, out, err = self.run_cmd("git branch -D x")
        self.assertEqual(rc, 2)
        self.assertIn(BLOCK_MARKER, err)

    def test_branch_safe_delete_allowed(self):
        rc, out, err = self.run_cmd("git branch -d x")
        self.assertEqual(rc, 0)
        self.assertEqual(err, "")

    def test_stash_drop_blocked(self):
        rc, out, err = self.run_cmd("git stash drop")
        self.assertEqual(rc, 2)
        self.assertIn("stashed work", err)

    def test_stash_list_allowed(self):
        rc, out, err = self.run_cmd("git stash list")
        self.assertEqual(rc, 0)
        self.assertEqual(err, "")

    # --- add/commit/push need explicit approval -----------------------

    def test_add_needs_approval(self):
        rc, out, err = self.run_cmd("git add -A")
        self.assertEqual(rc, 2)
        self.assertIn(APPROVAL_MARKER, err)
        self.assertIn("VIBE_GIT=allow", err)

    def test_commit_needs_approval(self):
        rc, out, err = self.run_cmd("git commit -m x")
        self.assertEqual(rc, 2)
        self.assertIn(APPROVAL_MARKER, err)

    def test_push_needs_approval(self):
        rc, out, err = self.run_cmd("git push")
        self.assertEqual(rc, 2)
        self.assertIn(APPROVAL_MARKER, err)

    def test_allow_prefix_bypasses_approval(self):
        rc, out, err = self.run_cmd("VIBE_GIT=allow git commit -m x")
        self.assertEqual(rc, 0)
        self.assertEqual(err, "")

    # --- off-switches --------------------------------------------------

    def test_env_off_bypasses_force_push(self):
        rc, out, err = self.run_cmd("git push --force",
                                    env={"VIBE_GIT_GUARD": "off"})
        self.assertEqual(rc, 0)
        self.assertEqual(err, "")

    def test_env_off_bypasses_malformed_stdin(self):
        rc, out, err = run_hook(SCRIPT, "not json{",
                                env={"VIBE_GIT_GUARD": "off"})
        self.assertEqual(rc, 0)
        self.assertEqual(err, "")

    def test_config_off_bypasses_force_push(self):
        rc, out, err = self.run_cmd("git push --force",
                                    config={"git_guard": "off"})
        self.assertEqual(rc, 0)
        self.assertEqual(err, "")

    # --- broken config keeps the guard active (fail safe) ---------------

    def test_malformed_config_keeps_guard_active(self):
        rc, out, err = self.run_cmd("git push --force", config="not json{")
        self.assertEqual(rc, 2)
        self.assertIn(BLOCK_MARKER, err)

    def test_malformed_config_breadcrumb_with_debug(self):
        rc, out, err = self.run_cmd("git push --force", config="not json{",
                                    env={"VIBE_DEBUG": "1"})
        self.assertEqual(rc, 2)
        self.assertIn("vibe-debug[git-guard]", err)
        self.assertIn(BLOCK_MARKER, err)

    def test_malformed_config_silent_without_debug(self):
        rc, out, err = self.run_cmd("git push --force", config="not json{")
        self.assertEqual(rc, 2)
        self.assertNotIn("vibe-debug", err)

    def test_unreadable_config_keeps_guard_active(self):
        # A directory where the config file should be makes open() fail
        # deterministically for any user (chmod tricks don't survive root).
        with tempfile.TemporaryDirectory() as td:
            proj = make_project(td)
            os.makedirs(os.path.join(proj, ".vibe", "config.json"))
            rc, out, err = run_hook(SCRIPT,
                                    bash_payload("git push --force", proj))
        self.assertEqual(rc, 2)
        self.assertIn(BLOCK_MARKER, err)

    # --- broken payload fails CLOSED (R-2) -------------------------------

    def test_malformed_stdin_fails_closed(self):
        rc, out, err = run_hook(SCRIPT, "not json{")
        self.assertEqual(rc, 2)
        self.assertIn("VIBE_GIT_GUARD=off", err)

    def test_malformed_stdin_breadcrumb_with_debug(self):
        rc, out, err = run_hook(SCRIPT, "not json{", env={"VIBE_DEBUG": "1"})
        self.assertEqual(rc, 2)
        self.assertIn("vibe-debug[git-guard]", err)
        self.assertIn("VIBE_GIT_GUARD=off", err)

    def test_list_payload_fails_closed(self):
        rc, out, err = run_hook(SCRIPT, ["not", "a", "dict"])
        self.assertEqual(rc, 2)
        self.assertIn("VIBE_GIT_GUARD=off", err)


if __name__ == "__main__":
    unittest.main()
