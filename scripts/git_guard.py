#!/usr/bin/env python3
"""vibe git safeguard (PreToolUse: Bash).

Blocks destructive git commands (exit 2) before they run — history rewrites
on shared state and irreversible working-tree/stash deletion. Active in every
project while the plugin is enabled (that is the point of a safeguard).

Bypass, in order of intent:
  - per-command, after explicit user confirmation: prefix with VIBE_GIT=allow
  - per-project: {"git_guard": "off"} in .vibe/config.json
  - global: environment VIBE_GIT_GUARD=off
Plain pull/merge/rebase/fetch are never touched. add/commit/push — every
push, including --force-with-lease — ask for the user's explicit go-ahead
first; --force-with-lease is only exempt from the DESTRUCTIVE force-push
rule, not from approval.

Scope: this is regex matching on the raw command string — evadable via
subshells, aliases, $IFS tricks, or exotic quoting. It is a guardrail
against accidental destruction, not a sandbox against adversarial input.
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


def _debug(context, exc):
    # R-3: swallowed failures leave a breadcrumb when VIBE_DEBUG is set.
    if os.environ.get("VIBE_DEBUG"):
        print(f"vibe-debug[git-guard] {context}: {type(exc).__name__}: {exc}",
              file=sys.stderr)


def main():
    # Global emergency bypass first: it must keep working even when the
    # payload itself is broken, or it is no emergency bypass.
    if os.environ.get("VIBE_GIT_GUARD", "").lower() == "off":
        sys.exit(0)

    try:
        payload = json.load(sys.stdin)
    except Exception as exc:
        _debug("parsing hook payload from stdin", exc)
        payload = None
    if not isinstance(payload, dict):
        # R-2: fail CLOSED — a guard that waves through whatever it cannot
        # read is no guard at all.
        print(
            "VIBE GIT GUARD: the hook payload on stdin was unreadable, so "
            "this command cannot be checked for destructive git usage and "
            "is blocked. If the harness is genuinely broken, emergency "
            "bypass: set VIBE_GIT_GUARD=off.",
            file=sys.stderr,
        )
        sys.exit(2)

    # R-6: shape-validate every payload field; wrong types read as absent.
    tool_name = payload.get("tool_name")
    if not isinstance(tool_name, str) or tool_name != "Bash":
        sys.exit(0)
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        tool_input = {}
    command = tool_input.get("command")
    if not isinstance(command, str):
        command = ""
    if "git" not in command:
        sys.exit(0)

    # Bypasses.
    if re.search(r"(^|\s|;|&&)\s*VIBE_GIT=allow\s", command + " "):
        sys.exit(0)
    cwd = payload.get("cwd")
    if not isinstance(cwd, str) or not cwd:
        cwd = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    try:
        with open(os.path.join(cwd, ".vibe", "config.json")) as f:
            if json.load(f).get("git_guard") == "off":
                sys.exit(0)
    except Exception as exc:
        # Deliberate swallow, and it fails SAFE: a missing, unreadable, or
        # malformed config only means the off-switch is absent — guard on.
        _debug("reading .vibe/config.json off-switch", exc)

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
