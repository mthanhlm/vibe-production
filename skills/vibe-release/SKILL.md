---
name: vibe-release
description: Maintainer-only release automation — validate the plugin, bump the semver, commit and push, then refresh the locally-installed copy through the marketplace (never --plugin-dir).
disable-model-invocation: true
user-invocable: false
---

# /vibe:release — publish a new version to your own machine

Personal automation for the plugin maintainer. Run from the plugin repo
root. The installed copy updates **via the marketplace** — explicit semver
in plugin.json pins installs, so no bump = no update, even after a push.

Arguments: $ARGUMENTS — `patch` (default) | `minor` | `major`, optionally
followed by a short release note for the commit message.

## Steps — stop at the first failure, report it, fix before retrying

1. **Preflight.** Confirm cwd is the plugin repo (`.claude-plugin/plugin.json`
   with `"name": "vibe"` exists). Run `claude plugin validate --strict .` —
   abort on failure. Show `git status --short`; if it includes files that
   look unrelated to the release, ask before sweeping them into the commit.
2. **Bump.** Read `version` from `.claude-plugin/plugin.json`, bump per the
   argument (default patch), write it back.
3. **Commit.** `VIBE_GIT=allow git add -A` then
   `VIBE_GIT=allow git commit -m "release: v<new version> — <note>"`.
   (The git guard requires user approval for add/commit/push; the user
   invoking /vibe:release IS that approval — hence the prefix.)
4. **Push.** If a remote is configured: `VIBE_GIT=allow git push` (never
   force). If none, say so and continue — a local marketplace works from
   the local repo.
5. **Refresh the installed copy** (marketplace path, NOT --plugin-dir):
   ```bash
   claude plugin marketplace update vibe-marketplace
   claude plugin update vibe@vibe-marketplace
   ```
   If either subcommand is missing on this CLI version, run
   `claude plugin --help` and use the current equivalents; as a last resort
   tell the user to run `/plugin marketplace update vibe-marketplace` then
   `/plugin update vibe` interactively.
6. **Verify + report.** `claude plugin list 2>/dev/null | grep -i vibe` (or
   the help-discovered equivalent) to confirm the new version is installed.
   Report old → new version and remind: running sessions need
   `/reload-plugins` or a restart to pick it up.
