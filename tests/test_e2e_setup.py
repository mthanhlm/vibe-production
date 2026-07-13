"""Subprocess tests for bin/vibe-e2e-setup (stdlib only).

The installer is exercised exactly as a skill would invoke it: a child
bash process with a controlled PATH of fake node/npm shims that log every
call. Never sourced, never mocked in-process. hookrunner.py is scoped to
hook scripts (WA-4), so this file carries its own tiny harness.
"""
import os
import shutil
import subprocess
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, "bin", "vibe-e2e-setup")
BASH = shutil.which("bash") or "/bin/bash"

FAKE_NODE = '#!/bin/sh\necho "node $@" >> "$VIBE_TEST_LOG"\nexit 0\n'
FAKE_NPM = (
    '#!/bin/sh\n'
    'echo "npm $@" >> "$VIBE_TEST_LOG"\n'
    'echo "skipdl=${PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD:-unset}" >> "$VIBE_TEST_LOG"\n'
    'mkdir -p node_modules/playwright node_modules/.bin\n'
    'exit 0\n'
)


class E2ESetupHarness(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="vibe-e2e-test.")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.e2e_dir = os.path.join(self.tmp, "toolkit")
        self.log = os.path.join(self.tmp, "calls.log")
        # utilbin: the only external tool the script needs besides node/npm
        self.utilbin = os.path.join(self.tmp, "utilbin")
        os.makedirs(self.utilbin)
        for tool in ("mkdir", "timeout"):
            os.symlink(shutil.which(tool), os.path.join(self.utilbin, tool))
        self.fakebin = os.path.join(self.tmp, "fakebin")
        os.makedirs(self.fakebin)

    def _shim(self, name, body):
        path = os.path.join(self.fakebin, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(body)
        os.chmod(path, 0o755)
        return path

    def run_setup(self, args=(), env=None, node=True, npm=True):
        if node and not os.path.exists(os.path.join(self.fakebin, "node")):
            self._shim("node", FAKE_NODE)
        if npm and not os.path.exists(os.path.join(self.fakebin, "npm")):
            self._shim("npm", FAKE_NPM)
        full_env = {
            "PATH": self.fakebin + os.pathsep + self.utilbin,
            "HOME": self.tmp,
            "VIBE_E2E_DIR": self.e2e_dir,
            "VIBE_TEST_LOG": self.log,
            "VIBE_E2E_PROBE_PATHS": "",
        }
        if env:
            full_env.update(env)
        proc = subprocess.run(
            [BASH, SCRIPT, *args], capture_output=True, text=True,
            env=full_env, cwd=self.tmp, timeout=30,
        )
        return proc.returncode, proc.stdout, proc.stderr

    def npm_calls(self):
        if not os.path.exists(self.log):
            return []
        with open(self.log, encoding="utf-8") as f:
            return [l for l in f.read().splitlines() if l.startswith("npm ")]

    def capability_lines(self, out):
        return [l for l in out.splitlines() if l.startswith("CAPABILITY: ")]


class TestInstall(E2ESetupHarness):
    def test_fresh_install_args_and_skip_download(self):
        rc, out, err = self.run_setup()
        self.assertEqual(rc, 0, err)
        calls = self.npm_calls()
        self.assertEqual(len(calls), 1)
        self.assertIn("install --no-fund --no-audit --loglevel=error playwright@^1", calls[0])
        with open(self.log, encoding="utf-8") as f:
            self.assertIn("skipdl=1", f.read())

    def test_package_json_written_without_npm_init(self):
        rc, _, err = self.run_setup()
        self.assertEqual(rc, 0, err)
        with open(os.path.join(self.e2e_dir, "package.json"), encoding="utf-8") as f:
            self.assertIn('"vibe-e2e"', f.read())

    def test_second_run_makes_zero_npm_calls(self):
        rc, _, _ = self.run_setup()
        self.assertEqual(rc, 0)
        os.remove(self.log)
        rc, out, err = self.run_setup()
        self.assertEqual(rc, 0, err)
        self.assertEqual(self.npm_calls(), [])
        self.assertEqual(len(self.capability_lines(out)), 1)

    def test_runs_dir_created_for_recipe_mktemp(self):
        rc, _, err = self.run_setup()
        self.assertEqual(rc, 0, err)
        self.assertTrue(os.path.isdir(os.path.join(self.e2e_dir, "runs")))

    def test_vibe_e2e_dir_override_honored(self):
        rc, _, _ = self.run_setup()
        self.assertEqual(rc, 0)
        self.assertTrue(os.path.isdir(
            os.path.join(self.e2e_dir, "node_modules", "playwright")))
        self.assertFalse(os.path.exists(
            os.path.join(self.tmp, ".claude", "vibe-e2e")))

    def test_missing_node_fails_actionably(self):
        rc, _, err = self.run_setup(node=False)
        self.assertNotEqual(rc, 0)
        self.assertIn("node", err)
        self.assertEqual(self.npm_calls(), [])

    def test_unknown_argument_rejected(self):
        rc, _, err = self.run_setup(args=("--frobnicate",))
        self.assertEqual(rc, 2)
        self.assertIn("unknown argument", err)


class TestProbe(E2ESetupHarness):
    def _browser(self, name):
        path = os.path.join(self.tmp, "browsers-bin", name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("#!/bin/sh\nexit 0\n")
        os.chmod(path, 0o755)
        return path

    def _cap(self, probe_paths):
        rc, out, err = self.run_setup(
            env={"VIBE_E2E_PROBE_PATHS": probe_paths})
        self.assertEqual(rc, 0, err)
        lines = self.capability_lines(out)
        self.assertEqual(len(lines), 1, out)
        return lines[0]

    def test_no_browsers_reports_none(self):
        self.assertEqual(self._cap(""), "CAPABILITY: none")

    def test_chrome_detected(self):
        self.assertEqual(self._cap(self._browser("google-chrome")),
                         "CAPABILITY: chrome")

    def test_precedence_chrome_over_edge_over_chromium(self):
        paths = os.pathsep.join([
            self._browser("chromium-browser"),
            self._browser("msedge"),
            self._browser("google-chrome-stable"),
        ])
        self.assertEqual(self._cap(paths), "CAPABILITY: chrome")

    def test_edge_over_chromium(self):
        paths = os.pathsep.join([
            self._browser("chromium"),
            self._browser("microsoft-edge"),
        ])
        self.assertEqual(self._cap(paths), "CAPABILITY: msedge")

    def test_nonexecutable_candidate_ignored(self):
        path = self._browser("google-chrome")
        os.chmod(path, 0o644)
        self.assertEqual(self._cap(path), "CAPABILITY: none")

    def test_headless_shell_detected_when_no_system_browser(self):
        os.makedirs(os.path.join(
            self.e2e_dir, "browsers", "chromium_headless_shell-999"))
        self.assertEqual(self._cap(""), "CAPABILITY: headless-shell")

    def test_system_browser_outranks_headless_shell(self):
        os.makedirs(os.path.join(
            self.e2e_dir, "browsers", "chromium_headless_shell-999"))
        self.assertEqual(self._cap(self._browser("chromium")),
                         "CAPABILITY: chromium")


if __name__ == "__main__":
    unittest.main()
