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
import tempfile


def _debug(context, exc):
    # R-3: swallowed failures leave a breadcrumb when VIBE_DEBUG is set.
    if os.environ.get("VIBE_DEBUG"):
        print(f"vibe-debug[stamp-plan] {context}: {type(exc).__name__}: {exc}",
              file=sys.stderr)


def _write_atomic(vibe_dir, name, text):
    # R-4: temp file in the same directory + os.replace, so readers never
    # see a half-written plan.md/STATE.md.
    fd, tmp = tempfile.mkstemp(prefix=name + ".", suffix=".tmp", dir=vibe_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, os.path.join(vibe_dir, name))
    except Exception:
        try:
            os.unlink(tmp)
        except Exception as exc:
            _debug(f"removing temp file {tmp}", exc)
        raise


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception as exc:
        _debug("parsing stdin payload", exc)
        return
    # R-6: a payload that is not a JSON object is malformed.
    if not isinstance(payload, dict):
        return

    cwd = payload.get("cwd")
    project = ((cwd if isinstance(cwd, str) else "")
               or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    vibe_dir = os.path.join(project, ".vibe")
    if not os.path.isdir(vibe_dir):
        return
    # R-8: resolve a symlinked .vibe so the temp file and its os.replace
    # target live in the same real directory.
    vibe_dir = os.path.realpath(vibe_dir)

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        tool_input = {}
    plan_md = tool_input.get("plan")
    if not isinstance(plan_md, str):
        plan_md = ""
    if not plan_md.strip():
        return

    plan_path = os.path.join(vibe_dir, "plan.md")
    # Never clobber an existing approved plan mid-feature.
    if os.path.isfile(plan_path):
        try:
            with open(plan_path, encoding="utf-8") as f:
                if re.search(r"^status:\s*approved\s*$", f.read(2000), re.MULTILINE):
                    return
        except Exception as exc:
            _debug("re-checking existing plan.md approval", exc)

    today = datetime.date.today().isoformat()
    title_m = re.search(r"^#\s+(.+)$", plan_md, re.MULTILINE)
    title = title_m.group(1).strip() if title_m else "Untitled plan"

    if not plan_md.lstrip().startswith("---"):
        plan_md = (
            f"---\nstatus: approved\ncreated: {today}\nretry_budget: 5\n"
            f"source: plan-mode\n---\n\n{plan_md}"
        )

    try:
        _write_atomic(vibe_dir, "plan.md", plan_md)
    except Exception as exc:
        # A failed stamp must not crash the hook; without plan.md there is
        # no approval to record, so STATE.md is skipped too.
        _debug("writing .vibe/plan.md", exc)
        return

    try:
        _write_atomic(
            vibe_dir, "STATE.md",
            f"---\nstatus: doing\nplan: .vibe/plan.md\nnext_action: /vibe:check\n"
            f"check_attempts: 0\nupdated: {today}\n---\n\n"
            f"# Current work\n\n{title}\n\n"
            "Plan approved via plan mode. Implement, then run /vibe:check.\n",
        )
    except Exception as exc:
        _debug("writing .vibe/STATE.md", exc)
        return

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
