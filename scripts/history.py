#!/usr/bin/env python3
"""vibe chat-history archiver (SessionStart | SessionEnd).

Copies session transcripts from ~/.claude/projects/ into a permanent
archive (default ~/.claude/vibe-history/) before Claude Code's 30-day
cleanup prunes them, and appends one summary line per archive event to
<archive>/index.jsonl. Append-only, idempotent, lock-free: concurrent
hooks copy identical bytes atomically (mkstemp + os.replace) and duplicate
index lines are deduped latest-wins by session_id on read. The index is a
rebuildable cache — the raw copies are the source of truth.

SessionEnd archives the current session; SessionStart additionally sweeps
every project dir (rescues hard-killed sessions, backfills history) under
a byte + time budget so a session start is never stalled.

Side-effect only: always exits 0, never writes to stdout. Archive paths
are derived from real directory listings and transcript_path's own
dirname — payload strings never feed a path (R-9 by construction).
Opt out per project with {"history": "off"} in .vibe/config.json.
"""
import json
import os
import re
import shutil
import sys
import tempfile
import time
from datetime import datetime, timezone

INDEX_VERSION = 1
DEFAULT_BUDGET_BYTES = 50 * 1024 * 1024
DEADLINE_SECONDS = 10
HEAD_PARSE_LINES = 200  # head fields (cwd/branch/first prompt) live early
TEXT_FIELD_LIMIT = 300  # keeps every index line well under 4 KB (atomic append)
_TIMESTAMP = re.compile(rb'"timestamp"\s*:\s*"([^"]+)"')


def _debug(context, exc):
    # R-3: swallowed failures leave a breadcrumb when VIBE_DEBUG is set.
    if os.environ.get("VIBE_DEBUG"):
        print(f"vibe-debug[history] {context}: {type(exc).__name__}: {exc}",
              file=sys.stderr)


def _str_field(payload, key):
    # R-6: a field of the wrong shape is treated as absent.
    value = payload.get(key)
    return value if isinstance(value, str) else ""


def _archive_root():
    # Env override exists so tests never touch the real ~/.claude.
    return os.environ.get("VIBE_HISTORY_DIR") or os.path.join(
        os.path.expanduser("~"), ".claude", "vibe-history")


def _history_off(project_cwd):
    # Mirrors the auto_chain switch: only a parseable {"history": "off"}
    # disables; absent or malformed config keeps archiving ON (never lose
    # data because a config file broke).
    if not project_cwd:
        return False
    try:
        with open(os.path.join(project_cwd, ".vibe", "config.json"),
                  encoding="utf-8") as f:
            return json.load(f).get("history") == "off"
    except Exception as exc:
        _debug("reading .vibe/config.json", exc)
        return False


def _budget():
    raw = os.environ.get("VIBE_HISTORY_BUDGET_BYTES", "")
    try:
        limit = int(raw) if raw else DEFAULT_BUDGET_BYTES
    except ValueError as exc:
        _debug("parsing VIBE_HISTORY_BUDGET_BYTES", exc)
        limit = DEFAULT_BUDGET_BYTES
    return {"bytes": limit, "deadline": time.monotonic() + DEADLINE_SECONDS}


def _budget_allows(budget, size):
    return size <= budget["bytes"] and time.monotonic() < budget["deadline"]


def _needs_copy(src, dst):
    # copystat preserves mtime on the copy, so size+mtime_ns equality
    # means up-to-date — no checksum needed.
    try:
        s = os.stat(src)
    except OSError as exc:
        _debug(f"stat source {src}", exc)
        return False
    if not os.path.exists(dst):
        return True
    try:
        d = os.stat(dst)
    except OSError as exc:
        _debug(f"stat archived copy {dst}", exc)
        return True
    return (s.st_size, s.st_mtime_ns) != (d.st_size, d.st_mtime_ns)


def _head_cwd(path):
    """cwd recorded in the transcript's own first conversation lines.

    Flattened dir names are ambiguous ("-" collisions), so the transcript
    is the authority for which project a swept file belongs to.
    """
    try:
        with open(path, "rb") as f:
            for _ in range(HEAD_PARSE_LINES):
                raw = f.readline()
                if not raw:
                    break
                if b'"cwd"' not in raw:
                    continue
                try:
                    record = json.loads(raw)
                except Exception as exc:
                    _debug("parsing transcript head line", exc)
                    continue
                if isinstance(record, dict) and isinstance(record.get("cwd"), str):
                    return record["cwd"]
    except Exception as exc:
        _debug(f"head-scanning {path}", exc)
    return ""


