#!/usr/bin/env python3
"""vibe deviation nudge (PostToolUse: Edit|Write).

Flag-don't-conform: when an edited file contains a pattern that violates a
production standard a linter can't catch, inject ONE short note (with the
rule ID, the fix, and an escape hatch) via additionalContext. Deduplicated
per session and per rule so it never nags twice. Advisory only — never blocks.
"""
import json
import os
import re
import sys
import tempfile

# Pure-data pattern list. Only patterns a linter typically can't/won't catch.
# Fields: id, langs (extensions), regex, note (rule + fix + escape hatch).
PATTERNS = [
    {
        "id": "swallowed-exception",
        "exts": (".py",),
        "regex": re.compile(r"except[^:\n]*:\s*(pass|\.\.\.)\s*$", re.MULTILINE),
        "note": (
            "Swallowed exception (`except: pass`) — errors disappear silently in "
            "production [OWASP Top-10 A09, vibe error-handling ref]. Log with context "
            "or re-raise; catch the narrowest type. If intentional, add a comment "
            "saying why."
        ),
    },
    {
        "id": "empty-catch",
        "exts": (".js", ".jsx", ".ts", ".tsx"),
        "regex": re.compile(r"catch\s*(\([^)]*\))?\s*\{\s*\}"),
        "note": (
            "Empty catch block — failures vanish silently in production [OWASP "
            "Top-10 A09, vibe error-handling ref]. Log with context or rethrow. "
            "If intentional, add a comment saying why."
        ),
    },
    {
        "id": "sql-string-build",
        "exts": (".py", ".js", ".ts", ".php", ".rb", ".go", ".java"),
        "regex": re.compile(
            r"""(?ix)
            (execute|query|raw)\s*\(\s*
            (f["']\s*(select|insert|update|delete)   # python f-string
            |["']\s*(select|insert|update|delete)[^"']*["']\s*[+%]  # concat/interp
            |`[^`]*(select|insert|update|delete)[^`]*\$\{)          # js template
            """
        ),
        "note": (
            "SQL built from string interpolation/concatenation — injection risk "
            "[ASVS 5.3.4, OWASP SQLi Cheat Sheet]. Use parameterized queries or the "
            "ORM binding API. If this string contains no user input, note that in a "
            "comment."
        ),
    },
    {
        "id": "hardcoded-secret",
        "exts": (".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".java", ".rb", ".yaml", ".yml"),
        "regex": re.compile(
            r"""(?i)(api[_-]?key|secret|password|token|private[_-]?key)\s*[:=]\s*["'][A-Za-z0-9_\-/+]{16,}["']"""
        ),
        "note": (
            "Possible hardcoded credential [ASVS 2.10.4, 12factor III (config in "
            "env)]. Load secrets from environment/secret manager; never commit "
            "them. If this is a placeholder or test fixture, name it clearly (e.g. "
            "`FAKE_...`)."
        ),
    },
    {
        "id": "http-no-timeout",
        "exts": (".py",),
        "regex": re.compile(r"requests\.(get|post|put|patch|delete|head)\((?![^)\n]*timeout=)[^)\n]*\)"),
        "note": (
            "HTTP call without a timeout — one slow dependency can hang the whole "
            "service [Azure Retry/Timeout patterns, vibe system-design ref]. Pass "
            "an explicit timeout=. If blocking forever is intended, say why in a "
            "comment."
        ),
    },
]


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return

    project = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    # Advisory nudges are also opt-in per project, same switch as the gate.
    if not os.path.isdir(os.path.join(project, ".vibe")):
        return

    file_path = (payload.get("tool_input") or {}).get("file_path") or ""
    ext = os.path.splitext(file_path)[1].lower()
    if not file_path or not os.path.isfile(file_path):
        return
    # Never scan tests/fixtures/vendored code — that's nagging, not signal.
    # Match whole path segments and test-file naming, not substrings.
    rel = os.path.relpath(os.path.realpath(file_path), project)
    segments = {s.lower() for s in rel.split(os.sep)[:-1]}
    if segments & {"test", "tests", "spec", "specs", "__tests__", "fixtures",
                   "node_modules", "vendor", ".vibe", ".claude"}:
        return
    base = os.path.basename(file_path).lower()
    if base.startswith(("test_", "conftest")) or re.search(r"([._-](test|spec))\.[a-z]+$", base):
        return

    try:
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            content = f.read(200_000)
    except Exception:
        return

    session = payload.get("session_id", "nosession")
    seen_path = os.path.join(tempfile.gettempdir(), f"vibe-nudge-{session}.json")
    try:
        with open(seen_path) as f:
            seen = set(json.load(f))
    except Exception:
        seen = set()

    notes = []
    for p in PATTERNS:
        if p["id"] in seen or ext not in p["exts"]:
            continue
        if p["regex"].search(content):
            notes.append(f"- [{p['id']}] {p['note']}")
            seen.add(p["id"])

    if not notes:
        return

    try:
        with open(seen_path, "w") as f:
            json.dump(sorted(seen), f)
    except Exception:
        pass

    context = (
        "VIBE STANDARDS NOTE (one-time, advisory — do not treat as a blocker):\n"
        + "\n".join(notes[:3])
        + "\nFix now if in scope; otherwise tell the user and suggest adding it to .vibe/ROADMAP.md."
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": context,
        }
    }))


if __name__ == "__main__":
    main()
