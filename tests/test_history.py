"""Subprocess-level tests for scripts/history.py (WA-4).

Every test builds a fake ~/.claude/projects tree in a tempdir and points
VIBE_HISTORY_DIR at a scratch archive, so the real ~/.claude is never
touched. The projects root is derived by the script from transcript_path.
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hookrunner import run_hook

FLAT = "-home-user-projA"
SID = "aaaaaaaa-1111-2222-3333-444444444444"


def records(cwd, prompt="add a login page to the app", title="Login page work"):
    return [
        {"type": "summary", "summary": "earlier work"},
        {"type": "user", "cwd": cwd, "gitBranch": "main", "sessionId": SID,
         "timestamp": "2026-07-12T08:00:00Z",
         "message": {"role": "user", "content": prompt}},
        {"type": "assistant", "timestamp": "2026-07-12T08:00:05Z",
         "message": {"role": "assistant",
                     "content": [{"type": "text", "text": "ok"}]}},
        {"type": "ai-title", "aiTitle": title, "sessionId": SID},
    ]


class HistoryBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.projects = os.path.join(self.tmp.name, "claude", "projects")
        self.archive = os.path.join(self.tmp.name, "archive")
        self.work = os.path.join(self.tmp.name, "work")
        os.makedirs(self.projects)
        os.makedirs(self.work)
        self.env = {"VIBE_HISTORY_DIR": self.archive}

    def write_transcript(self, flat=FLAT, sid=SID, cwd=None, lines=None):
        proj = os.path.join(self.projects, flat)
        os.makedirs(proj, exist_ok=True)
        path = os.path.join(proj, sid + ".jsonl")
        with open(path, "w") as f:
            for rec in (lines or records(cwd or self.work)):
                f.write(json.dumps(rec) + "\n")
        return path

    def payload(self, transcript, event="SessionEnd", cwd=None):
        return {"session_id": SID, "transcript_path": transcript,
                "cwd": cwd or self.work, "hook_event_name": event}

    def run_history(self, payload, env=None):
        full = dict(self.env)
        if env:
            full.update(env)
        return run_hook("history.py", payload, env=full)

    def archived(self, flat=FLAT, sid=SID):
        return os.path.join(self.archive, "projects", flat, sid + ".jsonl")

    def index_lines(self):
        path = os.path.join(self.archive, "index.jsonl")
        if not os.path.exists(path):
            return []
        with open(path) as f:
            return [json.loads(line) for line in f if line.strip()]


class TestArchiveOnSessionEnd(HistoryBase):
    def test_session_end_archives_transcript(self):
        src = self.write_transcript()
        rc, out, err = self.run_history(self.payload(src))
        self.assertEqual((rc, out, err), (0, "", ""))
        with open(src, "rb") as f_src, open(self.archived(), "rb") as f_dst:
            self.assertEqual(f_src.read(), f_dst.read())

    def test_index_line_has_schema_fields(self):
        src = self.write_transcript()
        self.run_history(self.payload(src))
        lines = self.index_lines()
        self.assertEqual(len(lines), 1)
        entry = lines[0]
        self.assertEqual(entry["v"], 1)
        self.assertEqual(entry["session_id"], SID)
        self.assertEqual(entry["project_dir"], FLAT)
        self.assertEqual(entry["cwd"], self.work)
        self.assertEqual(entry["git_branch"], "main")
        self.assertEqual(entry["started_at"], "2026-07-12T08:00:00Z")
        self.assertEqual(entry["last_ts"], "2026-07-12T08:00:05Z")
        self.assertEqual(entry["size_bytes"], os.path.getsize(src))
        self.assertEqual(entry["num_lines"], 4)
        self.assertEqual(entry["title"], "Login page work")
        self.assertEqual(entry["first_prompt"], "add a login page to the app")
        self.assertEqual(entry["via"], "end")
        self.assertFalse(entry["has_sidecar"])

    def test_sidecar_subagent_dir_copied(self):
        src = self.write_transcript()
        sidecar = os.path.join(self.projects, FLAT, SID, "subagents")
        os.makedirs(sidecar)
        with open(os.path.join(sidecar, "x.jsonl"), "w") as f:
            f.write('{"type":"assistant"}\n')
        rc, _, _ = self.run_history(self.payload(src))
        self.assertEqual(rc, 0)
        copy = os.path.join(self.archive, "projects", FLAT, SID,
                            "subagents", "x.jsonl")
        with open(copy) as f:
            self.assertEqual(f.read(), '{"type":"assistant"}\n')
        self.assertTrue(self.index_lines()[0]["has_sidecar"])


class TestIdempotence(HistoryBase):
    def test_unchanged_rerun_is_noop(self):
        src = self.write_transcript()
        self.run_history(self.payload(src))
        first_mtime = os.stat(self.archived()).st_mtime_ns
        rc, out, err = self.run_history(self.payload(src))
        self.assertEqual((rc, out, err), (0, "", ""))
        self.assertEqual(os.stat(self.archived()).st_mtime_ns, first_mtime)
        self.assertEqual(len(self.index_lines()), 1)

    def test_modified_transcript_recopied_and_reindexed(self):
        src = self.write_transcript()
        self.run_history(self.payload(src))
        with open(src, "a") as f:
            f.write(json.dumps({"type": "user", "timestamp": "2026-07-12T09:00:00Z",
                                "message": {"role": "user", "content": "more"}}) + "\n")
        self.run_history(self.payload(src))
        with open(src, "rb") as f_src, open(self.archived(), "rb") as f_dst:
            self.assertEqual(f_src.read(), f_dst.read())
        lines = self.index_lines()
        self.assertEqual(len(lines), 2)
        latest = lines[-1]  # readers dedup latest-wins by session_id
        self.assertEqual(latest["num_lines"], 5)
        self.assertEqual(latest["last_ts"], "2026-07-12T09:00:00Z")


class TestSweep(HistoryBase):
    def test_session_start_sweeps_sibling_projects(self):
        src = self.write_transcript()
        orphan_sid = "bbbbbbbb-1111-2222-3333-444444444444"
        self.write_transcript(flat="-home-user-projB", sid=orphan_sid)
        rc, out, err = self.run_history(self.payload(src, event="SessionStart"))
        self.assertEqual((rc, out, err), (0, "", ""))
        self.assertTrue(os.path.exists(self.archived()))
        self.assertTrue(os.path.exists(
            self.archived(flat="-home-user-projB", sid=orphan_sid)))
        via = {e["session_id"]: e["via"] for e in self.index_lines()}
        self.assertEqual(via[SID], "start")
        self.assertEqual(via[orphan_sid], "sweep")

    def test_sweep_respects_byte_budget(self):
        src = self.write_transcript()
        self.write_transcript(flat="-home-user-projB",
                              sid="bbbbbbbb-1111-2222-3333-444444444444")
        rc, out, err = self.run_history(
            self.payload(src, event="SessionStart"),
            env={"VIBE_HISTORY_BUDGET_BYTES": "1"})
        self.assertEqual((rc, out, err), (0, "", ""))
        self.assertFalse(os.path.exists(os.path.join(self.archive, "projects")))
        self.assertEqual(self.index_lines(), [])


class TestOptOut(HistoryBase):
    def opted_out_project(self):
        proj = os.path.join(self.tmp.name, "optout")
        os.makedirs(os.path.join(proj, ".vibe"), exist_ok=True)
        with open(os.path.join(proj, ".vibe", "config.json"), "w") as f:
            json.dump({"history": "off"}, f)
        return proj

    def test_history_off_skips_current_project(self):
        proj = self.opted_out_project()
        src = self.write_transcript(cwd=proj)
        rc, out, err = self.run_history(self.payload(src, cwd=proj))
        self.assertEqual((rc, out, err), (0, "", ""))
        self.assertFalse(os.path.exists(self.archive))

    def test_sweep_skips_opted_out_project(self):
        proj = self.opted_out_project()
        src = self.write_transcript()
        opted_sid = "cccccccc-1111-2222-3333-444444444444"
        self.write_transcript(flat="-home-user-optout", sid=opted_sid, cwd=proj)
        rc, _, _ = self.run_history(self.payload(src, event="SessionStart"))
        self.assertEqual(rc, 0)
        self.assertTrue(os.path.exists(self.archived()))
        self.assertFalse(os.path.exists(
            self.archived(flat="-home-user-optout", sid=opted_sid)))


class TestNeverBricks(HistoryBase):
    def test_malformed_stdin_is_silent_noop(self):
        rc, out, err = self.run_history("this is not json")
        self.assertEqual((rc, out, err), (0, "", ""))
        self.assertFalse(os.path.exists(self.archive))

    def test_missing_transcript_path_noop(self):
        rc, out, err = self.run_history(
            {"session_id": SID, "cwd": self.work,
             "hook_event_name": "SessionEnd"})
        self.assertEqual((rc, out, err), (0, "", ""))
        self.assertFalse(os.path.exists(self.archive))

    @unittest.skipIf(os.geteuid() == 0, "chmod 000 is not a barrier for root")
    def test_unreadable_source_skipped_sweep_continues(self):
        src = self.write_transcript()
        blocked_sid = "dddddddd-1111-2222-3333-444444444444"
        blocked = self.write_transcript(flat="-home-user-projB", sid=blocked_sid)
        os.chmod(blocked, 0)
        self.addCleanup(os.chmod, blocked, 0o644)
        rc, out, err = self.run_history(self.payload(src, event="SessionStart"))
        self.assertEqual((rc, out, err), (0, "", ""))
        self.assertTrue(os.path.exists(self.archived()))
        self.assertFalse(os.path.exists(
            self.archived(flat="-home-user-projB", sid=blocked_sid)))
        # Same failure with VIBE_DEBUG=1 leaves a breadcrumb (WA-6).
        rc, _, err = self.run_history(self.payload(src, event="SessionStart"),
                                      env={"VIBE_DEBUG": "1"})
        self.assertEqual(rc, 0)
        self.assertIn("vibe-debug[history]", err)


if __name__ == "__main__":
    unittest.main()
