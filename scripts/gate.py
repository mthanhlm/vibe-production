#!/usr/bin/env python3
"""vibe plan gate (PreToolUse: Edit|Write|NotebookEdit).

Blocks file writes (exit 2) until an approved plan exists at .vibe/plan.md.
The gate is OPT-IN per project: it only activates when a .vibe/ directory
exists (created by /vibe:setup or /vibe:plan). Exit 2 blocks the tool call
and feeds stderr back to Claude; exit 0 allows it.
"""
import json
import os
import re
import sys


def allow():
    sys.exit(0)


def block(msg):
    print(msg, file=sys.stderr)
    sys.exit(2)


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        allow()  # malformed input must never brick the session

    project = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    project = os.path.realpath(project)
    vibe_dir = os.path.join(project, ".vibe")

    # Gate is opt-in: inactive until the project has a .vibe/ directory.
    if not os.path.isdir(vibe_dir):
        allow()

    # Kill switch: VIBE_GATE=off or "gate": "off" in .vibe/config.json.
    if os.environ.get("VIBE_GATE", "").lower() == "off":
        allow()
    try:
        with open(os.path.join(vibe_dir, "config.json")) as f:
            if json.load(f).get("gate") == "off":
                allow()
    except Exception:
        pass

    # Plan mode is read-only research plus the plan itself — never gate it.
    if payload.get("permission_mode") == "plan":
        allow()

    file_path = (payload.get("tool_input") or {}).get("file_path") or ""
    if not file_path:
        allow()
    real = os.path.realpath(file_path)

    # Writes outside the project (scratchpads, /tmp) are not gated.
    if not real.startswith(project + os.sep):
        allow()

    rel = os.path.relpath(real, project)

    # Loop artifacts, rules, memory, and learnings are always writable —
    # otherwise the plan could never be written to open the gate.
    exempt = (".vibe/", ".claude/", "docs/solutions/")
    if rel.startswith(exempt) or rel in ("CLAUDE.md", ".gitignore"):
        allow()

    # Gate token: .vibe/plan.md with frontmatter `status: approved`.
    plan_path = os.path.join(vibe_dir, "plan.md")
    if os.path.isfile(plan_path):
        try:
            with open(plan_path, encoding="utf-8") as f:
                head = f.read(2000)
            if re.search(r"^status:\s*approved\s*$", head, re.MULTILINE):
                allow()
            block(
                "PLAN GATE: .vibe/plan.md exists but is not approved "
                "(frontmatter must say `status: approved`). Present the plan "
                "to the user for approval, set the status, then retry."
            )
        except Exception:
            allow()

    block(
        "PLAN GATE: no approved plan at .vibe/plan.md — this project requires "
        "a plan before code. Ask the user to run /vibe:plan (or /vibe:plan "
        "quick for a one-sentence diff). Do NOT retry this write until a plan "
        "is approved."
    )


if __name__ == "__main__":
    main()