def _new_extract():
    return {"cwd": "", "git_branch": "", "first_prompt": "", "title": "",
            "started_at": "", "last_ts": "", "num_lines": 0, "head_parsed": 0}


def _prompt_text(message):
    content = message.get("content") if isinstance(message, dict) else None
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and isinstance(block.get("text"), str):
                return block["text"].strip()
    return ""


def _feed(state, raw_line):
    """Extract index fields from one transcript line during the copy pass.

    Full json.loads only on the head lines and on ai-title lines; every
    other line pays a substring/regex check at most.
    """
    state["num_lines"] += 1
    match = _TIMESTAMP.search(raw_line)
    if match:
        ts = match.group(1).decode("utf-8", "replace")
        if not state["started_at"]:
            state["started_at"] = ts
        state["last_ts"] = ts
    need_head = ((not state["cwd"] or not state["first_prompt"])
                 and state["head_parsed"] < HEAD_PARSE_LINES)
    if not need_head and b'"ai-title"' not in raw_line:
        return
    try:
        record = json.loads(raw_line)
    except Exception as exc:
        _debug("parsing transcript line", exc)
        return
    if not isinstance(record, dict):
        return
    if need_head:
        state["head_parsed"] += 1
        if not state["cwd"] and isinstance(record.get("cwd"), str):
            state["cwd"] = record["cwd"]
            if isinstance(record.get("gitBranch"), str):
                state["git_branch"] = record["gitBranch"]
        if (not state["first_prompt"] and record.get("type") == "user"
                and record.get("isMeta") is not True
                and record.get("isSidechain") is not True):
            text = _prompt_text(record.get("message"))
            # Slash-command wrappers aren't the human's words — keep looking.
            if text and not text.startswith("<command-"):
                state["first_prompt"] = text[:TEXT_FIELD_LIMIT]
    if record.get("type") == "ai-title" and isinstance(record.get("aiTitle"), str):
        state["title"] = record["aiTitle"][:TEXT_FIELD_LIMIT]


def _copy_transcript(src, dst, budget):
    """Stream-copy src -> dst atomically, extracting index fields in the
    same single pass. Returns the extraction state, or None when skipped
    or failed (the caller then appends no index line)."""
    try:
        size = os.stat(src).st_size
    except OSError as exc:
        _debug(f"stat transcript {src}", exc)
        return None
    if not _budget_allows(budget, size):
        return None
    state = _new_extract()
    tmp_path = None
    try:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(dst),
                                        prefix="vibe-history-", suffix=".tmp")
        # R-4: temp file + os.replace — the archive never holds a
        # half-written copy that could stat as "in sync".
        with os.fdopen(fd, "wb") as out, open(src, "rb") as inp:
            for raw_line in inp:
                out.write(raw_line)
                _feed(state, raw_line)
        shutil.copystat(src, tmp_path)
        os.replace(tmp_path, dst)
    except Exception as exc:
        _debug(f"copying transcript {src}", exc)
        if tmp_path is not None:
            try:
                os.unlink(tmp_path)
            except Exception as cleanup_exc:
                _debug("removing temp copy", cleanup_exc)
        return None
    budget["bytes"] -= size
    return state


def _copy_file(src, dst, budget):
    """Plain atomic copy for sidecar files (no field extraction)."""
    try:
        size = os.stat(src).st_size
    except OSError as exc:
        _debug(f"stat sidecar {src}", exc)
        return False
    if not _budget_allows(budget, size):
        return False
    tmp_path = None
    try:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(dst),
                                        prefix="vibe-history-", suffix=".tmp")
        os.close(fd)
        shutil.copyfile(src, tmp_path)
        shutil.copystat(src, tmp_path)
        os.replace(tmp_path, dst)
    except Exception as exc:
        _debug(f"copying sidecar {src}", exc)
        if tmp_path is not None:
            try:
                os.unlink(tmp_path)
            except Exception as cleanup_exc:
                _debug("removing temp sidecar copy", cleanup_exc)
        return False
    budget["bytes"] -= size
    return True


def _mirror_sidecar(src_dir, dst_dir, budget):
    # Sidecar dirs (<sessionId>/ — subagents/, tool-results/, workflows/)
    # sync file-by-file on the same stat rule; they never touch the index.
    if os.path.islink(src_dir) or not os.path.isdir(src_dir):
        return
    for root, _dirs, files in os.walk(src_dir, followlinks=False):
        rel = os.path.relpath(root, src_dir)
        for name in files:
            src = os.path.join(root, name)
            if os.path.islink(src):
                continue
            dst = os.path.normpath(os.path.join(dst_dir, rel, name))
            if _needs_copy(src, dst):
                _copy_file(src, dst, budget)


