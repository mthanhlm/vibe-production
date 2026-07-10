#!/usr/bin/env python3
"""vibe git safeguard (PreToolUse: Bash).

Blocks destructive git commands (exit 2) before they run — history rewrites
on shared state and irreversible working-tree/stash deletion. Active in every
project while the plugin is enabled (that is the point of a safeguard).

Bypass, in order of intent:
  - per-command, after explicit user confirmation: prefix with VIBE_GIT=allow
  - per-project: {"git_guard": "off"} in .vibe/config.json
  - global: environment VIBE_GIT_GUARD=off
Plain add/commit/push/pull/merge/rebase and --force-with-lease are never blocked.
"""
import json
import os
import re
import sys

RULES = [
    (re.compile(r"\bgit\s+push\b(?=.*(\s--force\b|\s-f\b))(?!.*--force-with-lease)", re.S),
     "force-push rewrites remote history for everyone",
     "use --force-with-lease, or confirm with the user first"),
    (re.compile(r"\bgit\s+push\b.*(\s--delete\b|\s+\S+\s+:\S)", re.S),
     "deletes a remote branch",
     "confirm the branch name with the user first"),
    (re.compile(r"\bgit\s+reset\s+(?=.*--hard)", re.S),
     "discards local commits and uncommitted changes irreversibly",
     "prefer `git stash` or `git reset --keep`; confirm first"),
    (re.compile(r"\bgit\s+clean\b(?=.*(-[a-zA-Z]*f))", re.S),
     "permanently deletes untracked files",
     "run `git clean -n` (dry run) and show the user what would be removed"),
    (re.compile(r"\bgit\s+(checkout|restore)\s+(--\s+)?\.(\s|$)"),
     "discards ALL uncommitted changes in the working tree",
     "prefer `git stash`; or restore specific files, not `.`"),
    (re.compile(r"\bgit\s+branch\s+(?=.*-D\b)", re.S),
     "force-deletes a branch even if unmerged",
     "use -d (safe delete) or confirm the branch is disposable"),
    (re.compile(r"\bgit\s+stash\s+(drop|clear)\b"),
     "deletes stashed work irreversibly",
     "list the stash and confirm with the user first"),
]

# Not destructive, but they write history/remote state — the user decides
# when that happens, not the model. Checked AFTER the destructive rules so
# e.g. force-push gets its more specific message.
APPROVAL_RE = re.compile(r"\bgit\s+(add|commit|push)\b")


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if payload.get("tool_name") != "Bash":
        sys.exit(0)
    command = (payload.get("tool_input") or {}).get("command") or ""
    if "git" not in command:
        sys.exit(0)

    # Bypasses.
    if os.environ.get("VIBE_GIT_GUARD", "").lower() == "off":
        sys.exit(0)
    if re.search(r"(^|\s|;|&&)\s*VIBE_GIT=allow\s", command + " "):
        sys.exit(0)
    project = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    try:
        with open(os.path.join(project, ".vibe", "config.json")) as f:
            if json.load(f).get("git_guard") == "off":
                sys.exit(0)
    except Exception:
        pass

    for pattern, reason, alternative in RULES:
        if pattern.search(command):
            print(
                f"VIBE GIT GUARD: blocked — this command {reason}. "
                f"Safer path: {alternative}. If the user has explicitly asked "
                f"for exactly this, confirm with them, then re-run the command "
                f"prefixed with `VIBE_GIT=allow `.",
                file=sys.stderr,
            )
            sys.exit(2)

    if APPROVAL_RE.search(command):
        print(
            "VIBE GIT GUARD: git add/commit/push need the user's explicit "
            "go-ahead — do not stage, commit, or push on your own initiative. "
            "If the user just asked for this (or has approved it), re-run the "
            "command prefixed with `VIBE_GIT=allow `.",
            file=sys.stderr,
        )
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
