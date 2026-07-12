---
problem: Claude Code prunes ~/.claude/projects transcripts after 30 days and
  SessionEnd never fires on a hard kill, so any single-event archiver loses
  sessions silently.
solution: Pair SessionEnd (archive current) with a SessionStart catch-up
  sweep under a byte+time budget; stat compare (size + mtime_ns after
  copystat) makes sync stateless and resumable.
rules: [WA-6, WA-10, WA-11, R-4, R-9]
---

The sweep needs no cursor: copystat preserves mtime on the copy, so
size+mtime_ns equality IS the "already archived" marker, and an exhausted
budget just means the next session start resumes for free (52 MB / 0.8 s
per run measured; 420 sessions backfill in ~16 starts). Extract index
fields (title, first prompt, timestamps) during the copy stream — a second
parse pass is never needed. Keep index lines < 4 KB and append-only with
latest-wins-by-session_id so concurrent hooks need no lock; the index is a
rebuildable cache and the raw byte-identical copies are the only truth.
Derive every path from real directory listings, never payload strings —
R-9 by construction instead of by sanitizer. A live-payload smoke test
caught what fixtures couldn't: first_prompt captured a `<command-name>`
wrapper, not the human's words. Always smoke against one real transcript.
