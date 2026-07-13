---
problem: Live-verifying a web UI from WSL2 with no Linux browser — Windows
  Chrome exists but Playwright can't drive it; naive setups also download
  a ~400 MB browser or silently npm-fetch from a foreign cwd.
solution: Never bridge to Windows Chrome; install chromium-headless-shell
  under a toolkit-local PLAYWRIGHT_BROWSERS_PATH and run specs from a
  run dir inside the toolkit via the absolute .bin/playwright.
rules: [WA-12, WA-14, WA-15, D-2]
---

Proven by execution (spike 2026-07-13, WSL2 NAT):

- Windows chrome.exe binds CDP to the Windows-side 127.0.0.1 and ignores
  `--remote-debugging-address=0.0.0.0` — confirmed listening via
  powershell yet unreachable from WSL via localhost and the gateway IP.
  Don't ship a bridge branch; go straight to headless shell.
- `PLAYWRIGHT_BROWSERS_PATH` must be exported at RUN time too, not just
  during `playwright install`, or the runner looks in ~/.cache.
- The plain `playwright` npm package ships the runner; import from
  `'playwright/test'`. Force `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1`.
- Positional args to `playwright test` only filter files under `testDir`
  — put spec+config in a run dir under the toolkit and invoke the
  absolute `node_modules/.bin/playwright` (npx from a foreign cwd
  silently fetches from the registry).
- Streaming (SSE) checks: assert stream-open headers via waitForResponse
  (resolves on headers), then the rendered DOM text with a long timeout.
