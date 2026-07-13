"""Subprocess tests for bin/vibe-pptx-setup (stdlib only).

Same harness shape as test_e2e_setup.py: a controlled PATH of fake
python3 shims that log every call; the installer runs as a child bash
process, never sourced. The fake `python3 -m venv` materializes a fake
venv whose python/pip behave like the real thing (import fails until
pip "installs").
"""
import os
import shutil
import subprocess
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, "bin", "vibe-pptx-setup")
BASH = shutil.which("bash") or "/bin/bash"

VENV_PYTHON = (
    '#!/bin/sh\n'
    'echo "venvpython $@" >> "$VIBE_TEST_LOG"\n'
    'if [ "$1" = "-c" ]; then\n'
    '  [ -f "$(dirname "$0")/../installed" ] && exit 0 || exit 1\n'
    'fi\n'
    'exit 0\n'
)
VENV_PIP_OK = (
    '#!/bin/sh\n'
    'echo "pip $@" >> "$VIBE_TEST_LOG"\n'
    'touch "$(dirname "$0")/../installed"\n'
    'exit 0\n'
)
VENV_PIP_FAIL = (
    '#!/bin/sh\n'
    'echo "pip $@" >> "$VIBE_TEST_LOG"\n'
    'exit 1\n'
)


def fake_python3(pip_body):
    quoted_pip = pip_body.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$")
    quoted_py = VENV_PYTHON.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$")
    return (
        '#!/bin/sh\n'
        'echo "python3 $@" >> "$VIBE_TEST_LOG"\n'
        'if [ "$1" = "-m" ] && [ "$2" = "venv" ]; then\n'
        '  d="$3"\n'
        '  mkdir -p "$d/bin"\n'
        f'  printf "%b" "{quoted_py}" > "$d/bin/python"\n'
        f'  printf "%b" "{quoted_pip}" > "$d/bin/pip"\n'
        '  chmod +x "$d/bin/python" "$d/bin/pip"\n'
        'fi\n'
        'exit 0\n'
    )


FAKE_PYTHON3_VENV_FAIL = (
    '#!/bin/sh\n'
    'echo "python3 $@" >> "$VIBE_TEST_LOG"\n'
    'if [ "$1" = "-m" ] && [ "$2" = "venv" ]; then exit 1; fi\n'
    'exit 0\n'
)


class PptxSetupHarness(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="vibe-pptx-test.")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.pptx_dir = os.path.join(self.tmp, "toolkit")
        self.log = os.path.join(self.tmp, "calls.log")
        self.utilbin = os.path.join(self.tmp, "utilbin")
        os.makedirs(self.utilbin)
        for tool in ("mkdir", "timeout", "dirname", "touch", "chmod", "printf"):
            path = shutil.which(tool)
            if path:
                os.symlink(path, os.path.join(self.utilbin, tool))
        self.fakebin = os.path.join(self.tmp, "fakebin")
        os.makedirs(self.fakebin)

    def _shim(self, name, body):
        path = os.path.join(self.fakebin, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(body)
        os.chmod(path, 0o755)

    def run_setup(self, args=(), python3=True, pip_body=VENV_PIP_OK):
        if python3 and not os.path.exists(os.path.join(self.fakebin, "python3")):
            body = python3 if isinstance(python3, str) else fake_python3(pip_body)
            self._shim("python3", body)
        env = {
            "PATH": self.fakebin + os.pathsep + self.utilbin,
            "HOME": self.tmp,
            "VIBE_PPTX_DIR": self.pptx_dir,
            "VIBE_TEST_LOG": self.log,
        }
        proc = subprocess.run(
            [BASH, SCRIPT, *args], capture_output=True, text=True,
            env=env, cwd=self.tmp, timeout=30,
        )
        return proc.returncode, proc.stdout, proc.stderr

    def calls(self, prefix):
        if not os.path.exists(self.log):
            return []
        with open(self.log, encoding="utf-8") as f:
            return [l for l in f.read().splitlines() if l.startswith(prefix)]

    def status_lines(self, out):
        return [l for l in out.splitlines() if l.startswith("PPTX: ")]


class TestPptxSetup(PptxSetupHarness):
    def test_fresh_install_ready_and_pinned(self):
        rc, out, err = self.run_setup()
        self.assertEqual(rc, 0, err)
        self.assertEqual(self.status_lines(out), ["PPTX: ready"])
        pips = self.calls("pip ")
        self.assertEqual(len(pips), 1)
        self.assertIn("install --quiet python-pptx<2", pips[0])

    def test_second_run_zero_pip_calls(self):
        rc, _, _ = self.run_setup()
        self.assertEqual(rc, 0)
        os.remove(self.log)
        rc, out, err = self.run_setup()
        self.assertEqual(rc, 0, err)
        self.assertEqual(self.calls("pip "), [])
        self.assertEqual(self.calls("python3 "), [])  # venv not recreated
        self.assertEqual(self.status_lines(out), ["PPTX: ready"])

    def test_missing_python3(self):
        rc, out, err = self.run_setup(python3=False)
        self.assertEqual(rc, 1)
        self.assertEqual(self.status_lines(out), ["PPTX: no-python3"])
        self.assertIn("python3", err)

    def test_venv_failure_actionable(self):
        rc, out, err = self.run_setup(python3=FAKE_PYTHON3_VENV_FAIL)
        self.assertEqual(rc, 1)
        self.assertEqual(self.status_lines(out), ["PPTX: venv-failed"])
        self.assertIn("python3-venv", err)

    def test_install_failure(self):
        rc, out, err = self.run_setup(pip_body=VENV_PIP_FAIL)
        self.assertEqual(rc, 1)
        self.assertEqual(self.status_lines(out), ["PPTX: install-failed"])
        self.assertIn("pip install", err)

    def test_vibe_pptx_dir_honored(self):
        rc, _, _ = self.run_setup()
        self.assertEqual(rc, 0)
        self.assertTrue(os.path.isdir(os.path.join(self.pptx_dir, "bin")))
        self.assertFalse(os.path.exists(
            os.path.join(self.tmp, ".claude", "vibe-pptx")))

    def test_unknown_argument_rejected(self):
        rc, _, err = self.run_setup(args=("--frobnicate",))
        self.assertEqual(rc, 2)
        self.assertIn("unknown argument", err)


if __name__ == "__main__":
    unittest.main()
