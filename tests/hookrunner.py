"""Shared subprocess harness for hook-script tests (stdlib only).

Every test runs a hook script exactly the way the Claude Code harness does:
a child process with a JSON payload on stdin, asserting exit code, stderr,
and stdout. Never import the scripts as modules.
"""
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(REPO, "scripts")

# Session variables that must never leak from the developer's environment
# into a test subprocess.
ISOLATE = ("VIBE_GATE", "VIBE_GIT_GUARD", "VIBE_GIT", "VIBE_DEBUG",
           "CLAUDE_PROJECT_DIR", "TMPDIR")


def run_hook(script, payload, env=None, cwd=None, timeout=30):
    """Run scripts/<script> with `payload` on stdin.

    payload: dict (JSON-encoded) or raw str (sent as-is, e.g. malformed).
    env: extra environment overrides for the child.
    Returns (returncode, stdout, stderr).
    """
    data = payload if isinstance(payload, str) else json.dumps(payload)
    full_env = {k: v for k, v in os.environ.items() if k not in ISOLATE}
    if env:
        full_env.update(env)
    proc = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS, script)],
        input=data, capture_output=True, text=True,
        env=full_env, cwd=cwd or REPO, timeout=timeout,
    )
    return proc.returncode, proc.stdout, proc.stderr


def make_project(tmpdir, vibe=True, config=None, plan=None):
    """Create a throwaway project dir under tmpdir; return its path.

    config: dict or raw str written to .vibe/config.json when given.
    plan:   raw str written to .vibe/plan.md when given.
    """
    proj = os.path.join(tmpdir, "proj")
    os.makedirs(proj, exist_ok=True)
    if vibe:
        vibe_dir = os.path.join(proj, ".vibe")
        os.makedirs(vibe_dir, exist_ok=True)
        if config is not None:
            text = config if isinstance(config, str) else json.dumps(config)
            with open(os.path.join(vibe_dir, "config.json"), "w") as f:
                f.write(text)
        if plan is not None:
            with open(os.path.join(vibe_dir, "plan.md"), "w") as f:
                f.write(plan)
    return proj


APPROVED_PLAN = "---\nstatus: approved\ncreated: 2026-01-01\n---\n# T\n"
DRAFT_PLAN = "---\nstatus: draft\ncreated: 2026-01-01\n---\n# T\n"
