#!/usr/bin/env python3
"""vibe plan stamp (PostToolUse: ExitPlanMode).

When the user approves a plan in native plan mode, persist it to
.vibe/plan.md (opening the plan gate) and update .vibe/STATE.md so any
fresh session knows what to do next. Only active in projects that opted in
(.vibe/ exists). ExitPlanMode does not fire in headless runs — /vibe:plan
stamps the artifact itself as the portable path.
"""
import datetime
import json
import os
import re
import sys


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return

    project = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    vibe_dir = os.path.join(project, ".vibe")
    if not os.path.isdir(vibe_dir):
        return

    plan_md = (payload.get("tool_input") or {}).get("plan") or ""
    if not plan_md.strip():
        return

    plan_path = os.path.join(vibe_dir, "plan.md")
    # Never clobber an existing approved plan mid-feature.
    if os.path.isfile(plan_path):
        try:
            with open(plan_path, encoding="utf-8") as f:
                if re.search(r"^status:\s*approved\s*$", f.read(2000), re.MULTILINE):
                    return
        except Exception:
            pass

    today = datetime.date.today().isoformat()
    title_m = re.search(r"^#\s+(.+)$", plan_md, re.MULTILINE)
    title = title_m.group(1).strip() if title_m else "Untitled plan"

    if not plan_md.lstrip().startswith("---"):
        plan_md = (
            f"---\nstatus: approved\ncreated: {today}\nretry_budget: 5\n"
            f"source: plan-mode\n---\n\n{plan_md}"
        )

    with open(plan_path, "w", encoding="utf-8") as f:
        f.write(plan_md)

    state_path = os.path.join(vibe_dir, "STATE.md")
    with open(state_path, "w", encoding="utf-8") as f:
        f.write(
            f"---\nstatus: doing\nplan: .vibe/plan.md\nnext_action: /vibe:check\n"
            f"check_attempts: 0\nupdated: {today}\n---\n\n"
            f"# Current work\n\n{title}\n\n"
            "Plan approved via plan mode. Implement, then run /vibe:check.\n"
        )

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": (
                "VIBE: approved plan stamped to .vibe/plan.md (gate open) and "
                ".vibe/STATE.md updated. If the plan lacks an 'Objective' and a "
                "'Done means' checklist, offer the user /vibe:plan to formalize "
                "it. If plan_language in .vibe/config.json is set (e.g. vi), "
                "offer to write the translated .vibe/plan.<lang>.md."
            ),
        }
    }))


if __name__ == "__main__":
    main()