def _append_index(root, entry):
    # A single write() on an O_APPEND handle; lines stay < 4 KB so
    # concurrent appends never interleave.
    try:
        os.makedirs(root, exist_ok=True)
        line = json.dumps(entry, ensure_ascii=False) + "\n"
        with open(os.path.join(root, "index.jsonl"), "a", encoding="utf-8") as f:
            f.write(line)
    except Exception as exc:
        _debug("appending index line", exc)


def _archive_session(archive_root, transcript_path, via, budget, payload_cwd=""):
    src = os.path.realpath(transcript_path)
    if not src.endswith(".jsonl") or not os.path.isfile(src):
        return
    root_real = os.path.realpath(archive_root)
    if src == root_real or src.startswith(root_real + os.sep):
        return  # never archive the archive itself
    project_cwd = payload_cwd or _head_cwd(src)
    if _history_off(project_cwd):
        return
    flat = os.path.basename(os.path.dirname(src))
    sid = os.path.basename(src)[:-len(".jsonl")]
    dst = os.path.join(archive_root, "projects", flat, sid + ".jsonl")

    state = None
    if _needs_copy(src, dst):
        state = _copy_transcript(src, dst, budget)

    sidecar_src = src[:-len(".jsonl")]
    has_sidecar = not os.path.islink(sidecar_src) and os.path.isdir(sidecar_src)
    if has_sidecar:
        _mirror_sidecar(sidecar_src, dst[:-len(".jsonl")], budget)

    if state is None:
        return  # nothing (re)copied — the index already reflects this state
    try:
        st = os.stat(dst)
        size_bytes, mtime_ns = st.st_size, st.st_mtime_ns
    except OSError as exc:
        _debug(f"stat fresh copy {dst}", exc)
        size_bytes, mtime_ns = 0, 0
    _append_index(archive_root, {
        "v": INDEX_VERSION,
        "session_id": sid,
        "project_dir": flat,
        "cwd": state["cwd"] or project_cwd,
        "git_branch": state["git_branch"] or None,
        "archived_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "started_at": state["started_at"] or None,
        "last_ts": state["last_ts"] or None,
        "size_bytes": size_bytes,
        "mtime_ns": mtime_ns,
        "num_lines": state["num_lines"],
        "title": state["title"] or None,
        "first_prompt": state["first_prompt"],
        "via": via,
        "has_sidecar": has_sidecar,
    })


def _sweep(archive_root, projects_root, budget):
    """Catch-up pass over every project dir: rescues hard-killed sessions
    and backfills, converging over a few session starts under the budget."""
    root_real = os.path.realpath(archive_root)
    try:
        project_dirs = sorted(os.listdir(projects_root))
    except OSError as exc:
        _debug(f"listing projects root {projects_root}", exc)
        return
    for flat in project_dirs:
        proj_dir = os.path.join(projects_root, flat)
        if not os.path.isdir(proj_dir):
            continue
        proj_real = os.path.realpath(proj_dir)
        if proj_real == root_real or proj_real.startswith(root_real + os.sep):
            continue
        try:
            names = sorted(os.listdir(proj_dir))
        except OSError as exc:
            _debug(f"listing {proj_dir}", exc)
            continue
        for name in names:
            if not name.endswith(".jsonl"):
                continue
            if budget["bytes"] <= 0 or time.monotonic() >= budget["deadline"]:
                return  # budget exhausted — the next sweep resumes for free
            _archive_session(archive_root, os.path.join(proj_dir, name),
                             "sweep", budget)


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception as exc:
        _debug("parsing stdin payload", exc)
        return
    if not isinstance(payload, dict):
        return

    event = _str_field(payload, "hook_event_name")
    if event not in ("SessionStart", "SessionEnd"):
        return
    transcript = _str_field(payload, "transcript_path")
    if not transcript:
        return

    archive_root = _archive_root()
    budget = _budget()
    via = "end" if event == "SessionEnd" else "start"
    _archive_session(archive_root, transcript, via, budget,
                     payload_cwd=_str_field(payload, "cwd"))

    if event == "SessionStart":
        # Projects root is derived from the transcript's own location —
        # no second knob, and tests get a fully fake tree for free.
        projects_root = os.path.dirname(os.path.dirname(os.path.realpath(transcript)))
        if os.path.isdir(projects_root):
            _sweep(archive_root, projects_root, budget)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # an archiver must never brick the session
        _debug("unhandled failure", exc)
