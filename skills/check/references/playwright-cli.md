# Playwright via CLI — driving a web UI for real (consent-gated)

Loaded from live-verification.md rung 3 when a web feature needs real
interaction (clicks, forms, multi-step flows) that headless-Chrome flags
can't drive. Everything here ran successfully on a real machine before it
was written down. **No browser is ever downloaded on the default path** —
Playwright's npm package drives the Chrome/Edge/Chromium the user already
has.

## 1. Consent first (WA-12)

Read the `e2e` key from the target project's `.vibe/config.json`. The key
gates the *feature*; the toolkit's presence on disk
(`~/.claude/vibe-e2e/node_modules/playwright`) is the *machine-local*
consent — config.json is team-shared, so a key committed by a teammate is
never a license to install on this machine.

| config key | toolkit on disk | do |
|---|---|---|
| `"e2e": "playwright-chrome"` | yes | proceed silently |
| `"e2e": "playwright-chrome"` | no | ask one line: "This project enables browser E2E; install the toolkit to ~/.claude/vibe-e2e now? One npm package, no browser download." Decline → rung 2 / UNVERIFIABLE-live; leave config alone |
| absent | — | ask once. Yes → record `"e2e": "playwright-chrome"` and install. No → record `"e2e": "none"` (that's what makes "asked once per project" true) and fall back |
| `"e2e": "none"` | — | user already declined — rung 2 / UNVERIFIABLE-live, don't re-ask |

## 2. Toolkit setup

```bash
vibe-e2e-setup            # bundled; idempotent, ~50 MB npm package, no browser
```

(The plugin's `bin/` is on PATH; if the name doesn't resolve, run it from
the plugin root: `<plugin>/bin/vibe-e2e-setup`.)

It prints exactly one `CAPABILITY: chrome|chromium|msedge|headless-shell|none`
line — branch on it:

| CAPABILITY | config `use:` addition |
|---|---|
| `chrome` | `channel: 'chrome'` |
| `msedge` | `channel: 'msedge'` |
| `chromium` | `launchOptions: { executablePath: '<command -v chromium chromium-browser \| head -1>' }` |
| `headless-shell` | nothing extra; export `PLAYWRIGHT_BROWSERS_PATH="$HOME/.claude/vibe-e2e/browsers"` when running |
| `none` | see §6 |

## 3. Throwaway spec + config — always in a run dir under the toolkit

Never write test files into the target project, and **never run npx from
the target project** (npx in a foreign cwd silently fetches packages from
the registry). The run dir keeps module resolution working: node walks up
from `runs/<id>/` to the toolkit's `node_modules`.

```bash
E2E="$HOME/.claude/vibe-e2e"
mkdir -p "$E2E/runs"          # older toolkit installs may lack it
RUN=$(mktemp -d "$E2E/runs/XXXXXX")
EVID="<project>/.vibe/evidence/$(date +%F)-<plan-slug>"; mkdir -p "$EVID"
```

`$RUN/playwright.config.js` (proven template — keep every knob):

```js
const { defineConfig } = require('playwright/test');
module.exports = defineConfig({
  testDir: __dirname,
  outputDir: '<absolute $EVID>',
  workers: 1, retries: 0, timeout: 15000, globalTimeout: 240000,
  reporter: [['line']],                     // never html — it opens a server
  use: { headless: true, screenshot: 'on', trace: 'retain-on-failure',
         /* + the CAPABILITY row from §2 */ },
});
```

`$RUN/verify.spec.js` — derive from the plan's Verification section, the
thinnest true slice: ONE happy path + the riskiest unhappy path (read the
page/template source for real selectors — don't guess ids). Import
from `'playwright/test'` (the plain `playwright` package ships the runner):

```js
const { test, expect } = require('playwright/test');
test('happy path from the plan', async ({ page }) => {
  await page.goto('http://127.0.0.1:<port>/');
  await expect(page.locator('h1')).toHaveText('…');
  // click / fill / submit per the plan's Verification section
});
```

Async UIs (chatbots, background jobs): assert on the network call, never
on sleeps — register the wait BEFORE the click that triggers it:

```js
const respP = page.waitForResponse(
  r => r.url().includes('/api/chat') && r.request().method() === 'POST',
  { timeout: 60000 });
await page.click('#send');
const resp = await respP;
expect(resp.status()).toBe(200);          // the POST was made and answered
await expect(page.locator('#reply')).toContainText('…');  // and rendered
```

Raise the config `timeout` above the slowest expected response (an LLM
reply can take longer than the 15 s default).

Streaming replies (SSE / fetch-streamed): the chunks aren't readable via
`waitForResponse` — assert the stream OPENED (status + content-type),
then assert the *rendered* text the user ends up seeing, with a timeout
longer than the whole stream:

```js
const respP = page.waitForResponse(
  r => r.url().includes('/api/stream'), { timeout: 60000 });
await page.click('#send');
const resp = await respP;                 // resolves on headers, not stream end
expect(resp.status()).toBe(200);
expect(resp.headers()['content-type']).toContain('text/event-stream');
await expect(page.locator('#reply')).toContainText('<final text>', { timeout: 60000 });
```

(WebSocket transports need `page.on('websocket')` instead — unproven in
this recipe; prove it by execution before relying on it.)

## 4. Run — bounded, exit code captured directly

Start the dev server per live-verification.md's "Never get stuck"
discipline (background with log capture, readiness loop ≤ ~60 s, trap
kill). Then:

```bash
timeout 300 "$E2E/node_modules/.bin/playwright" test \
  --config="$RUN/playwright.config.js" > "$SCRATCH/e2e.log" 2>&1
RC=$?   # capture immediately — piping the run through tail/grep eats the code
```

For `headless-shell` capability, prefix the invocation with
`PLAYWRIGHT_BROWSERS_PATH="$E2E/browsers"` — required at run time, not
just at install time, or the runner looks in `~/.cache/ms-playwright`.

## 5. Evidence, then teardown

- Quote in the check report: `RC`, the decisive lines of
  `$SCRATCH/e2e.log`, and the PNG path(s) — under
  `$EVID/<abbreviated-test-dir>/test-finished-1.png` (Playwright shortens
  the dir name; find them with `find "$EVID" -name '*.png'`); on failure a
  `trace.zip` sits beside them (inspect with `…/.bin/playwright show-trace <zip>` only if
  the user asks — it opens a GUI).
- A live result that contradicts a test result is a FAIL.
- Teardown: kill the dev server (also on the failure path), then
  `rm -rf "$RUN"` — evidence stays, the throwaway spec does not. The
  target repo must show changes only under `.vibe/`
  (`git status --porcelain`).
- Traces are zips and evidence accumulates: offer once to add an
  `evidence/` line to `.vibe/.gitignore` (a file the project may not have
  yet) — the user decides; don't touch the root `.gitignore`.

## 6. CAPABILITY: none — no drivable browser

- Offer, as a second consent (~100 MB download):
  `vibe-e2e-setup --headless-shell` — its CAPABILITY line becomes
  `headless-shell`; continue at §2's table. (On WSL, never try to drive a
  Windows-side chrome.exe instead — CDP across the NAT boundary was
  proven unreachable: Chrome binds 127.0.0.1 on the Windows side and
  ignores `--remote-debugging-address`.)
- No browser and the user declines the shell (or no node/npm at all):
  mark the criterion **UNVERIFIABLE-live** and hand the user exact manual
  steps — URL to open, thing to click, what they should see. Honest beats
  silent skipping.
