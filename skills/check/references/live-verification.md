# Live verification — how to actually drive the feature

Goal: observe the real feature behaving, with **zero new installs by
default**. Work down this ladder and stop at the first rung that works.

## 1. Reuse what the repo already has

- An existing e2e/integration setup (Playwright or Cypress in
  devDependencies, `npm run test:e2e`, a Makefile target, pytest markers)
  → run THAT. Never bring a second tool when the project already chose one.
- The project's own entry points: dev-server script, seed script, CLI
  binary, fixtures.

## 2. Built-ins that need no install

- CLI features: run the real command with real input; evidence = exit code
  + decisive output lines.
- Hooks/daemons: pipe a real payload into the real process
  (`echo '{...}' | python3 scripts/<hook>.py`), point state at a scratch
  dir via the feature's env overrides.
- HTTP/APIs: start the server, probe with `curl --max-time 10`; parse JSON
  with `python3 -m json.tool` (always present) or `jq` if installed.
- Web UIs without installing anything: if a browser binary exists
  (`command -v google-chrome chromium chromium-browser msedge`), headless
  flags replace a framework: `--headless=new --dump-dom <url>` for the
  rendered DOM, `--screenshot=<path> <url>` for visual evidence. SPAs may
  render after the load event — add `--virtual-time-budget=5000` before
  `--dump-dom`, and when the dump looks empty treat the screenshot as the
  decisive evidence.

## 3. Real browser automation — consent-gated, no browser download

- A web UI needing real interaction (clicks, forms, multi-step flows)
  beyond rung 2's flags → read `references/playwright-cli.md` (bundled):
  the consent-gated Playwright toolkit — one global npm package driving
  the user's own Chrome; a browser is never downloaded on the default
  path, and nothing installs without the user's OK.
- If the user declines, or no drivable browser exists: mark that criterion
  **UNVERIFIABLE-live** in the report and give the user the exact manual
  steps to click through — the user becomes the driver. Honest beats
  silent skipping.

## Docker projects

- A repo Dockerfile / compose file IS the natural driver:
  `docker compose up -d --build` → bounded readiness loop (healthcheck or
  `curl` retry, ≤ ~60 s) → run the probes against the mapped port →
  **always** `docker compose down -v`, on failure too.
- No Docker daemon available → run the service directly (rung 2) or
  UNVERIFIABLE-live.

## Never get stuck

- Every live command gets an explicit bound, scaled to the operation:
  probes `--max-time 10`, server start ≤ ~60 s (retry loop, e.g. 30 × 1 s),
  image builds minutes (`timeout 300 docker compose up -d --build`).
- Background what you start WITH output captured
  (`<cmd> > "$SCRATCH/server.log" 2>&1 &`), remember the PID, kill it when
  done — also on the failure path (`trap 'kill $PID' EXIT`).
- Readiness never comes → capture the last ~30 log lines as evidence,
  report FAIL (or UNVERIFIABLE-live if the environment, not the feature,
  is at fault; unsure which → FAIL and state the doubt), clean up, move
  on. No infinite waits, no orphan processes.

## Complex features

- Drive the thinnest true slice: ONE happy path + the riskiest unhappy
  path named in the plan's Verification section. This is a check, not a
  regression suite.
- Seed the minimum data; never point at production.
- A dependency that can't run locally may be faked — the feature itself
  never is; say in the report what was faked.

## Evidence

Quote exit codes, the decisive output lines, and screenshot paths in the
check report. A live result that contradicts a test result is a FAIL.
